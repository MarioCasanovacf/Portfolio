"""Command-line entrypoint for the quantitative-finance toolkit.

Installed as ``qfinance`` via ``[project.scripts]`` in ``pyproject.toml``.

Examples:
    qfinance --version
    qfinance generate-data --all
    qfinance generate-data --lob --out-dir data/raw
    QFINANCE_RANDOM_SEED=99 qfinance generate-data
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from quantitative_finance import __version__
from quantitative_finance.config import get_settings
from quantitative_finance.data.generator import (
    generate_all,
    generate_asset_prices,
    generate_lob_events,
    write_csv,
)
from quantitative_finance.utils.logging import configure_logging


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="qfinance",
        description="Quantitative finance toolkit: synthetic data, models, reports.",
    )
    parser.add_argument("--version", action="version", version=f"qfinance {__version__}")
    parser.add_argument("--log-level", default=None, help="Override log level (e.g., DEBUG).")

    sub = parser.add_subparsers(dest="command", required=True)

    gen = sub.add_parser("generate-data", help="Generate synthetic LOB and/or asset CSVs.")
    gen.add_argument("--lob", action="store_true", help="Generate LOB events only.")
    gen.add_argument("--assets", action="store_true", help="Generate asset prices only.")
    gen.add_argument("--all", dest="all_", action="store_true", help="Generate both (default).")
    gen.add_argument("--out-dir", type=Path, default=None, help="Override data directory.")

    return parser


def _cmd_generate(args: argparse.Namespace) -> int:
    settings = get_settings()
    if args.out_dir is not None:
        settings = settings.model_copy(update={"data_dir": args.out_dir})

    if not (args.lob or args.assets) and not args.all_:
        args.all_ = True

    written: dict[str, Path] = {}
    if args.all_:
        written = generate_all(settings)
    else:
        if args.lob:
            df = generate_lob_events(settings)
            written["lob"] = write_csv(
                df, settings.data_dir / settings.lob_filename, include_index=False
            )
        if args.assets:
            df = generate_asset_prices(settings)
            written["assets"] = write_csv(
                df, settings.data_dir / settings.assets_filename, include_index=True
            )

    for name, path in written.items():
        sys.stdout.write(f"{name}: {path}\n")
    return 0


def main(argv: list[str] | None = None) -> int:
    """Entry point. Returns the process exit code."""
    parser = _build_parser()
    args = parser.parse_args(argv)

    settings = get_settings()
    log_level = args.log_level or settings.log_level
    configure_logging(log_level)

    if args.command == "generate-data":
        return _cmd_generate(args)

    parser.print_help()
    return 1


if __name__ == "__main__":
    sys.exit(main())
