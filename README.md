# NDI-Camera-Selector
A tool to support dynamically switching between NDI PTZ cameras (or other sources) in a live-stream setup

## Introduction

*NDI Camera Selector* is intended to be used in a live-stream, or other video production, station based on PTZ cameras using the [NDI](https://ndi.video/) video over IP protocol.

It can be used as part of a setup including my [VISCA Game Controller application](https://github.com/DanTappan/VISCA-Game-Controller)

It supports the following features:

- the ability to dynamically select between *N* NDI video sources (e.g. PTZ cameras) on the LAN, and map them into *M* slots: CAM1-CAM*N*. This allows the operator to configure a video switching application (such as [OBS](https://obsproject.com/) or [VMix](https://www.vmix.com/)) with a set of video sources or scenes, and dynamically change which cameras appear in each scene
- the ability to route IP VISCA packets, to control the cameras, to the appropriate IP destination for each slot. This allows the operator to statically configure the targets for an IP VISCA Joystick controller, and have the VISCA packets automatically mapped to the current set of selected cameras.
- an additional benefit of this is that many VISCA joystick controllers require that targets be configured by IP address; accessing the camera through the VISCA router allows specifying cameras by name
- to support the case of an NDI camera mounted on a separate Pan/Tilt controller, or when a camera that supports VISCA and HDMI is connected to the network through an HDMI->NDI adaptor, the VISCA target for each camera can be specified separately
- a graphics based interface with persistent configurable parameters

## Use

When run, the application displays the following window

![NDI Camera Selector](Screenshots/NDICameraSelector.png)

This has the following sections:
- **Cameras** - defines the list of configures camera sources. These will be advertised over NDI as "*Host* (CAM*n*)", through an NDI Router. That is, when a program accesses (e.g.) "**VideoStation (CAM1)**" it will be directed to the camera mapped to the **CAM1** slot. There is also a VISCA PTZ controller associated with each camera slot. This defaults to the same address as the NDI source. The VISCA port is currently hardwired to UDP 52381
- **Sources** - lists the set of NDI sources which are visible on the local network via NDI discovery. Currently the application does not support the use of an NDI Discovery Server. Click on a source to select it.
- **Viewer** - displays a snapshot from the current selected NDI source
- to map a source to a camera slot
  - select a source
  - type the number of the slot (1-N) in the text box next to the **Set Camera** button
  - either hit *return* or click on the **Set Camera** button
- to set the address of the VISCA PTZ controller associated with a camera
  - type the name or IP address of the controller into the text box next to the **Set PTZ** button
  - either hit *return* or click on the **Set PTZ** button
 
The window also includes a menu with the following items
- Configure - pops up a configuration dialog which allows setting the number of supported camera slots (currently up to 7)
- Exit - exits the program.

**NOTE:** in order to prevent accidentally closing the Camera Selector app, which would break the operation of the live-streaming station, closing the app either through the menu, through the window close box, or through the task bar, requires an extra confirmation.

## Installation

A [Windows Installer](https://dantappan.net/projects/#NDI-Camera-Selector) for the latest version is available. Alternatively, clone the repository through Github and go to town.

## Credits

The program uses the following libraries

- the [NewTek NDI SDK](https://ndi.video/for-developers/ndi-sdk/download/)
- the [NDI-Python](https://pypi.org/project/ndi-python/) library for the NDI SDK. **NOTE** this library currently only support up to Python 3.10, therefore this program must be built using Python 3.10 or earlier.
- the [PySimpleGUI](https://pysimplegui.com/) GUI library. **NOTE** you may be required to register for a [free Hobbyist licence for PySimplGui](https://pysimplegui.com/pricing) in order to use this program
- the program icon is based on [Ptz camera icons created by Freepik - Flaticon](https://www.flaticon.com/free-icons/ptz-camera)
- the program was developed using the [PyCharm Community Edition IDE](https://www.jetbrains.com/pycharm/)
- the Windows installer was created using [InstallForge](https://installforge.net/)
