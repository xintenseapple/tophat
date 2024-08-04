from __future__ import annotations

import multiprocessing as mp
import multiprocessing.synchronize as mp_sync
import select
import socket
from argparse import ArgumentParser
from pathlib import Path

from typing_extensions import Self, final, override

import board
from tophat.devices.neopixel import NeopixelCommand, NeopixelDevice

DEFAULT_SOCKET_PATH: Path = Path('/srv/tophat/neopixel.socket')
MAX_SEND_RECV_SIZE: int = 512


@final
class NeopixelServer:

    def start(self: Self) -> None:
        neopixel_device: NeopixelDevice = NeopixelDevice.from_impl('neopixels',
                                                                   self._pin, self._num_leds)
        if self._socket_path.is_socket():
            self._socket_path.unlink()
            print(f'Removing old socket at {self._socket_path}', flush=True)

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_socket:
            print(f'Starting server...', flush=True)
            server_socket.bind(str(self._socket_path))
            self._socket_path.chmod(0o776)
            server_socket.settimeout(1.0)
            server_socket.listen()

            while True:
                try:
                    client_socket: socket.socket
                    client_socket, addr = server_socket.accept()
                except socket.timeout:
                    continue
                else:
                    with client_socket:
                        print(f'Accepted connection...', flush=True)
                        poller = select.poll()
                        poller.register(client_socket, select.POLLIN)
                        if poller.poll(2000):
                            raw_data: bytes = client_socket.recv(MAX_SEND_RECV_SIZE)
                            command: NeopixelCommand = NeopixelCommand.deserialize(raw_data)
                            print(f'Received {type(command).__name__} command!', flush=True)
                            neopixel_device.run(self._lock, command)

    @override
    def __init__(self,
                 socket_path: Path,
                 pin: board.pin.Pin,
                 num_leds: int) -> None:
        self._socket_path: Path = socket_path
        self._pin: board.pin.Pin = pin
        self._num_leds: int = num_leds

        self._lock: mp_sync.Lock = mp.Lock()


if __name__ == '__main__':
    arg_parser = ArgumentParser()
    arg_parser.add_argument('socket_path', type=Path)
    arg_parser.add_argument('pin', type=int)
    arg_parser.add_argument('num_leds', type=int)

    args = arg_parser.parse_args()
    server: NeopixelServer = NeopixelServer(DEFAULT_SOCKET_PATH, board.pin.Pin(args.pin), args.num_leds)

    try:
        server.start()
    except KeyboardInterrupt:
        print('Received keyboard interrupt, shutting down...')
