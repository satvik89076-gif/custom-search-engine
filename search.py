import json
import math
import os
import time
from indexer import tokenize

DATA_DIR = "crawled_data"
INDEX_FILE = os.path.join(DATA_DIR, "inverted_index.json")
PAGERANK_FILE = os.path.join(DATA_DIR, "pagerank.json")


class SearchEngine:
    def __init__(self):
        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        with open(PAGERANK_FILE, "r", encoding="utf-8") as f:
            self.pagerank = json.load(f)

        self.total_docs = data["total_docs"]
        self.avg_doc_length = data["avg_doc_length"]
        self.documents = data["documents"]
        self.index = data["index"]

        # BM25 standard tuning parameters
        self.k1 = 1.5
        self.b = 0.75

    def compute_bm25(self, term, doc_id):
        """Calculates BM25 relevance score for a single word in a single document."""
        if term not in self.index or doc_id not in self.index[term]:
            return 0.0

        # Inverse Document Frequency (IDF): rarer words get higher weight
        docs_with_term = len(self.index[term])
        idf = math.log(
            (self.total_docs - docs_with_term + 0.5) / (docs_with_term + 0.5) + 1.0
        )

        # Term Frequency (TF) normalized by document length
        tf = self.index[term][doc_id]
        doc_len = self.documents[doc_id]["doc_length"]
        numerator = tf * (self.k1 + 1)
        denominator = tf + self.k1 * (
            1 - self.b + self.b * (doc_len / self.avg_doc_length)
        )

        return idf * (numerator / denominator)

    def search(self, query, top_k=5):
        start_time = time.perf_counter()
        query_tokens = tokenize(query)

        if not query_tokens:
            return [], 0.0

        # Find all candidate documents containing at least one query word
        candidate_docs = set()
        for token in query_tokens:
            if token in self.index:
                candidate_docs.update(self.index[token].keys())

        results = []
        for doc_id in candidate_docs:
            # Sum BM25 scores across all words in the user's search query
            bm25_score = sum(self.compute_bm25(token, doc_id) for token in query_tokens)

            # Blend with Google PageRank authority score
            pr_score = self.pagerank.get(doc_id, 0.1)
            final_score = bm25_score * (1.0 + pr_score)

            meta = self.documents[doc_id]
            results.append(
                {
                    "doc_id": doc_id,
                    "title": meta["title"],
                    "url": meta["url"],
                    "snippet": meta["snippet"],
                    "score": round(final_score, 4),
                    "bm25": round(bm25_score, 4),
                    "pagerank": pr_score,
                }
            )

        # Sort highest score first
        results.sort(key=lambda x: x["score"], reverse=True)
        elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)

        return results[:top_k], elapsed_ms


if __name__ == "__main__":
    engine = SearchEngine()
    print("=== Mini-Google Terminal Search Test ===")
    print("Type a search query (or 'exit' to quit).\n")

    while True:
        query = input("Search > ").strip()
        if query.lower() in ("exit", "quit"):
            break

        results, latency_ms = engine.search(query)
        print(f"\nFound {len(results)} results in {latency_ms} ms:\n")

        for rank, res in enumerate(results, 1):
            print(
                f"{rank}. {res['title']} [Score: {res['score']} | BM25:"
                f" {res['bm25']} | PR: {res['pagerank']}]"
            )
            print(f"   {res['url']}")
            print(f"   {res['snippet'][:120]}...\n")
