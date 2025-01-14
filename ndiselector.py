from os import path
import sys
import PySimpleGUI as Sg
import NDIlib as Ndi
import time
import re
import ndirouter
import viscarelay
import ndi_image
import socket
import config
import threading
import companion

ProgName = 'NDI Camera Selector'

Debug = False

config = config.Config()
bitfocus_info = config.bitfocus_info()
if bitfocus_info is not None:
    bitfocus = companion.Companion(target=bitfocus_info[0],
                                   page=bitfocus_info[1],
                                   row=0)
else:
    bitfocus = None

camera_count = config.camera_count()

# Constants
ViscaPort = 52381
ViewerSize = (480, 270)

class NDISource(dict):
    """ Single NDI Source instance
        active sources are type 'dynamic'
    """
    def __init__(self, name: str, srctype: str, lastseen: float = 0.0, ptz_name=None):
        if ptz_name is None:
            ptz_name = name.split(' ')[0]  # Assume hostname is the first part of string
        dict.__init__(self, name=name, srctype=srctype, lastseen=lastseen,
                      ndi_source=None, ptz_name=ptz_name)

    def ptz_set(self, ptz_name):
        if ptz_name == '':
            ptz_name = self['name'].split(' ')[0]
        if 'dynamic' == self['srctype']:
            self['ptz_name'] = ptz_name

    def ptz_get(self):
        return self['ptz_name']

    def name_get(self):
        return self['name']

    def ndi_source_get(self):
        return self['ndi_source']

    def local(self):
        return self['srctype'] == 'local'

    def dynamic(self):
        return self['srctype'] == 'dynamic'

    def stale(self):
        # test whether a source has gone stale
        # defined as no advertisement seem in 1 minute
        return (self.dynamic() and
                (time.monotonic() - self["lastseen"]) > 60.0)

ndi_None = NDISource("None", "static")


class NDISourceList:
    """ Manipulate the cache of known NDI Sources
    """
    def __init__(self):
        desc = Ndi.FindCreate()
        desc.show_local_sources = False
        self.ndi_find = Ndi.find_create_v2(desc)
        self.cache = {"None": ndi_None}

    def delete(self):
        """" Cleanup before re-initing the list """
        Ndi.find_destroy(self.ndi_find)

    def update(self) -> bool:
        """ Update the list of dynamic sources, returns True if changed """
        changed = False

        if not Ndi.find_wait_for_sources(self.ndi_find, 0):
            return changed

        sources = Ndi.find_get_current_sources(self.ndi_find)
        for i, s in enumerate(sources):
            if re.search("Remote Connection", s.ndi_name):
                continue

            if s.ndi_name in self.cache:
                self.cache[s.ndi_name]["lastseen"] = time.monotonic()
            else:
                self.cache[s.ndi_name] = NDISource(s.ndi_name, "dynamic", time.monotonic())
                changed = True

            self.cache[s.ndi_name]["ndi_source"] = s

        return changed

    def find(self, name: str):
        """ Find a source by name """
        return self.cache.get(name)

    def srclist(self) -> list:
        """ Return a sorted list of dynamic sources, with "None" at the top """
        src_list = []
        for key in self.cache:
            src = self.cache[key]
            if src.dynamic():
                src_list.insert(-1, src.name_get())
        src_list.sort()
        src_list.insert(0, self.cache["None"].name_get())
        return src_list

    def src_save(self) -> list:
        """ return list of tuples (name, ptz) """
        srclist = []
        idx = 0
        for key in self.cache:
            src = self.cache[key]
            value = (src.name_get(), src.ptz_get())
            srclist.insert(idx, value)
            idx = idx + 1
        return srclist

    def src_load(self, srcptzlist: list):
        """ update ptz values from srclist """
        if srcptzlist is not None:
            for value in srcptzlist:
                if value[0] in self.cache:
                    src = self.cache[value[0]]
                    src.ptz_set(value[1])

class CameraList:
    """ List of active cameras. """
    def __init__(self, count, routerlist: ndirouter.NDIRouterList = None,
                 viscalist: viscarelay.ViscaRelayList = None):
        self.camera_list = []
        self.max_camera = count
        self.routerlist = routerlist
        self.viscalist = viscalist

        for idx in range(count):
            tmpdict = {"name": 'CAM' + str(idx + 1) + ':', "ndi_source": ndi_None}
            self.camera_list.insert(idx, tmpdict)

    def max(self):
        return self.max_camera

    def cam_name(self, cam_num):
        return self.camera_list[cam_num]["name"]

    def cam_source_get(self, cam_num: int) -> NDISource:
        return self.camera_list[cam_num]["ndi_source"]

    def cam_source_set(self, cam_num: int, src: NDISource) -> bool:
        old_src = self.camera_list[cam_num]["ndi_source"]
        self.camera_list[cam_num]["ndi_source"] = src
        if src != old_src:
            self.routerlist.set_routing(cam_num, src.ndi_source_get())
        if src != ndi_None:
            self.viscalist.ptz_set(cam_num, src.ptz_get())
        return src != old_src

