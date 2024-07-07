import boto3


def test_loop(dev_aws_cloudwatch_usecase):
    dev_aws_cloudwatch_usecase.loop("bash:latest", 'bash -c "echo hello"')


