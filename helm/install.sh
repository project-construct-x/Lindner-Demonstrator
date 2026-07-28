#!/bin/bash

# Demonstrator Helm Chart Install Script

set -e

KUBE_CONTEXT="eecc-prod"
NAMESPACE="cx-uc-demonstrator"
VALUES_FILE="values-construct-x.yaml"
RELEASE_NAME="demonstrator"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status()  { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
print_dry_run() { echo -e "${YELLOW}[DRY-RUN]${NC} $1"; }

DRY_RUN=false

show_usage() {
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --dry-run    Show what would be installed without making changes"
    echo "  -h, --help   Show this help message"
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run) DRY_RUN=true; shift ;;
            -h|--help) show_usage; exit 0 ;;
            *) print_error "Unknown option: $1"; show_usage; exit 1 ;;
        esac
    done
}

check_prerequisites() {
    print_status "Checking prerequisites..."

    if ! command -v kubectl &> /dev/null; then
        print_error "kubectl is not installed or not in PATH"
        exit 1
    fi
    if ! command -v helm &> /dev/null; then
        print_error "helm is not installed or not in PATH"
        exit 1
    fi
    if ! kubectl --context "$KUBE_CONTEXT" cluster-info &> /dev/null; then
        print_error "Cannot connect to cluster '$KUBE_CONTEXT'. Check your kubeconfig."
        exit 1
    fi
    if [ ! -f "Chart.yaml" ]; then
        print_error "Chart.yaml not found. Run this script from the helm directory."
        exit 1
    fi
    if [ ! -f "$VALUES_FILE" ]; then
        print_error "Values file not found: $VALUES_FILE"
        exit 1
    fi

    print_success "Prerequisites check passed"
}

install_chart() {
    local helm_cmd=(helm --kube-context "$KUBE_CONTEXT" upgrade --install "$RELEASE_NAME" .
        -f values.yaml
        -f "$VALUES_FILE"
        --namespace "$NAMESPACE"
        --create-namespace
        --wait
        --timeout=10m)

    if [ "$DRY_RUN" = true ]; then
        print_dry_run "Would run: ${helm_cmd[*]}"
        helm --kube-context "$KUBE_CONTEXT" template "$RELEASE_NAME" . \
            -f values.yaml -f "$VALUES_FILE" --namespace "$NAMESPACE"
    else
        print_status "Installing demonstrator in namespace '$NAMESPACE' on cluster '$KUBE_CONTEXT'..."
        "${helm_cmd[@]}"
        print_success "Demonstrator installed successfully"
    fi
}

show_final_status() {
    if [ "$DRY_RUN" = true ]; then
        return 0
    fi

    echo ""
    helm --kube-context "$KUBE_CONTEXT" list -n "$NAMESPACE"
    echo ""
    kubectl --context "$KUBE_CONTEXT" get pods,ingress -n "$NAMESPACE" -l release="$RELEASE_NAME"
}

main() {
    parse_arguments "$@"
    check_prerequisites
    install_chart
    show_final_status
}

main "$@"
