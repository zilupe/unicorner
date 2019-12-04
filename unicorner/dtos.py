"""
These DTOs are the format in which we export data.
"""

import dataclasses
import datetime as dt
from typing import Dict, List


class DtoMixin:

    @classmethod
    def get_field_names(self) -> List[str]:
        return [f.name for f in dataclasses.fields(self)]

    def to_dict(self) -> Dict:
        return dataclasses.asdict(self)


@dataclasses.dataclass
class FranchiseDto(DtoMixin):
    id: int = None
    name: str = None


@dataclasses.dataclass
class SeasonDto(DtoMixin):
    id: int = None
    league_id: int = None
    division_id: int = None
    name: str = None
    sequence_number: int = None
    first_week_date: dt.date = None
    last_week_date: dt.date = None


@dataclasses.dataclass
class TeamDto(DtoMixin):
    team_id: int = None
    season_id: int = None
    franchise_id: int = None
    name: str = None
    id: str = dataclasses.field(init=False, default=None)

    def __post_init__(self):
        self.id = f"{self.season_id:0>4}.{self.team_id}"


@dataclasses.dataclass
class TeamSeasonDto(DtoMixin):
    id: str = None


@dataclasses.dataclass
class GameDto(DtoMixin):
    id: int = None
    scheduled_time: dt.datetime = None
    season_id: int = None
    season_stage: str = None
    home_team_id: str = None
    home_team_pts: int = None
    home_team_outcome: str = None
    away_team_id: str = None
    away_team_pts: int = None
    away_team_outcome: str = None
