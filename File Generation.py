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
        runners = [[0]*3]*2
        current_hitters_index = [[0]*9]*2
        hitters_list, fielders_list, current_fielders_list = create_hitter_fielder_dictionaries(box_score)

        outs = 0

        for play in play_by_play["allPlays"]:
            breakpoints = find_breakpoints(play)
            substitutions = find_substitutions(play)
            runner_going, runner_out = find_runners(play["runners"])
            for i in range(len(breakpoints)):
                file.write(game_key + ",")
                file.write(away_team + ",")
                file.write(str(play["about"]["inning"]) + ",")
                if play["about"]["halfInning"] == "top":
                    file.write("0,")
                else:
                    file.write("1,")
                file.write(str(outs) + ",")
                if breakpoints[i] in runner_out:
                    outs = (outs + 1) % 3

                if game_key == "BAL201704080":
                    print(play)
                if len(breakpoints) > len(runner_going) and i == len(breakpoints) - 1:
                    file.write(get_count(play))
                else:
                    file.write(runner_count(play, runner_going[i]))

                s = ""
                if play["result"]["event"] == "Intent Walk" and len(play["pitchIndex"]) == 0:
                    s = "VVVV"
                else:
                    if len(play["pitchIndex"]) == 0:
                        s += "N"
                    else:
                        for j in range(play["pitchIndex"][0], breakpoints[i] + 1):
                            if play["playEvents"][j]["isPitch"]:
                                s += play["playEvents"][j]["details"]["code"]

                file.write(s + ",")

                file.write("\n")
            outs = play["count"]["outs"] % 3

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
    starting_fielders = [0]*10

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
    if play["pitchIndex"]:
        first_pitch = play["pitchIndex"][0]
        last_pitch = play["pitchIndex"][len(play["pitchIndex"]) - 1]
    else:
        first_pitch = 0
        last_pitch = 0
    for action in play["actionIndex"]:
        event = play["playEvents"][action]["details"]["event"]
        if first_pitch < action < last_pitch and "Sub" not in event and "Game Advisory" not in event \
                and "Challenge" not in event and "Injury" not in event:
            breakpoints.append(action)
            count = 1
            while first_pitch < action < last_pitch:
                first_pitch = play["pitchIndex"][count]
                count += 1
    breakpoints.append(last_pitch)
    return breakpoints


def find_substitutions(play):
    pitching_changes = list()
    pinch_hitters = list()
    pinch_runners = list()
    defensive_subs = list()
    for action in play["actionIndex"]:
        if "Pitching Substitution" in play["playEvents"][action]["details"]["event"]:
            pitching_changes.append(action)
        elif "Pinch-hitter" in play["playEvents"][action]["details"]["description"]:
            pinch_hitters.append(action)
        elif "Pinch-runner" in play["playEvents"][action]["details"]["description"]:
            pinch_runners.append(action)
        elif "Defensive Sub" in play["playEvents"][action]["details"]["event"]:
            defensive_subs.append(action)

    return pitching_changes, pinch_hitters, pinch_runners, defensive_subs


def get_count(play):
    s = ""
    balls = play["count"]["balls"]
    strikes = play["count"]["strikes"]
    if play["result"]["event"] == "Hit By Pitch":
        s += str(balls - 1) + "," + str(strikes) + ","
    else:
        if balls == 4:
            s += "3," + str(strikes) + ","
        elif strikes == 3:
            s += str(balls) + "," + "2,"
        else:
            s += str(balls) + "," + str(strikes) + ","
    return s


def runner_count(play, i):
    s = ""
    if play["playEvents"][i]["isPitch"]:
        s += make_count(play["playEvents"][i])
    elif i - 1 >= 0 and play["playEvents"][i - 1]["isPitch"]:
        s += make_count(play["playEvents"][i - 1])
    else:
        s += "0,0,"
    return s


def make_count(play):
    s = ""
    balls = play["count"]["balls"]
    strikes = play["count"]["strikes"]
    if play["details"]["call"]["code"] == "S":
        s += str(balls) + "," + str(strikes - 1) + ","
    elif play["details"]["call"]["code"] == "B":
        s += str(balls - 1) + "," + str(strikes) + ","
    else:
        s += str(balls) + "," + str(strikes) + ","
    return s


def find_runners(runners):
    steal = []
    defensive_indifference = []
    caught_stealing = []
    wild_pitch = []
    runner_out = []
    passed_ball = []
    errors = []
    pick = []
    balk = []
    runner_going = []
    out = []
    for runner in runners:
        event = runner["details"]["event"]
        index = runner["details"]["playIndex"] - 1
        if "Stolen Base" in event:
            steal.append(index)
            runner_going.append(index)
        elif "Defensive Indiff" in event:
            defensive_indifference.append(index)
            runner_going.append(index)
        elif "Caught Stealing" in event:
            caught_stealing.append(index)
            runner_going.append(index)
        elif "Wild Pitch" in event:
            wild_pitch.append(index)
            runner_going.append(index)
        elif "Runner Out" in event:
            runner_out.append(index)
            runner_going.append(index)
        elif "Passed Ball" in event:
            passed_ball.append(index)
            runner_going.append(index)
        elif "Error" == event:
            errors.append(index)
            runner_going.append(index)
        elif "Pickoff" in event:
            pick.append(index)
            runner_going.append(index)
        elif "Balk" in event:
            balk.append(index)
            runner_going.append(index)
        if runner["movement"]["end"] is None:
            out.append(index)
    return runner_going, out


generate()
