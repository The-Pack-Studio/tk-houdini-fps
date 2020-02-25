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

    ###############################################################################################
    # implementation

    def hou_callback(self, event_type):
        if event_type == hou.hipFileEventType.AfterLoad or event_type == hou.hipFileEventType.AfterSave:
            self.fps_scene_opened()

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
            if len(hou.node('/obj').children()) != 0:
                self.log_info("Detected that Houdini fps does not match the Shotgun project fps!")
                
                # Prompt the user if they want to change the fps, return if negative
                if hou.ui.displayMessage("The current hip file fps ({}) does not match the Shotgun project fps ({})!\nChange FPS?".format(hou.fps(), project_fps), buttons=("Yes", "No")) != 0:
                    return
                    
            hou.setFps(project_fps)