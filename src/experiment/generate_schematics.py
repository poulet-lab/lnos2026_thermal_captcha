"""Pre-generate all schematic trace images."""

from src.experiment.schematics import generate_all_schematics


def main() -> None:
    paths = generate_all_schematics()
    print(f"Generated {len(paths)} schematics in reports/stimulus_traces/")


if __name__ == "__main__":
    main()
