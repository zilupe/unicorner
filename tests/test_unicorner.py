from pathlib import Path

import pytest

from unicorner import SeasonParse
from unicorner.dtos import FranchiseDto, GameDto, SeasonDto
from unicorner.extraction import create_extraction


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parents[0] / "data"


def test_parses_season_standings_and_fixtures(data_dir):
    sp = SeasonParse()
    sp.parse_standings_page(path=data_dir / "season-114-standings.html")
    sp.parse_fixtures_page(path=data_dir / "season-114-fixtures.html")

    assert sp.season_name == "Spring 2019"
    assert sp.season_id == 114
    assert sp.league_id == 505
    assert sp.division_id == 3568
    assert len(sp.teams) == 8
    assert len(sp.game_days) == 12


def test_extraction(data_dir):
    extraction = create_extraction(input_dir=data_dir)
    assert len(extraction[SeasonDto]) == 1
    assert extraction[SeasonDto][0].id == 114

    assert len(extraction[GameDto]) == 44
    assert extraction[GameDto][0].season_id == 114

    assert isinstance(extraction[FranchiseDto][0], FranchiseDto)
    assert extraction[FranchiseDto][0].name == "Supernova"
