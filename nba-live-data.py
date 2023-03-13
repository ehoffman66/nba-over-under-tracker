import datetime
import requests
import time
import threading
import os
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
api_key = config.get('API_Key', 'key')

def refresh_game_data(over_under_data):
  """
    This function calls the official NBA API and recieves the current days scores. The
    data for all of the days games are parsed and sent over to game_info function.

    Args:
        No Arguments

    Returns:
        No Returns
  """
  url = "https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json"
  response = requests.get(url)
  games = response.json()['scoreboard']['games']
  game_info(games,over_under_data)

def refresh_over_under():
  url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?regions=us&oddsFormat=american&markets=totals&apiKey="
  url = url + api_key
  response = requests.get(url)
  over_under = response.json()
  over_under_game_data = []
  for game in over_under:
    for market in game['bookmakers']:
      if market['key'] == 'draftkings' or market['key'] == "DraftKings":
        print(market['markets'][0]['outcomes'])
        over = market['markets'][0]['outcomes'][0]['point']
        under = market['markets'][0]['outcomes'][1]['point']
        over_under_game_data.append((game['home_team'],over,under))   
  return over_under_game_data

def game_info(games,over_under_data):
  for game in games:
    teamData(game)
    dt = formatDate(game['gameEt'])
    formatted_date = dt.strftime("%m/%d/%Y %I:%M %p")
    current_date = datetime.datetime.now()
    overunder = 0
    if current_date > dt:
      print(game['gameStatusText'])
      for value in over_under_data:
        home_team = game['homeTeam']['teamCity'] + " " + game['homeTeam']['teamName']
        if value[0] == home_team:
          overunder = value[1]
      game_score(game,overunder)
    else:
      print(formatted_date)
    print("\n")

def formatDate(date):
  dt = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
  dt = dt.replace(tzinfo=None)
  return dt

def teamData(game):
    away_team_name = game['awayTeam']['teamCity'] + " " + game['awayTeam']['teamName']
    home_team_name = game['homeTeam']['teamCity'] + " " + game['homeTeam']['teamName']
    away_team_view = away_team_name + " (" + str(game['awayTeam']['wins']) + "-" + str(game['awayTeam']['losses']) + ")"
    home_team_view = home_team_name + " (" + str(game['homeTeam']['wins']) + "-" + str(game['homeTeam']['losses']) + ")"
    print(away_team_view + " vs " + home_team_view)

def game_score(game,overunder):
  homePeriods = game['homeTeam']['periods'] 
  awayPeriods = game['awayTeam']['periods'] 
  print("Away Team: " + str(game['awayTeam']['score']))
  print("Periods : " + str(awayPeriods[0]['score']), str(awayPeriods[1]['score']), str(awayPeriods[2]['score']), str(awayPeriods[3]['score']))
  print("Home Team: " + str(game['homeTeam']['score'])) 
  print("Periods : " + str(homePeriods[0]['score']), str(homePeriods[1]['score']), str(homePeriods[2]['score']), str(homePeriods[3]['score']))
  print("Total: "     + str((game['homeTeam']['score'] + game['awayTeam']['score'])))
  print("Over/Under: " + str(overunder))

over_under_data = refresh_over_under()

while True:
  os.system('clear')
  threading.Timer(5.0, refresh_game_data(over_under_data)).start()
  time.sleep(5)


