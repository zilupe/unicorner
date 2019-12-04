from pathlib import Path

import pytest

from unicorner import SeasonParse


@pytest.fixture
def data_dir() -> Path:
    return Path(__file__).parents[0] / "data"


def test_parses_season_standings_and_fixtures(data_dir):
    sp = SeasonParse()
    sp.parse_standings_page(path=data_dir / "standings.html")
    sp.parse_fixtures_page(path=data_dir / "fixtures.html")

    assert sp.season_name == "Spring 2019"
    assert sp.season_id == 114
    assert sp.league_id == 505
    assert sp.division_id == 3568
    assert len(sp.teams) == 8
    assert len(sp.game_days) == 12
