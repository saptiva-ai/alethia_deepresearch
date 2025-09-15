#!/bin/bash

# ===========================================
# Aletheia Remote Server Deployment Script
# Deployments via SSH to internal servers
# ===========================================

set -euo pipefail

# Load environment variables
if [[ -f ".env" ]]; then
    source .env
fi

# Default values
ENVIRONMENT="production"
IMAGE_TAG="latest"
REGISTRY="ghcr.io/saptiva-ai/alethia_deepresearch"
CONTAINER_NAME="aletheia-deepresearch"
PORT="8000"
DRY_RUN=false
VERBOSE=false
BUILD_LOCAL=true

# Server configuration from .env
SERVER_IP="${PROD_IP:-}"
SSH_USER="${PORD_SSH_USER:-}"
SSH_KEY="${SSH_KEY_PATH:-$HOME/.ssh/id_rsa}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
usage() {
    cat << EOF
🚀 Aletheia Remote Server Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment    Target environment [default: production]
    -t, --tag           Docker image tag [default: latest]
    -s, --server        Server IP address [default: from .env PROD_IP]
    -u, --user          SSH user [default: from .env PORD_SSH_USER]
    -k, --key           SSH key path [default: ~/.ssh/id_rsa]
    -p, --port          Application port [default: 8000]
    -r, --registry      Docker registry [default: ghcr.io/saptiva-ai/alethia_deepresearch]
    --no-build          Skip local Docker build
    -d, --dry-run       Preview changes without applying
    -v, --verbose       Enable verbose output
    -h, --help          Show this help message

Examples:
    $0                                      # Deploy to production server from .env
    $0 -t v1.2.3 --verbose                # Deploy specific version with verbose output
    $0 -s 192.168.1.100 -u myuser         # Deploy to custom server
    $0 --dry-run                           # Preview deployment without executing

Server Configuration (from .env):
    PROD_IP=$SERVER_IP
    PORD_SSH_USER=$SSH_USER

EOF
}

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

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -e|--environment)
            ENVIRONMENT="$2"
            shift 2
            ;;
        -t|--tag)
            IMAGE_TAG="$2"
            shift 2
            ;;
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
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        --no-build)
            BUILD_LOCAL=false
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
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

FULL_CONTAINER_NAME="${CONTAINER_NAME}-${ENVIRONMENT}"
IMAGE_NAME="${REGISTRY}:${IMAGE_TAG}"

log_info "🚀 Starting Aletheia remote deployment..."
log_info "Target Server: $SSH_USER@$SERVER_IP"
log_info "Environment: $ENVIRONMENT"
log_info "Container: $FULL_CONTAINER_NAME"
log_info "Image: $IMAGE_NAME"
log_info "Port: $PORT"
log_info "Build Local: $BUILD_LOCAL"
log_info "Dry Run: $DRY_RUN"

# Check prerequisites
check_prerequisites() {
    log_info "🔍 Checking prerequisites..."

    # Check SSH key
    if [[ ! -f "$SSH_KEY" ]]; then
        log_error "SSH key not found: $SSH_KEY"
        exit 1
    fi

    # Check Docker (if building locally)
    if [[ "$BUILD_LOCAL" == "true" ]]; then
        if ! command -v docker &> /dev/null; then
            log_error "Docker is required for local builds"
            exit 1
        fi

        if ! docker info &> /dev/null; then
            log_error "Docker daemon is not running"
            exit 1
        fi
    fi

    # Test SSH connection
    log_info "Testing SSH connection to $SSH_USER@$SERVER_IP..."
    if [[ "$DRY_RUN" == "false" ]]; then
        if ! ssh -i "$SSH_KEY" -o BatchMode=yes -o ConnectTimeout=10 "$SSH_USER@$SERVER_IP" "echo 'SSH connection successful'" &> /dev/null; then
            log_error "Cannot connect to $SSH_USER@$SERVER_IP via SSH"
            log_error "Check your SSH key and server access"
            exit 1
        fi
    fi

    log_success "Prerequisites check passed"
}

# Build Docker image locally
build_image() {
    if [[ "$BUILD_LOCAL" == "false" ]]; then
        log_info "⏩ Skipping local Docker build"
        return 0
    fi

    log_info "🔨 Building Docker image locally..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would build image: $IMAGE_NAME"
        return 0
    fi

    local build_cmd="docker build -t $IMAGE_NAME --target production ."

    if [[ "$VERBOSE" == "true" ]]; then
        log_info "Running: $build_cmd"
        eval "$build_cmd"
    else
        eval "$build_cmd" > /dev/null 2>&1
    fi

    if [[ $? -eq 0 ]]; then
        log_success "Docker image built successfully"
    else
        log_error "Failed to build Docker image"
        exit 1
    fi
}

# Save and transfer Docker image
transfer_image() {
    log_info "📦 Transferring Docker image to server..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would transfer image to server"
        return 0
    fi

    local temp_image="/tmp/alethia-$(date +%s).tar"

    # Save Docker image to tar file
    log_info "Saving Docker image to: $temp_image"
    docker save "$IMAGE_NAME" -o "$temp_image"

    # Transfer to server
    log_info "Transferring image to server..."
    if [[ "$VERBOSE" == "true" ]]; then
        scp -i "$SSH_KEY" "$temp_image" "$SSH_USER@$SERVER_IP:/tmp/"
    else
        scp -i "$SSH_KEY" "$temp_image" "$SSH_USER@$SERVER_IP:/tmp/" > /dev/null 2>&1
    fi

    # Load image on server
    log_info "Loading image on server..."
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "docker load -i $temp_image && rm -f $temp_image"

    # Clean up local temp file
    rm -f "$temp_image"

    log_success "Image transferred and loaded successfully"
}

