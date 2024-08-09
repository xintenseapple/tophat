from __future__ import annotations

import logging
import multiprocessing as mp
import multiprocessing.managers as mp_mngr
import multiprocessing.synchronize as mp_sync
import pickle
import signal
import socket
import sys
import uuid
from concurrent.futures import Future, ProcessPoolExecutor
from functools import partial
from pathlib import Path
from typing import Any, Dict, Generic, Optional, Tuple, Type, TypeVar

from docker import DockerClient
from docker.errors import DockerException
from docker.models.containers import Container
from typing_extensions import Self, final, override

from tophat.api.device import (AsyncCommand, Device, DeviceBase, DeviceExtraParams, DeviceType, ResultType,
                               UnsupportedCommandError)
from tophat.api.hat import HackableHat
from tophat.api.message import CommandRequest, CommandResponse, MAX_SEND_RECV_SIZE, ResponseCode

LOGGER = logging.getLogger('tophat')
LOGGER.setLevel(logging.DEBUG)
LOGGER.addHandler(logging.StreamHandler(sys.stdout))

HAT_SOCKET_PATH: Path = Path('/var/run/tophat/tophat.socket')

DeviceLockPair = Tuple[DeviceBase, mp_sync.Lock]
DeviceMap = Dict[str, DeviceLockPair]
HatMap = Dict[Type[HackableHat], "HatBox"]

BaseDeviceType = TypeVar('BaseDeviceType', bound=DeviceBase)
HatType = TypeVar('HatType', bound=HackableHat)
ExceptionType = TypeVar("ExceptionType",
                        bound=BaseException)


def _supress_sigint() -> None:
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def _result_callback(client_socket: socket.socket,
                     result_future: Future[ResultType]) -> None:
    response: CommandResponse
    if result_future.cancelled():
        LOGGER.error(f'Command was cancelled somehow?')
        response = CommandResponse.from_error(ResponseCode.CANCELLED)

    elif result_future.exception() is not None:
        exception = result_future.exception()
        if isinstance(exception, UnsupportedCommandError):
            LOGGER.error(f'Attempted to run unsupported command: {exception}')
            response = CommandResponse.from_error(ResponseCode.ERROR_UNSUPPORTED_COMMAND)

        else:
            LOGGER.error(f'Command failed with exception: {exception}')
            response = CommandResponse.from_error(ResponseCode.ERROR_UNKNOWN)

    else:
        LOGGER.debug(f'Finished running command')
        response = CommandResponse.from_success(result_future.result())
    client_socket.sendall(pickle.dumps(response))
    client_socket.shutdown(socket.SHUT_WR)


