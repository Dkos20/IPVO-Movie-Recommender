import redis
import json
from flask import Flask, request, jsonify
from sqlalchemy import func, cast, Float
from search import create_index, index_movie, search_movies
from werkzeug.security import generate_password_hash, check_password_hash
from db import SessionLocal, Movie, Rating, User, init_db


app = Flask(__name__)

redis_client = redis.Redis(
    host="redis",
    port=6379,
    decode_responses=True
)


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    with SessionLocal() as db:
        user = db.query(User).filter(User.username == data["username"]).first()


    if user and check_password_hash(user.password_hash, data["password"]):
        return jsonify({
            "id": user.id,
            "username": user.username
        })

    return jsonify({"error": "Invalid credentials"}), 401

@app.route("/register", methods=["POST"])
def register():
    data = request.json

    with SessionLocal() as db:
        existing_user = db.query(User).filter(User.username == data["username"]).first()
        if existing_user:
            return jsonify({"error": "User exists"}), 400

        user = User(
            username=data["username"],
            password_hash=generate_password_hash(data["password"]),
            email=data["email"]
        )
        db.add(user)
        db.commit()

    return jsonify({"status": "ok"})


@app.route("/movies/latest", methods=["GET"])
def latest_movies():
    session = SessionLocal()

    movies = (
        session.query(
            Movie.id,
            Movie.title,
            Movie.genre,
            Movie.tmdb_rating,
            func.avg(Rating.score).label("avg_rating")
        )
        .outerjoin(Rating)
        .group_by(Movie.id)
        .order_by(Movie.id.desc())
        .limit(10)
        .all()
    )

    session.close()

    return jsonify([
        {
            "id": m.id,
            "title": m.title,
            "genre": m.genre,
            "tmdb_rating": float(m.tmdb_rating) if m.tmdb_rating is not None else None,
            "avg_rating": round(float(m.avg_rating), 2) if m.avg_rating else None
        }
        for m in movies
    ])



@app.route("/movies", methods=["GET"])
def all_movies():
    session = SessionLocal()

    movies = session.query(
        Movie.id,
        Movie.title,
        Movie.genre
    ).all()

    session.close()

    return jsonify([
        {
            "id": m.id,
            "title": m.title,
            "genre": m.genre
        }
        for m in movies
    ])



@app.route("/rate", methods=["POST"])
def rate_movie():
    data = request.json
    session = SessionLocal()

    rating = Rating(
        user_id=data["user_id"],
        movie_id=data["movie_id"],
        score=data["score"]
    )

    session.add(rating)
    session.commit()
    redis_client.delete(f"recommendations:{data['user_id']}")

    return jsonify({"status": "ok"})



@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    results = search_movies(query)
    return jsonify(results)



@app.route("/recommendations/<int:user_id>")
def recommendations(user_id):
    cache_key = f"recommendations:{user_id}"
    cached = redis_client.get(cache_key)

    if cached:
        return jsonify(json.loads(cached))

    session = SessionLocal()

    try:
        favorite_genre = (
            session.query(Movie.genre)
            .join(Rating, Rating.movie_id == Movie.id)
            .filter(Rating.user_id == user_id)
            .group_by(Movie.genre)
            .order_by(func.count(Movie.genre).desc())
            .first()
        )

        if not favorite_genre:
            favorite_genre = (
                session.query(Movie.genre)
                .group_by(Movie.genre)
                .order_by(func.count(Movie.id).desc())
                .first()
            )

        if not favorite_genre:
            return jsonify([])

        rated_movie_ids = (
            session.query(Rating.movie_id)
            .filter(Rating.user_id == user_id)
            .subquery()
        )

        avg_user_rating = cast(func.coalesce(func.avg(Rating.score), 0), Float)
        tmdb = cast(func.coalesce(Movie.tmdb_rating, 0), Float)
        hybrid_score = (0.7 * tmdb) + (0.3 * avg_user_rating)


        rows = (
            session.query(
                Movie.id,
                Movie.title,
                Movie.genre,
                avg_user_rating.label("avg_rating"),
                tmdb.label("tmdb_rating"),
                hybrid_score.label("hybrid_score")
            )
            .outerjoin(Rating, Rating.movie_id == Movie.id)
            .filter(Movie.genre == favorite_genre[0])
            .filter(~Movie.id.in_(rated_movie_ids))
            .group_by(Movie.id)
            .order_by(hybrid_score.desc())
            .limit(3)
            .all()
        )

        result = [
            {
                "id": r.id,
                "title": r.title,
                "genre": r.genre,
                "avg_rating": round(float(r.avg_rating), 2) if r.avg_rating is not None else 0,
                "tmdb_rating": round(float(r.tmdb_rating), 2) if r.tmdb_rating is not None else 0,
                "score": round(float(r.hybrid_score), 2)
            }
            for r in rows
        ]

        redis_client.setex(cache_key, 300, json.dumps(result))
        return jsonify(result)

    finally:
        session.close()

@app.route("/my-ratings/<int:user_id>")
def my_ratings(user_id):
    session = SessionLocal()

    rows = (
        session.query(
            Movie.title,
            Movie.genre,
            Rating.score
        )
        .join(Rating, Rating.movie_id == Movie.id)
        .filter(Rating.user_id == user_id)
        .order_by(Rating.id.desc())
        .all()
    )

    session.close()

    return jsonify([
        {
            "title": r.title,
            "genre": r.genre,
            "score": float(r.score)
        }
        for r in rows
    ])


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    init_db()
    create_index()
    app.run(host="0.0.0.0", port=5000)
