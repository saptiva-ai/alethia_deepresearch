#!/bin/bash

# ===========================================
# Server Setup Script for Aletheia Deployment
# Installs Docker and configures the server
# ===========================================

set -euo pipefail

# Load environment variables
if [[ -f ".env" ]]; then
    source .env
fi

# Server configuration from .env
SERVER_IP="${PROD_IP:-}"
SSH_USER="${PORD_SSH_USER:-}"
SSH_KEY="${SSH_KEY_PATH:-$HOME/.ssh/id_ed25519}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Help function
usage() {
    cat << EOF
🔧 Aletheia Server Setup Script

Usage: $0 [OPTIONS]

Options:
    -s, --server        Server IP address [default: from .env PROD_IP]
    -u, --user          SSH user [default: from .env PORD_SSH_USER]
    -k, --key           SSH key path [default: from .env SSH_KEY_PATH]
    -h, --help          Show this help message

This script will:
    - Install Docker
    - Configure Docker for non-root user
    - Install Docker Compose
    - Create necessary directories
    - Configure firewall (if needed)

EOF
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -s|--server)
            SERVER_IP="$2"
            shift 2
            ;;
        -u|--user)
            SSH_USER="$2"
            shift 2
            ;;
        -k|--key)
            SSH_KEY="$2"
            shift 2
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            usage
            exit 1
            ;;
    esac
done

# Validate required parameters
if [[ -z "$SERVER_IP" ]]; then
    log_error "Server IP is required. Set PROD_IP in .env or use -s option"
    exit 1
fi

if [[ -z "$SSH_USER" ]]; then
    log_error "SSH user is required. Set PORD_SSH_USER in .env or use -u option"
    exit 1
fi

log_info "🔧 Setting up server for Aletheia deployment..."
log_info "Target Server: $SSH_USER@$SERVER_IP"

# Check SSH connection
check_connection() {
    log_info "🔍 Testing SSH connection..."
    if ! ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$SSH_USER@$SERVER_IP" "echo 'SSH connection successful'" &> /dev/null; then
        log_error "Cannot connect to $SSH_USER@$SERVER_IP via SSH"
        exit 1
    fi
    log_success "SSH connection successful"
}

# Detect OS
detect_os() {
    log_info "🔍 Detecting operating system..."
    OS=$(ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "cat /etc/os-release | grep ^ID= | cut -d'=' -f2 | tr -d '\"'")
    VERSION=$(ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "cat /etc/os-release | grep ^VERSION_ID= | cut -d'=' -f2 | tr -d '\"'")

    log_info "Detected OS: $OS $VERSION"

    case $OS in
        ubuntu|debian)
            PACKAGE_MANAGER="apt-get"
            ;;
        centos|rhel|rocky|almalinux)
            PACKAGE_MANAGER="yum"
            ;;
        fedora)
            PACKAGE_MANAGER="dnf"
            ;;
        *)
            log_error "Unsupported OS: $OS"
            exit 1
            ;;
    esac
}

# Update system
update_system() {
    log_info "📦 Updating system packages..."

    case $PACKAGE_MANAGER in
        apt-get)
            ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "sudo apt-get update && sudo apt-get upgrade -y"
            ;;
        yum)
            ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "sudo yum update -y"
            ;;
        dnf)
            ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "sudo dnf update -y"
            ;;
    esac

    log_success "System updated"
}

# Install Docker
install_docker() {
    log_info "🐳 Installing Docker..."

    # Check if Docker is already installed
    if ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "command -v docker &> /dev/null"; then
        log_info "Docker is already installed"
        return 0
    fi

    case $PACKAGE_MANAGER in
        apt-get)
            ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "
                # Install prerequisites
                sudo apt-get install -y ca-certificates curl gnupg lsb-release

                # Add Docker's official GPG key
                sudo mkdir -p /etc/apt/keyrings
                curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg

                # Set up repository
                echo \"deb [arch=\$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \$(lsb_release -cs) stable\" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null

                # Install Docker Engine
                sudo apt-get update
                sudo apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            "
            ;;
        yum|dnf)
            ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "
                # Install prerequisites
                sudo $PACKAGE_MANAGER install -y yum-utils

                # Add Docker repository
                sudo yum-config-manager --add-repo https://download.docker.com/linux/centos/docker-ce.repo

                # Install Docker Engine
                sudo $PACKAGE_MANAGER install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
            "
            ;;
    esac

    log_success "Docker installed"
}

