import argparse
import random
from pathlib import Path
from typing import Optional


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Shuffle lines in a JSONL file (one JSON object per line)."
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/MBE_test.jsonl"),
        help="Input JSONL file path.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/MBE_test.shuffled.jsonl"),
        help="Output JSONL file path.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Random seed for reproducible shuffling.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite output file if it already exists.",
    )
    return parser.parse_args()


def shuffle_jsonl(input_path: Path, output_path: Path, seed: Optional[int]) -> int:
    with input_path.open("r", encoding="utf-8") as f:
        lines = [line for line in f if line.strip()]

    if seed is not None:
        rng = random.Random(seed)
        rng.shuffle(lines)
    else:
        random.shuffle(lines)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        f.writelines(lines)

    return len(lines)


def main() -> None:
    args = parse_args()
    input_path: Path = args.input
    output_path: Path = args.output

    if not input_path.exists() or not input_path.is_file():
        raise FileNotFoundError(f"Input JSONL not found: {input_path}")

    if output_path.exists() and not args.overwrite:
        raise FileExistsError(
            f"Output file exists: {output_path}. Use --overwrite to replace it."
        )

    total = shuffle_jsonl(input_path=input_path, output_path=output_path, seed=args.seed)
    print(f"Shuffled {total} records -> {output_path}")


if __name__ == "__main__":
    main()
