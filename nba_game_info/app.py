from flask import Flask, render_template, jsonify, url_for
import datetime
import requests
import os
import configparser
from nba_api.stats.static import teams
from nba_api.stats.endpoints import teamgamelog, commonteamroster, playergamelog
import datetime

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
api_key = config.get('API_Key', 'key')

# Cache variables
game_data_cache = None
cache_expiry_time = datetime.datetime.now()

# Cache duration in seconds
cache_duration = 30

def refresh_game_data(over_under_data):
    url = "https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json"
    response = requests.get(url)
    games = response.json()['scoreboard']['games']
    return game_info(games, over_under_data)

def get_team_id(team_name):
    all_teams = teams.get_teams()
    for team in all_teams:
        if team_name == team['full_name']:
            return team['id']
    return None

def get_team_logo_url(team_name):
    logo_filename = team_name + ".png"
    logo_path = os.path.join("team_logos", logo_filename)
    static_folder = os.path.join(app.root_path, "static")
    if os.path.exists(os.path.join(static_folder, logo_path)):
        return url_for("static", filename=logo_path)
    else:
        return url_for("static", filename="team_logos/default_logo.png")

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

def team_played_day_before(team_name, game_date):
    team_id = get_team_id(team_name)
    if team_id is None:
        return False

    team_game_log = teamgamelog.TeamGameLog(team_id=team_id).get_data_frames()[0]
    team_game_log['GAME_DATE'] = pd.to_datetime(team_game_log['GAME_DATE'])

    game_date = datetime.datetime.strptime(game_date, "%Y-%m-%d")
    day_before = game_date - datetime.timedelta(days=1)

    return any(team_game_log['GAME_DATE'] == day_before)    

def get_injury_report(team_name):
    team_id = get_team_id(team_name)
    if team_id is None:
        return []

    roster = commonteamroster.CommonTeamRoster(team_id=team_id).get_data_frames()[0]
    injured_players = []

    for _, player in roster.iterrows():
        player_id = player['PLAYER_ID']
        player_game_log = playergamelog.PlayerGameLog(player_id=player_id).get_data_frames()[0]

        if len(player_game_log) == 0:
            continue

        last_game = player_game_log.iloc[0]
        if last_game['INJURY_STATUS'] != 'ACTIVE':
            injured_players.append({
                'name': player['PLAYER'],
                'injury_status': last_game['INJURY_STATUS']
            })

    return injured_players

def teamData(game):
    away_team_name = game['awayTeam']['teamCity'] + " " + game['awayTeam']['teamName']
    home_team_name = game['homeTeam']['teamCity'] + " " + game['homeTeam']['teamName']
    away_team_view = away_team_name + " (" + str(game['awayTeam']['wins']) + "-" + str(game['awayTeam']['losses']) + ")"
    home_team_view = home_team_name + " (" + str(game['homeTeam']['wins']) + "-" + str(game['homeTeam']['losses']) + ")"
    return away_team_view + " vs " + home_team_view

def game_score(game, overunder):
    home_team_name = game['homeTeam']['teamCity'] + "_" + game['homeTeam']['teamName']
    away_team_name = game['awayTeam']['teamCity'] + "_" + game['awayTeam']['teamName']

    home_team_logo_url = get_team_logo_url(home_team_name)
    away_team_logo_url = get_team_logo_url(away_team_name)

    homePeriods = game['homeTeam']['periods']
    awayPeriods = game['awayTeam']['periods']
    game_score_output = []

    game_score_output.append("<table class='score-table'>")
    game_score_output.append("<tr><th></th><th>1</th><th>2</th><th>3</th><th>4</th><th class='total'>Total</th></tr>")
    game_score_output.append("<tr><td><img src='" + away_team_logo_url + "' alt='" + away_team_name + "' class='team-logo'></td>")
    for period in awayPeriods:
        game_score_output.append(f"<td>{period['score']}</td>")
    game_score_output.append(f"<td class='total'>{game['awayTeam']['score']}</td></tr>")
    
    game_score_output.append("<tr><td><img src='" + home_team_logo_url + "' alt='" + home_team_name + "' class='team-logo'></td>")
    for period in homePeriods:
        game_score_output.append(f"<td>{period['score']}</td>")
    game_score_output.append(f"<td class='total'>{game['homeTeam']['score']}</td></tr>")
    game_score_output.append("</table>")

    game_score_output.append("<span class='total-text'>Total: " + str((game['homeTeam']['score'] + game['awayTeam']['score'])) + "</span><br>")
    if overunder != 0:
        game_score_output.append("Over/Under: " + str(overunder) + " (" + str(overunder - (game['homeTeam']['score'] + game['awayTeam']['score'])) +  ")" + "<br>")
    
    home_score = game['homeTeam']['score']
    away_score = game['awayTeam']['score']
    is_close_game = abs(home_score - away_score) <= 5

    status = game['gameStatusText']
    if any(quarter in status for quarter in ["Q1", "Q2", "Q3", "Q4", "OT", "Half"]) and status != "Final/OT2":
        status = ""
        status += '<span class="live"> Live</span>'
        if is_close_game:
            status += ' <span class="close-game">Close Game</span>'
        game_score_output.append(status + '<br>')

    return ''.join(game_score_output)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/game_data")
def game_data():
    global game_data_cache, cache_expiry_time, cache_duration
    current_time = datetime.datetime.now()

    should_refresh_cache = (
        game_data_cache is None
        or current_time > cache_expiry_time
        or any(game['status'].lower().startswith("q") for game in game_data_cache)
    )

    if should_refresh_cache:
        over_under_data = refresh_over_under()
        game_data_cache = refresh_game_data(over_under_data)
        cache_expiry_time = current_time + datetime.timedelta(seconds=cache_duration)

    return jsonify(game_data_cache)

@app.route('/over_under_data')
def over_under_data():
    over_under_data = refresh_over_under()
    return jsonify(over_under_data)

if __name__ == "__main__":
    app.run(debug=True)