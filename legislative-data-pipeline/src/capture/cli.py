"""CLI entry point for the legislative data capture module."""

import argparse
import sys

import structlog

from capture.dipmex import DipMexClient
from capture.diputados import DiputadosScraper
from config import get_settings

logger = structlog.get_logger(__name__)

SCRAPERS = {
    "dipmex": DipMexClient,
    "diputados": DiputadosScraper,
}


def main(argv: list[str] | None = None) -> int:
    """Run one or more scrapers from the command line.

    Args:
        argv: Command-line arguments (defaults to sys.argv[1:]).

    Returns:
        Exit code (0 for success, 1 for failure).
    """
    parser = argparse.ArgumentParser(
        description="Capture Mexican legislative data from public sources.",
    )
    parser.add_argument(
        "sources",
        nargs="*",
        default=list(SCRAPERS.keys()),
        choices=list(SCRAPERS.keys()),
        help="Data sources to scrape. Defaults to all.",
    )
    parser.add_argument(
        "--log-level",
        default=None,
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Override log level.",
    )
    args = parser.parse_args(argv)

    settings = get_settings()
    log_level = args.log_level or settings.log_level

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(structlog, log_level, structlog.INFO)
        ),
    )

    total_files: list[str] = []
    errors: list[str] = []

    for source_name in args.sources:
        scraper_cls = SCRAPERS[source_name]
        logger.info("running_scraper", source=source_name)

        try:
            with scraper_cls(settings.capture) as scraper:
                paths = scraper.scrape()
                total_files.extend(str(p) for p in paths)
                logger.info("scraper_complete", source=source_name, files=len(paths))
        except Exception:
            logger.exception("scraper_error", source=source_name)
            errors.append(source_name)

    logger.info(
        "capture_complete",
        total_files=len(total_files),
        errors=len(errors),
        failed_sources=errors,
    )

    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
