def test_try_send_aws_log(dev_integration_aws_cloudwatch):
    logs = "testing probe"
    result = dev_integration_aws_cloudwatch.send_logs([logs])
    assert result is True

