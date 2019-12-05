# unicorner

GM season standings and fixtures parser as a reusable library.

This library can change at any time. Same applies to GM's actual websites. Use at your own risk.

### Install

    pip install unicorner

### Usage

#### Parsing Standings and Fixtures Pages

Standings page has to parsed before fixtures can be parsed.

    from unicorner import SeasonParse
    
    sp = SeasonParse()
    sp.parse_standings_page(path="standings.html")
    sp.parse_fixtures_page(path="fixtures.html")
    print(sp.game_days[0])

#### Extracting to CSV

    python -m unicorner extract_all --help

### GM Data Model Issues

* GM does not store the historical team names - only the latest version of the name is preserved.
* In the past, GM would reuse the same team object for unrelated groups of people so you would
  have one season `TeamId=23` point to to *Team A* and the next season, if all the people of *Team A* left,
  `TeamId=23` could point to another group of players *Team B*. You would see this in team history page
  which would show past games that the new group of players had never heard of.

Both of the above are caused by not having a *season-team* model.

We work around this by first introducing
the concept of **Franchise** - the identity of a group of players playing together that spans over
more than one season. Each franchise should be given an ID which is independent from GM IDs.
These can be maintained in a `franchises.csv` file.

Then, for each season that a franchise joins, we create a separate **Team** object whose ID is a 
concatenation of zero-padded GM season's ID and team ID. 
For example, team identified by GM with `TeamId=23` playing in season `SeasonId=101` gets ID `0101.23`

Each such team can have its own name so every season a franchise can use a different name. The mapping
from teams to franchises is maintained in a `franchise_seasons.csv` file.

Examples of both files can be found under `tests/data/`
