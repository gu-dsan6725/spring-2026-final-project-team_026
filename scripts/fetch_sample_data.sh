#!/usr/bin/env bash
set -euo pipefail

# Fetch a pinned sample repository into ./old-demos
#
# Usage examples:
#   ./scripts/fetch_sample_data.sh
#   SAMPLE_REPO_URL="https://github.com/aws-samples/foundation-model-benchmarking-tool.git" \
#   SAMPLE_REPO_REF="v0.0.0" \
#   ./scripts/fetch_sample_data.sh
#
# Notes:
# - If SAMPLE_REPO_REF is empty, this script will use the default branch HEAD.
# - Pinning by commit hash or tag is recommended for reproducible demos.

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
DEST_DIR="${ROOT_DIR}/old-demos"

SAMPLE_REPO_URL="${SAMPLE_REPO_URL:-https://github.com/aws-samples/foundation-model-benchmarking-tool.git}"
SAMPLE_REPO_REF="${SAMPLE_REPO_REF:-}"

echo "==> Destination: ${DEST_DIR}"
echo "==> Repo: ${SAMPLE_REPO_URL}"
if [[ -n "${SAMPLE_REPO_REF}" ]]; then
  echo "==> Ref: ${SAMPLE_REPO_REF}"
else
  echo "==> Ref: (not set) using default branch HEAD (less reproducible)"
fi

rm -rf "${DEST_DIR}"
mkdir -p "${DEST_DIR}"

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

git clone --depth 1 "${SAMPLE_REPO_URL}" "${tmp_dir}/repo"

if [[ -n "${SAMPLE_REPO_REF}" ]]; then
  (
    cd "${tmp_dir}/repo"
    # fetch ref if not in shallow clone (best-effort)
    git fetch --depth 1 origin "${SAMPLE_REPO_REF}" || true
    git checkout "${SAMPLE_REPO_REF}"
  )
fi

echo "==> Copying repo into old-demos/"
rsync -a --delete --exclude ".git" "${tmp_dir}/repo/" "${DEST_DIR}/"

echo "==> Done. Sample data ready at: ${DEST_DIR}"

