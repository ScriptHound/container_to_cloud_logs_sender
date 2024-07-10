import argparse
import asyncio
import datetime
import logging

from src.services import AsyncAwsCloudWatchService, DockerDeploymentService
from src.usecases import AsyncAwsLogsUseCase
from src.validation import DockerCredentials, ProgramArguments


def get_cli_arguments():
    parser = argparse.ArgumentParser()
    parser.add_argument("--docker-image", type=str, required=True)
    parser.add_argument("--bash-command", type=str, required=True)
    parser.add_argument("--aws-cloudwatch-group", type=str, required=True)
    parser.add_argument("--aws-cloudwatch-stream", type=str, required=True)
    parser.add_argument("--aws-access-key-id", type=str, required=True)
    parser.add_argument("--aws-secret-key", type=str, required=True)
    parser.add_argument("--aws-region", type=str, required=True)
    parser.add_argument("--docker-username", type=str, required=False)
    parser.add_argument("--docker-password", type=str, required=False)
    return parser.parse_args()


def main():
    logging.basicConfig(level=logging.INFO)

    arguments = get_cli_arguments()
    validated_arguments = ProgramArguments(**vars(arguments))
    docker_arguments = DockerCredentials(**vars(arguments))

    aws_cloudwatch_service = AsyncAwsCloudWatchService(validated_arguments)
    container_service = DockerDeploymentService(docker_arguments)
    logs_monitoring_usecase = AsyncAwsLogsUseCase(container_service, aws_cloudwatch_service, validated_arguments)

    start_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(minutes=1)).timestamp()
    loop_coro = logs_monitoring_usecase.loop(validated_arguments.docker_image, validated_arguments.bash_command)
    asyncio.run(loop_coro)
    end_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=1)).timestamp()
