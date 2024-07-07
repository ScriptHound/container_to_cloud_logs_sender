import datetime


def test_loop(dev_aws_cloudwatch_usecase):
    start_time = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).timestamp()
    dev_aws_cloudwatch_usecase.loop("bash:latest", 'bash -c "echo hello"')
    end_time = (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=1)).timestamp()
    logs = dev_aws_cloudwatch_usecase.get_logs_from_cloud(start_time, end_time)
    assert logs != []