# List of cameras and NDI sources
cameras: CameraList = CameraList(count=camera_count,
                                 routerlist=ndirouter.NDIRouterList(camera_count),
                                 viscalist=viscarelay.ViscaRelayList(camera_count,
                                                                     bitfocus,
                                                                     config.relay_port_base(),
                                                                     ViscaPort))
ndi_sources: NDISourceList = NDISourceList()
ndi_sources_lock = threading.Lock()

def ndi_sources_clear(win):
    """ Initalize/Clear the list of NDI sources.
        This is called at startup and as a result of the 'Refresh' menu item """
    global ndi_sources, ndi_sources_lock, ndi_None, cameras

    win['--NDILIST--'].update([])
    for num in range(cameras.max()):
        cameras.cam_source_set(num, ndi_None)
        win['--CAMSRC'+str(num)].update(ndi_None.name_get())
        win['--CAMPTZ'+str(num)].update(ndi_None.ptz_get())

    with ndi_sources_lock:
        if ndi_sources is not None:
            ndi_sources.delete()

        ndi_sources = NDISourceList()

    # Set a one-shot timer to load the saved camera configuration after giving enough time
    # for the active NDI sources to show up. In practice, they seem to show up within
    # about 1 second
    (win.timer_start(frequency_ms=2500, key='-LOAD-STATE-TIMER-', repeating=False))


def save_camera_state():
    """ Save the current list of selected cameras and associated PTZ addresses"""
    ndi_list = ndi_sources.src_save()

    camera_name_list = []
    for idx in range(cameras.max()):
        camera_name_list.insert(idx, cameras.cam_source_get(idx).name_get())
    config.save_camera_state((ndi_list, camera_name_list))


def load_camera_state():
    """ Reload the selected cameras and the associated PTZ addresses from the
        saved configuration state """
    ndi_list, camera_list = config.load_camera_state()

    ndi_sources.src_load(ndi_list)

    if camera_list is not None:
        for idx in range(len(camera_list)):
            src = ndi_sources.find(camera_list[idx])
            if src is not None and idx < cameras.max():
                cameras.cam_source_set(idx, src)


# background thread to update NDI sources list
#
def update_ndi_thread(win: Sg.Window):
    """ Periodic background thread to watch for new NDI sources on the network"""
    global ndi_sources, ndi_sources_lock

    time.sleep(1)
    while True:
        with ndi_sources_lock:
            if ndi_sources.update():
                win.write_event_value(('-THREAD-', 'NDICHANGE'), 'NDICHANGE')

        time.sleep(2)


#
# All the main window stuff here
#
frame_layout = [[]]
for x in range(cameras.max()):
    ndi_src = cameras.cam_source_get(x)
    frame_layout.insert(x,
                        [Sg.Text(cameras.cam_name(x)),
                         Sg.Text(ndi_src.name_get(), font=('Courier', 12, 'bold'), size=20, key='--CAMSRC' + str(x)),
                         Sg.Text(ndi_src.ptz_get(), font=('Courier', 12, 'italic'), size=20, key='--CAMPTZ' + str(x))])

sources_layout = [[Sg.Listbox(ndi_sources.srclist(), size=(54, 7), key='--NDILIST--', enable_events=True,
                              tooltip='Click on NDI source to select')],
                  [[Sg.Button('Set Camera', tooltip='Set Camera <n> to selected NDI Source'),
                    Sg.InputText(size=3, key='CAM_INPUT', do_not_clear=False, tooltip='Enter camera number to set'),
                    Sg.Button('Set PTZ', tooltip='Set the PTZ name/address for selected NDI Source to input value'),
                    Sg.InputText(size=10, key='PTZ_INPUT', do_not_clear=False,
                                 tooltip='Enter hostname of PTZ for selected NDI source')
                    ]]
                  ]
viewer_layout = [[Sg.Image(size=ViewerSize, key="--VIEWER--")]]

