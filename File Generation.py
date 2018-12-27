import requests
import json


def generate():
    year = 2017
    file = open(".\\data\\" + str(year) + "cmp.csv", 'w+')
    game_list = generate_game_list(year)
    for game_id in game_list:
        try:
            box_score = requests.get("https://statsapi.mlb.com/api/v1/game/" + str(game_id) + "/boxscore").json()
            live_feed = requests.get("https://statsapi.mlb.com/api/v1.1/game/" + str(game_id) + "/feed/live").json()
            play_by_play = requests.get("https://statsapi.mlb.com/api/v1/game/" + str(game_id) + "/playByPlay").json()
        except json.decoder.JSONDecodeError:
            continue
        except requests.exceptions.ChunkedEncodingError:
            continue

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
            runner_going, runner_out = find_runners(play["runners"], play["playEvents"])
            running_on_last_pitch = running_ends_ab(runner_going, play["actionIndex"], play["pitchIndex"])
            for i in breakpoints:
                file.write(game_key + ",")
                file.write(away_team + ",")
                file.write(str(play["about"]["inning"]) + ",")

                if play["about"]["halfInning"] == "top":
                    file.write("0,")
                else:
                    file.write("1,")

                file.write(str(outs) + ",")

                if i in runner_out:
                    outs = (outs + 1) % 3

                if play["result"]["event"] == "Intent Walk" and not play["pitchIndex"]:
                    file.write("3,0,")
                elif not play["playEvents"]:
                    file.write("0,0,")
                elif i in runner_going or running_on_last_pitch:
                    file.write(runner_count(play, i))
                else:
                    file.write(get_count(play, i))

                # s = ""
                # if play["result"]["event"] == "Intent Walk" and len(play["pitchIndex"]) == 0:
                #     s = "VVVV"
                # else:
                #     if len(play["pitchIndex"]) == 0:
                #         s += "N"
                #     else:
                #         for j in range(play["pitchIndex"][0], i + 1):
                #             if play["playEvents"][j]["isPitch"]:
                #                 s += play["playEvents"][j]["details"]["code"]
                #
                # file.write(s + ",")

                file.write("\n")
            outs = play["count"]["outs"] % 3

    file.close()


def generate_game_list(year):
    parameters = {"sportId": 1, "gameTypes": "R", "startDate": "01/01/" + str(year), "endDate": "12/31/" + str(year)}
    json_schedule = requests.get("https://statsapi.mlb.com/api/v1/schedule", params=parameters).json()
    game_list = list()

    for date in json_schedule["dates"]:
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
    first_pitch, last_pitch = 0, 0

    if play["pitchIndex"]:
        first_pitch = play["pitchIndex"][0]
        last_pitch = play["pitchIndex"][-1]

    for action in play["actionIndex"]:
        event = play["playEvents"][action]["details"]["event"]
        if (first_pitch < action < last_pitch and "Sub" not in event and "Game Advisory" not in event
                and "Challenge" not in event and "Injury" not in event and "Ejection" not in event
                and "Defensive Switch" not in event) or "Balk" == event:
            breakpoints.append(action)
            first_pitch = new_first_pitch(first_pitch, action, play["pitchIndex"])
    breakpoints.append(last_pitch)

    return breakpoints


def new_first_pitch(first_pitch, action, pitch_index):
    count = 1

    while first_pitch < action:
        first_pitch = pitch_index[count]
        count += 1

    return first_pitch


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


def get_count(play, i):
    s = ""
    event = play["result"]["event"]

    if play["playEvents"] and play["playEvents"][i]["count"]:
        balls = play["playEvents"][i]["count"]["balls"]
        strikes = play["playEvents"][i]["count"]["strikes"]
    else:
        balls = play["count"]["balls"]
        strikes = play["count"]["strikes"]

    if event == "Hit By Pitch":
        s += str(balls - 1) + "," + str(strikes) + ","
    elif "Runner Out" == event:
        s += runner_count(play, i)
    elif balls == 4:
        s += "3," + str(strikes) + ","
    elif strikes == 3:
        s += str(balls) + "," + "2,"
    else:
        s += str(balls) + "," + str(strikes) + ","

    return s


def runner_count(play, i):
    s = ""
    index = 0

    while index <= i:
        if play["playEvents"][i - index]["isPitch"]:
            s += make_count(play["playEvents"][i - index])
            break
        index += 1

    if s == "":
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


def find_runners(runners, play_events):
    runner_going = []
    out = []

    for runner in runners:
        event = runner["details"]["event"]
        index = runner["details"]["playIndex"]
        if "Stolen Base" in event:
            runner_going.append(index)
        elif "Defensive Indiff" in event:
            runner_going.append(index)
        elif event.startswith("Caught Stealing"):
            runner_going.append(index)
        elif "Wild Pitch" in event:
            if runner["movement"]["start"] is not None:
                runner_going.append(index)
        elif "Passed Ball" in event:
            if runner["movement"]["start"] is not None:
                runner_going.append(index)
        elif "Runner Out" == event:
            runner_going.append(index)
        elif event.startswith("Caught Stealing"):
            runner_going.append(index)
        elif "Pickoff Caught Stealing" in event:
            if play_events[index - 1]["details"]["fromCatcher"]:
                runner_going.append(index)

        if runner["movement"]["end"] is None and "DP" not in runner["details"]["event"]:
            out.append(index)

    return runner_going, out


def running_ends_ab(running, action_index, pitch_index):
    if running:
        i = running[-1]
    else:
        return False

    if i not in action_index and pitch_index and i > pitch_index[-1]:
        return True
    elif not pitch_index:
        return True

    return False


generate()
