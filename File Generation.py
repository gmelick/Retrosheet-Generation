import requests


def generate():
    year = 2017
    parameters = {"sportId": 1, "gameTypes": "R", "startDate": "01/01/" + str(year), "endDate": "12/31/" + str(year)}
    response = requests.get("https://statsapi.mlb.com/api/v1/schedule", params=parameters).json()
    game_list = generate_game_list(response)
    for game in game_list:
        box_score = requests.get("https://statsapi.mlb.com/api/v1/game/" + str(game) + "/boxscore").json()


def generate_game_list(json):
    game_list = list()
    for date in json["dates"]:
        for game in date["games"]:
            game_list.append(game["gamePk"])
    return game_list

def abbreviation_dictionary():
    abbr_dict = dict()
    abbr_dict["LAA"] = "ANA"
    abbr_dict["BAL"] = "BAL"
    abbr_dict["BOS"] = "BOS"
generate()
