from __future__ import annotations

import logging
import multiprocessing as mp
import multiprocessing.managers as mp_managers
import multiprocessing.pool as mp_pool
import multiprocessing.synchronize as mp_sync
import pickle
import signal
import socket
import sys
import uuid
from pathlib import Path
from typing import Any, Callable, Concatenate, Dict, Generic, Optional, ParamSpec, Tuple, Type, TypeVar

from docker import DockerClient
from docker.errors import DockerException
from docker.models.containers import Container
from typing_extensions import Self, final, override

from tophat.api.device import AsyncCommand, Device, DeviceBase, DeviceType, ResultType, UnsupportedCommandError
from tophat.api.hat import HackableHat
from tophat.api.message import CommandRequest, CommandResponse, MAX_SEND_RECV_SIZE, ResponseCode

LOGGER = logging.getLogger('tophat')
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))

HAT_SOCKET_PATH: Path = Path('/var/run/hatbox.socket')

DeviceLockPair = Tuple[DeviceBase, mp_sync.Lock]
DeviceMap = Dict[int, DeviceLockPair]
HatMap = Dict[Type[HackableHat], "HatBox"]

BaseDeviceType = TypeVar('BaseDeviceType', bound=DeviceBase)
HatType = TypeVar('HatType', bound=HackableHat)
ExceptionType = TypeVar("ExceptionType",
                        bound=BaseException)

DeviceExtraArgs = ParamSpec("DeviceExtraArgs")


def _supress_sigint() -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)


@final
class _ResultCallback(Generic[ResultType]):

    def success(self: Self,
                result: ResultType) -> None:
        LOGGER.debug(f'Finished running command')
        self._client_socket.sendall(pickle.dumps(CommandResponse.from_success(result)))
        self._client_socket.close()

    def error(self: Self,
              exception: ExceptionType) -> None:
        response: CommandResponse
        if isinstance(exception, UnsupportedCommandError):
            LOGGER.error(f'Attempted to run unsupported command: {exception}')
            response = CommandResponse.from_error(ResponseCode.ERROR_UNSUPPORTED_COMMAND)

        else:
            LOGGER.error(f'Command failed with exception: {exception}')
            response = CommandResponse.from_error(ResponseCode.ERROR_UNKNOWN)

        self._client_socket.sendall(pickle.dumps(response))
        self._client_socket.close()

    @override
    def __init__(self,
                 client_socket: socket.socket) -> None:
        self._client_socket: socket.socket = client_socket


