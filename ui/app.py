import os
from flask import Flask, request, jsonify, render_template, redirect, url_for
from pymongo import MongoClient
import configparser
import requests

app = Flask(__name__)

# Load configuration from file or environment variables
config = configparser.ConfigParser()
config_path = os.path.join(os.path.dirname(__file__), 'config.conf')
print(f"Loading configuration from {config_path}")
config.read(config_path)

db_uri = os.getenv('DB_URI', config.get('database', 'uri'))
db_username = os.getenv('DB_USERNAME', config.get('database', 'username'))
db_password = os.getenv('DB_PASSWORD', config.get('database', 'password'))
db_name = os.getenv('DB_NAME', config.get('database', 'db_name'))

backend_host = os.getenv('BACKEND_HOST', config.get('backend', 'host'))
backend_port = os.getenv('BACKEND_PORT', config.getint('backend', 'port'))

print(f"Database URI: {db_uri}")
print(f"Database Name: {db_name}")

client = MongoClient(db_uri, username=db_username, password=db_password)
db = client[db_name]

@app.route('/')
def index():
    genres = list(db.genres.find())
    years = sorted(db.movies.distinct('year'))
    return render_template('index.html', genres=genres, years=years)

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.get_json()
        print(f"Received data for scraping: {data}")
        scraper_url = f'http://{backend_host}:{backend_port}/scrape'
        response = requests.post(scraper_url, json=data)
        print(f"Response from backend: {response.status_code}, {response.json()}")
        if response.status_code == 200:
            return jsonify({'redirect': url_for('results')}), 200
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Exception occurred in /scrape: {e}")
        return jsonify({'error': 'Failed to process request'}), 400

@app.route('/scrape_genres', methods=['POST'])
def scrape_genres():
    try:
        scraper_url = f'http://{backend_host}:{backend_port}/scrape_genres'
        response = requests.post(scraper_url)
        print(f"Response from backend: {response.status_code}, {response.json()}")
        if response.status_code == 200:
            return jsonify({'redirect': url_for('results')}), 200
        return jsonify(response.json()), response.status_code
    except Exception as e:
        print(f"Exception occurred in /scrape_genres: {e}")
        return jsonify({'error': 'Failed to process request'}), 400

@app.route('/results')
def results():
    genres = list(db.genres.find())
    years = sorted(db.movies.distinct('year'))
    genre_filters = request.args.getlist('genre')
    year_filters = request.args.getlist('year')
    query = {}
    if genre_filters:
        query['genres'] = {'$in': genre_filters}
    if year_filters:
        query['year'] = {'$in': [int(y) for y in year_filters]}
    
    movies = list(db.movies.find(query))
    return render_template('results.html', results=movies, genres=genres, years=years)

if __name__ == '__main__':
    ui_host = os.getenv('UI_HOST', config.get('ui', 'host'))
    ui_port = os.getenv('UI_PORT', config.getint('ui', 'port'))
    app.run(host=ui_host, port=ui_port, debug=True)
