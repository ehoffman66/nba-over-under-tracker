from flask import Flask, render_template, jsonify, url_for
import datetime
import requests
import os
import configparser
from nba_api.stats.static import teams
from nba_api.stats.endpoints import commonteamroster, PlayerDashboardByYearOverYear
from nba_api.stats.endpoints import LeagueDashPlayerStats
import datetime
import pandas as pd

app = Flask(__name__)

config = configparser.ConfigParser()
config.read('config.ini')
api_key = config.get('API_Key', 'key')

# Cache variables
game_data_cache = None
cache_expiry_time = datetime.datetime.now()

# Cache duration in seconds
cache_duration = 30

headers = {
  'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36',
  'Referer': 'https://www.nba.com/'
}
payload={}

def refresh_game_data(over_under_data):
    url = "https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json"
    response = requests.get(url)
    games = response.json()['scoreboard']['games']
    return game_info(games, over_under_data)

def get_team_id(team_name):
    team_name_mapping = {
        'LA Lakers': 'Los Angeles Lakers',
        'LA Clippers': 'Los Angeles Clippers',
        # ... add more mappings as needed
    }
    full_team_name = team_name_mapping.get(team_name, team_name)
    all_teams = teams.get_teams()
    for team in all_teams:
        if team['full_name'].lower() == full_team_name.lower():
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
        home_team_name = game['homeTeam']['teamCity'] + " " + game['homeTeam']['teamName']
        away_team_name = game['awayTeam']['teamCity'] + " " + game['awayTeam']['teamName']
        home_team_logo_name = game['homeTeam']['teamCity'] + "_" + game['homeTeam']['teamName']
        away_team_logo_name = game['awayTeam']['teamCity'] + "_" + game['awayTeam']['teamName']
        game_data['home_team_logo'] = get_team_logo_url(home_team_logo_name)
        game_data['away_team_logo'] = get_team_logo_url(away_team_logo_name)
        game_data['home_team_top_players'] = "<b>Top " + home_team_name + " players:</b>" + get_top_players(home_team_name, num_players=3)
        game_data['away_team_top_players'] = "<b>Top " + away_team_name + " players:</b>" +get_top_players(away_team_name, num_players=3)
        dt = formatDate(game['gameEt'])
        formatted_date = dt.strftime("%m/%d/%Y %I:%M %p")
        current_date = datetime.datetime.now()
        overunder = 0
        if current_date > dt:
            game_data['status'] = game['gameStatusText']
            for value in over_under_data:
                # Use home_team_name instead of home_team
                if value[0] == home_team_name:
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

def get_top_players(team_name, num_players=3):
    team_id = get_team_id(team_name)
    url = "https://stats.nba.com/stats/leaguedashplayerstats?LastNGames=0&MeasureType=Base&Month=0&OpponentTeamID=0&PaceAdjust=N&PerMode=Totals&Period=0&PlusMinus=N&Rank=N&Season=2022-23&SeasonType=Regular+Season"
    # Get the league-wide player statistics
    response = requests.request("GET", url, headers=headers, data=payload)
    player_stats = response.json()
    player_stats = pd.DataFrame(data=player_stats['resultSets'][0]["rowSet"], columns=player_stats['resultSets'][0]["headers"])
    # Filter the player statistics to keep only the players from the specified team
    team_players_stats = player_stats[player_stats['TEAM_ID'] == team_id]
    
    # Sort the player statistics by points per game (PTS) in descending order
    team_players_sorted_by_pts = team_players_stats.sort_values(by='PTS', ascending=False)
    
    # Get the top 'num_players' players based on points per game
    top_players_df = team_players_sorted_by_pts.head(num_players)
    
    # Create a list to store the top players' information
    #top_players_info = []

    top_players_info = ""
    
    # Iterate through each player in the top players data frame
    for _, player in top_players_df.iterrows():
        player_name = player['PLAYER_NAME']
        player_pts = round(player['PTS'] / player['GP'],1)
        player_ast = player['AST']
        player_reb = player['REB']
        
        # Create a dictionary with the player's information and stats
        #player_info = {
        #    'name': player_name,
        #    'points_per_game': player_pts,
        #    'assists_per_game': player_ast,
        #    'rebounds_per_game': player_reb
        #}

        top_players_info = top_players_info + " " + player_name + "(" + str(player_pts) + ")"

        # Add the player's information to the top players list
        #top_players_info.append(player_info)
    
    return top_players_info

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