#!/bin/bash

# Demonstrator Helm Chart Upgrade Script

set -e

KUBE_CONTEXT="eecc-prod"
NAMESPACE="construct-x"
VALUES_FILE="values-construct-x.yaml"
RELEASE_NAME="demonstrator"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status()  { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }
print_dry_run() { echo -e "${YELLOW}[DRY-RUN]${NC} $1"; }

DRY_RUN=false
HELM_EXTRA_ARGS=()

show_usage() {
    echo "Usage: $0 [OPTIONS] [-- HELM_OPTIONS...]"
    echo ""
    echo "Examples:"
    echo "  $0"
    echo "  $0 -- --set backend.image.tag=abc123 --set frontend.image.tag=abc123"
}

parse_arguments() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --dry-run) DRY_RUN=true; shift ;;
            -h|--help) show_usage; exit 0 ;;
            --)
                shift
                HELM_EXTRA_ARGS=("$@")
                break
                ;;
            *) print_error "Unknown option: $1"; show_usage; exit 1 ;;
        esac
    done
}

upgrade_chart() {
    local helm_cmd=(helm --kube-context "$KUBE_CONTEXT" upgrade "$RELEASE_NAME" .
        -f values.yaml
        -f "$VALUES_FILE"
        --namespace "$NAMESPACE"
        --wait
        --timeout=10m)

    if [ ${#HELM_EXTRA_ARGS[@]} -gt 0 ]; then
        helm_cmd+=("${HELM_EXTRA_ARGS[@]}")
    fi

    if [ "$DRY_RUN" = true ]; then
        print_dry_run "Would run: ${helm_cmd[*]}"
        helm --kube-context "$KUBE_CONTEXT" template "$RELEASE_NAME" . \
            -f values.yaml -f "$VALUES_FILE" --namespace "$NAMESPACE"
    else
        print_status "Upgrading demonstrator..."
        "${helm_cmd[@]}"
        print_success "Upgrade complete"
    fi
}

main() {
    parse_arguments "$@"
    upgrade_chart
}

main "$@"
