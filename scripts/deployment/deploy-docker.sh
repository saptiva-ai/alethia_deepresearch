#!/bin/bash

# ===========================================
# Aletheia Docker Deployment Script
# Para servidores internos usando Docker directamente
# ===========================================

set -euo pipefail

# Default values
ENVIRONMENT="development"
IMAGE_TAG="latest"
REGISTRY="ghcr.io/saptiva-ai/alethia_deepresearch"
CONTAINER_NAME="aletheia-deepresearch"
PORT="8000"
DRY_RUN=false
VERBOSE=false
BACKUP_DATA=true

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
usage() {
    cat << EOF
🐳 Aletheia Docker Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment    Target environment (development|staging|production) [default: development]
    -t, --tag           Docker image tag [default: latest]
    -r, --registry      Docker registry [default: ghcr.io/saptiva-ai/alethia_deepresearch]
    -p, --port          Host port [default: 8000]
    -n, --name          Container name [default: aletheia-deepresearch]
    -d, --dry-run       Preview changes without applying
    -v, --verbose       Enable verbose output
    --no-backup         Skip data backup
    -h, --help          Show this help message

Examples:
    $0 -e development                         # Deploy to development
    $0 -e production -t v1.2.3 -p 80         # Deploy specific version to production on port 80
    $0 -e staging -t latest --dry-run        # Preview staging deployment

Environment variables (.env file will be loaded automatically):
    SAPTIVA_API_KEY=your_api_key
    TAVILY_API_KEY=your_tavily_key
    WEAVIATE_URL=http://localhost:8080
    OPENAI_API_KEY=your_openai_key (optional)

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
        -r|--registry)
            REGISTRY="$2"
            shift 2
            ;;
        -p|--port)
            PORT="$2"
            shift 2
            ;;
        -n|--name)
            CONTAINER_NAME="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --no-backup)
            BACKUP_DATA=false
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

# Validate environment
if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
    log_error "Invalid environment: $ENVIRONMENT"
    log_error "Must be one of: development, staging, production"
    exit 1
fi

# Set container name based on environment
FULL_CONTAINER_NAME="${CONTAINER_NAME}-${ENVIRONMENT}"
IMAGE_NAME="${REGISTRY}:${IMAGE_TAG}"

log_info "🐳 Starting Aletheia Docker deployment..."
log_info "Environment: $ENVIRONMENT"
log_info "Container: $FULL_CONTAINER_NAME"
log_info "Image: $IMAGE_NAME"
log_info "Port: $PORT"
log_info "Dry Run: $DRY_RUN"

# Check prerequisites
check_prerequisites() {
    log_info "🔍 Checking prerequisites..."

    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is required but not installed"
        exit 1
    fi

    # Check Docker daemon
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running"
        exit 1
    fi

    # Check if .env file exists
    if [[ ! -f ".env" ]]; then
        log_warning ".env file not found. Make sure to set environment variables manually."
        if [[ "$ENVIRONMENT" == "production" ]]; then
            log_warning ".env file not found, but production deployment can continue if environment variables are set externally"
        fi
    else
        log_info "Found .env file"
    fi

    log_success "Prerequisites check passed"
}

# Pull latest image
pull_image() {
    log_info "📥 Pulling Docker image: $IMAGE_NAME"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would pull image: $IMAGE_NAME"
        return 0
    fi

    if [[ "$VERBOSE" == "true" ]]; then
        docker pull "$IMAGE_NAME"
    else
        docker pull "$IMAGE_NAME" > /dev/null 2>&1
    fi

    if [[ $? -eq 0 ]]; then
        log_success "Image pulled successfully"
    else
        log_error "Failed to pull image: $IMAGE_NAME"
        exit 1
    fi
}

