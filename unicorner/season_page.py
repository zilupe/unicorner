import dataclasses
import datetime as dt
import logging
import re
from pathlib import Path
from typing import Dict, List
from urllib.parse import parse_qs

from bs4 import BeautifulSoup

from .env import UnicornerEnv
from .values import GameOutcomes, ScoreStatuses, SeasonStages

log = logging.getLogger(__name__)


def parse_gm_date(date_str):
    """
    Parses date in the format "Thursday 06 Nov 2014"
    and returns a datetime.
    """
    return dt.datetime.strptime(date_str, '%A %d %b %Y')


def parse_gm_time(time_str):
    return dt.datetime.strptime(time_str, '%H:%M')


def extract_from_link(link, field):
    return parse_qs(link['href'])[field][0]


@dataclasses.dataclass
class Game:
    id: int = None
    starts_at: dt.datetime = None
    season_stage: str = None
    venue: str = None
    home_team_id: str = None
    home_team_score: int = None
    home_team_outcome: str = None
    away_team_id: str = None
    away_team_score: int = None
    away_team_outcome: str = None
    score_status: str = None
    score_status_comments: str = None


@dataclasses.dataclass
class GameDay:
    date: dt.datetime = None
    week_number: int = None
    games: List[Game] = dataclasses.field(default_factory=list)


@dataclasses.dataclass
class Team:
    id: str = None
    name: str = None
    gm_id: int = None
    position: int = None
    played: int = None
    won: int = None
    lost: int = None
    drawn: int = None
    forfeit_for: int = None
    forfeit_against: int = None
    score_for: int = None
    score_against: int = None
    score_difference: int = None
    bonus_points: int = None
    points: int = None
    finals_rank: int = None