column1_layout = [[Sg.Frame('Cameras', frame_layout, key="--CAMFRAME--",
                            tooltip='Cameras, and associated PTZ controllers, active on the NDI switch')],
                  [Sg.Frame('Sources', sources_layout)]]

column2_layout = [[Sg.Frame('Viewer', viewer_layout)]]

menu_layout = Sg.Menu([['Menu', ['Refresh', 'Configure', 'Exit']]])
if Debug:
    debug_layout = [Sg.Multiline(autoscroll=True, size=(80, 5), reroute_stdout=True)]
    layout = [[menu_layout], [Sg.Column(column1_layout), Sg.Column(column2_layout)], [debug_layout]]
else:
    layout = [[menu_layout], [Sg.Column(column1_layout), Sg.Column(column2_layout)]]
# Create the Window
window = Sg.Window(ProgName, layout, finalize=True,   enable_close_attempted_event=True,
                   icon=path.abspath(path.join(path.dirname(__file__), 'NDI-Camera-Selector.ico')))

window['PTZ_INPUT'].bind("<Return>", '_Set')
window['CAM_INPUT'].bind('<Return>', '_Set')

update_thread = window.start_thread(lambda: update_ndi_thread(window), ('-THREAD-', '-THEAD ENDED-'))

# Event Loop to process "events" and get the "values" of the inputs

# clear/refresh the sources list
ndi_sources_clear(window)

while True:
    event, values = window.read()

    if event == Sg.WIN_CLOSED:
        break
    if event == Sg.WINDOW_CLOSE_ATTEMPTED_EVENT:
        if Sg.popup_ok_cancel("Really Close?", keep_on_top=True) == 'OK':
            window.close()
            break
    elif event == 'Exit':
        window.close()
        break

    elif event == 'Refresh':
        ndi_sources_clear(window)

    elif event == 'Configure':
        config.configure()

    elif event[0] == '-THREAD-':
        if event[1] == 'NDICHANGE':
            window['--NDILIST--'].update(ndi_sources.srclist())
        elif event[1] == 'NDI_IMAGE':
            window['--VIEWER--'].update(values[event])

    elif event == '--NDILIST--':
        # User selected a camera, try to grab an image
        ndi = ndi_sources.find(values['--NDILIST--'][0])
        ndi_source = ndi.ndi_source_get()
        window.start_thread(lambda: ndi_image.getframe_task(window, ndi_source, ViewerSize),
                            ('-THREAD-', '-THEAD ENDED-'))

    elif event == '-LOAD-STATE-TIMER-':
        load_camera_state()
        for x in range(cameras.max()):
            ndi = cameras.cam_source_get(x)
            window['--CAMSRC' + str(x)].update(ndi.name_get())
            window['--CAMPTZ' + str(x)].update(ndi.ptz_get())

    elif (event == 'Set PTZ') or (event == 'PTZ_INPUT_Set'):
        try:
            ndi = ndi_sources.find(values['--NDILIST--'][0])
        except IndexError:
            Sg.popup_error("no NDI source selected")
            continue
        if not ndi.dynamic():
            Sg.popup_error("Can't set PTZ for " + ndi.name_get())
            continue

        ptz_str = values['PTZ_INPUT']
        try:
            # Make sure PTZ host name is known, empty string means reset PTZ name to default
            if not ptz_str == '':
                socket.gethostbyname(ptz_str)
        except socket.gaierror:
            Sg.popup_error("PTZ not found: " + ptz_str)
        else:
            ndi.ptz_set(ptz_str)

            for x in range(cameras.max()):
                if cameras.cam_source_get(x) is ndi:
                    window['--CAMPTZ' + str(x)].update(ndi.ptz_get())
                    cameras.cam_source_set(x, ndi)
            save_camera_state()

    elif event == 'Set Camera' or event == 'CAM_INPUT_Set':
        camnumstr = values['CAM_INPUT']
        if camnumstr == '':
            continue
        try:
            ndi_str = values['--NDILIST--'][0]
        except IndexError:
            Sg.popup_error("no NDI source selected")
            continue
        try:
            camnum = int(camnumstr)-1
        except ValueError:
            camnum = -1

        if camnum < 0 or camnum >= cameras.max():
            Sg.popup_error("Set Camera - bad value: " + camnumstr)
            continue

        ndi = ndi_sources.find(ndi_str)

        cameras.cam_source_set(camnum, ndi)
        window['--CAMSRC'+str(camnum)].update(ndi.name_get())
        window['--CAMPTZ'+str(camnum)].update(ndi.ptz_get())
        save_camera_state()

window.close()

sys.exit(0)