# Backup existing data
backup_data() {
    if [[ "$BACKUP_DATA" == "false" ]]; then
        log_info "⏩ Skipping data backup"
        return 0
    fi

    log_info "💾 Creating data backup..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would create data backup"
        return 0
    fi

    # Check if container exists and has volumes
    if docker container inspect "$FULL_CONTAINER_NAME" &> /dev/null; then
        local backup_dir="./backups/$(date +%Y-%m-%d_%H-%M-%S)"
        mkdir -p "$backup_dir"

        # Backup volumes (adjust paths as needed)
        local volumes=$(docker inspect "$FULL_CONTAINER_NAME" --format='{{range .Mounts}}{{.Source}}:{{.Destination}} {{end}}')

        if [[ -n "$volumes" ]]; then
            log_info "Backing up container volumes to: $backup_dir"

            while read -r volume; do
                if [[ -n "$volume" ]]; then
                    local src=$(echo "$volume" | cut -d: -f1)
                    local dest=$(echo "$volume" | cut -d: -f2)

                    if [[ -d "$src" ]]; then
                        cp -r "$src" "$backup_dir/$(basename "$dest")" 2>/dev/null || true
                    fi
                fi
            done <<< "$volumes"

            log_success "Data backup completed: $backup_dir"
        else
            log_info "No volumes to backup"
        fi
    else
        log_info "Container $FULL_CONTAINER_NAME does not exist, skipping backup"
    fi
}

# Stop and remove existing container
stop_existing_container() {
    log_info "🛑 Stopping existing container if running..."

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would stop and remove container: $FULL_CONTAINER_NAME"
        return 0
    fi

    if docker container inspect "$FULL_CONTAINER_NAME" &> /dev/null; then
        log_info "Stopping container: $FULL_CONTAINER_NAME"
        docker stop "$FULL_CONTAINER_NAME" > /dev/null 2>&1 || true

        log_info "Removing container: $FULL_CONTAINER_NAME"
        docker rm "$FULL_CONTAINER_NAME" > /dev/null 2>&1 || true

        log_success "Existing container stopped and removed"
    else
        log_info "No existing container found"
    fi
}

# Start new container
start_container() {
    log_info "🚀 Starting new container..."

    # Prepare Docker run command
    local docker_cmd="docker run -d"
    docker_cmd+=" --name $FULL_CONTAINER_NAME"
    docker_cmd+=" --restart unless-stopped"
    docker_cmd+=" -p $PORT:8000"

    # Environment-specific configurations
    case $ENVIRONMENT in
        development)
            docker_cmd+=" -e DEBUG=true"
            docker_cmd+=" -e LOG_LEVEL=DEBUG"
            ;;
        staging)
            docker_cmd+=" -e DEBUG=false"
            docker_cmd+=" -e LOG_LEVEL=INFO"
            ;;
        production)
            docker_cmd+=" -e DEBUG=false"
            docker_cmd+=" -e LOG_LEVEL=WARNING"
            docker_cmd+=" --memory=2g"
            docker_cmd+=" --cpus=2"
            ;;
    esac

    # Add .env file if exists
    if [[ -f ".env" ]]; then
        docker_cmd+=" --env-file .env"
    else
        # Add basic environment variables for production
        docker_cmd+=" -e ENVIRONMENT=$ENVIRONMENT"
        docker_cmd+=" -e DEBUG=false"
        docker_cmd+=" -e LOG_LEVEL=INFO"
    fi

    # Add persistent volumes
    docker_cmd+=" -v $PWD/runs:/app/runs"
    docker_cmd+=" -v $PWD/logs:/app/logs"

    # Add health check
    docker_cmd+=" --health-cmd='curl -f http://localhost:8000/health || exit 1'"
    docker_cmd+=" --health-interval=30s"
    docker_cmd+=" --health-timeout=10s"
    docker_cmd+=" --health-retries=3"

    # Add image
    docker_cmd+=" $IMAGE_NAME"

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run command:"
        echo "$docker_cmd"
        return 0
    fi

    log_info "Running command: $docker_cmd"

    if [[ "$VERBOSE" == "true" ]]; then
        eval "$docker_cmd"
    else
        eval "$docker_cmd" > /dev/null
    fi

    if [[ $? -eq 0 ]]; then
        log_success "Container started successfully"
    else
        log_error "Failed to start container"
        exit 1
    fi
}

