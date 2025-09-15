#!/bin/bash

# ===========================================
# Aletheia Deployment Script
# Supports: development, staging, production
# ===========================================

set -euo pipefail

# Default values
ENVIRONMENT="development"
NAMESPACE=""
IMAGE_TAG="latest"
DRY_RUN=false
VERBOSE=false

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Help function
usage() {
    cat << EOF
🚀 Aletheia Deployment Script

Usage: $0 [OPTIONS]

Options:
    -e, --environment    Target environment (development|staging|production) [default: development]
    -t, --tag           Docker image tag [default: latest]
    -n, --namespace     Kubernetes namespace (auto-generated if not provided)
    -d, --dry-run       Preview changes without applying
    -v, --verbose       Enable verbose output
    -h, --help          Show this help message

Examples:
    $0 -e development                    # Deploy to development
    $0 -e staging -t v1.2.3             # Deploy specific version to staging
    $0 -e production -t v1.2.3 --dry-run # Preview production deployment
    
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
        -n|--namespace)
            NAMESPACE="$2"
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

# Set namespace if not provided
if [[ -z "$NAMESPACE" ]]; then
    case $ENVIRONMENT in
        development) NAMESPACE="aletheia-dev" ;;
        staging) NAMESPACE="aletheia-staging" ;;
        production) NAMESPACE="aletheia-prod" ;;
    esac
fi

log_info "🚀 Starting Aletheia deployment..."
log_info "Environment: $ENVIRONMENT"
log_info "Namespace: $NAMESPACE"
log_info "Image Tag: $IMAGE_TAG"
log_info "Dry Run: $DRY_RUN"

# Check prerequisites
check_prerequisites() {
    log_info "🔍 Checking prerequisites..."
    
    # Check kubectl
    if ! command -v kubectl &> /dev/null; then
        log_error "kubectl is required but not installed"
        exit 1
    fi
    
    # Check kustomize
    if ! command -v kustomize &> /dev/null; then
        log_warning "kustomize not found, using kubectl built-in kustomize"
    fi
    
    # Check cluster connection
    if ! kubectl cluster-info &> /dev/null; then
        log_error "Cannot connect to Kubernetes cluster"
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "📁 Ensuring namespace exists: $NAMESPACE"
    
    if ! kubectl get namespace "$NAMESPACE" &> /dev/null; then
        if [[ "$DRY_RUN" == "true" ]]; then
            log_info "[DRY RUN] Would create namespace: $NAMESPACE"
        else
            kubectl create namespace "$NAMESPACE"
            kubectl label namespace "$NAMESPACE" aletheia.ai/environment="$ENVIRONMENT" --overwrite
            log_success "Created namespace: $NAMESPACE"
        fi
    else
        log_info "Namespace $NAMESPACE already exists"
    fi
}

# Deploy application
deploy_application() {
    log_info "🚀 Deploying Aletheia to $ENVIRONMENT..."
    
    local kustomization_dir="infra/k8s/environments/$ENVIRONMENT"
    
    if [[ ! -d "$kustomization_dir" ]]; then
        log_error "Kustomization directory not found: $kustomization_dir"
        exit 1
    fi
    
    # Update image tag in kustomization
    if [[ "$IMAGE_TAG" != "latest" ]] && [[ "$IMAGE_TAG" != "develop" ]]; then
        log_info "📝 Updating image tag to: $IMAGE_TAG"
        
        # Create temporary kustomization with new tag
        local temp_dir=$(mktemp -d)
        cp -r "$kustomization_dir"/* "$temp_dir/"
        
        # Update image tag in kustomization.yaml
        sed -i.bak "s/newTag: .*/newTag: $IMAGE_TAG/" "$temp_dir/kustomization.yaml"
        kustomization_dir="$temp_dir"
    fi
    
    # Build and apply manifests
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Generated manifests:"
        kubectl kustomize "$kustomization_dir"
    else
        if [[ "$VERBOSE" == "true" ]]; then
            kubectl apply -k "$kustomization_dir" --verbose=2
        else
            kubectl apply -k "$kustomization_dir"
        fi
        log_success "Deployment applied successfully"
    fi
    
    # Clean up temporary directory if created
    if [[ "$IMAGE_TAG" != "latest" ]] && [[ "$IMAGE_TAG" != "develop" ]]; then
        rm -rf "$temp_dir"
    fi
}