@final
class TopHatServer:

    @property
    def socket_path(self: Self) -> Path:
        return self._socket_path

    def register_device(self: Self,
                        device_constructor: Callable[Concatenate[int, DeviceExtraArgs], BaseDeviceType],
                        *args: DeviceExtraArgs.args,
                        device_id: Optional[int] = None,
                        **kwargs: DeviceExtraArgs.kwargs) -> int:
        if device_id is not None:
            if device_id in self._device_map:
                raise ValueError(f'Device {device_id} already registered')
        else:
            device_id = max(self._device_map.keys(), default=0) + 1
        self._device_map[device_id] = device_constructor(device_id, *args, **kwargs), self._manager.Lock()
        return device_id

    def get_device(self: Self,
                   device_id: int) -> Optional[Device]:
        return self._device_map.get(device_id, None)

    def register_hat(self: Self,
                     hat: HackableHat) -> None:
        if type(hat) in self._hat_map:
            raise ValueError(f'Hat {type(hat).__name__} already registered')
        else:
            self._hat_map[type(hat)] = HatBox(self, hat)

    def get_hat(self: Self,
                hat_type: Type[HatType]) -> Optional[HatType]:
        if hat_type in self._hat_map:
            return self._hat_map[hat_type].hat
        else:
            return None

    def start(self: Self) -> None:
        if self._socket_path.exists():
            LOGGER.warning('Found existing tophat socket, removing...')
            self._socket_path.unlink()

        try:
            LOGGER.info('Starting tophat server...')
            with (mp_pool.Pool(initializer=_supress_sigint) as process_pool,
                  socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_socket):
                server_socket.bind(str(self._socket_path))
                server_socket.listen()

                while True:
                    client_socket: socket.socket
                    client_address: Any
                    client_socket, client_address = server_socket.accept()

                    LOGGER.debug(f'Accepted connection')
                    try:
                        request: CommandRequest[DeviceType, ResultType] = self._await_request(client_socket)
                        self._handle_request(process_pool, client_socket, request)

                    except socket.error as socket_error:
                        LOGGER.error(f'Socket error occurred: {socket_error}')
                        client_socket.close()

        except KeyboardInterrupt:
            LOGGER.info('Closing tophat server...')
            for hat_box in self._hat_map.values():
                hat_box.stop()
            self._socket_path.unlink(missing_ok=True)

    @override
    def __init__(self,
                 socket_path: Optional[Path] = None) -> None:
        self._socket_path = socket_path if socket_path is not None else Path(f'/srv/tophat/{uuid.uuid4()}.socket')
        self._device_map: DeviceMap = {}
        self._hat_map: HatMap = {}

        mp.set_start_method('spawn', True)
        self._manager: mp_managers.SyncManager = mp.Manager()

    @staticmethod
    def _await_request(client_socket: socket.socket) -> Optional[CommandRequest[DeviceType, ResultType]]:
        try:
            request: Any = pickle.loads(client_socket.recv(MAX_SEND_RECV_SIZE))
            if not isinstance(request, CommandRequest):
                LOGGER.error(f'Received unexpected tophat request of type: {type(request)}')
                return None

            LOGGER.debug(f'Received {type(request.command).__name__} targeting device {hex(request.device_id)}')
            return request

        except socket.error as socket_error:
            LOGGER.error(f'Failed to communicate with client: {socket_error}')

        except pickle.UnpicklingError as unpickling_error:
            LOGGER.error(f'Received malformed tophat request: {unpickling_error}')

        except pickle.PicklingError as pickling_error:
            LOGGER.error(f'Failed to pickle response: {pickling_error}')

    def _handle_request(self: Self,
                        process_pool: mp_pool.Pool,
                        client_socket: socket.socket,
                        request: CommandRequest[DeviceType, ResultType]) -> None:
        if request.device_id not in self._device_map:
            LOGGER.error(f'Unknown device ID: {request.device_id}')
            client_socket.sendall(
                pickle.dumps(CommandResponse.from_error(ResponseCode.ERROR_INVALID_DEVICE)))
            client_socket.close()
            return

        target_device: BaseDeviceType
        device_lock: mp_sync.Lock
        target_device, device_lock = self._device_map[request.device_id]
        if isinstance(request.command, AsyncCommand):
            LOGGER.debug(f'Running {type(request.command).__name__} asynchronously on device '
                         f'{hex(target_device.id)}...')
            try:
                process_pool.apply_async(target_device.run, (device_lock, request.command,)).get(0.0)
            except mp.TimeoutError:
                pass
            LOGGER.debug(f'Command left to run asynchronously')
            client_socket.sendall(pickle.dumps(CommandResponse.from_success(None)))
            client_socket.close()
            return

        else:
            LOGGER.debug(f'Running {type(request.command).__name__} on device '
                         f'{hex(target_device.id)}...')
            result_callback: _ResultCallback = _ResultCallback(client_socket)
            process_pool.apply_async(
                target_device.run,
                (device_lock, request.command,),
                callback=result_callback.success,
                error_callback=result_callback.error)
            return


@final
class HatBox(Generic[HatType]):

    @property
    def hat(self: Self) -> HatType:
        return self._hat

    def start(self: Self) -> bool:
        try:
            container: Container = self._docker_client.containers.run(image=self._hat.image_name,
                                                                      detach=True,
                                                                      auto_remove=True,
                                                                      cpu_percent=20,
                                                                      network_disabled=True,
                                                                      volumes=self._container_volumes())

            container.wait()
            return True

        except DockerException:
            return False

    def stop(self: Self):
        self._docker_client.close()

    @override
    def __init__(self,
                 tophat: TopHatServer,
                 hat: HatType) -> None:
        self._tophat: TopHatServer = tophat
        self._hat: HatType = hat
        self._docker_client: DockerClient = DockerClient.from_env()

    @property
    def _container_volumes(self: Self):
        return {
            str(self._tophat.socket_path): {
                'bind': str(HAT_SOCKET_PATH),
                'mode': 'rw'
            }
        }
