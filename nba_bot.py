import requests
from bs4 import BeautifulSoup
import tweepy
import json
import time
from datetime import datetime, timedelta
import random
from typing import Dict, List, Tuple
import logging
import openai

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('sports_bot.log'),
        logging.StreamHandler()
    ]
)

class Config:
    def __init__(self, config_path: str = 'config.json'):
        with open(config_path, 'r') as f:
            config = json.load(f)
        self.twitter_api_key = config['twitter']['api_key']
        self.twitter_api_secret = config['twitter']['api_secret']
        self.twitter_access_token = config['twitter']['access_token']
        self.twitter_access_token_secret = config['twitter']['access_token_secret']
        self.openai_api_key = config['openai']['api_key']
        self.sport = config['sport']
        self.team_nicknames = config['team_nicknames']

class GameScraper:
    def __init__(self, sport: str):
        self.sport = sport
        self.base_url = f"https://www.espn.com/{sport}/scoreboard"
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }

    def get_latest_games(self) -> List[Dict]:
        """Scrape the latest games from ESPN."""
        try:
            response = requests.get(self.base_url, headers=self.headers)
            soup = BeautifulSoup(response.text, 'html.parser')
            games = []

            game_containers = soup.find_all('div', class_='scoreboard')
            
            for game in game_containers:
                game_data = {
                    'teams': self._extract_teams(game),
                    'score': self._extract_score(game),
                    'stats': self._extract_player_stats(game),
                    'injuries': self._extract_injuries(game)
                }
                games.append(game_data)

            return games

        except Exception as e:
            logging.error(f"Error scraping games: {str(e)}")
            return []

    def _extract_teams(self, game_container) -> Tuple[str, str]:
        """Extract team names from game container."""
        pass

    def _extract_score(self, game_container) -> Tuple[int, int]:
        """Extract final score from game container."""
        pass

    def _extract_player_stats(self, game_container) -> Dict:
        """Extract player statistics from game container."""
        pass

    def _extract_injuries(self, game_container) -> List[str]:
        """Extract injury reports from game container."""
        pass

class JokeGenerator:
    def __init__(self, openai_api_key: str):
        self.openai_api_key = openai_api_key
        openai.api_key = openai_api_key

    def generate_game_joke(self, game_data: Dict) -> str:
        """Generate a contextual joke about the game using OpenAI."""
        try:
            prompt = self._create_joke_prompt(game_data)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are a witty sports commentator who makes clever, good-natured jokes about games."},
                    {"role": "user", "content": prompt}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logging.error(f"Error generating joke: {str(e)}")
            return self._get_fallback_joke()

    def _create_joke_prompt(self, game_data: Dict) -> str:
        """Create a prompt for joke generation based on game data."""
        winner, loser = self._determine_winner(game_data)
        return f"Create a short, funny joke about a game where {winner} beat {loser} with a score of {game_data['score']}. Include relevant player stats if available."

    def _determine_winner(self, game_data: Dict) -> Tuple[str, str]:
        """Determine winner and loser from game data."""
        team1, team2 = game_data['teams']
        score1, score2 = game_data['score']
        return (team1, team2) if score1 > score2 else (team2, team1)

    def _get_fallback_joke(self) -> str:
        """Return a fallback joke if API fails."""
        fallback_jokes = [
            "This game was so one-sided, the losing team's GPS kept saying 'make a U-turn'!",
            "The score was so lopsided, they had to check if gravity was working on both sides of the field!",
            "That wasn't a game, that was a live demonstration of social distancing!"
        ]
        return random.choice(fallback_jokes)

class TwitterPoster:
    def __init__(self, config: Config):
        auth = tweepy.OAuthHandler(
            config.twitter_api_key,
            config.twitter_api_secret
        )
        auth.set_access_token(
            config.twitter_access_token,
            config.twitter_access_token_secret
        )
        self.api = tweepy.API(auth)
        self.client = tweepy.Client(
            consumer_key=config.twitter_api_key,
            consumer_secret=config.twitter_api_secret,
            access_token=config.twitter_access_token,
            access_token_secret=config.twitter_access_token_secret
        )

    def post_game_update(self, game_data: Dict, joke: str) -> bool:
        """Post game update and joke to Twitter."""
        try:
            tweet_text = self._format_tweet(game_data, joke)
            self.client.create_tweet(text=tweet_text)
            logging.info(f"Successfully posted tweet about {game_data['teams']}")
            return True
        except Exception as e:
            logging.error(f"Error posting to Twitter: {str(e)}")
            return False

    def _format_tweet(self, game_data: Dict, joke: str) -> str:
        """Format game data and joke into a tweet."""
        team1, team2 = game_data['teams']
        score1, score2 = game_data['score']
        
        hashtag1 = self.config.team_hashtags.get(team1, f"#{team1.replace(' ', '')}")
        hashtag2 = self.config.team_hashtags.get(team2, f"#{team2.replace(' ', '')}")
        
        arena = self.config.team_arenas.get(team1)
        location = f" at {arena}" if arena else ""
        
        tweet = f"🏁 FINAL SCORE{location}:\n{team1} {score1} - {team2} {score2}\n\n"
        
        if game_data['stats']:
            tweet += "📊 Key Stats:\n"
            for stat in list(game_data['stats'].items())[:2]:
                tweet += f"• {stat[0]}: {stat[1]}\n"
        
        if game_data['injuries']:
            tweet += "\n🏥 Injuries:\n"
            tweet += f"• {game_data['injuries'][0]}\n"
        
        tweet += f"\n😄 {joke}\n\n#Sports #GameDay"
        
        return tweet[:280] 
        
def main():
    config = Config()
    scraper = GameScraper(config.sport)
    joke_generator = JokeGenerator(config.openai_api_key)
    twitter_poster = TwitterPoster(config)
    while True:
        try:
            games = scraper.get_latest_games()
            for game in games:
                joke = joke_generator.generate_game_joke(game)
                twitter_poster.post_game_update(game, joke)
#This time below is so rate limits aren't hit!
            time.sleep(60)
            time.sleep(300)      
        except Exception as e:
            logging.error(f"Error in main loop: {str(e)}")
            time.sleep(300)  

if __name__ == "__main__":
    main()