# Wait for deployment to be ready
wait_for_deployment() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would wait for deployment to be ready"
        return 0
    fi
    
    log_info "⏳ Waiting for deployment to be ready..."
    
    # Wait for deployment rollout
    if kubectl rollout status deployment/aletheia -n "$NAMESPACE" --timeout=300s; then
        log_success "Deployment is ready!"
    else
        log_error "Deployment failed to become ready"
        
        # Show recent events for troubleshooting
        log_info "Recent events:"
        kubectl get events -n "$NAMESPACE" --sort-by='.lastTimestamp' | tail -10
        
        # Show pod status
        log_info "Pod status:"
        kubectl get pods -n "$NAMESPACE" -l app=aletheia
        
        exit 1
    fi
}

# Run health checks
health_checks() {
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "[DRY RUN] Would run health checks"
        return 0
    fi
    
    log_info "🧪 Running health checks..."
    
    # Port forward to test locally
    local pod=$(kubectl get pods -n "$NAMESPACE" -l app=aletheia -o jsonpath='{.items[0].metadata.name}')
    
    if [[ -n "$pod" ]]; then
        log_info "Testing health endpoint via port-forward..."
        
        # Start port-forward in background
        kubectl port-forward -n "$NAMESPACE" "$pod" 8080:8000 &
        local pf_pid=$!
        
        # Wait a moment for port-forward to establish
        sleep 3
        
        # Test health endpoint
        if curl -f -s "http://localhost:8080/health" > /dev/null; then
            log_success "Health check passed!"
        else
            log_warning "Health check failed, but deployment may still be starting"
        fi
        
        # Kill port-forward
        kill $pf_pid 2>/dev/null || true
    else
        log_warning "No pods found for health check"
    fi
}

# Show deployment status
show_status() {
    if [[ "$DRY_RUN" == "true" ]]; then
        return 0
    fi
    
    log_info "📊 Deployment Status:"
    echo
    
    # Show deployments
    kubectl get deployments -n "$NAMESPACE" -l app=aletheia
    echo
    
    # Show pods
    kubectl get pods -n "$NAMESPACE" -l app=aletheia
    echo
    
    # Show services
    kubectl get services -n "$NAMESPACE" -l app=aletheia
    echo
    
    # Show ingress if it exists
    if kubectl get ingress -n "$NAMESPACE" &> /dev/null; then
        log_info "Ingress:"
        kubectl get ingress -n "$NAMESPACE"
        echo
    fi
    
    # Show HPA if it exists (production only)
    if [[ "$ENVIRONMENT" == "production" ]]; then
        if kubectl get hpa -n "$NAMESPACE" &> /dev/null; then
            log_info "HPA Status:"
            kubectl get hpa -n "$NAMESPACE"
            echo
        fi
    fi
}

# Main execution
main() {
    log_info "🎯 Aletheia Deep Research Deployment"
    log_info "===================================="
    
    check_prerequisites
    create_namespace
    deploy_application
    wait_for_deployment
    health_checks
    show_status
    
    if [[ "$DRY_RUN" == "true" ]]; then
        log_info "🔍 Dry run completed successfully"
        log_info "Run without --dry-run to apply changes"
    else
        log_success "🎉 Deployment completed successfully!"
        
        case $ENVIRONMENT in
            development)
                log_info "🔗 Access the API via port-forward: kubectl port-forward -n $NAMESPACE svc/aletheia 8000:80"
                ;;
            staging)
                log_info "🔗 Staging URL: https://staging.aletheia.yourdomain.com"
                ;;
            production)
                log_info "🔗 Production URL: https://aletheia.yourdomain.com"
                ;;
        esac
    fi
}

# Execute main function
main "$@"