@final
class TopHatServer:

    @property
    def socket_path(self: Self) -> Path:
        return self._socket_path

    @property
    def manager(self: Self) -> mp_mngr.SyncManager:
        return self._manager

    def register_device(self: Self,
                        device_type: Type[BaseDeviceType],
                        device_name: str,
                        *args: DeviceExtraParams.args,
                        **kwargs: DeviceExtraParams.kwargs) -> BaseDeviceType:
        if device_name in self._device_map:
            raise ValueError(f'Device {device_name} already registered')

        device: BaseDeviceType = device_type.from_impl(device_name, *args, **kwargs)
        self._device_map[device_name] = device, self._manager.Lock()
        return device

    def get_device(self: Self,
                   device_name: str) -> Optional[Device]:
        return self._device_map.get(device_name, None)

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
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as server_socket:
                server_socket.bind(str(self._socket_path))

                for hat_box in self._hat_map.values():
                    hat_box.start()

                    LOGGER.info('Starting tophat server...')

                    with ProcessPoolExecutor(max_workers=2, initializer=_supress_sigint) as process_pool:
                        server_socket.listen()

                        while True:
                            client_socket: socket.socket
                            client_address: Any
                            client_socket, client_address = server_socket.accept()

                            LOGGER.debug(f'Accepted connection')
                            try:
                                request: CommandRequest[DeviceType, ResultType] = self._await_request(client_socket)
                                self._handle_request(process_pool, client_socket, request)

                            except OSError as socket_error:
                                LOGGER.error(f'Socket error occurred: {socket_error}')
                                client_socket.close()

        except KeyboardInterrupt:
            LOGGER.info('Closing tophat server...')

        finally:
            for hat_box in self._hat_map.values():
                hat_box.stop()
            self._socket_path.unlink(missing_ok=True)
            exit(0)

    @override
    def __init__(self,
                 socket_path: Optional[Path] = None) -> None:
        self._socket_path = socket_path if socket_path is not None else Path(f'/srv/tophat/{uuid.uuid4()}.socket')
        self._device_map: DeviceMap = {}
        self._hat_map: HatMap = {}
        self._manager: mp_mngr.SyncManager() = mp.Manager()

    @staticmethod
    def _await_request(client_socket: socket.socket) -> Optional[CommandRequest[DeviceType, ResultType]]:
        try:
            request: Any = pickle.loads(client_socket.recv(MAX_SEND_RECV_SIZE))
            if not isinstance(request, CommandRequest):
                LOGGER.error(f'Received unexpected tophat request of type: {type(request)}')
                return None

            LOGGER.debug(f'Received {type(request.command).__name__} targeting device {request.device_name}')
            return request

        except OSError as socket_error:
            LOGGER.error(f'Failed to communicate with client: {socket_error}')

        except pickle.UnpicklingError as unpickling_error:
            LOGGER.error(f'Received malformed tophat request: {unpickling_error}')

        except pickle.PicklingError as pickling_error:
            LOGGER.error(f'Failed to pickle response: {pickling_error}')

    def _handle_request(self: Self,
                        process_pool: ProcessPoolExecutor,
                        client_socket: socket.socket,
                        request: CommandRequest[DeviceType, ResultType]) -> None:
        if request.device_name not in self._device_map:
            LOGGER.error(f'Unknown device ID: {request.device_name}')
            client_socket.sendall(pickle.dumps(CommandResponse.from_error(ResponseCode.ERROR_INVALID_DEVICE)))
            client_socket.shutdown(socket.SHUT_WR)
            return

        target_device: BaseDeviceType
        device_lock: mp_sync.Lock
        target_device, device_lock = self._device_map[request.device_name]
        if isinstance(request.command, AsyncCommand):
            LOGGER.debug(f'Running {type(request.command).__name__} asynchronously on device {target_device.name}...')
            try:
                result_future: Future[ResultType] = process_pool.submit(target_device.run, device_lock, request.command)
                result_future.result(0.0)
            except TimeoutError:
                pass
            LOGGER.debug(f'Command left to run asynchronously')
            client_socket.sendall(pickle.dumps(CommandResponse.from_success(None)))
            client_socket.shutdown(socket.SHUT_WR)
            return

        else:
            LOGGER.debug(f'Running {type(request.command).__name__} on device {target_device.name}...')
            result_future: Future[ResultType] = process_pool.submit(target_device.run, device_lock, request.command)
            result_future.add_done_callback(partial(_result_callback, client_socket))
            return


@final
class HatBox(Generic[HatType]):

    @property
    def hat(self: Self) -> HatType:
        return self._hat

    def start(self: Self) -> bool:
        try:
            self._container = self._docker_client.containers.run(image=self._hat.image_name,
                                                                 detach=True,
                                                                 auto_remove=True,
                                                                 cpu_percent=25,
                                                                 volumes=self._container_volumes,
                                                                 **self._hat.extra_docker_args)
            return True

        except DockerException:
            return False

    def stop(self: Self):
        if self._container is not None:
            self._container.stop(timeout=8)
        self._docker_client.close()

    @override
    def __init__(self,
                 tophat: TopHatServer,
                 hat: HatType) -> None:
        self._tophat: TopHatServer = tophat
        self._hat: HatType = hat
        self._docker_client: DockerClient = DockerClient.from_env()
        self._container: Optional[Container] = None

    @property
    def _container_volumes(self: Self):
        return {
            str(self._tophat.socket_path): {
                'bind': str(HAT_SOCKET_PATH),
                'mode': 'rw'
            }
        }
