#
# Code to handle ViscaRelay instances
#
import socket
import threading
import struct
import time

# Workaround for bug in PTZ Controller INQUIRY commands
Fix_INQUIRY = True

class ViscaRelayInstance:
    def ptz_set(self, ptz: str):
        """ Set a new ptz destination """
        try:
            ptz_address = socket.gethostbyname(ptz)
            self.ptz_sockaddr = (ptz_address, self.ptz_port)
        except socket.gaierror:
            pass

    def relaythread(self):
        """ Loop:
            - receive packet
            - if packet src socket == ViscaPort then it's from the camera -> Forward back to the last sockaddr
              seen from the controller
            - otherwise, forward to the current sockaddr for the camera
        """
        s = self.socket
        self.recv_sockaddr = None

        while True:
            time.sleep(0.001)
            try:
                buffer, address = s.recvfrom(1024)
                if address == self.ptz_sockaddr:
                    # Packet is a response from the camera
                    dst_sockaddr = self.recv_sockaddr
                    # We don't clear the sockaddr here because it is possible to get multiple packets in response
                    # eg: CMD-> ACK, REPLY
                else:
                    # Packet is a (probably) from a controller. Save address for later reply
                    self.recv_sockaddr = address
                    # forward packet to the camera
                    dst_sockaddr = self.ptz_sockaddr

                    # Patch around bug in AVKANS controller, it encapsulates INQUIRY commands
                    # in Visca CMD packets
                    if Fix_INQUIRY and len(buffer) > 10:
                        fmt= "!HHL"
                        (vcmd, vlen, seq)= struct.unpack_from(fmt, buffer)
                        payload = buffer[struct.calcsize(fmt):]
                        cmd = 0
                        if len(payload) > 2:
                            (cmd)= struct.unpack_from("!H", payload)

                        if cmd[0] == 0x8109 and vcmd == 0x0100:
                            vcmd = 0x0110
                            buffer = struct.pack('!HHL', vcmd, vlen, seq) + payload

                if dst_sockaddr is not None:
                    s.sendto(buffer, dst_sockaddr)
            except ConnectionResetError:
                pass

            # Loop forever

    def __init__(self, rcv_port: int, ptz_port: int):
        """ Init:
            - create and bind socket for input.
            - create send sockaddr for sending to camera
            - create task to perform relay
            - packets to be relayed from controller will be from a random socket
            - response packets from camera will be from port 52381
            - forward packets back to controller
        """
        self.rcv_port = rcv_port
        self.ptz_port = ptz_port
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        address = ("", rcv_port)
        self.socket.bind(address)
        self.recv_sockaddr = None
        self.ptz_sockaddr = None
        self.thread = threading.Thread(target=self.relaythread)
        self.thread.daemon = True
        self.thread.start()


class ViscaRelayList:
    def __init__(self, count: int, baseport: int, viscaport: int):
        self.relaylist = []
        for x in range(count):
            self.relaylist.insert(x, ViscaRelayInstance(baseport, viscaport))
            baseport = baseport + 1

    def ptz_set(self, index: int, ptz: str):
        self.relaylist[index].ptz_set(ptz)
