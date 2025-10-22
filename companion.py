#
# Interface to BitFocus Companion to trigger actions, like camera switching
#
# For now we assume that:
# - Companion is running on the local machine - 127.0.0.1
# - The UDP API is configured on the default port (16759)
#
import socket
import PySimpleGUI as Sg

class Companion:
    def __init__(self, target:str="127.0.0.1", port:int=16759, page='0', row:int=0):
        self.page = page
        self.row = row
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = (target, port)
        try:
            self.socket.connect(address)
        except socket.gaierror:
            Sg.popup_error(f'BitFocus Companion connect: Bad address "{target}"')

    def pushbutton(self, page=None, row=None, column:int=0):
        if page is None:
            page = self.page

        if row is None:
            row = self.row

        buffer = f"LOCATION {page}/{row}/{column} PRESS"
        self.socket.send(buffer.encode('utf-8'))