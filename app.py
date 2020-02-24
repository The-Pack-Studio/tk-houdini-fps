from tank.platform import Application

import hou

class TkHouFpsHandler(Application):

    def init_app(self):
        """Initialize the handler.
        
        :params app: The application instance. 
        
        """

        # keep a reference to the app for easy access to templates, settings,
        # logging methods, tank, context, etc.
        self.fps_scene_opened() # run the method when the app is started
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
        # compare maya scene fps and shotgun project fps. If the maya scene is new/empty set it's framerate to the shotgun project fps without
        # asking the user. If scene is not new (has already objects) warn the user and give him the choice
        # to either leave the maya scene fps unchanged or to change it to the shotgun project fps.

        project = self.context.project
        sg_filters = [['id', 'is', project['id']]]
        project_fps = self.sgtk.shotgun.find_one('Project', filters=sg_filters, fields=["sg_projectfps"])['sg_projectfps']
        
        # force to 25 if not defined in Shotgun
        if not project_fps:
            project_fps = 25.0
            self.log_warning("Shotgun project fps is not defined, assuming it should be 25.0")
        
        if project_fps != hou.fps():
            # check if scene is not empty
            if len(hou.node('/obj').children()) != 0:
                self.log_info("Detected that Houdini fps does not match the Shotgun project fps!")
                
                # Prompt the user if they want to change the fps, return if negative
                if hou.ui.displayMessage("The current hip file fps ({}) does not match the Shotgun project fps ({})!\nChange FPS?".format(hou.fps(), project_fps), buttons=("Yes", "No")) != 0:
                    return
                    
            hou.setFps(project_fps)