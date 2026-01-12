import time
from elasticsearch import Elasticsearch

es = Elasticsearch("http://elasticsearch:9200")
INDEX_NAME = "movies"


def create_index():
    for _ in range(10):  # retry 10x
        try:
            if not es.indices.exists(index=INDEX_NAME):
                es.indices.create(
                    index=INDEX_NAME,
                    mappings={
                        "properties": {
                            "id": {"type": "integer"},
                            "title": {"type": "text"},
                            "genre": {"type": "keyword"}
                        }
                    }
                )
            return
        except Exception as e:
            print("Elasticsearch not ready, retrying...")
            time.sleep(2)


def index_movie(movie):
    es.index(
        index=INDEX_NAME,
        id=movie.id,
        document={
            "id": movie.id,
            "title": movie.title,
            "genre": movie.genre
        }
    )


def search_movies(query):
    res = es.search(
        index=INDEX_NAME,
        query={
            "multi_match": {
                "query": query,
                "fields": ["title", "genre"]
            }
        }
    )
    return [hit["_source"] for hit in res["hits"]["hits"]]
