from __future__ import annotations

import multiprocessing as mp
import multiprocessing.synchronize as mp_sync
import os
import select
import socket
import subprocess
from pathlib import Path

import board
import neopixel
from typing_extensions import Self, final, override

from tophat.api.device import DeviceProxy
from tophat.devices.neopixel import NeopixelCommand, NeopixelDevice

DEFAULT_SOCKET_PATH: Path = Path('/srv/tophat/neopixel.socket')
MAX_SEND_RECV_SIZE: int = 512


@final
class NeopixelServer(mp.Process):

    @override
    def run(self: Self) -> None:
        neopixel_device: NeopixelDevice = NeopixelDevice(0x0, neopixel.NeoPixel(self._pin, self._num_leds))
        server_socket: socket.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        with server_socket.bind(str(self._socket_path)):
            server_socket.settimeout(1)
            server_socket.listen()

            while not self._stop_event.is_set():
                try:
                    client_socket: socket.socket
                    client_socket, addr = server_socket.accept()
                except socket.timeout:
                    continue
                else:
                    poller = select.poll()
                    poller.register(client_socket, select.POLLIN)
                    if poller.poll(2000):
                        raw_data: bytes = server_socket.recv(MAX_SEND_RECV_SIZE)
                        command: NeopixelCommand = NeopixelCommand.deserialize(raw_data)
                        neopixel_device.run(self._lock, command)

    @override
    def __init__(self,
                 socket_path: Path,
                 pin: board.Pin,
                 num_leds: int) -> None:
        super().__init__(name='neopixel-server',
                         daemon=True)
        self._socket_path: Path = socket_path
        self._pin: board.Pin = pin
        self._num_leds: int = num_leds

        self._lock: mp_sync.Lock = mp.Lock()


@final
class NeopixelDeviceProxy(DeviceProxy[NeopixelDevice]):

    @override
    def run(self: Self,
            lock: mp_sync.Lock,
            command: NeopixelCommand) -> None:
        client_socket: socket.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        with client_socket.connect(str(self._socket_path)):
            client_socket.sendall(command.serialize())

    @override
    def __init__(self,
                 device_id: int,
                 pin: board.Pin,
                 num_leds: int) -> None:
        super().__init__(device_id)
