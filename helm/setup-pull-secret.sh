#!/bin/bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$(readlink -f "$0")")" && pwd)"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

DEFAULT_KUBE_CONTEXT="eecc-prod"
DEFAULT_NAMESPACE="cx-uc-demonstrator"
DEFAULT_SECRET_NAME="cx-registry-pull-secret"
DEFAULT_REGISTRY="ghcr.io"

KUBE_CONTEXT=""
NAMESPACE=""
SECRET_NAME=""
REGISTRY=""
GITHUB_USER=""
GITHUB_TOKEN=""
DRY_RUN=""
FORCE=""

print_status()  { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error()   { echo -e "${RED}[ERROR]${NC} $1"; }

load_env_file() {
    local env_file=""

    if [[ -f ".env" ]]; then
        env_file=".env"
    elif [[ -f "$SCRIPT_DIR/.env" ]]; then
        env_file="$SCRIPT_DIR/.env"
    fi

    if [[ -z "$env_file" ]]; then
        return 0
    fi

    print_status "Loading configuration from $env_file ..."

    while IFS= read -r line || [[ -n "$line" ]]; do
        [[ "$line" =~ ^[[:space:]]*# ]] && continue
        [[ -z "${line// }" ]] && continue

        if [[ "$line" =~ ^[[:space:]]*([A-Za-z_][A-Za-z0-9_]*)[[:space:]]*=[[:space:]]*(.*) ]]; then
            local key="${BASH_REMATCH[1]}"
            local value="${BASH_REMATCH[2]}"
            value="${value#\"}"; value="${value%\"}"
            value="${value#\'}"; value="${value%\'}"

            if [[ -z "${!key:-}" ]]; then
                export "$key=$value"
            fi
        fi
    done < "$env_file"
}

load_config() {
    load_env_file

    KUBE_CONTEXT="${KUBE_CONTEXT:-$DEFAULT_KUBE_CONTEXT}"
    NAMESPACE="${NAMESPACE:-$DEFAULT_NAMESPACE}"
    SECRET_NAME="${SECRET_NAME:-$DEFAULT_SECRET_NAME}"
    REGISTRY="${REGISTRY:-$DEFAULT_REGISTRY}"
    GITHUB_USER="${GITHUB_USER:-}"
    GITHUB_TOKEN="${GITHUB_TOKEN:-}"
    DRY_RUN="${DRY_RUN:-false}"
    FORCE="${FORCE:-false}"
}

show_usage() {
    cat << EOF
Usage: $0 [OPTIONS]

Create the GHCR pull secret used by this chart (same as edc/helm/edc).

OPTIONS:
    -c, --context CONTEXT     kubectl context (default: $DEFAULT_KUBE_CONTEXT)
    -n, --namespace NAMESPACE Kubernetes namespace (default: $DEFAULT_NAMESPACE)
    -s, --secret NAME         Secret name (default: $DEFAULT_SECRET_NAME)
    -r, --registry URL        Registry URL (default: $DEFAULT_REGISTRY)
    -u, --user USERNAME       GitHub username (or set GITHUB_USER)
    -t, --token TOKEN         GitHub PAT with read:packages (or set GITHUB_TOKEN)
    -d, --dry-run             Show what would be done without applying
    -f, --force               Overwrite existing secret without prompt
    -h, --help                Show this help message

EXAMPLES:
    cp .env.example .env
    # edit .env, then:
    ./setup-pull-secret.sh

    ./setup-pull-secret.sh -u myuser -t ghp_xxx
EOF
}

parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            -c|--context) KUBE_CONTEXT="$2"; shift 2 ;;
            -n|--namespace) NAMESPACE="$2"; shift 2 ;;
            -s|--secret) SECRET_NAME="$2"; shift 2 ;;
            -r|--registry) REGISTRY="$2"; shift 2 ;;
            -u|--user) GITHUB_USER="$2"; shift 2 ;;
            -t|--token) GITHUB_TOKEN="$2"; shift 2 ;;
            -d|--dry-run) DRY_RUN="true"; shift ;;
            -f|--force) FORCE="true"; shift ;;
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

    if ! kubectl --context "$KUBE_CONTEXT" cluster-info &> /dev/null; then
        print_error "kubectl cannot connect to context '$KUBE_CONTEXT'"
        exit 1
    fi

    if [[ -z "$GITHUB_USER" ]]; then
        if [[ -t 0 ]]; then
            read -p "GitHub username: " GITHUB_USER
        else
            print_error "GITHUB_USER not set"
            exit 1
        fi
    fi

    if [[ -z "$GITHUB_TOKEN" ]]; then
        if [[ -t 0 ]]; then
            read -s -p "GitHub PAT (read:packages): " GITHUB_TOKEN
            echo
        else
            print_error "GITHUB_TOKEN not set"
            exit 1
        fi
    fi

    print_success "Prerequisites check passed"
}

ensure_namespace() {
    if ! kubectl --context "$KUBE_CONTEXT" get namespace "$NAMESPACE" &> /dev/null; then
        if [[ "$DRY_RUN" == "true" ]]; then
            print_warning "Dry run: Would create namespace $NAMESPACE"
            return 0
        fi
        print_status "Creating namespace $NAMESPACE..."
        kubectl --context "$KUBE_CONTEXT" create namespace "$NAMESPACE"
    fi
}

create_pull_secret() {
    print_status "Creating pull secret '$SECRET_NAME' in namespace '$NAMESPACE'..."
    print_status "Registry: $REGISTRY"
    print_status "Username: $GITHUB_USER"

    if kubectl --context "$KUBE_CONTEXT" get secret "$SECRET_NAME" -n "$NAMESPACE" &> /dev/null; then
        if [[ "$FORCE" != "true" && "$DRY_RUN" != "true" ]]; then
            print_warning "Secret '$SECRET_NAME' already exists in namespace '$NAMESPACE'"
            read -p "Overwrite? (y/N): " -n 1 -r
            echo
            if [[ ! $REPLY =~ ^[Yy]$ ]]; then
                print_status "Skipping existing secret"
                return 0
            fi
        fi
        kubectl --context "$KUBE_CONTEXT" delete secret "$SECRET_NAME" -n "$NAMESPACE" 2>/dev/null || true
    fi

    if [[ "$DRY_RUN" == "true" ]]; then
        kubectl --context "$KUBE_CONTEXT" create secret docker-registry "$SECRET_NAME" \
            --namespace "$NAMESPACE" \
            --docker-server="$REGISTRY" \
            --docker-username="$GITHUB_USER" \
            --docker-password="$GITHUB_TOKEN" \
            --dry-run=client -o yaml
        return 0
    fi

    kubectl --context "$KUBE_CONTEXT" create secret docker-registry "$SECRET_NAME" \
        --namespace "$NAMESPACE" \
        --docker-server="$REGISTRY" \
        --docker-username="$GITHUB_USER" \
        --docker-password="$GITHUB_TOKEN"

    print_success "Secret '$SECRET_NAME' created in namespace '$NAMESPACE'"
}

main() {
    load_config
    parse_args "$@"
    check_prerequisites
    ensure_namespace
    create_pull_secret
}

main "$@"
