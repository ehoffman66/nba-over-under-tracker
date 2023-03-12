import datetime
import requests
import time
import threading
import os
import configparser

config = configparser.ConfigParser()
config.read('config.ini')
api_key = config.get('API_Key', 'key')

def refresh_data():
  url = "https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json"
  response = requests.get(url)
  games = response.json()['scoreboard']['games']
  game_info(games)

def refresh_over_under():
  url = "https://api.the-odds-api.com/v4/sports/basketball_nba/odds/?regions=us&oddsFormat=american&markets=totals&apiKey="
  url = url + api_key
  response = requests.get(url)
  over_under = response.json()
  for game in over_under:
    for market in game['bookmakers']:
      if market['key'] == 'draftkings':
        print(market['markets'])

def game_info(games):
  os.system('clear')
  #refresh_over_under()
  for game in games:
    teamData(game)
    dt = formatDate(game['gameEt'])
    formatted_date = dt.strftime("%m/%d/%Y %I:%M %p")
    current_date = datetime.datetime.now()
    if current_date > dt:
      print(game['gameStatusText'])
      game_score(game)
    else:
      print(formatted_date)
    print("\n")

def formatDate(date):
  dt = datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
  dt = dt.replace(tzinfo=None)
  return dt

def teamData(game):
    awayTeamView = game['awayTeam']['teamCity'] + " " + game['awayTeam']['teamName'] + " (" + str(game['awayTeam']['wins']) + "-" + str(game['awayTeam']['losses']) + ")"
    homeTeamView = game['homeTeam']['teamCity'] + " " + game['homeTeam']['teamName'] + " (" + str(game['homeTeam']['wins']) + "-" + str(game['homeTeam']['losses']) + ")"
    print(awayTeamView + " vs " + homeTeamView)

def game_score(game):
  homePeriods = game['homeTeam']['periods'] 
  awayPeriods = game['awayTeam']['periods'] 
  print("Away Team: " + str(game['awayTeam']['score']))
  print("Periods : " + str(awayPeriods[0]['score']), str(awayPeriods[1]['score']), str(awayPeriods[2]['score']), str(awayPeriods[3]['score']))
  print("Home Team: " + str(game['homeTeam']['score'])) 
  print("Periods : " + str(homePeriods[0]['score']), str(homePeriods[1]['score']), str(homePeriods[2]['score']), str(homePeriods[3]['score']))
  print("Total: "     + str((game['homeTeam']['score'] + game['awayTeam']['score']))) 

refresh_data()
while True:
  threading.Timer(2.0, refresh_data).start()
  time.sleep(2)
