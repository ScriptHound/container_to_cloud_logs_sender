import asyncio
import logging
import queue
import threading
from abc import ABC, abstractmethod
from typing import Generator, List, Optional

from src.services import (
    IAsyncCloudMonitoringService,
    ICloudMonitoringService,
    IContainerDeploymentService,
)
from src.validation import ProgramArguments


class ILogsMonitoringUseCase(ABC):
    @abstractmethod
    def get_logs_from_container(self) -> Generator[bytes, None, None]:
        pass

    @abstractmethod
    def run_bash_command_on_container(self, bash_command: str) -> str:
        pass

    @abstractmethod
    def send_logs_to_cloud(self, logs: List[str]) -> None:
        pass

    @abstractmethod
    def loop(self, image_name: str, bash_command: str) -> None:
        pass


class AwsCloudWatchUseCase(ILogsMonitoringUseCase):
    def __init__(
        self,
        container_service: IContainerDeploymentService,
        cloud_service: ICloudMonitoringService,
        arguments: Optional[ProgramArguments] = None,
    ):
        self.cloud_service = cloud_service
        self.container_service = container_service
        self.arguments = arguments
        self.queue = queue.Queue()

    def get_logs_from_container(self) -> Generator[bytes, None, None]:
        return self.container_service.get_logs()

    def get_logs_from_cloud(self, start_time: float, end_time: float) -> str:
        return self.cloud_service.get_logs(int(start_time * 1000), int(end_time * 1000))

    def run_bash_command_on_container(self, bash_command: str) -> str:
        return self.container_service.run_bash_command(bash_command)

    def send_logs_to_cloud(self, logs: List[str]) -> None:
        self.cloud_service.send_logs(logs)

    def logging_loop(self):
        while self.container_service.container_is_running():
            logs_generator = self.get_logs_from_container()
            for log in logs_generator:
                self.queue.put(log.decode("utf-8"))

    def sending_loop(self):
        while not self.queue.empty() or self.container_service.container_is_running():
            log_batch = []
            while not self.queue.empty() or len(log_batch) < 15:
                log_batch.append(self.queue.get())
            if len(log_batch) > 0:
                success = self.cloud_service.send_logs(log_batch)
                if not success:
                    raise Exception("Failed to send logs to cloudwatch")

    def loop(self, image_name: str, bash_command: str) -> None:
        self.container_service.login()
        self.container_service.pull_image(image_name)
        self.container_service.run_container(bash_command)

        logging_thread = threading.Thread(target=self.logging_loop)
        sending_thread = threading.Thread(target=self.sending_loop)

        logging_thread.start()
        sending_thread.start()

        logging_thread.join()
        sending_thread.join()

        post_mortem_logs = self.get_logs_from_container()
        logs = [log.decode("utf-8") for log in post_mortem_logs]
        self.cloud_service.send_logs(logs)


class AsyncAwsLogsUseCase(ILogsMonitoringUseCase):
    def __init__(
        self,
        container_service: IContainerDeploymentService,
        cloud_service: IAsyncCloudMonitoringService,
        arguments: Optional[ProgramArguments] = None,
    ):
        self.cloud_service = cloud_service
        self.container_service = container_service
        self.arguments = arguments
        self.queue = queue.Queue()
        self.semafore = asyncio.Semaphore(29)

    async def send_logs_to_cloud(self, logs: List[str]) -> None:
        async with self.semafore:
            logging.info(logs)
            await self.cloud_service.send_logs(logs)

    async def run_bash_command_on_container(self, bash_command: str) -> str:
        return self.container_service.run_bash_command(bash_command)

    async def get_logs_from_container(self) -> Generator[bytes, None, None]:
        return self.container_service.get_logs()

    def logging_loop(self):
        while self.container_service.container_is_running():
            logs_generator = self.container_service.get_logs()
            for log in logs_generator:
                if log is not None:
                    logging.info(log)
                    self.queue.put(log.decode("utf-8"))

    async def sending_loop(self):
        while not self.queue.empty() or self.container_service.container_is_running():
            # noinspection PyAsyncCall
            if not self.queue.empty():
                log = self.queue.get()
                if log is not None:
                    asyncio.create_task(self.send_logs_to_cloud([log]))
                    await asyncio.sleep(0.1)

    def create_event_loop(self, loop):
        asyncio.set_event_loop(loop)
        asyncio.run_coroutine_threadsafe(self.sending_loop(), loop)
        loop.run_forever()

    async def loop(self, image_name: str, bash_command: str):
        self.container_service.login()
        self.container_service.pull_image(image_name)
        self.container_service.run_container(bash_command)

        logging_thread = threading.Thread(target=self.logging_loop)
        logging_thread.start()

        loop = asyncio.new_event_loop()
        sending_thread = threading.Thread(target=self.create_event_loop, args=(loop,))

        sending_thread.start()
        logging_thread.join()
        sending_thread.join()