# Transfer configuration files
transfer_config() {
    log_info "📁 Transferring configuration files..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would transfer configuration files"
        return 0
    fi

    # Create deployment directory on server
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "mkdir -p ~/aletheia-deployment/{logs,runs,config}"

    # Transfer environment file
    local env_file=".env.${ENVIRONMENT}"
    if [[ -f "$env_file" ]]; then
        log_info "Transferring $env_file..."
        scp -i "$SSH_KEY" "$env_file" "$SSH_USER@$SERVER_IP:~/aletheia-deployment/.env"
    else
        log_warning "Environment file $env_file not found, using default .env"
        scp -i "$SSH_KEY" ".env" "$SSH_USER@$SERVER_IP:~/aletheia-deployment/.env"
    fi

    # Transfer docker deployment script
    log_info "Transferring deployment script..."
    scp -i "$SSH_KEY" "scripts/deployment/deploy-docker.sh" "$SSH_USER@$SERVER_IP:~/alethia-deployment/"

    # Make script executable
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "chmod +x ~/alethia-deployment/deploy-docker.sh"

    log_success "Configuration files transferred"
}

# Deploy on remote server
deploy_remote() {
    log_info "🚀 Deploying application on remote server..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would deploy application on server"
        return 0
    fi

    # Prepare deployment command
    local deploy_cmd="cd ~/alethia-deployment && ./deploy-docker.sh"
    deploy_cmd+=" --environment $ENVIRONMENT"
    deploy_cmd+=" --tag $IMAGE_TAG"
    deploy_cmd+=" --port $PORT"
    deploy_cmd+=" --registry $REGISTRY"

    if [[ "$VERBOSE" == "true" ]]; then
        deploy_cmd+=" --verbose"
    fi

    log_info "Executing remote deployment..."
    if [[ "$VERBOSE" == "true" ]]; then
        ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "$deploy_cmd"
    else
        ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "$deploy_cmd" 2>&1 | grep -E "(SUCCESS|ERROR|WARNING|INFO)"
    fi

    if [[ ${PIPESTATUS[0]} -eq 0 ]]; then
        log_success "Remote deployment completed successfully"
    else
        log_error "Remote deployment failed"
        exit 1
    fi
}

# Verify deployment
verify_deployment() {
    log_info "🧪 Verifying deployment..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would verify deployment"
        return 0
    fi

    # Check if container is running
    log_info "Checking container status..."
    local container_status=$(ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "docker ps --filter name=$FULL_CONTAINER_NAME --format '{{.Status}}'")

    if [[ -n "$container_status" ]]; then
        log_success "Container is running: $container_status"
    else
        log_error "Container is not running"
        exit 1
    fi

    # Test health endpoint
    log_info "Testing health endpoint..."
    local health_check=$(ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "curl -f -s http://localhost:$PORT/health" 2>/dev/null || echo "failed")

    if [[ "$health_check" != "failed" ]]; then
        log_success "Health check passed"
    else
        log_warning "Health check failed, but container may still be starting"
    fi

    # Show deployment info
    log_info "Deployment information:"
    ssh -i "$SSH_KEY" "$SSH_USER@$SERVER_IP" "docker ps --filter name=$FULL_CONTAINER_NAME --format 'table {{.Names}}\t{{.Status}}\t{{.Ports}}'"
}

# Show access information
show_access_info() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    log_info "🔗 Access Information:"
    echo
    log_info "Application URLs:"
    log_info "  - API: http://$SERVER_IP:$PORT"
    log_info "  - Health: http://$SERVER_IP:$PORT/health"
    log_info "  - Docs: http://$SERVER_IP:$PORT/docs"
    echo
    log_info "SSH Commands:"
    log_info "  - Connect: ssh -i $SSH_KEY $SSH_USER@$SERVER_IP"
    log_info "  - Logs: ssh -i $SSH_KEY $SSH_USER@$SERVER_IP 'docker logs -f $FULL_CONTAINER_NAME'"
    log_info "  - Stop: ssh -i $SSH_KEY $SSH_USER@$SERVER_IP 'docker stop $FULL_CONTAINER_NAME'"
    log_info "  - Restart: ssh -i $SSH_KEY $SSH_USER@$SERVER_IP 'docker restart $FULL_CONTAINER_NAME'"
}

# Main execution
main() {
    log_info "🎯 Aletheia Remote Server Deployment"
    log_info "===================================="

    check_prerequisites
    build_image
    transfer_image
    transfer_config
    deploy_remote
    verify_deployment
    show_access_info

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "🔍 Dry run completed successfully"
        log_info "Run without --dry-run to execute deployment"
    else
        log_success "🎉 Remote deployment completed successfully!"
        log_info "Your application is now running at: http://$SERVER_IP:$PORT"
    fi
}

# Execute main function
main "$@"