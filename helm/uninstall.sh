#!/bin/bash

# Demonstrator Helm Chart Uninstall Script

set -e

KUBE_CONTEXT="eecc-prod"
NAMESPACE="cx-uc-demonstrator"
RELEASE_NAME="demonstrator"

RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status()  { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

show_usage() {
    echo "Usage: $0"
    echo ""
    echo "Uninstalls demonstrator from namespace '$NAMESPACE' on cluster '$KUBE_CONTEXT'."
}

uninstall_chart() {
    print_status "Uninstalling release '$RELEASE_NAME'..."
    helm --kube-context "$KUBE_CONTEXT" uninstall "$RELEASE_NAME" --namespace "$NAMESPACE"
    print_success "Uninstall complete"
}

main() {
    if [[ "${1:-}" == "-h" || "${1:-}" == "--help" ]]; then
        show_usage
        exit 0
    fi

    uninstall_chart
}

main "$@"
