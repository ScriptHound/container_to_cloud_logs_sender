from typing import Optional

from pydantic import BaseModel


class ProgramArguments(BaseModel):
    docker_image: str
    bash_command: str
    aws_cloudwatch_group: str
    aws_cloudwatch_stream: str
    aws_access_key_id: str
    aws_secret_key: str
    aws_region: str


class DockerCredentials(BaseModel):
    username: Optional[str] = None
    password: Optional[str] = None
