# Container-to-Cloud resender utility (CCRU)

This cli utility is supposed to send logs from a container to a cloud logs storage
Main feature is that it is very easy to add support for container tool and 
cloud logging provider of your choice

# Setup
Before starting to use this tool user have to install and set up dependencies, such
as Docker or AWS IAM to ensure this tool is able to use them

### For example, if you use docker:
Assuming tool is running on Ubuntu, you can install docker with the following command:
```bash
sudo apt get install docker -y
```
The next step is to retrieve AWS CloudWatchLogs credentials. And then we are ready 
to install CCRU
# Installation

local install:
```bash
python -m pip install -e .
```

Or from github repository:
```bash
python -m pip install git+https://github.com/ScriptHound/container_to_cloud_logs_sender.git
```


# Usage
When all is set use the tool like that:
```bash
ccru --docker-image=bash:latest --bash-command="bash -c 'echo hello'" --aws-cloudwatch-group=my-post-dev-group-1 --aws-cloudwatch-stream=my-post-dev-stream-1 --aws-access-key-id=aws_id --aws-secret-key=aws_key --aws-region=us-west-2
```

Or, if you are developing the project you can start try the tool in a following manner
```bash
python src --docker-image=bash:latest --bash-command="bash -c 'echo hello'" --aws-cloudwatch-group=my-post-dev-group-1 --aws-cloudwatch-stream=my-post-dev-stream-1 --aws-access-key-id=aws_id --aws-secret-key=aws_key --aws-region=us-west-2
```

## Writing support for additional cloud or container providers

To add support for example, for Azure cloud you just have to write your own
class which implements ICloudMonitoringService interface, which is located at src/services.py

```python
class ICloudMonitoringService(ABC):

    @abstractmethod
    def send_logs(self, logs: str) -> bool:
        pass

    # arguments really depend on concrete cloud provider
    @abstractmethod
    def get_logs(self, start_time: int, end_time: int, max_logs: Optional[int] = 100) -> str:
        pass
```

If you need to add support for your own container provider you will have to implement
IContainerDeploymentService which is located at src/services.py for brevity sake
I did not provide interface code itself in this README.md, for details check the code


# Testing
For testing purposes environment variables must be defined with following commands:
```bash
export DOCKER_HOST=unix:///var/run/docker.sock
export LOGS_MONITORING_AWS_SECRET_KEY_TEST=key
export LOGS_MONITORING_AWS_ACCESS_KEY_TEST=key
```

Example at tests/test_environment_export_example.sh is also provided

Then just write
```bash
pytest
```