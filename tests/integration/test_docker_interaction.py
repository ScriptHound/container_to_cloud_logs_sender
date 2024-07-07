import datetime
import logging

logging.basicConfig(level=logging.INFO)


def test_docker_interactions_dont_raise_exception(dev_integration_container_service):
    dev_integration_container_service.login()
    dev_integration_container_service.pull_image("bash:latest")
    dev_integration_container_service.run_container('bash -c "echo hello"')

    while dev_integration_container_service.container_is_running():
        pass

    logs = dev_integration_container_service.get_logs()
    logs_str = ""
    for log in logs:
        logs_str += log.decode("utf-8")
    assert "hello" in logs_str

    dev_integration_container_service.stop_container()
    dev_integration_container_service.remove_container()
