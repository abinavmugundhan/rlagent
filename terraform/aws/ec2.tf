# ============================================================================
# AWS EC2 — k3s Server Node
# ============================================================================

data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }

  filter {
    name   = "virtualization-type"
    values = ["hvm"]
  }
}

resource "aws_instance" "k3s_server" {
  ami                    = data.aws_ami.ubuntu.id
  instance_type          = var.ec2_instance_type
  key_name               = var.ec2_key_name
  subnet_id              = aws_subnet.public.id
  vpc_security_group_ids = [aws_security_group.k3s.id]
  iam_instance_profile   = aws_iam_instance_profile.ec2_profile.name

  root_block_device {
    volume_size = 20
    volume_type = "gp3"
  }

  user_data = <<-EOF
    #!/bin/bash
    set -euxo pipefail

    # Install k3s
    curl -sfL https://get.k3s.io | sh -s - server \
      --write-kubeconfig-mode 644

    # Wait for k3s to be ready
    until kubectl get nodes; do sleep 5; done

    # Install Prometheus via Helm
    curl https://raw.githubusercontent.com/helm/helm/main/scripts/get-helm-3 | bash
    helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
    helm repo update
    helm install prometheus prometheus-community/prometheus \
      --namespace monitoring --create-namespace \
      --set server.service.type=NodePort

    # Deploy sample web-app
    kubectl create deployment web-app --image=nginx:alpine --replicas=3
    kubectl expose deployment web-app --port=80 --type=NodePort

    echo "k3s + Prometheus bootstrap complete"
  EOF

  tags = { Name = "rl-autoscaler-k3s-${var.environment}" }
}
