import streamlit as st
import requests


st.set_page_config(page_title="Movie Recommender", layout="centered")

API_URL = "http://nginx"


if "user" not in st.session_state:
    st.session_state.user = None

if "page" not in st.session_state:
    st.session_state.page = "login"



if st.session_state.user is None and st.session_state.page == "login":
    st.title("Login")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        res = requests.post(f"{API_URL}/login", json={
            "username": username,
            "password": password
        })

        if res.status_code == 200:
            st.session_state.user = res.json()
            st.rerun()
        else:
            st.error("Invalid credentials")

    st.markdown("Don't have an account?")
    if st.button("Create account"):
        st.session_state.page = "register"
        st.rerun()

    st.stop()

if st.session_state.user is None and st.session_state.page == "register":
    st.title("Create Account")

    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    email = st.text_input("Email")

    if st.button("Register"):
        res = requests.post(f"{API_URL}/register", json={
            "username": username,
            "password": password,
            "email": email
        })

        if res.status_code == 200:
            st.success("Account created. Please login.")
            st.session_state.page = "login"
            st.rerun()
        else:
            st.error("User already exists")

    if st.button("Back to login"):
        st.session_state.page = "login"
        st.rerun()

    st.stop()

st.success(f"Logged in as {st.session_state.user['username']}")

st.title("🎬 Movie Recommender")

if st.button("🚪 Logout"):
    st.session_state.user = None
    st.rerun()

def get_movies():
    try:
        r = requests.get(f"{API_URL}/movies")
        return r.json()
    except:
        st.error("Backend not reachable")
        return []

def get_recommendations():
    try:
        r = requests.get(
            f"{API_URL}/recommendations/{st.session_state.user['id']}"
        )
        return r.json()
    except:
        return []

def add_movie(title, genre):
    if st.session_state.user:
        requests.post(
            f"{API_URL}/movies",
            json={
                "title": title,
                "genre": genre,
                "user_id": st.session_state.user["id"]
            }
        )
    else:
        st.error("You must be logged in to add a movie")



def rate_movie(movie_id, score):
    requests.post(
        f"{API_URL}/rate",
        json={
            "user_id": st.session_state.user["id"],
            "movie_id": movie_id,
            "score": score
        }
    )


st.header("🔍 Search movies")

query = st.text_input("Search by title or genre")

if query:
    try:
        res = requests.get(f"{API_URL}/search", params={"q": query})
        results = res.json()

        if results:
            for m in results:
                st.write(f"**{m['title']}** ({m['genre']})")
        else:
            st.info("No results found.")
    except:
        st.error("Search service unavailable")


st.header("Recommended for you")

try:
    res = requests.get(
        f"{API_URL}/recommendations/{st.session_state.user['id']}"
    )
    recs = res.json()

    if recs:
        for m in recs:
            st.write(
                f"**{m['title']}** ({m['genre']}) — ⭐ {m['avg_rating']}"
            )
    else:
        st.info("Not enough data for recommendations yet :(")
except:
    st.error("Recommendation service unavailable...")



st.header("Movie Library")

movies = get_movies()

if movies:
    for m in movies:
        st.write(
            f"**{m['title']}** ({m['genre']}) "
            f"— ⭐ {m['avg_rating'] if m['avg_rating'] else 'N/A'}"
        )
else:
    st.info("No movies yet.")

st.divider()
st.header("➕ Add new movie")

with st.form("add_movie"):
    title = st.text_input("Title")
    genre = st.text_input("Genre")
    submitted = st.form_submit_button("Add movie")

    if submitted and title and genre:
        add_movie(title, genre)
        st.success("Movie added!")
        st.rerun()

st.divider()
st.header("⭐ Rate movie")

if movies:
    movie_map = {f"{m['title']} ({m['genre']})": m["id"] for m in movies}
    selected = st.selectbox("Select movie", movie_map.keys())
    score = st.slider("Rating", 1, 5, 3)

    if st.button("Submit rating"):
        rate_movie(movie_map[selected], score)
        st.success("Rating submitted!")
        st.rerun()
else:
    st.info("Add a movie first.")
