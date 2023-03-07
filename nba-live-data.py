from nba_api.live.nba.endpoints import scoreboard
import datetime
import requests
import time
import threading
import os

# Today's Score Board
games = scoreboard.ScoreBoard()

# json
testgames = games.get_json()

# dictionary
games.get_dict()

def refresh_data():
  response = requests.get("https://nba-prod-us-east-1-mediaops-stats.s3.amazonaws.com/NBA/liveData/scoreboard/todaysScoreboard_00.json")
  games = response.json()['scoreboard']['games']
  game_info(games)

def game_info(games):
  os.system('clear')
  for game in games:
    print(game['awayTeam']['teamName'] + " vs " + game['homeTeam']['teamName'])
    print(game['gameStatusText'])
    date_str = game['gameEt']
    dt = datetime.datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%S%z")
    dt = dt.replace(tzinfo=None)
    formatted_date = dt.strftime("%m/%d/%Y %I:%M %p")
    current_date = datetime.datetime.now()
    if current_date > dt:
      game_score(game)
    else:
      print(formatted_date)
    print("\n")

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
  threading.Timer(5.0, refresh_data).start()
  time.sleep(5)
