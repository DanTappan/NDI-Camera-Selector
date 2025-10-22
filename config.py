# Python Configuration file for NDISELECTOR
import PySimpleGUI as Sg
import os
import sys
import gc

ProgName = 'NDI Camera Selector'
ProgVers = "1.0beta1"

credits_text = """
Dan Tappan (https://dantappan.net) - (c) 2024, 2025

Written/debugged using PyCharm Community Edition
    https://www.jetbrains.com/pycharm/

NDI Support: 
    ndi-python (https://github.com/buresu/ndi-python)

Graphical interface: 
    PySimpleGUI-foss 
    https://github.com/andor-pierdelacabeza/PySimpleGUI-4-foss
    psgtray-foss

Icon based on: 
    https://www.flaticon.com/free-icons/ptz-camera
    created by Freepik
 """

def restart_program():
    """Restart the current program """
    python = sys.executable
    os.execv(python, ['python'] + sys.argv)

class Config:
    def __init__(self):
        self.user_settings = Sg.UserSettings()
        self._camera_count = self.user_settings.get("-CAMERACOUNT-", 7)
        self._relay_port_base = self.user_settings.get("-RELAYPORT-", 10001)
        self._bitfocus_enable = self.user_settings.get('-BITFOCUSENABLE-', False)
        self._bitfocus_target = self.user_settings.get('-BITFOCUSTARGET-', '127.0.0.1')
        self._bitfocus_page = self.user_settings.get('-BITFOCUSPAGE-', '0')
        # pattern for the sources we advertise
        # TODO: make this configurable
        self._cam_name = "@CAM"

    def cam_name(self):
        return self._cam_name

    def camera_count(self):
        return self._camera_count

    def relay_port_base(self):
        return self._relay_port_base

    def bitfocus_info(self):
        if self._bitfocus_enable:
            return [self._bitfocus_target, self._bitfocus_page]
        else:
            return None

    def save_camera_state(self, statetuple):
        self.user_settings["-CAMSTATE-"] = statetuple

    def load_camera_state(self):
        statetuple = self.user_settings.get("-CAMSTATE-", (None, None))
        return statetuple

    @property
    def credits_text(self):
        return f"{ProgName} {ProgVers}\n" + credits_text

    def configure(self):
        # Run dialog to set configuration parameters
        # this will restart the program if parameters change

        layout = [
                  [Sg.Text(f"{ProgName} version {ProgVers}")],
                  [Sg.Text('Camera Count '), Sg.Input(default_text=str(self._camera_count),
                                                      key='CAMERACOUNT', size=4),],
                  [Sg.Checkbox('Enable Bitfocus Companion Interface',
                               default=self._bitfocus_enable, key='BITFOCUSENABLE'), ],
                  [Sg.Text('Bitfocus Companion Address'),
                   Sg.Input(default_text=self._bitfocus_target, key='BITFOCUSTARGET', size=15)],
                   [Sg.Text('Bitfocus Companion Page'),
                   Sg.Input(default_text=self._bitfocus_page, key='BITFOCUSPAGE', size=4)],
                  [Sg.Button('Save&Exit'), Sg.Button('Cancel')]
                  ]
        window = Sg.Window(title='Configure', layout=layout, finalize=True, keep_on_top=True)
        while True:
            event, values = window.read()

            if event == 'Cancel' or event == Sg.WINDOW_CLOSED:
                break

            elif event == 'Save&Exit':
                self.user_settings['-CAMERACOUNT-'] = int(values['CAMERACOUNT'])
                if values['BITFOCUSENABLE']:
                    self.user_settings['-BITFOCUSPAGE-'] = int(values['BITFOCUSPAGE'])
                    self.user_settings['-BITFOCUSTARGET-'] = values['BITFOCUSTARGET']
                self.user_settings['-BITFOCUSENABLE-'] = values['BITFOCUSENABLE']

                window.close()
                sys.exit(0)

        window.close()
        # 'fix' for PySimpleGUI/Tkintr issue with threading
        del layout
        del window
        gc.collect()



