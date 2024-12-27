# Python Configuration file for NDISELECTOR
import PySimpleGUI as Sg
import os
import sys
import gc

def restart_program():
    """Restart the current program """
    python = sys.executable
    os.execv(python, ['python'] + sys.argv)


class Config:
    def __init__(self):
        self.user_settings = Sg.UserSettings()
        self._camera_count = self.user_settings.get("-CAMERACOUNT-", 7)
        self._relay_port_base = self.user_settings.get("-RELAYPORT-", 10001)

    def camera_count(self):
        return self._camera_count

    def relay_port_base(self):
        return self._relay_port_base

    def save_camera_state(self, statetuple):
        self.user_settings["-CAMSTATE-"] = statetuple

    def load_camera_state(self):
        statetuple = self.user_settings.get("-CAMSTATE-", (None, None))
        return statetuple

    def configure(self):
        # Run dialog to set configuration parameters
        # this will restart the program if parameters change

        layout = [
                  [Sg.Text('Camera Count '), Sg.Input(default_text=str(self._camera_count),
                                                      key='CAMERACOUNT', size=4),],
                  [Sg.Button('Save&Exit'), Sg.Button('Cancel')]
                  ]
        window = Sg.Window(title='Configure', layout=layout, finalize=True, keep_on_top=True)
        while True:
            event, values = window.read()

            if event == 'Cancel' or event == Sg.WINDOW_CLOSED:
                break

            elif event == 'Save&Exit':
                self.user_settings['-CAMERACOUNT-'] = int(values['CAMERACOUNT'])
                window.close()
                sys.exit(0)

        window.close()
        # 'fix' for PySimpleGUI/Tkintr issue with threading
        layout = None
        Window = None
        gc.collect()



