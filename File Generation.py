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
        print(game_id)
        print(game_key)

        away_team = box_score["teams"]["away"]["team"]["teamCode"].upper()
        runners = [[0 for i in range(3)] for j in range(2)]
        current_hitters_index = [[0 for i in range(9)] for j in range(2)]
        hitter_fielder_dictionaries = create_hitter_fielder_dictionaries(box_score)
        hitters_list = hitter_fielder_dictionaries[0]
        fielders_list = hitter_fielder_dictionaries[1]
        current_fielders_list = hitter_fielder_dictionaries[2]

        for play in play_by_play["allPlays"]:
            breakpoints = find_breakpoints(play)
            substitutions = find_substitutions(play)

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
    if "Y" in live_feed["gameData"]["game"]["doubleHeader"]:
        game_number = live_feed["gameData"]["game"]["gameNumber"]
    else:
        game_number = live_feed["gameData"]["game"]["gameNumber"] - 1
    return home_abbr + timestamp + str(game_number)


def create_hitter_fielder_dictionaries(box_score):
    home_dict = create_dictionary(box_score, "home")
    away_dict = create_dictionary(box_score, "away")

    hitters_dict = [away_dict[0], home_dict[0]]
    fielders_dict = [home_dict[1], away_dict[1]]
    starting_fielders_list = [home_dict[2], away_dict[2]]

    return hitters_dict, fielders_dict, starting_fielders_list


def create_dictionary(box_score, home_away):
    hitters_dictionary = dict()
    fielders_dictionary = dict()
    starting_fielders = [0 for i in range(10)]

    players = box_score["teams"][home_away]["players"]
    for player in players:
        player_id = players[player]["person"]["id"]
        if "allPositions" in players[player]:
            for position in players[player]["allPositions"]:
                if int(position["code"]) <= 10:
                    if player_id not in fielders_dictionary:
                        fielders_dictionary[player_id] = list()
                    fielders_dictionary[player_id].append(int(position["code"]))
            if not players[player]["gameStatus"]["isSubstitute"]:
                starting_position = fielders_dictionary[player_id][0]
                starting_fielders[starting_position - 1] = player_id
        if "battingOrder" in players[player]:
            hitters_dictionary[player_id] = players[player]["battingOrder"]

    return hitters_dictionary, fielders_dictionary, starting_fielders


def find_breakpoints(play):
    breakpoints = list()
    first_pitch = play["pitchIndex"][0]
    for action in play["actionIndex"]:
        event = play["playEvents"][action]["details"]["event"]
        if action > first_pitch and "Sub" not in event and "Game Advisory" not in event:
            breakpoints.append(action)
            count = 1
            while first_pitch < action:
                first_pitch = play["pitchIndex"][count]
                count += 1
    return breakpoints


def find_substitutions(play):
    pitching_changes = list()
    pinch_hitters = list()
    pinch_runners = list()
    defensive_subs = list()
    for action in play["actionIndex"]:
        if "Pitching Substitution" in play["playEvents"][action]["details"]:
            pitching_changes.append(action)
        elif "Pinch-hitter" in play["playEvents"][action]["description"]:
            pinch_hitters.append(action)
        elif "Pinch-runner" in play["playEvents"][action]["description"]:
            pinch_runners.append(action)
        elif "Defensive Sub" in play["playEvents"][action]["details"]:
            defensive_subs.append(action)

    return pitching_changes, pinch_hitters, pinch_runners, defensive_subs


generate()
