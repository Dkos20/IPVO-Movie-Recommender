from flask import Flask, request, jsonify
from sqlalchemy import func
from search import create_index, index_movie, search_movies
from werkzeug.security import generate_password_hash, check_password_hash

from db import SessionLocal, Movie, Rating, User, init_db

app = Flask(__name__)


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



@app.route("/movies", methods=["GET"])
def get_movies():
    session = SessionLocal()

    movies = session.query(
        Movie.id,
        Movie.title,
        Movie.genre,
        func.avg(Rating.score).label("avg_rating")
    ).outerjoin(Rating).group_by(Movie.id).all()

    session.close()

    return jsonify([
        {
            "id": m.id,
            "title": m.title,
            "genre": m.genre,
            "avg_rating": round(m.avg_rating, 2) if m.avg_rating else None
        }
        for m in movies
    ])


@app.route("/movies", methods=["POST"])
def add_movie():
    data = request.json
    session = SessionLocal()
    user_id = data["user_id"]

    movie = Movie(
        title=data["title"],
        genre=data["genre"],
        user_id=user_id
    )
    session.add(movie)
    session.commit()
    index_movie(movie)

    session.close()
    return jsonify({"message": "Movie added"}), 201


@app.route("/rate", methods=["POST"])
def rate_movie():
    data = request.json
    session = SessionLocal()

    rating = Rating(
        movie_id=data["movie_id"],
        score=data["score"]
    )
    session.add(rating)
    session.commit()

    session.close()
    return jsonify({"message": "Rating added"}), 201

@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("q", "")
    if not query:
        return jsonify([])

    results = search_movies(query)
    return jsonify(results)



@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

if __name__ == "__main__":
    init_db()
    create_index()
    app.run(host="0.0.0.0", port=5000)
