from logging import Handler
import socket

class UDPLoggerHandler(Handler):

    def __init__(self, host, port):
        Handler.__init__(self)
        self.host = host
        self.port = port

    def emit(self,record):
        sock = socket.socket(socket.AF_INET,  # internet
                               socket.SOCK_DGRAM  # UDP
                               )
        try:
            log_entry = self.format(record)
            step = 1400 #fragmentar si es mayor a 1400 bytes
            datagrams = [log_entry[i:i + step] for i in range(0, len(log_entry), step)]
            [sock.sendto(bytes(d, "utf-8"), (self.host, self.port)) for d in datagrams]
        finally:
            sock.close()

