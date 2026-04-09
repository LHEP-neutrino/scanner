#!/bin/bash
# Create system user
sudo useradd --system --no-create-home --shell /usr/sbin/nologin myproject

# Create directories
sudo mkdir -p /etc/myproject
sudo mkdir -p /opt/myproject

# Install config
sudo cp config.yaml /etc/myproject/config.yaml
sudo chown root:myproject /etc/myproject/config.yaml
sudo chmod 640 /etc/myproject/config.yaml

# Create secrets file
sudo touch /etc/myproject/secrets.env
sudo chmod 600 /etc/myproject/secrets.env
echo "MYPROJECT_API_KEY=changeme" | sudo tee /etc/myproject/secrets.env

# Install venv
sudo python3 -m venv /opt/myproject/venv
sudo /opt/myproject/venv/bin/pip install .

# Install and enable service
sudo cp myproject_server.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable myproject_server