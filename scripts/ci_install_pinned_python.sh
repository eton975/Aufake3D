#!/usr/bin/env bash
# GitHub-hosted Ubuntu 26.04 and Ubuntu 26.10 are not supported by
# actions/setup-python's Python 3.13.7 manifest. Install the exact release
# via a pinned uv executable instead, without falling back to system Python.
set -euo pipefail
: "${RUNNER_TEMP:?RUNNER_TEMP must be set by GitHub Actions}"
: "${GITHUB_PATH:?GITHUB_PATH must be set by GitHub Actions}"
readonly VERSION='3.13.7'
# Keep interpreter and shims out of the project tree. The three-build
# reproducibility gate copies source and must not copy toolchain payloads.
export UV_PYTHON_INSTALL_DIR="${RUNNER_TEMP}/aufake3d-managed-python"
uv python install "${VERSION}" --managed-python --no-bin
python_bin="$(uv python find --managed-python "${VERSION}")"
if [[ ! -x "${python_bin}" ]]; then
    echo "Pinned Python is not executable: ${python_bin}" >&2
    exit 1
fi
"${python_bin}" -c 'import sys; assert sys.version_info[:3] == (3, 13, 7), sys.version'
# Explicit shims, not reliance on uv aliases or the system's `python3`.
shim_dir="${RUNNER_TEMP}/aufake3d-python-shims"
mkdir -p "${shim_dir}"
ln -sfn "${python_bin}" "${shim_dir}/python"
ln -sfn "${python_bin}" "${shim_dir}/python3"
printf '%s\n' "${shim_dir}" >> "${GITHUB_PATH}"
printf 'Pinned interpreter: %s\n' "${python_bin}"
