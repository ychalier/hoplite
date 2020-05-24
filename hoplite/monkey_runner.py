"""Communication with MonkeyRunner.
"""

import os
import io
import time
import socket
import logging
import subprocess


LOGGER = logging.getLogger(__name__)


class MonkeyRunnerInterface:
    """Socket client to communicate with the MonkeyRunner script.

    Parameters
    ----------
    mr_script : str
        Path to the MonkeyRunner executable.

    Attributes
    ----------
    process : subprocess.Popen
        Dedicated process for the MonkeyRunner script.
    client : socket.socket
        Socket client.
    SERVER_ADDRESS : tuple[str, int]
        Host and port of the socket server to connect to.
    MAX_CONNECTION_ATTEMPTS : int
        Number of tries for connecting to the server.
    DELAY_BETWEEN_ATTEMPTS : float
        Delay between two connections to the server.
    mr_script

    """

    SERVER_ADDRESS = ("localhost", 9898)
    MAX_CONNECTION_ATTEMPTS = 10
    DELAY_BETWEEN_ATTEMPTS = .5  # seconds

    def __init__(self, mr_script):
        self.mr_script = mr_script
        self.process = None
        self.client = None

    def open(self):
        """Connect to the server.
        """
        self.process = subprocess.Popen(
            [self.mr_script, os.path.realpath("monkey.py")],
            cwd=os.path.dirname(self.mr_script)
        )
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        for attempt in range(self.MAX_CONNECTION_ATTEMPTS):
            try:
                LOGGER.debug("Connection attempt no. %d", attempt + 1)
                self.client.connect(self.SERVER_ADDRESS)
                break
            except ConnectionRefusedError:
                time.sleep(self.DELAY_BETWEEN_ATTEMPTS)

    def snapshot(self, as_stream=False):
        """Take a snapshot of the screen.

        Parameters
        ----------
        as_stream : bool
            Whether to wrap the output in a `io.BytesIO` stream.

        Returns
        -------
        list[bytes]
            Screenshot PNG image data.

        """
        self.client.sendall(b"SNAP")
        size = self.client.recv(16)
        image_data = self.client.recv(int(size))
        if as_stream:
            return io.BytesIO(image_data)
        return image_data

    def touch(self, touch_x, touch_y):
        """Touch the screen at given coordinates.

        Parameters
        ----------
        touch_x : int
            x coordinate of the point to touch on screen.
        touch_y : int
            y coordinate of the point to touch on screen.

        """
        self.client.sendall(b"TOCH")
        self.client.sendall(str(touch_x).zfill(16).encode("ascii"))
        self.client.sendall(str(touch_y).zfill(16).encode("ascii"))

    def close(self):
        """Send a stop command to the server and close the socket client.
        """
        self.client.sendall(b"QUIT")
        self.client.close()
        self.process.wait()
