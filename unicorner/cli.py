import logging
from pathlib import Path

import aarghparse

from unicorner.extraction import extract_all


def configure_logging(level=logging.INFO):
    logging.basicConfig(level=level)


@aarghparse.cli
def cli(parser, subcommand):
    configure_logging()

    @subcommand(name="extract_all", args=[
        ["--input-dir"],
        ["--output-dir"],
    ])
    def cmd_extract_all(args):
        """
        Extract all there is to extract.
        """

        input_dir = Path(args.input_dir) if args.input_dir else Path.cwd()
        assert input_dir.exists()

        output_dir = Path(args.output_dir) if args.output_dir else Path.cwd()
        assert output_dir.exists()

        extract_all(input_dir=input_dir, output_dir=output_dir)


def main():
    cli.run()
