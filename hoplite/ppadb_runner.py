"""Communication with device using pure python adb.
"""
import logging
import io
from typing import Optional
from ppadb.client import Client as AdbClient
from ppadb.device import Device

LOGGER = logging.getLogger(__name__)


class PurePythonAdbInterface:
    """Implementation for abstract communication with devices

    Parameters
    ----------
    device_serial : Optional[str]
        Serial name of user device from adb

    Attributes
    ----------
    HOST : str
        Host for adb client
    PORT : int
        Port for adb client
    DEFAULT_DEVICE_SERIAL : str
        AVD default device serial name for adb
    device: ppadb.device.Device
        Device interface for touch and snapshot
    """

    HOST = "localhost"
    PORT = 5037
    DEFAULT_DEVICE_SERIAL = "emulator-5554"

    def __init__(self, device_serial: Optional[str]):
        serial = device_serial or self.DEFAULT_DEVICE_SERIAL
        device = AdbClient(host=self.HOST, port=self.PORT).device(serial)
        if not device:
            raise ConnectionRefusedError(
                "Cannot connect to device with serial", serial)
        if not isinstance(device, Device):  # Should never occur
            raise ConnectionRefusedError()
        self.device = device

    def open(self):
        """For compatibility"""

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
        image_data = self.device.screencap()
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
        self.device.input_tap(touch_x, touch_y)

    def close(self):
        """For compatibility"""
