#!/usr/bin/env bash
# Launch Thermal Captcha operator menu (micromamba env + python -m src.experiment.run).
# Use with a Desktop .desktop launcher — see README.md § Desktop shortcut (Linux).

set -eo pipefail

init_micromamba() {
    if command -v micromamba >/dev/null 2>&1 && [[ -n "${MAMBA_ROOT_PREFIX:-}" ]]; then
        return 0
    fi

    local profile
    for profile in \
        "${MAMBA_ROOT_PREFIX:+$MAMBA_ROOT_PREFIX/etc/profile.d/micromamba.sh}" \
        "${HOME}/micromamba/etc/profile.d/micromamba.sh" \
        "${HOME}/.local/share/mamba/etc/profile.d/micromamba.sh"; do
        if [[ -n "${profile}" && -f "${profile}" ]]; then
            # shellcheck source=/dev/null
            source "${profile}"
            return 0
        fi
    done

    local mamba_bin="${HOME}/.local/bin/micromamba"
    if [[ -x "${mamba_bin}" ]]; then
        export MAMBA_ROOT_PREFIX="${MAMBA_ROOT_PREFIX:-${HOME}/micromamba}"
        # Nounset breaks the hook; desktop shortcuts start with a minimal env.
        set +u
        eval "$("${mamba_bin}" shell hook -s bash -r "${MAMBA_ROOT_PREFIX}")"
        set -e
        return 0
    fi

    if command -v micromamba >/dev/null 2>&1; then
        set +u
        eval "$(micromamba shell hook -s bash)"
        set -e
        return 0
    fi

    return 1
}

if ! init_micromamba; then
    echo "micromamba not found." >&2
    echo "Install the env (README § micromamba) or set MAMBA_ROOT_PREFIX in the .desktop file." >&2
    exit 1
fi

set +u
micromamba activate lnos2026_thermal_captcha
set -e

proj="$(cd "$(dirname "$0")/.." && pwd)"
cd "$proj"

git pull --ff-only
python -m src.experiment.run
