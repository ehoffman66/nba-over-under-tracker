from flask import Flask, render_template, jsonify
import datetime
import requests
import time
import threading
import os
import configparser

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
api_key = config.get('API_Key', 'key')

# Cache variables
game_data_cache = None
cache_expiry_time = datetime.datetime.now()

# Cache duration in seconds
cache_duration = 60

def refresh_game_data(over_under_data):
    url = "https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json"
    response = requests.get(url)
    games = response.json()['scoreboard']['games']
    return game_info(games, over_under_data)

def refresh_over_under():
    url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?regions=us&oddsFormat=american&markets=totals&apiKey="
    url = url + api_key
    response = requests.get(url)
    over_under = response.json()
    over_under_game_data = []
    for game in over_under:
        for market in game['bookmakers']:
            if market['key'] == 'draftkings' or market['key'] == "DraftKings":
                over = market['markets'][0]['outcomes'][0]['point']
                under = market['markets'][0]['outcomes'][1]['point']
                over_under_game_data.append((game['home_team'], over, under))   
    return over_under_game_data

def game_info(games, over_under_data):
    game_list = []
    for game in games:
        game_data = {}
        game_data['teams'] = teamData(game)
        dt = formatDate(game['gameEt'])
        formatted_date = dt.strftime("%m/%d/%Y %I:%M %p")
        current_date = datetime.datetime.now()
        overunder = 0
        if current_date > dt:
            game_data['status'] = game['gameStatusText']
            for value in over_under_data:
                home_team = game['homeTeam']['teamCity'] + " " + game['homeTeam']['teamName']
                if value[0] == home_team:
                    overunder = value[1]
            game_data['score'] = game_score(game, overunder)
        else:
            game_data['status'] = formatted_date
        game_list.append(game_data)
    return game_list

def formatDate(date):
    dt = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
    dt = dt.replace(tzinfo=None)
    return dt

def teamData(game):
    away_team_name = game['awayTeam']['teamCity'] + " " + game['awayTeam']['teamName']
    home_team_name = game['homeTeam']['teamCity'] + " " + game['homeTeam']['teamName']
    away_team_view = away_team_name + " (" + str(game['awayTeam']['wins']) + "-" + str(game['awayTeam']['losses']) + ")"
    home_team_view = home_team_name + " (" + str(game['homeTeam']['wins']) + "-" + str(game['homeTeam']['losses']) + ")"
    return away_team_view + " vs " + home_team_view

def game_score(game, overunder):
    homePeriods = game['homeTeam']['periods']
    awayPeriods = game['awayTeam']['periods']
    game_score_output = []

    game_score_output.append("<table class='score-table'>")
    game_score_output.append("<tr><th></th><th>1</th><th>2</th><th>3</th><th>4</th><th class='total'>Total</th></tr>")
    game_score_output.append("<tr><td>Away Team:</td>")
    for period in awayPeriods:
        game_score_output.append(f"<td>{period['score']}</td>")
    game_score_output.append(f"<td class='total'>{game['awayTeam']['score']}</td></tr>")
    
    game_score_output.append("<tr><td>Home Team:</td>")
    for period in homePeriods:
        game_score_output.append(f"<td>{period['score']}</td>")
    game_score_output.append(f"<td class='total'>{game['homeTeam']['score']}</td></tr>")
    game_score_output.append("</table>")

    game_score_output.append("<span class='total-text'>Total: " + str((game['homeTeam']['score'] + game['awayTeam']['score'])) + "</span><br>")
    if overunder != 0:
        game_score_output.append("Over/Under: " + str(overunder) + " (" + str(overunder - (game['homeTeam']['score'] + game['awayTeam']['score'])) +  ")" + "<br>")
    
    if any(quarter in game['gameStatusText'] for quarter in ["Q1", "Q2", "Q3", "Q4", "OT", "Half"]) and game['gameStatusText'] != "Final/OT2":
        game_score_output.append("<span class='live'>Live</span><br>")
    
    return ''.join(game_score_output)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/game_data")
def game_data():
    global game_data_cache, cache_expiry_time
    current_time = datetime.datetime.now()

    if game_data_cache is None or current_time > cache_expiry_time:
        over_under_data = refresh_over_under()
        game_data_cache = refresh_game_data(over_under_data)
        cache_expiry_time = current_time + datetime.timedelta(seconds=cache_duration)

    return jsonify(game_data_cache)

@app.route('/over_under_data')
def over_under_data():
    # Replace the following with the actual API call for all games
    over_under_data = refresh_over_under()
    return jsonify(over_under_data)

if __name__ == "__main__":
    app.run(debug=True)