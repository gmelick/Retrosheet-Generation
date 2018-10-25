import requests


def generate():
    year = 2017
    file = open(".\\data\\" + str(year) + "cmp.csv", 'w+')
    game_list = generate_game_list(year)
    for game_id in game_list:
        box_score = requests.get("https://statsapi.mlb.com/api/v1/game/" + str(game_id) + "/boxscore").json()
        live_feed = requests.get("https://statsapi.mlb.com/api/v1.1/game/" + str(game_id) + "/feed/live").json()
        play_by_play = requests.get("https://statsapi.mlb.com/api/v1/game/" + str(game_id) + "/playByPlay").json()

        game_key = generate_game_key(box_score, live_feed)
        away_team = box_score["teams"]["away"]["team"]["teamCode"].upper()
        runners = [[0 for i in range(3)] for j in range(2)]
        current_hitters_index = [[0 for i in range(9)] for j in range(2)]
        current_fielder_index = [[0 for i in range(9)] for j in range(2)]
        hitter_fielder_dictionaries = create_hitter_fielder_dictionaries(box_score)
        hitters_list = hitter_fielder_dictionaries[0]
        fielders_list = hitter_fielder_dictionaries[1]

        print(game_id)
        print(game_key)
    file.close()


def generate_game_list(year):
    parameters = {"sportId": 1, "gameTypes": "R", "startDate": "01/01/" + str(year), "endDate": "12/31/" + str(year)}
    json = requests.get("https://statsapi.mlb.com/api/v1/schedule", params=parameters).json()
    game_list = list()
    for date in json["dates"]:
        for game in date["games"]:
            game_list.append(game["gamePk"])
    return game_list


def generate_game_key(box_score, live_feed):
    home_abbr = box_score["teams"]["home"]["team"]["teamCode"].upper()
    timestamp = live_feed["gameData"]["datetime"]["originalDate"].replace("-", "")
    game_number = live_feed["gameData"]["game"]["gameNumber"] - 1
    return home_abbr + timestamp + str(game_number)


def create_hitter_fielder_dictionaries(box_score):
    home_dict = create_dictionary(box_score, "home")
    away_dict = create_dictionary(box_score, "away")

    hitters_list_home = home_dict[0]
    hitters_list_away = away_dict[0]
    fielders_list_home = home_dict[1]
    fielders_list_away = home_dict[1]

    hitters_dict = [hitters_list_away, hitters_list_home]
    fielders_dict = [fielders_list_home, fielders_list_away]

    return hitters_dict, fielders_dict


def create_dictionary(box_score, home_away):
    hitters_dictionary = dict()
    fielders_dictionary = dict()

    players = box_score["teams"][home_away]["players"]
    for player in players:
        player_id = players[player]["person"]["id"]
        if "allPositions" in players[player]:
            for position in players[player]["allPositions"]:
                if player_id not in fielders_dictionary:
                    fielders_dictionary[player_id] = list()
                fielders_dictionary[player_id].append(position["code"])
        if "battingOrder" in players[player]:
            hitters_dictionary[player_id] = players[player]["battingOrder"]

    return hitters_dictionary, fielders_dictionary


generate()
