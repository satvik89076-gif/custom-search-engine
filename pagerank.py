import json
import os

DATA_DIR = "crawled_data"
GRAPH_FILE = os.path.join(DATA_DIR, "web_graph.json")
INDEX_FILE = os.path.join(DATA_DIR, "inverted_index.json")
PAGERANK_FILE = os.path.join(DATA_DIR, "pagerank.json")


def compute_pagerank(damping=0.85, iterations=30):
    print("Computing Google PageRank scores...\n")

    with open(GRAPH_FILE, "r", encoding="utf-8") as f:
        raw_graph = json.load(f)

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        index_data = json.load(f)

    # Map URLs -> Doc IDs so we only rank our crawled pages
    url_to_id = {
        meta["url"]: doc_id for doc_id, meta in index_data["documents"].items()
    }
    valid_urls = set(url_to_id.keys())
    N = len(valid_urls)

    if N == 0:
        print("No pages found to rank.")
        return

    # Filter outgoing links so we only keep links pointing between our crawled pages
    outgoing_links = {}
    incoming_links = {url: [] for url in valid_urls}

    for url in valid_urls:
        # Remove duplicate links on the same page
        links = list(
            set(
                link
                for link in raw_graph.get(url, [])
                if link in valid_urls and link != url
            )
        )
        outgoing_links[url] = links
        for target in links:
            incoming_links[target].append(url)

    # Step 1: Every page starts with an equal score of 1/N
    scores = {url: 1.0 / N for url in valid_urls}

    # Step 2: Run power iteration until scores stabilize
    for _ in range(iterations):
        new_scores = {}
        # Handle "dangling nodes" (pages with 0 outgoing links)
        dangling_sum = sum(scores[u] for u in valid_urls if len(outgoing_links[u]) == 0)

        for url in valid_urls:
            rank = (1.0 - damping) / N
            rank += damping * (dangling_sum / N)

            for source_url in incoming_links[url]:
                rank += damping * (scores[source_url] / len(outgoing_links[source_url]))

            new_scores[url] = rank

        scores = new_scores

    # Normalize scores to a clean 0.1 - 1.0 scale for easy blending with keyword search
    max_score = max(scores.values()) if scores else 1.0
    normalized_by_id = {}

    print("Top Ranked Pages by Authority (PageRank):")
    sorted_pages = sorted(scores.items(), key=lambda x: x[1], reverse=True)

    for url, raw_score in sorted_pages:
        doc_id = url_to_id[url]
        norm_score = round(raw_score / max_score, 4)
        normalized_by_id[doc_id] = norm_score
        title = index_data["documents"][doc_id]["title"]
        print(f"  [Score: {norm_score:.4f}] Doc #{doc_id}: {title[:50]}")

    with open(PAGERANK_FILE, "w", encoding="utf-8") as f:
        json.dump(normalized_by_id, f, indent=2)

    print(f"\nSaved PageRank scores to '{PAGERANK_FILE}'.")


if __name__ == "__main__":
    compute_pagerank()
