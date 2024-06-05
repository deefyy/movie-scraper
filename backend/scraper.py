import requests
from bs4 import BeautifulSoup
import re
from pymongo import MongoClient
import asyncio
from flask import Flask, request, jsonify
import configparser
import os
from multiprocessing import Pool, cpu_count

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

print(f"Database URI: {db_uri}")
print(f"Database Name: {db_name}")

client = MongoClient(db_uri, username=db_username, password=db_password)
db = client[db_name]

@app.route('/')
def home():
    return "Welcome to the Movie Scraper API"

@app.route('/test_db_connection')
def test_db_connection():
    try:
        client = MongoClient(db_uri, username=db_username, password=db_password)
        db = client[db_name]
        collections = db.list_collection_names()
        return jsonify({'message': 'Connected to MongoDB', 'collections': collections}), 200
    except Exception as e:
        return jsonify({'error': 'Failed to connect to MongoDB', 'details': str(e)}), 500

def fetch_content(url):
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Referer': 'https://www.google.com/',
            'Connection': 'keep-alive',
            'Height': '10000'
        }
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            print(f"Successfully fetched content from {url}")
            return response.text
        else:
            print(f"Error: Received status code {response.status_code} for URL {url}")
            return None
    except Exception as e:
        print(f"Exception occurred while fetching URL {url}: {e}")
        return None

def parse_movies(html, category=None):
    if html is None:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    movies = []
    
    for item in soup.find_all('div', class_='g-body-desc'):
        try:
            title_tag = item.find('a')
            if title_tag:
                title = title_tag.text.strip()
            else:
                title = 'N/A'

            year_text = item.find('p').text if item.find('p') else 'N/A'
            year = re.search(r'\((\d{4})\)', year_text).group(1) if re.search(r'\((\d{4})\)', year_text) else 'N/A'

            rating_tag = item.find('div', class_='g-box')
            rating = rating_tag.text.strip().replace('/ 10', '') if rating_tag else 'N/A'

            # Extract the correct description
            description_tag = item.find_next('div', class_='g-right')
            if description_tag:
                pro_tags = description_tag.find_all('pro')
                if pro_tags:
                    last_pro_tag = pro_tags[-1]
                    full_description = last_pro_tag.find_next_sibling(text=True).strip() if last_pro_tag.find_next_sibling(text=True) else 'N/A'
                    sentences = full_description.split('. ')
                    filtered_sentences = [sentence for sentence in sentences if not (sentence.startswith("Występują") or sentence.startswith("Reżyser") or sentence.startswith(title))]
                    description = '. '.join(filtered_sentences[:3]) + '.' if len(filtered_sentences) > 3 else '. '.join(filtered_sentences) + '.'

                    # Truncate description to 150 characters
                    if len(description) > 150:
                        description = description[:150].rsplit(' ', 1)[0] + '...'
                else:
                    description = 'N/A'
            else:
                description = 'N/A'

            # Extract the poster URL
            poster_tag = item.find('div', class_='g-left').find('img')
            poster_url = poster_tag['src'] if poster_tag else 'N/A'

            # Use the provided category
            genres = [category] if category else []

            movies.append({'title': title, 'year': year, 'rating': rating, 'description': description, 'poster_url': poster_url, 'genres': genres})
        except Exception as e:
            print(f"Exception occurred while parsing movie: {e}")
            continue
    
    print(f"Parsed {len(movies)} movies from HTML content.")
    return movies

def parse_genres(html):
    if html is None:
        return []
    soup = BeautifulSoup(html, 'html.parser')
    genres = []
    
    for item in soup.find_all('a', class_='filter genre-filter'):
        genre = item.text.strip()
        url = 'https://kinomaniak.pl' + item['href']
        genres.append({'name': genre, 'url': url})
    
    print(f"Parsed genres: {genres}")
    return genres

def scrape_url(args):
    url, parser, category = args
    html = fetch_content(url)
    if html:
        if parser == parse_genres:
            data = parser(html)
        else:
            data = parser(html, category)
        print(f"Scraped {len(data)} items from {url}.")
        return data
    else:
        return []

def genre_exists(collection, genre_name):
    existing_genre = collection.find_one({'name': genre_name})
    return existing_genre is not None

def movie_exists(collection, title, year):
    existing_movie = collection.find_one({'title': title, 'year': year})
    return existing_movie is not None

def save_to_mongodb(data, db_name, collection_name):
    try:
        print(f"Saving to MongoDB: {len(data)} items")
        client = MongoClient(db_uri, username=db_username, password=db_password)
        db = client[db_name]
        collection = db[collection_name]
        
        new_items = []
        for item in data:
            if 'title' in item and 'year' in item:
                if not movie_exists(collection, item['title'], item['year']):
                    new_items.append(item)
            elif 'name' in item:
                if not genre_exists(collection, item['name']):
                    new_items.append(item)
        
        if new_items:
            print(f"New items to insert: {new_items}")
            collection.insert_many(new_items)
            print(f"Inserted {len(new_items)} new documents into {db_name}.{collection_name}")
        else:
            print("No new items to insert.")
    except Exception as e:
        print(f"Exception occurred while saving to MongoDB: {e}")
        raise

def scrape_and_save(urls, parser, db_name, collection_name, pages=1, category=None):
    try:
        print(f"Starting scrape and save for URLs: {urls}")
        all_items = []
        tasks = []
        for url in urls:
            for page in range(1, pages + 1):
                paginated_url = f"{url}&p={str(page)}"
                tasks.append((paginated_url, parser, category))
        
        with Pool(cpu_count()) as pool:
            results = pool.map(scrape_url, tasks)
        
        for result in results:
            if result:
                all_items.extend(result)
        
        print(f"Total items scraped: {len(all_items)}")
        save_to_mongodb(all_items, db_name, collection_name)
    except Exception as e:
        print(f"Exception occurred in scrape_and_save: {e}")
        raise

@app.route('/scrape', methods=['POST'])
def scrape():
    try:
        data = request.get_json()
        print(f"Received data for scraping: {data}")
        urls = data.get('urls')
        pages = int(data.get('pages', 5))
        category = data.get('category', None)
        if not urls:
            print("No URLs provided")
            return jsonify({'error': 'No URLs provided'}), 400
        scrape_and_save(urls, parse_movies, 'movie_database', 'movies', pages, category)
        return jsonify({'message': 'Scraping started in the background'}), 200
    except Exception as e:
        print(f"Exception occurred in /scrape: {e}")
        return jsonify({'error': 'Failed to process request', 'details': str(e)}), 400

@app.route('/scrape_genres', methods=['POST'])
def scrape_genres():
    try:
        url = 'https://kinomaniak.pl/katalog?g=&k=&d=&q=&sf=imdbRating&s=DESC'
        print(f"Starting genre scrape for URL: {url}")
        scrape_and_save([url], parse_genres, 'movie_database', 'genres')
        print("Genres scraping initiated")
        return jsonify({'message': 'Scraping genres started in the background'}), 200
    except Exception as e:
        print(f"Exception occurred in /scrape_genres: {e}")
        return jsonify({'error': 'Failed to process request', 'details': str(e)}), 400

if __name__ == '__main__':
    backend_host = os.getenv('BACKEND_HOST', config.get('backend', 'host'))
    backend_port = os.getenv('BACKEND_PORT', config.getint('backend', 'port'))
    print(f"Starting Flask server on {backend_host}:{backend_port}")
    app.run(host=backend_host, port=backend_port, debug=True)
