import logging
from pathlib import Path
from pprint import pprint

import aarghparse

from unicorner import UnicornerEnv, SeasonParse
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

    @subcommand(name="parse_standings_page", args=[
        ["path",],
    ])
    def cmd_parse_standings_page(args):
        env = UnicornerEnv()
        season = SeasonParse(env=env)
        season.parse_standings_page(path=args.path)
        pprint(season.__dict__)


def main():
    cli.run()
