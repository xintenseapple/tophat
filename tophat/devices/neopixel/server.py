from __future__ import annotations

import multiprocessing as mp
import multiprocessing.synchronize as mp_sync
import select
import socket
from argparse import ArgumentParser
from pathlib import Path

import board
import neopixel
from typing_extensions import Self, final, override

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


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('socket_path', type=Path)
    arg_parser.add_argument('pin', type=int)
    arg_parser.add_argument('num_leds', type=int)

    args = arg_parser.parse_args()
    server: NeopixelServer = NeopixelServer(DEFAULT_SOCKET_PATH, board.Pin(args.pin), args.num_leds)
