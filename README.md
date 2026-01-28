# IPVO-Movie-Recommender

A full-stack movie recommendation system built with Flask, PostgreSQL, Redis, Elasticsearch, Kafka, and Streamlit.

The app:

* Loads ~10,000 movies from TMDB (500 Imdb pages)
* Lets users register/login
* Search movies (Elasticsearch)
* Rate movies (1–10)
* Shows personalized recommendations
* Displays rating history
* Uses Redis for caching recommendations
* Uses Kafka to stream movies into Elasticsearch
* Streamlit provides the UI
* Nginx load-balances two backend instances

### High level flow:

1. TMDB movies are seeded into Postgres
2. Movies are also sent to Kafka
3. Kafka Indexer consumes movies and indexes them into Elasticsearch
4. Users rate movies
5. Recommendations are computed in Flask and cached in Redis
6. Streamlit displays everything

---

## How to Start the Application

From the project root:

<pre class="overflow-visible! px-0!" data-start="1212" data-end="1249"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-[calc(--spacing(9)+var(--header-height))] @w-xl/main:top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>docker compose up --build
</span></span></code></div></div></pre>

Wait until all containers are healthy.

Then open:

* Frontend:

<pre class="overflow-visible! px-0!" data-start="1327" data-end="1356"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-[calc(--spacing(9)+var(--header-height))] @w-xl/main:top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre!"><span><span>http:</span><span>//localhost:8501</span><span>
</span></span></code></div></div></pre>

---

## Seed Movies from TMDB

This fetches movies from TMDB and inserts them into Postgres (and publishes to Kafka):

<pre class="overflow-visible! px-0!" data-start="1480" data-end="1540"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-[calc(--spacing(9)+var(--header-height))] @w-xl/main:top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>docker compose </span><span>exec</span><span> backend1 python seed_tmdb.py
</span></span></code></div></div></pre>

(You can run it from `backend2` as well, but one instance is enough.)

Make sure `TMDB_API_KEY` is set in docker-compose.

---

## Main Services Explained

### Flask Backend (backend1 / backend2)

* User auth (login/register)
* Rating movies
* Recommendation logic
* Talks to:
  * PostgreSQL (data)
  * Redis (cache)
  * Elasticsearch (search)

Two instances are running behind Nginx for load balancing.

---

### PostgreSQL

Main database:

* users
* movies
* ratings

Stores:

* TMDB movies
* user ratings
* user accounts

---

### Redis

Used for caching:

* `/recommendations/<user_id>`

Each user’s recommendations are cached for 5 minutes.

This avoids recomputing expensive SQL queries every refresh.

---

### Elasticsearch

Full-text search engine.

Used for:

* Movie title search
* Genre search

Kafka feeds Elasticsearch automatically.

---

### Kafka + Zookeeper

Event streaming system.

Used for:

* Sending movies from `seed_tmdb.py`
* Kafka Indexer consumes movies
* Indexes them into Elasticsearch

---

### Kafka Indexer

Custom consumer service:

* Listens to Kafka topic `movies`
* Pushes every movie into Elasticsearch

This decouples ingestion from indexing.

---

### Streamlit (Frontend)

User interface:

* Login / Register
* Search movies
* Rate movies
* View recommendations
* See rating history
* View recently added movies

---

### Nginx

Reverse proxy + load balancer.

Routes traffic to:

* backend1
* backend2

Provides a single API entry point.

---

## Recommendation Logic

1. Find user’s favorite genre (most rated)
2. Exclude already rated movies
3. Rank remaining movies by:

<pre class="overflow-visible! px-0!" data-start="3230" data-end="3294"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-[calc(--spacing(9)+var(--header-height))] @w-xl/main:top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre!"><span><span>hybrid_score</span><span> = </span><span>0.7</span><span> * avg_user_rating + </span><span>0.3</span><span> * tmdb_rating
</span></span></code></div></div></pre>

Results are cached in Redis.

---

## API Endpoints (Main)

Backend exposes:

* `POST /login`
* `POST /register`
* `POST /rate`
* `GET /recommendations/<user_id>`
* `GET /movies/latest`
* `GET /search?q=...`
* `GET /my-ratings/<user_id>`

---

## Tech Stack

* Python / Flask
* SQLAlchemy
* PostgreSQL
* Redis
* Elasticsearch
* Kafka + Zookeeper
* Streamlit
* Nginx
* Docker / Docker Compose
* TMDB API

---

## Typical Dev Commands

Start everything:

<pre class="overflow-visible! px-0!" data-start="3800" data-end="3837"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-[calc(--spacing(9)+var(--header-height))] @w-xl/main:top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>docker compose up --build
</span></span></code></div></div></pre>

Seed movies:

<pre class="overflow-visible! px-0!" data-start="3853" data-end="3913"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-[calc(--spacing(9)+var(--header-height))] @w-xl/main:top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>docker compose </span><span>exec</span><span> backend1 python seed_tmdb.py
</span></span></code></div></div></pre>

View logs:

<pre class="overflow-visible! px-0!" data-start="3927" data-end="4007"><div class="contain-inline-size rounded-2xl corner-superellipse/1.1 relative bg-token-sidebar-surface-primary"><div class="sticky top-[calc(--spacing(9)+var(--header-height))] @w-xl/main:top-9"><div class="absolute end-0 bottom-0 flex h-9 items-center pe-2"><div class="bg-token-bg-elevated-secondary text-token-text-secondary flex items-center gap-4 rounded-sm px-2 font-sans text-xs"></div></div></div><div class="overflow-y-auto p-4" dir="ltr"><code class="whitespace-pre! language-bash"><span><span>docker compose logs -f backend1
docker compose logs -f kafka_indexer
</span></span></code></div></div></pre>

---
