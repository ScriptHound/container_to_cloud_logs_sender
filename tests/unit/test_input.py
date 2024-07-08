import sys

import pytest

from src.main import get_cli_arguments
from src.validation import DockerCredentials, ProgramArguments


def test_no_exceptions(mock_cloudwatch_service, mock_container_service, monkeypatch):
    monkeypatch.setattr(sys, "argv", [
        "main.py",
        "--docker-image", "test-image",
        "--bash-command", "echo hello",
        "--aws-cloudwatch-group", "test-group",
        "--aws-cloudwatch-stream", "test-stream",
        "--aws-access-key-id", "test-access-key",
        "--aws-secret-key", "test-secret-key",
        "--aws-region", "test-region",
        "--docker-username", "test-username",
        "--docker-password", "test-password"
    ])

    arguments = get_cli_arguments()
    ProgramArguments(**vars(arguments))
    DockerCredentials(**vars(arguments))


def test_raises_exception_if_no_required_arguments(mock_cloudwatch_service, mock_container_service, monkeypatch):
    with pytest.raises(SystemExit):
        monkeypatch.setattr(sys, "argv", [
            "main.py",
            "--docker-image", "test-image",
            "--bash-command", "echo hello",
            "--aws-cloudwatch-group", "test-group",
            "--aws-cloudwatch-stream", "test-stream",
            "--aws-access-key-id", "test-access-key",
            "--aws-secret-access-key", "test-secret-key",
            "--docker-username", "test-username",
            "--docker-password", "test-password"
        ])
        arguments = get_cli_arguments()
        ProgramArguments(**vars(arguments))




