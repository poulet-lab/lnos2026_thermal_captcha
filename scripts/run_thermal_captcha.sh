#!/usr/bin/env bash
# Launch Thermal Captcha operator menu (micromamba env + python -m src.experiment.run).
# Use with a Desktop .desktop launcher — see README.md § Desktop shortcut (Linux).

set -eo pipefail

ENV_NAME="lnos2026_thermal_captcha"

find_micromamba() {
    if [[ -n "${MICROMAMBA_BIN:-}" && -x "${MICROMAMBA_BIN}" ]]; then
        echo "${MICROMAMBA_BIN}"
        return 0
    fi
    local candidate
    for candidate in \
        "${HOME}/.local/bin/micromamba" \
        "${HOME}/bin/micromamba" \
        "/usr/local/bin/micromamba"; do
        if [[ -x "${candidate}" ]]; then
            echo "${candidate}"
            return 0
        fi
    done
    if command -v micromamba >/dev/null 2>&1; then
        command -v micromamba
        return 0
    fi
    return 1
}

find_mamba_root() {
    if [[ -n "${MAMBA_ROOT_PREFIX:-}" && -d "${MAMBA_ROOT_PREFIX}" ]]; then
        echo "${MAMBA_ROOT_PREFIX}"
        return 0
    fi
    local root
    for root in \
        "${HOME}/micromamba" \
        "${HOME}/.local/share/mamba" \
        "${HOME}/mambaforge" \
        "${HOME}/miniforge3" \
        "${HOME}/miniconda3"; do
        if [[ -d "${root}/envs/${ENV_NAME}" ]] || [[ -f "${root}/etc/profile.d/micromamba.sh" ]]; then
            echo "${root}"
            return 0
        fi
    done
    if [[ -d "${HOME}/micromamba" ]]; then
        echo "${HOME}/micromamba"
        return 0
    fi
    return 1
}

MICROMAMBA="$(find_micromamba)" || {
    echo "micromamba not found." >&2
    echo "Install micromamba or set MICROMAMBA_BIN in your .desktop file." >&2
    exit 1
}

MAMBA_ROOT="$(find_mamba_root)" || {
    echo "MAMBA_ROOT_PREFIX not found." >&2
    echo "Set MAMBA_ROOT_PREFIX in your .desktop file (often ~/micromamba)." >&2
    exit 1
}
export MAMBA_ROOT_PREFIX="${MAMBA_ROOT}"

if [[ ! -d "${MAMBA_ROOT_PREFIX}/envs/${ENV_NAME}" ]]; then
    echo "Environment '${ENV_NAME}' not found at ${MAMBA_ROOT_PREFIX}/envs/${ENV_NAME}." >&2
    echo "Create it with: micromamba create -f environment.yml" >&2
    "${MICROMAMBA}" env list -r "${MAMBA_ROOT_PREFIX}" 2>/dev/null || true
    exit 1
fi

proj="$(cd "$(dirname "$0")/.." && pwd)"
cd "$proj"

git pull --ff-only
"${MICROMAMBA}" run -r "${MAMBA_ROOT_PREFIX}" -n "${ENV_NAME}" python -m src.experiment.run
