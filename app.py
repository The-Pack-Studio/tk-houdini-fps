from tank.platform import Application

import hou

class TkHouFpsHandler(Application):

    def init_app(self):
        """Initialize the handler.
        
        :params app: The application instance. 
        
        """
        
        # get configuration
        self._default_fps = self.get_setting('default_fps')
        self._shotgun_fps_field = self.get_setting('shotgun_fps_field')
        
        # run the method when the app is started
        self.fps_scene_opened()

        # add callback
        hou.hipFile.addEventCallback(self.hou_callback)
        self.log_info("Creating file callback for the TkHouFpsHandler!")

    @property
    def context_change_allowed(self):
        """
        Specifies that context changes are allowed.
        """
        return True


    def destroy_app(self):
        """
        Called when the app is unloaded/destroyed
        """
        self.log_debug("Destroying tk-houdini-fps app")

        hou.hipFile.removeEventCallback(self.hou_callback)



    ###############################################################################################
    # implementation

    def hou_callback(self, event_type):
        if event_type == hou.hipFileEventType.AfterLoad:
            self.fps_scene_opened()
            self.check_frame_range()



    def fps_scene_opened(self):
        # get shotgun project fps
        project = self.context.project
        sg_filters = [['id', 'is', project['id']]]
        project_fps = self.sgtk.shotgun.find_one('Project', filters=sg_filters, fields=[self._shotgun_fps_field])[self._shotgun_fps_field]
        
        # force to self._default_fps if not defined in Shotgun
        if not project_fps:
            project_fps = self._default_fps
            self.log_warning("Shotgun project fps is not defined, assuming it should be {}".format(self._default_fps))
        
        if project_fps != hou.fps():
            # check if scene is not empty
            if (len(hou.node('/obj').children()) + len(hou.node('/stage/').children())) != 0:
                self.log_info("Detected that Houdini fps does not match the Shotgun project fps!")
                
                if hou.isUIAvailable():
                    # Prompt the user if they want to change the fps, return if negative
                    if hou.ui.displayMessage("The current hip file fps ({}) does not match the Shotgun project fps ({})!\nChange FPS?".format(hou.fps(), project_fps), buttons=("Yes", "No")) != 0:
                        return
                else:
                    # No UI - rendering in deadline but with a difference between Houdini FPS and ShotGrid FPS ; let's crash the render
                    self.log_error("Error: The frame rate in ShotGrid is: {}fps, the one in the Houdini scene is: {}fps. I'm resigning".format(project_fps, hou.fps()))


            hou.setFps(project_fps)


    def check_frame_range(self):
        '''
        Compare the frame range inside Houdini with the frame range of ShotGrid
        '''

        set_framerange_app = self.engine.apps.get("tk-multi-setframerange")
        if not set_framerange_app:
            return None


        in_frame, out_frame, head_frame, tail_frame = set_framerange_app.get_frame_range_from_shotgun()

        current_in, current_out, current_head, current_tail = set_framerange_app.get_current_frame_range()

        # If no values or missing values in SG, skip
        if (not head_frame 
            or not tail_frame
            or not in_frame
            or not out_frame):

            return None


        if (current_in != in_frame or 
            current_out != out_frame or
            current_head != head_frame or
            current_tail != tail_frame):

            message_text = ("The frame range has been modified in ShotGrid\n"
                            "since you last saved this file.\n\n"
                            "Do you want to sync the frame range ?"
                            )

            message = hou.ui.displayMessage(message_text, buttons=("OK", "Cancel"), severity=hou.severityType.Warning)

            if message == 0:
                set_framerange_app.run_app()
            