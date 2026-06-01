"""Generate schematic trace images (pre-event, not during sessions)."""

from __future__ import annotations

from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

from .globals import (
    BASELINE_TEMPERATURE,
    SCHEMATIC_Y_MAX,
    SCHEMATIC_Y_MIN,
    STIMULUS_TRACES_DIR,
)
from .stimuli import STIMULUS_POOL, StimulusDefinition


def render_schematic(stimulus: StimulusDefinition, output_path: Path | None = None) -> Path:
    """Render one schematic: black trace, dashed gray baseline, no axes.

    All schematics share the same fixed y-range so amplitudes are visually comparable.
    """
    t, temp = stimulus.theoretical_trace()
    if output_path is None:
        output_path = STIMULUS_TRACES_DIR / f"{stimulus.name}.png"

    output_path.parent.mkdir(parents=True, exist_ok=True)

    fig, ax = plt.subplots(figsize=(4, 2), dpi=100)
    ax.set_xlim(t[0], t[-1])
    ax.set_ylim(SCHEMATIC_Y_MIN, SCHEMATIC_Y_MAX)
    ax.plot(
        [t[0], t[-1]],
        [BASELINE_TEMPERATURE, BASELINE_TEMPERATURE],
        color="0.6",
        linestyle="--",
        linewidth=1.5,
    )
    ax.plot(t, temp, color="black", linewidth=2)
    ax.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1)
    fig.savefig(output_path, bbox_inches="tight", pad_inches=0.05, transparent=False)
    plt.close(fig)
    return output_path


def generate_all_schematics(output_dir: Path | None = None) -> list[Path]:
    output_dir = output_dir or STIMULUS_TRACES_DIR
    output_dir.mkdir(parents=True, exist_ok=True)
    paths = []
    for name, stimulus in STIMULUS_POOL.items():
        paths.append(render_schematic(stimulus, output_dir / f"{name}.png"))
    return paths
