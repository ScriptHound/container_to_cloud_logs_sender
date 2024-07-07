import os
from datetime import datetime
from typing import Optional

import pytest

from src.services import (
    AwsCloudWatchService,
    DockerDeploymentService,
    ICloudMonitoringService,
    IContainerDeploymentService,
)
from src.usecases import AwsCloudWatchUseCase
from src.validation import DockerCredentials, ProgramArguments


@pytest.fixture
def integration_program_arguments():
    return ProgramArguments(
        docker_image="bash:latest",
        bash_command="echo hello",
        aws_cloudwatch_group="test-task-group-1",
        aws_cloudwatch_stream="test-task-stream-1",
        aws_access_key_id=os.getenv("LOGS_MONITORING_AWS_ACCESS_KEY_TEST"),
        aws_secret_key=os.getenv("LOGS_MONITORING_AWS_SECRET_KEY_TEST"),
        aws_region="us-west-2"
    )


@pytest.fixture
def dev_integration_aws_cloudwatch(integration_program_arguments):
    if (
            integration_program_arguments.aws_secret_key is None
            or integration_program_arguments.aws_access_key_id is None
    ):
        raise ValueError("no access key and access key set, set them using LOGS_MONITORING_AWS_ACCESS_KEY_TEST and "
                         "LOGS_MONITORING_AWS_ACCESS_ACCESS_TEST environment variables")

    return AwsCloudWatchService(integration_program_arguments)


@pytest.fixture
def dev_integration_container_service():
    return DockerDeploymentService()


@pytest.fixture
def dev_aws_cloudwatch_usecase(dev_integration_aws_cloudwatch, dev_integration_container_service):
    return AwsCloudWatchUseCase(dev_integration_container_service, dev_integration_aws_cloudwatch)


@pytest.fixture
def mock_cloudwatch_service():
    class MockCloudWatchService(ICloudMonitoringService):
        def __init__(self, arguments: ProgramArguments):
            self.aws_access_key_id = arguments.aws_access_key_id
            self.aws_secret_key = arguments.aws_secret_key
            self.aws_region = arguments.aws_region
            self.cloudwatch_group = arguments.aws_cloudwatch_group
            self.cloudwatch_stream = arguments.aws_cloudwatch_stream

        def send_logs(self, logs: str) -> None:
            pass

    return MockCloudWatchService


@pytest.fixture
def mock_container_service():
    class MockContainerService(IContainerDeploymentService):
        def __init__(self, credentials: Optional[DockerCredentials]):
            self.docker_username = credentials.username or ""
            self.docker_password = credentials.password or ""

        def pull_image(self, image_name: str) -> None:
            pass

        def run_container(self, command: str) -> None:
            pass

        def run_bash_command(self, command: str) -> str:
            return "hello"

        def get_logs(self, since: datetime) -> str:
            return "hello"

    return MockContainerService