# Configure Docker
configure_docker() {
    log_info "⚙️ Configuring Docker..."

    # Start and enable Docker service
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "
        sudo systemctl start docker
        sudo systemctl enable docker
    "

    # Add user to docker group
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "
        sudo usermod -aG docker $SSH_USER
    "

    log_success "Docker configured"
    log_warning "Note: You may need to log out and back in for group changes to take effect"
}

# Create directories
create_directories() {
    log_info "📁 Creating application directories..."

    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "
        mkdir -p ~/alethia-deployment/{logs,runs,config,backups}
        chmod 755 ~/alethia-deployment
        chmod 755 ~/alethia-deployment/{logs,runs,config,backups}
    "

    log_success "Directories created"
}

# Configure firewall (optional)
configure_firewall() {
    log_info "🔥 Configuring firewall..."

    # Check if ufw is available (Ubuntu/Debian)
    if ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "command -v ufw &> /dev/null"; then
        ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "
            # Allow SSH (keep current connection)
            sudo ufw allow ssh

            # Allow application port
            sudo ufw allow 8000/tcp

            # Enable firewall (only if not already enabled)
            sudo ufw status | grep -q 'Status: active' || sudo ufw --force enable
        "
        log_success "UFW firewall configured"
    # Check if firewalld is available (RHEL/CentOS)
    elif ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "command -v firewall-cmd &> /dev/null"; then
        ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "
            sudo systemctl start firewalld
            sudo systemctl enable firewalld

            # Allow application port
            sudo firewall-cmd --permanent --add-port=8000/tcp
            sudo firewall-cmd --reload
        "
        log_success "Firewalld configured"
    else
        log_warning "No firewall management tool found. Manual configuration may be needed."
    fi
}

# Test Docker installation
test_docker() {
    log_info "🧪 Testing Docker installation..."

    # Test Docker command (may need to use sudo for first time)
    if ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "docker --version &> /dev/null"; then
        log_success "Docker is working"
    elif ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "sudo docker --version &> /dev/null"; then
        log_success "Docker is working (with sudo)"
        log_warning "User may need to log out/in for docker group to take effect"
    else
        log_error "Docker installation test failed"
        exit 1
    fi

    # Test with hello-world (using sudo if needed)
    log_info "Running Docker hello-world test..."
    if ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "docker run --rm hello-world &> /dev/null"; then
        log_success "Docker hello-world test passed"
    elif ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "sudo docker run --rm hello-world &> /dev/null"; then
        log_success "Docker hello-world test passed (with sudo)"
    else
        log_error "Docker hello-world test failed"
        exit 1
    fi
}

# Show server info
show_server_info() {
    log_info "📊 Server Information:"
    echo

    # System info
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "
        echo 'OS Info:'
        cat /etc/os-release | grep PRETTY_NAME
        echo
        echo 'System Resources:'
        echo 'CPU:' \$(nproc) 'cores'
        echo 'Memory:' \$(free -h | awk '/^Mem:/ {print \$2}')
        echo 'Disk:' \$(df -h / | awk 'NR==2 {print \$4}' | head -1) 'available'
        echo
        echo 'Docker Version:'
        docker --version 2>/dev/null || sudo docker --version
        echo
        echo 'Docker Compose Version:'
        docker compose version 2>/dev/null || sudo docker compose version 2>/dev/null || echo 'Docker Compose not available'
    "
}

# Main execution
main() {
    log_info "🎯 Aletheia Server Setup"
    log_info "========================"

    check_connection
    detect_os
    update_system
    install_docker
    configure_docker
    create_directories
    configure_firewall
    test_docker
    show_server_info

    log_success "🎉 Server setup completed successfully!"
    log_info "Your server is now ready for Aletheia deployment."
    log_info "You can now run: ./scripts/deployment/deploy-remote.sh"
}

# Execute main function
main "$@"