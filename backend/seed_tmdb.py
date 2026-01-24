import os
import time
import requests
from db import SessionLocal, Movie

TMDB_API_KEY = os.getenv("TMDB_API_KEY")
TMDB_URL = "https://api.themoviedb.org/3"
LANG = "en-US"
MAX_PAGES = 500

GENRE_MAP = {}

def load_genres():
    url = f"{TMDB_URL}/genre/movie/list"
    r = requests.get(url, params={
        "api_key": TMDB_API_KEY,
        "language": LANG
    })
    data = r.json()
    for g in data["genres"]:
        GENRE_MAP[g["id"]] = g["name"]


def seed_movies():
    session = SessionLocal()
    inserted = 0

    for page in range(1, MAX_PAGES + 1):
        print(f" Fetching page {page}")

        r = requests.get(
            f"{TMDB_URL}/discover/movie",
            params={
                "api_key": TMDB_API_KEY,
                "language": LANG,
                "page": page,
                "sort_by": "popularity.desc",
                "vote_count.gte": 50
            }
        )

        if r.status_code != 200:
            print("TMDB error, stopping")
            break

        for m in r.json()["results"]:
            if not m.get("title") or not m.get("genre_ids"):
                continue

            genre = GENRE_MAP.get(m["genre_ids"][0], "Unknown")

            exists = session.query(Movie).filter_by(title=m["title"]).first()
            if exists:
                continue

            movie = Movie(
                title=m["title"],
                genre=genre,
                tmdb_rating=m.get("vote_average", 0)
            )
            session.add(movie)
            inserted += 1

        session.commit()
        time.sleep(0.2)

    session.close()
    print(f"Inserted {inserted} movies")


if __name__ == "__main__":
    print("Loading TMDB genres...")
    load_genres()
    print("Seeding movies...")
    seed_movies()
