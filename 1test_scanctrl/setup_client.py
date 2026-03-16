from setuptools import setup, find_packages

setup(
    name="your_service_client",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "click",
        "requests"
    ],
    entry_points={
        "console_scripts": [
            "your-service-cli=client.cli:cli",
        ],
    },
    python_requires=">=3.7",
)
