import argparse
import logging

from src.services import AwsCloudWatchService, DockerDeploymentService
from src.usecases import AwsCloudWatchUseCase
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
    arguments = get_cli_arguments()
    validated_arguments = ProgramArguments(**vars(arguments))
    docker_arguments = DockerCredentials(**vars(arguments))

    aws_cloudwatch_service = AwsCloudWatchService(validated_arguments)
    container_service = DockerDeploymentService(docker_arguments)

    result = aws_cloudwatch_service.send_logs("testing probe")
    if not result:
        logging.error("Failed to send logs to cloudwatch")


if __name__ == "__main__":
    main()
