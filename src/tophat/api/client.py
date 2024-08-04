import pickle
import socket
from pathlib import Path
from typing import Any

from typing_extensions import Self, final, override

from tophat.api.device import Command, DeviceType, ResultType
from tophat.api.message import CommandRequest, CommandResponse, MAX_SEND_RECV_SIZE, ResponseCode


@final
class TopHatClient:

    def send_command(self: Self,
                     device_name: str,
                     command: Command[DeviceType, ResultType]) -> ResultType:
        if not self._socket_path.is_socket():
            raise RuntimeError(f'Failed to find tophat socket at {self._socket_path}')

        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_socket:
            try:
                server_socket.connect(str(self._socket_path))

                request: CommandRequest[DeviceType, ResultType] = CommandRequest(device_name, command)
                server_socket.sendall(pickle.dumps(request))
                response: Any = pickle.loads(server_socket.recv(MAX_SEND_RECV_SIZE))

                if not isinstance(response, CommandResponse):
                    raise RuntimeError('Received unexpected tophat response')

                if response.code is not ResponseCode.SUCCESS:
                    raise RuntimeError(f'Request failed with code: {response.code.name}')
                else:
                    return response.result

            except socket.error as socket_error:
                raise RuntimeError(f'Failed to connect to tophat server with error') from socket_error

            except pickle.PicklingError as pickling_error:
                raise RuntimeError(f'Failed to pickle request') from pickling_error

            except pickle.UnpicklingError as unpickling_error:
                raise RuntimeError(f'Received malformed tophat response') from unpickling_error

    @override
    def __init__(self,
                 socket_path: Path) -> None:
        if not socket_path.is_socket():
            raise RuntimeError(f'Failed to find tophat socket at {socket_path}')
        self._socket_path: Path = socket_path
