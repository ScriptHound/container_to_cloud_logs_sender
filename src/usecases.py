from abc import ABC, abstractmethod
from typing import Generator, Optional

from src.services import ICloudMonitoringService, IContainerDeploymentService
from src.validation import ProgramArguments


class ILogsMonitoringUseCase(ABC):
    @abstractmethod
    def get_logs_from_container(self) -> Generator[bytes, None, None]:
        pass

    @abstractmethod
    def run_bash_command_on_container(self, bash_command: str) -> str:
        pass

    @abstractmethod
    def send_logs_to_cloud(self, logs: str) -> None:
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

    def get_logs_from_container(self) -> Generator[bytes, None, None]:
        return self.container_service.get_logs()

    def get_logs_from_cloud(self, start_time: int, end_time: int) -> str:
        return self.cloud_service.get_logs(int(start_time * 1000), int(end_time * 1000))

    def run_bash_command_on_container(self, bash_command: str) -> str:
        return self.container_service.run_bash_command(bash_command)

    def send_logs_to_cloud(self, logs: str) -> None:
        self.cloud_service.send_logs(logs)

    def loop(self, image_name: str, bash_command: str) -> None:
        self.container_service.login()
        self.container_service.pull_image(image_name)
        self.container_service.run_container(bash_command)

        while self.container_service.container_is_running():
            logs_generator = self.get_logs_from_container()
            for log in logs_generator:
                success = self.cloud_service.send_logs(log.decode("utf-8"))
                if not success:
                    raise Exception("Failed to send logs to cloudwatch")

        post_mortem_logs = self.get_logs_from_container()
        for log in post_mortem_logs:
            self.cloud_service.send_logs(log.decode("utf-8"))