# Wait for container to be healthy
wait_for_health() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would wait for container health check"
        return 0
    fi

    log_info "⏳ Waiting for container to be healthy..."

    local max_attempts=30
    local attempt=0

    while [[ $attempt -lt $max_attempts ]]; do
        local health_status=$(docker inspect --format='{{.State.Health.Status}}' "$FULL_CONTAINER_NAME" 2>/dev/null || echo "unknown")

        case $health_status in
            "healthy")
                log_success "Container is healthy!"
                return 0
                ;;
            "unhealthy")
                log_error "Container is unhealthy"

                # Show recent logs
                log_info "Recent container logs:"
                docker logs --tail 20 "$FULL_CONTAINER_NAME"
                exit 1
                ;;
            "starting"|"unknown")
                echo -n "."
                sleep 10
                ((attempt++))
                ;;
        esac
    done

    log_warning "Health check timeout, but container may still be starting"
    log_info "Check container status with: docker logs $FULL_CONTAINER_NAME"
}

# Run basic tests
run_tests() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run basic tests"
        return 0
    fi

    log_info "🧪 Running basic tests..."

    # Test health endpoint
    local health_url="http://localhost:$PORT/health"

    if curl -f -s "$health_url" > /dev/null; then
        log_success "Health endpoint test passed"
    else
        log_warning "Health endpoint test failed"
        log_info "Manual check: curl $health_url"
    fi

    # Test docs endpoint
    local docs_url="http://localhost:$PORT/docs"

    if curl -f -s "$docs_url" > /dev/null; then
        log_success "Documentation endpoint test passed"
    else
        log_warning "Documentation endpoint test failed"
        log_info "Manual check: curl $docs_url"
    fi
}

# Show deployment status
show_status() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi

    log_info "📊 Deployment Status:"
    echo

    # Show container status
    docker ps --filter name="$FULL_CONTAINER_NAME" --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
    echo

    # Show container logs (last 10 lines)
    log_info "Recent logs:"
    docker logs --tail 10 "$FULL_CONTAINER_NAME"
    echo

    # Show resource usage
    log_info "Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}" "$FULL_CONTAINER_NAME"
}

# Cleanup old images
cleanup_images() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would cleanup old images"
        return 0
    fi

    log_info "🧹 Cleaning up old images..."

    # Remove images older than 7 days
    docker image prune -f --filter "until=168h" > /dev/null 2>&1 || true

    log_success "Image cleanup completed"
}

# Main execution
main() {
    log_info "🎯 Aletheia Deep Research Docker Deployment"
    log_info "==========================================="

    check_prerequisites
    pull_image
    backup_data
    stop_existing_container
    start_container
    wait_for_health
    run_tests
    show_status
    cleanup_images

    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "🔍 Dry run completed successfully"
        log_info "Run without --dry-run to apply changes"
    else
        log_success "🎉 Deployment completed successfully!"

        log_info "🔗 Access the application:"
        log_info "  - API: http://localhost:$PORT"
        log_info "  - Health: http://localhost:$PORT/health"
        log_info "  - Docs: http://localhost:$PORT/docs"

        log_info "📋 Useful commands:"
        log_info "  - Logs: docker logs -f $FULL_CONTAINER_NAME"
        log_info "  - Stop: docker stop $FULL_CONTAINER_NAME"
        log_info "  - Restart: docker restart $FULL_CONTAINER_NAME"
        log_info "  - Shell: docker exec -it $FULL_CONTAINER_NAME /bin/bash"
    fi
}

# Execute main function
main "$@"