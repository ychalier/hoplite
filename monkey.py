"""
MonkeyRunner script for communicating with the Android phone.

This script should NOT be started manually, but instead called via the
MonkeyRunner tool executable.
"""


import sys
import socket
import logging
from com.android.monkeyrunner import MonkeyRunner, MonkeyDevice  # pylint: disable=E0401


class MonkeyServer:
    """
    Socket server handling communication with main script.
    """

    SERVER_ADDRESS = ("localhost", 9898)
    LOGGER_NAME = "monkey_server"

    def __init__(self):
        self.server = None
        self.device = None
        self.logger = logging.getLogger(self.LOGGER_NAME)

    def snap(self, connection):
        """
        Take a screenshot and send back the PNG data, preceded by its size as
        a 16-bytes integer.
        """
        snapshot = self.device.takeSnapshot().convertToBytes()
        size = str(len(snapshot)).zfill(16)
        connection.sendall(size)
        connection.sendall(snapshot)

    def touch(self, connection):
        """
        Receives 16 bytes twice for the coordinates and touch the specified
        point on the screen.
        """
        x = int(connection.recv(16))  # pylint: disable=C0103
        y = int(connection.recv(16))  # pylint: disable=C0103
        self.device.touch(x, y, MonkeyDevice.DOWN_AND_UP)

    def run(self):
        """
        Main server loop.
        """
        log_level = logging.INFO
        if len(sys.argv) > 1:
            log_level = int(sys.argv[1])
        logging.basicConfig(level=log_level)
        self.logger.debug("Waiting for Android device...")
        self.device = MonkeyRunner.waitForConnection()
        self.logger.debug("Android device connected")
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind(self.SERVER_ADDRESS)
        self.server.listen(1)
        self.logger.info("Starting socket server at %s:%d", *self.SERVER_ADDRESS)
        connection, address = self.server.accept()
        self.logger.debug("Accepting connection from %s:%d", *address)
        while True:
            command = connection.recv(4).decode("ascii")
            self.logger.debug("Received command '%s'", command)
            if command in ["", "QUIT"]:
                break
            if command == "SNAP":
                self.snap(connection)
            elif command == "TOCH":
                self.touch(connection)
        self.logger.info("Closing")


MonkeyServer().run()
