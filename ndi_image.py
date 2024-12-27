import NDIlib as Ndi
from PIL import Image
import io
import PySimpleGUI as sg
import time


def getframe_ndi(ndi_src: Ndi.Source):
    """ Get one video frame as PNG data """

    if ndi_src is None:
        return None

    ndi_recv_create = Ndi.RecvCreateV3(source_to_connect_to=ndi_src)
    ndi_recv_create.color_format = Ndi.RECV_COLOR_FORMAT_BGRX_BGRA
    # Kludge - AVKANS cameras don't support "BANDWIDTH_LOWEST"
    # TODO: figure out a cleaner way to do this
    if 'BIRDDOG' in ndi_src.ndi_name:
        ndi_recv_create.bandwidth = Ndi.RECV_BANDWIDTH_LOWEST
    elif 'AVKANS' in ndi_src.ndi_name:
        ndi_recv_create.bandwidth = Ndi.RECV_BANDWIDTH_HIGHEST
    else:
        ndi_recv_create.bandwidth = Ndi.RECV_BANDWIDTH_LOWEST

    ndi_recv_create.allow_video_fields = False
    ndi_recv = Ndi.recv_create_v3(ndi_recv_create)
    if ndi_recv is None:
        return None

    tries = 0
    while True:
        t, v, _, _ = Ndi.recv_capture_v2(ndi_recv, 0)

        if t == Ndi.FRAME_TYPE_VIDEO:
            img = Image.frombytes("RGBA", (v.xres, v.yres), v.data, "raw")
            Ndi.recv_free_video_v2(ndi_recv, v)
            break
        time.sleep(0.25)
        tries = tries + 1
        if tries > 10:
            img = None
            break

    Ndi.recv_destroy(ndi_recv)
    return img


def getframe_blank(imgsize: tuple[int, int]) -> Image:
    """ return a blank image"""
    img = Image.new("RGBA", size=imgsize, color="Black")
    return img


def getframe_task(window: sg.Window, ndi_src: Ndi.Source, imgsize: tuple[int, int]):
    """ External function - call as a task lambda from the PySimpleGUI window manager """
    try:
        img = getframe_ndi(ndi_src)
        if img is None:
            img = getframe_blank(imgsize)

        if img is not None:
            img.thumbnail(imgsize)
            bio = io.BytesIO()
            img.save(bio, format="PNG")
            window.write_event_value(('-THREAD-', 'NDI_IMAGE'), bio.getvalue())
            bio.close()
    except Exception as exc:
        print("getframe_task: exception ", exc)

