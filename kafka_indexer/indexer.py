from kafka import KafkaConsumer
from elasticsearch import Elasticsearch
import json
import time
import sys

print("Waiting for Kafka...", flush=True)

while True:
    try:
        consumer = KafkaConsumer(
            "movies",
            bootstrap_servers="kafka:9092",
            value_deserializer=lambda m: json.loads(m.decode("utf-8")),
            auto_offset_reset='earliest', 
            enable_auto_commit=True,
            group_id='indexer-group'
        )
        break
    except Exception as e:
        print(f"Kafka not ready ({e}), retrying...", flush=True)
        time.sleep(5)

print("Kafka connected", flush=True)

es = Elasticsearch(
    "http://elasticsearch:9200",
    meta_header=False
)

print("Kafka indexer started. Waiting for messages...", flush=True)

try:
    for msg in consumer:
        movie = msg.value
        print(f"Indexing movie: {movie.get('title')}", flush=True)

        es.index(
            index="movies",
            id=movie.get("id"),
            document={
                "title": movie.get("title"),
                "genre": movie.get("genre"),
                "tmdb_rating": movie.get("tmdb_rating")
            }
        )
except Exception as e:
    print(f"Error during indexing: {e}", flush=True)