import logging
import time
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Generator, Optional, List

import aioboto3
import boto3
import docker
from botocore.client import BaseClient
from docker import DockerClient
from docker.models.containers import Container

from src.erorrs import CloudClientQueryError, CloudServerQueryError
from src.validation import DockerCredentials, ProgramArguments


# since a lot of container services use containers in OCI format,
# I let this service know what container exactly is
# being used and what command is being run
class IContainerDeploymentService(ABC):
    image_name: str

    @abstractmethod
    def container_is_running(self) -> bool:
        pass

    @abstractmethod
    def pull_image(self, image_name: str) -> None:
        pass

    @abstractmethod
    def run_container(self, command: Optional[str] = None) -> None:
        pass

    @abstractmethod
    def run_bash_command(self, command: str) -> str:
        pass

    @abstractmethod
    def get_logs(self) -> Generator[bytes, None, None]:
        pass

    @abstractmethod
    def stop_container(self):
        pass

    @abstractmethod
    def remove_container(self):
        pass

    @abstractmethod
    def login(self):
        pass


class DockerDeploymentService(IContainerDeploymentService):
    def __init__(self, credentials: Optional[DockerCredentials] = None):
        if credentials is None:
            self.docker_username = ""
            self.docker_password = ""
        else:
            self.docker_username = credentials.username
            self.docker_password = credentials.password

        self.client: Optional[DockerClient] = None
        self.container: Optional[Container] = None
        self.image_name: Optional[str] = None
        self.time_started: Optional[datetime] = None

    def container_is_running(self) -> bool:
        if self.container is None:
            return False

        container_name = self.container.name
        container = self.client.containers.get(container_name)
        container_state = container.attrs["State"]
        return container_state["Status"] == "running"

    def login(self):
        self.client = docker.from_env()
        if self.docker_username and self.docker_password:
            self.client.login(username=self.docker_username, password=self.docker_password)

    def run_bash_command(self, command: str) -> str:
        if not self.container:
            raise ValueError("Container is not running")

        return str(self.container.exec_run(command))

    def pull_image(self, image_name: str) -> None:
        if image_name not in [image.tags[0] for image in self.client.images.list()]:
            logging.info(f"pulling {image_name}")
            self.client.images.pull(image_name)
        else:
            logging.info(f"{image_name} already exists")
        self.image_name = image_name

    def run_container(self, command: Optional[str] = None) -> None:
        logging.info(f"starting {self.image_name} with command {command}")
        self.time_started = datetime.now(tz=timezone.utc)
        self.container = self.client.containers.run(image=self.image_name, command=command or None, detach=True)

    def get_logs(self) -> Generator[bytes, None, None]:
        if not self.container:
            raise ValueError("Container was not created yet")
        logs = self.container.logs(stream=True)
        return logs

    def stop_container(self):
        if self.container is not None and self.container_is_running():
            self.container.stop()

    def remove_container(self):
        if self.container is not None:
            self.container.remove()


class ICloudMonitoringService(ABC):

    @abstractmethod
    def send_logs(self, logs: List[str]) -> bool:
        pass

    # arguments really depend on concrete cloud provider
    @abstractmethod
    def get_logs(self, start_time: int, end_time: int, max_logs: Optional[int] = 100) -> str:
        pass


class AwsCloudWatchService(ICloudMonitoringService):
    def __init__(self, arguments: ProgramArguments):
        self.aws_access_key_id = arguments.aws_access_key_id
        self.aws_secret_key = arguments.aws_secret_key
        self.aws_region = arguments.aws_region
        self.cloudwatch_group = arguments.aws_cloudwatch_group
        self.cloudwatch_stream = arguments.aws_cloudwatch_stream
        self.client: Optional[BaseClient] = None

    def login(self):
        self.client: BaseClient = boto3.client(
            "logs",
            aws_access_key_id=self.aws_access_key_id,
            aws_secret_access_key=self.aws_secret_key,
            region_name=self.aws_region
        )

        if not self.client.describe_log_groups(logGroupNamePrefix=self.cloudwatch_group)["logGroups"]:
            self.client.create_log_group(logGroupName=self.cloudwatch_group)

        if not self.client.describe_log_streams(
                logGroupName=self.cloudwatch_group,
                logStreamNamePrefix=self.cloudwatch_stream)["logStreams"]:
            self.client.create_log_stream(logGroupName=self.cloudwatch_group, logStreamName=self.cloudwatch_stream)

        self.client.put_retention_policy(
            logGroupName=self.cloudwatch_group,
            retentionInDays=3
        )

    def get_logs(self, start_time: int, end_time: int, max_logs: Optional[int] = 100) -> str:
        self.login()
        response = self.client.start_query(
            logGroupName=self.cloudwatch_group,
            queryString="fields @timestamp, @message | sort @timestamp asc",
            limit=max_logs,
            startTime=round(start_time),
            endTime=round(end_time)
        )

        if response["ResponseMetadata"]["HTTPStatusCode"] // 100 == 4:
            logging.error("Client side error while attempting to get logs from cloudwatch")
            raise CloudClientQueryError("Something went wrong on client side")
        elif response["ResponseMetadata"]["HTTPStatusCode"] // 100 == 5:
            logging.error("Server side error while attempting to get logs from cloudwatch")
            raise CloudServerQueryError("Something went wrong on server side")

        query_id = response["queryId"]

        while True:
            time.sleep(1)
            results = self.client.get_query_results(queryId=query_id)
            if results["status"] in [
                "Complete",
                "Failed",
                "Cancelled",
                "Timeout",
                "Unknown",
            ]:
                return results.get("results", [])

    def send_logs(self, logs: List[str]) -> bool:
        self.login()
        if len(logs) == 0:
            return False
        log_events = [{"timestamp": int(datetime.now().timestamp() * 1000), "message": log} for log in logs]
        response = self.client.put_log_events(
            logGroupName=self.cloudwatch_group,
            logStreamName=self.cloudwatch_stream,
            logEvents=log_events
        )
        return response["ResponseMetadata"]["HTTPStatusCode"] == 200
