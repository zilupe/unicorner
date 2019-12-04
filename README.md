# unicorner

GM season standings and fixtures parser as a reusable library.

### Usage

    from unicorner import SeasonParse
    
    sp = SeasonParse()
    sp.parse_standings_page(path="standings.html")
    sp.parse_fixtures_page(path="fixtures.html")
    print(sp.game_days[0])
