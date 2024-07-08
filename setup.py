from setuptools import find_packages, setup

BASE_DEPS = (
    "docker==7.1.0",
    "boto3==1.34.139",
    "botocore==1.34.139",
    "pydantic==2.8.2",
)

setup(
    name = "CCRU",
    version = "1.0.0",
    author = "Seva Syrov",
    license = "MIT",
    description = "container to cloud transmission tool",
    py_modules = ["src"],
    packages = find_packages(),
    python_requires=">=3.12",
    install_requires=BASE_DEPS,
    classifiers=[
        "Programming Language :: Python :: 3.12",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points = """
        [console_scripts]
        ccru=src.main:main
    """
)