class SeasonParse:
    def __init__(self, env: UnicornerEnv = None):
        self.env = env or UnicornerEnv()
        self.game_days: List[GameDay] = None
        self.season_id: int = None
        self.season_name: str = None
        self.division_id: int = None
        self.league_id: int = None
        self.teams: Dict[str, Team] = None

    def unicorn_team_id(self, gm_team_id):
        """
        Build unicorn team id which consists of GM SeasonId concatenated with GM TeamId
        """
        return '{:0>4}.{}'.format(int(self.season_id), int(gm_team_id))

    def parse_standings_page(self, *, html=None, path: Path = None):
        # Do not extract team names because we are assigning them manually --
        # GoMammoth shows the latest team name in all seasons.

        if html is None:
            html = Path(path).read_text()

        soup = BeautifulSoup(html, 'html.parser')

        self.season_name = soup.find('head').find('title').text.strip().split(' - ')[4]

        if self.season_id is None:
            fixtures_link = soup.find('h3').find('a')
            self.season_id = int(extract_from_link(fixtures_link, 'SeasonId'))
            self.division_id = int(extract_from_link(fixtures_link, 'DivisionId'))
            self.league_id = int(extract_from_link(fixtures_link, 'LeagueId'))

        self.teams = {}
        team_row_regex = re.compile("STRow.*")
        for i, st_tr in enumerate(soup.find('table', class_='STTable').find_all('tr', class_=team_row_regex)):
            gm_team_id = int(extract_from_link(st_tr.find('td', class_='STTeamCell').find('a'), 'TeamId'))
            team_id = self.unicorn_team_id(gm_team_id)
            tds = st_tr.find_all('td')
            self.teams[team_id] = Team(
                id=team_id,
                name=tds[1].text.strip(),
                gm_id=gm_team_id,
                position=i + 1,
                played=int(tds[2].text.strip()),
                won=int(tds[3].text.strip()),
                lost=int(tds[4].text.strip()),
                drawn=int(tds[5].text.strip()),
                forfeit_for=int(tds[6].text.strip()),
                forfeit_against=int(tds[7].text.strip()),
                score_for=int(tds[8].text.strip()),
                score_against=int(tds[9].text.strip()),
                score_difference=int(tds[10].text.strip()),
                bonus_points=int(tds[11].text.strip()),
                points=int(tds[12].find('a').text.strip() if tds[12].find('a') else 0),
            )

        self.game_days = []
        season_stage = SeasonStages.regular

        for week_number, t in enumerate(soup.find_all('table', class_='FTable')):
            week_date = parse_gm_date(t.find('tr', class_='FHeader').find('td').text.strip())
            week_games = []
            for g in t.find_all('tr', class_='FRow'):
                sc = g.find('td', class_='FTitle')
                if sc:
                    decoded_ss = SeasonStages.decode_gm_season_stage(sc.text.strip())
                    if decoded_ss is not None:
                        season_stage = decoded_ss

                game_season_stage = season_stage

                tc = g.find('td', class_='FDate')
                if not tc:
                    continue
                game_time_str = tc.text.strip()
                if game_time_str == 'Bye':
                    continue
                game_time = parse_gm_time(game_time_str)

                ic = g.find('td', class_='FScore')
                if not ic:
                    continue
                game_id = int(ic.find('nobr')['data-fixture-id'])

                game_score_status = ScoreStatuses.winner_and_score_ok
                game_score_status_comments = None
                game_home_team_id = None
                game_away_team_id = None

                if game_id in self.env.score_overrides:
                    fs = self.env.score_overrides[game_id]
                    game_home_team_id = fs['home_team_id']
                    game_away_team_id = fs['away_team_id']
                    game_score = (fs['home_team_score'], fs['away_team_score'])
                    game_score_status = fs['score_status']
                    game_score_status_comments = fs['score_status_comments']
                    if fs['season_stage']:
                        game_season_stage = fs['season_stage']
                else:
                    if ic.find('nobr').find('div'):
                        game_score = (
                            ic.find('nobr').find('div').find('nobr').text.strip().split(' - ')
                        )
                    else:
                        log.warning((
                            'Encountered a game with no score and no manual score provided: '
                            'week_date={} game_time={} game_id={}'
                        ).format(week_date, game_time, game_id))
                        game_score = (None, None)
                        game_score_status = ScoreStatuses.unknown
                        game_score_status_comments = 'Unresolved'

                game_venue = g.find('td', class_='FPlayingArea').text.strip()

                htc = g.find('td', class_='FHomeTeam')
                atc = g.find('td', class_='FAwayTeam')

                game = Game(
                    id=game_id,
                    starts_at=game_time.replace(
                        year=week_date.year, month=week_date.month, day=week_date.day
                    ),
                    season_stage=game_season_stage,
                    venue=game_venue,
                    home_team_id=self.unicorn_team_id(game_home_team_id or extract_from_link(htc.find('a'), 'TeamId')),
                    home_team_score=int(game_score[0]) if game_score[0] is not None else None,
                    away_team_id=self.unicorn_team_id(game_away_team_id or extract_from_link(atc.find('a'), 'TeamId')),
                    away_team_score=int(game_score[1]) if game_score[1] is not None else None,
                    score_status=game_score_status,
                    score_status_comments=game_score_status_comments,
                )

                game.home_team_outcome, game.away_team_outcome = GameOutcomes.from_scores(
                    game.home_team_score,
                    game.away_team_score,
                )
                game.home_team_points = GameOutcomes.get_points_for(game.home_team_outcome, game.season_stage)
                game.away_team_points = GameOutcomes.get_points_for(game.away_team_outcome, game.season_stage)

                week_games.append(game)

                # TODO This is very specific to our league
                custom_season_stages = {
                    105: {
                        SeasonStages.semifinal1: SeasonStages.final7th,
                        SeasonStages.semifinal2: SeasonStages.final5th,
                        SeasonStages.semifinal5th1: SeasonStages.final3rd,
                    },
                    108: {
                        SeasonStages.semifinal2: SeasonStages.final5th,
                        SeasonStages.semifinal5th1: SeasonStages.final3rd,
                    },
                }

                if self.season_id in custom_season_stages:
                    game.season_stage = custom_season_stages[self.season_id].get(
                        game_season_stage,
                        game_season_stage,
                    )

                if game.season_stage == SeasonStages.final1st:
                    if game.home_team_outcome in (GameOutcomes.won, GameOutcomes.forfeit_for):
                        self.teams[game.home_team_id].finals_rank = 1
                        self.teams[game.away_team_id].finals_rank = 2
                    elif game.home_team_outcome in (GameOutcomes.lost, GameOutcomes.forfeit_against):
                        self.teams[game.home_team_id].finals_rank = 2
                        self.teams[game.away_team_id].finals_rank = 1
                elif game.season_stage == SeasonStages.final3rd:
                    if game.home_team_outcome in (GameOutcomes.won, GameOutcomes.forfeit_for):
                        self.teams[game.home_team_id].finals_rank = 3
                        self.teams[game.away_team_id].finals_rank = 4
                    elif game.home_team_outcome in (GameOutcomes.lost, GameOutcomes.forfeit_against):
                        self.teams[game.home_team_id].finals_rank = 4
                        self.teams[game.away_team_id].finals_rank = 3
                elif game.season_stage == SeasonStages.final5th:
                    if game.home_team_outcome in (GameOutcomes.won, GameOutcomes.forfeit_for):
                        self.teams[game.home_team_id].finals_rank = 5
                        self.teams[game.away_team_id].finals_rank = 6
                    elif game.home_team_outcome in (GameOutcomes.lost, GameOutcomes.forfeit_against):
                        self.teams[game.home_team_id].finals_rank = 6
                        self.teams[game.away_team_id].finals_rank = 5
                elif game.season_stage == SeasonStages.final7th:
                    if game.home_team_outcome in (GameOutcomes.won, GameOutcomes.forfeit_for):
                        self.teams[game.home_team_id].finals_rank = 7
                        self.teams[game.away_team_id].finals_rank = 8
                    elif game.home_team_outcome in (GameOutcomes.lost, GameOutcomes.forfeit_against):
                        self.teams[game.home_team_id].finals_rank = 8
                        self.teams[game.away_team_id].finals_rank = 7
                elif game.season_stage == SeasonStages.semifinal5th1:
                    # In a 7 team league losing 5th place semifinal means you finish last (7th)
                    if game.home_team_outcome in (GameOutcomes.won, GameOutcomes.forfeit_for):
                        self.teams[game.away_team_id].finals_rank = 7
                    elif game.home_team_outcome in (GameOutcomes.lost, GameOutcomes.forfeit_against):
                        self.teams[game.home_team_id].finals_rank = 7

            self.game_days.append(GameDay(
                date=week_date,
                week_number=week_number,
                games=week_games,
            ))

    def parse_fixtures_page(self, *, html=None, path: Path = None):
        assert self.teams, 'Teams should be already loaded before parsing fixtures page'

        if html is None:
            html = Path(path).read_text()

        soup = BeautifulSoup(html, 'html.parser')

        for ft in soup.find_all('table', class_='FTable'):
            week_date = parse_gm_date(ft.find('tr', class_='FHeader').find('td').text.strip())
            week_games = []

            game_day = None
            matching_game_days = [gd for gd in self.game_days if gd.date == week_date]
            if matching_game_days:
                game_day = matching_game_days[0]

            for fr in ft.find_all('tr', class_='FRow'):
                game_time_cell = fr.find('td', class_='FDate')
                if not game_time_cell:
                    continue
                game_time_str = game_time_cell.text.strip()
                game_time = parse_gm_time(game_time_str).replace(
                    year=week_date.year, month=week_date.month, day=week_date.day
                )

                game_id_cell = fr.find('td', class_='FScore')
                if not game_id_cell:
                    continue
                game_id = int(game_id_cell.find('nobr')['data-fixture-id'])

                game_venue = fr.find('td', class_='FPlayingArea').text.strip()

                htc = fr.find('td', class_='FHomeTeam')
                atc = fr.find('td', class_='FAwayTeam')

                if not htc or not atc:
                    continue

                if not htc.find('a') or not atc.find('a'):
                    continue

                game_home_team_id = None
                game_away_team_id = None

                game = None
                if game_day:
                    matching_games = [g for g in game_day.games if g.id == game_id]
                    if matching_games:
                        # Do not register a duplicate, the game is already known probably due to the standings page.
                        log.warning(
                            f"Discarding game {game_id} ({game_time}) from fixtures page, "
                            f"the game is already present in the GameDay (probably from standings page)."
                        )
                        continue
                    game = matching_games[0]

                if not game:
                    game = Game(
                        id=game_id,
                        starts_at=game_time,
                        season_stage=SeasonStages.regular,
                        venue=game_venue,
                        home_team_id=self.unicorn_team_id(game_home_team_id or extract_from_link(htc.find('a'), 'TeamId')),
                        away_team_id=self.unicorn_team_id(game_away_team_id or extract_from_link(atc.find('a'), 'TeamId')),
                    )

                week_games.append(game)

            if not game_day:
                self.game_days.append(GameDay(
                    date=week_date,
                    games=week_games,
                ))
