"""
Utilities to extract information from scraped GM fixtures and standings pages.
"""
import collections
import csv
from pathlib import Path
from typing import Dict, Generator, List, Type

from unicorner import SeasonParse
from unicorner.dtos import DtoMixin, FranchiseDto, GameDto, SeasonDto, TeamDto
from unicorner.env import UnicornerEnv, get_logger

log = get_logger(__name__)


def parse_seasons(input_dir: Path, env: UnicornerEnv = None) -> Generator[SeasonParse, None, None]:
    seasons: Dict[int, SeasonParse] = {}

    # Standings should be parsed before fixtures in order to get the teams list first
    # so we are sorting items in reverse order.
    for item in sorted(input_dir.iterdir(), reverse=True):
        if item.suffix != ".html":
            log.debug(f"Skipping {item}")
            continue

        log.info(f"Parsing {item}")

        parts = item.name.split("-")
        gm_season_id = int(parts[1])
        is_fixtures = parts[2] == "fixtures.html"
        if gm_season_id not in seasons:
            seasons[gm_season_id] = SeasonParse(env=env)

        if is_fixtures:
            seasons[gm_season_id].parse_fixtures_page(html=item.read_text())
        else:
            seasons[gm_season_id].parse_standings_page(html=item.read_text())

    yield from seasons.values()


def create_extraction(input_dir: Path) -> Dict[Type[DtoMixin], List[DtoMixin]]:
    """
    This expects the following files to be present in input_dir:
        franchises.csv
        franchise_seasons.csv
        score_overrides.csv
        season-SEASONID-fixtures.html
        season-SEASONID-standings.html

    The input_dir can contain fixtures and standings for any number of seasons as long as SEASONID in the file names
    match the season id.

    Files season-SEASONID-fixtures.html and season-SEASONID-standings.html can be obtained by navigating in browser
    to your league's fixtures/standings page and saving the HTML file following the naming convention.
    """

    season: SeasonParse
    season_dto: SeasonDto

    extraction: Dict[Type[DtoMixin], List[DtoMixin]] = collections.defaultdict(list)

    score_overrides_path = input_dir / "score_overrides.csv"
    score_overrides = {}
    if score_overrides_path.exists():
        with score_overrides_path.open() as f:
            for row in csv.DictReader(f):
                game_id = int(row['game_id'])
                score_overrides[game_id] = {
                    "game_id": game_id,
                    "home_team_id": int(row["home_team_id"] or 0),
                    "home_team_score": int(row["home_team_score"]),
                    "away_team_id": int(row["away_team_id"] or 0),
                    "away_team_score": int(row["away_team_score"]),
                    "score_status": int(row["score_status"]),
                    "score_status_comments": row["score_status_comments"],
                    "season_stage": row["season_stage"] or None,
                }
        log.info(f"{len(score_overrides)} score overrides loaded from {score_overrides_path}")
    else:
        log.info(f"No score overrides loaded")

    franchises_path = input_dir / "franchises.csv"
    if franchises_path.exists():
        with franchises_path.open() as f:
            extraction[FranchiseDto] = [
                FranchiseDto(**row)
                for row in csv.DictReader(f)
            ]

    franchise_seasons_path = input_dir / "franchise_seasons.csv"
    if franchise_seasons_path.exists():
        with franchise_seasons_path.open() as f:
            for fs in csv.DictReader(f):
                extraction[TeamDto].append(TeamDto(
                    season_id=fs["season_id"],
                    team_id=fs["team_id"],
                    franchise_id=fs["franchise_id"],
                    name=fs["name"],
                ))

    env = UnicornerEnv()
    env.score_overrides = score_overrides

    for season in parse_seasons(input_dir=input_dir, env=env):
        game_days = sorted(season.game_days, key=lambda gd: gd.date)
        extraction[SeasonDto].append(SeasonDto(
            id=season.season_id,
            league_id=season.league_id,
            division_id=season.division_id or None,
            name=season.season_name,
            first_week_date=game_days[0].date if season.game_days else None,
            last_week_date=game_days[-1].date if season.game_days else None,
        ))

        for game_day in season.game_days:
            for g in game_day.games:
                extraction[GameDto].append(GameDto(
                    id=g.id,
                    scheduled_time=g.starts_at,
                    season_id=season.season_id,
                    season_stage=g.season_stage,
                    home_team_id=g.home_team_id,
                    home_team_pts=g.home_team_score,
                    home_team_outcome=g.home_team_outcome,
                    away_team_id=g.away_team_id,
                    away_team_pts=g.away_team_score,
                    away_team_outcome=g.away_team_outcome,
                ))

    for i, season_dto in enumerate(sorted(extraction[SeasonDto], key=lambda s: s.first_week_date)):
        season_dto.sequence_number = i + 1

    return extraction


def write_extraction(extraction: Dict[Type[DtoMixin], List[DtoMixin]], output_dir: Path):
    assert output_dir.exists()

    for dto_cls, dtos in extraction.items():
        output_path = output_dir / f"gm{dto_cls.__name__.lower()[:-3]}s.csv"
        with output_path.open("w") as f:
            csv_writer = csv.DictWriter(f, fieldnames=dto_cls.get_field_names(), quoting=csv.QUOTE_ALL)
            csv_writer.writeheader()
            csv_writer.writerows(dto.to_dict() for dto in dtos)
        log.info(f"{len(dtos)} {dto_cls.__name__}s written to {output_path}")


def extract_all(input_dir: Path, output_dir: Path):
    extraction = create_extraction(input_dir=input_dir)
    write_extraction(extraction=extraction, output_dir=output_dir)
