#!/bin/bash
set -e

# Update system
dnf update -y

# Install NATS CLI tools
cd /tmp
curl -L https://github.com/nats-io/natscli/releases/download/v0.1.5/nats-0.1.5-linux-amd64.tar.gz | tar -xz
mv nats /usr/local/bin/
chmod +x /usr/local/bin/nats

# Install nats-bench (different approach - build from source)
dnf install -y golang
export GOPATH=/root/go
go install github.com/nats-io/nats.go/examples/nats-bench@latest
mv /root/go/bin/nats-bench /usr/local/bin/
chmod +x /usr/local/bin/nats-bench

# Install Python and testing tools
dnf install -y python3 python3-pip
pip3 install nats-py

# Install monitoring tools
dnf install -y htop nc telnet

# Create test scripts
mkdir -p /home/ec2-user/load-tests
cat > /home/ec2-user/test-nats-connection.sh << 'SCRIPT'
#!/bin/bash
NATS_URL="nats://nats-production-1dd94609d95c94d4.elb.us-east-1.amazonaws.com:4222"
echo "Testing NATS connectivity..."
nats --server $NATS_URL pub test.connectivity "Hello from bastion"
echo "✅ Connection test complete"
SCRIPT

chmod +x /home/ec2-user/test-nats-connection.sh
chown ec2-user:ec2-user /home/ec2-user/test-nats-connection.sh
chown ec2-user:ec2-user /home/ec2-user/load-tests

echo "Bastion setup complete" > /tmp/bastion-ready

