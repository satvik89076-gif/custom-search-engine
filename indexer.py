from collections import defaultdict
import json
import os
import re

DATA_DIR = "crawled_data"
INDEX_FILE = os.path.join(DATA_DIR, "inverted_index.json")

# Common words that add noise and don't help search relevance
STOP_WORDS = {
    "a",
    "an",
    "the",
    "and",
    "or",
    "but",
    "if",
    "then",
    "else",
    "when",
    "at",
    "by",
    "for",
    "with",
    "about",
    "against",
    "between",
    "into",
    "through",
    "during",
    "before",
    "after",
    "above",
    "below",
    "to",
    "from",
    "up",
    "down",
    "in",
    "out",
    "on",
    "off",
    "over",
    "under",
    "again",
    "further",
    "once",
    "here",
    "there",
    "where",
    "why",
    "how",
    "all",
    "any",
    "both",
    "each",
    "few",
    "more",
    "most",
    "other",
    "some",
    "such",
    "no",
    "nor",
    "not",
    "only",
    "own",
    "same",
    "so",
    "than",
    "too",
    "very",
    "s",
    "t",
    "can",
    "will",
    "just",
    "don",
    "should",
    "now",
    "is",
    "are",
    "was",
    "were",
    "be",
    "been",
    "being",
    "have",
    "has",
    "had",
    "having",
    "do",
    "does",
    "did",
    "doing",
    "of",
    "this",
    "that",
    "these",
    "those",
    "it",
    "its",
    "as",
}


def tokenize(text):
    """Converts text to lowercase, strips punctuation, and removes stop words."""
    # Find all alphanumeric words of length 2 or more
    words = re.findall(r"\b[a-z0-9]{2,}\b", text.lower())
    return [word for word in words if word not in STOP_WORDS]


def build_inverted_index():
    # Maps: word -> { doc_id_str: term_frequency }
    inverted_index = defaultdict(lambda: defaultdict(int))
    doc_metadata = {}
    total_docs = 0

    print("Building Inverted Index...\n")

    # Loop through every crawled document
    for filename in sorted(os.listdir(DATA_DIR)):
        if filename.startswith("doc_") and filename.endswith(".json"):
            filepath = os.path.join(DATA_DIR, filename)

            with open(filepath, "r", encoding="utf-8") as f:
                doc = json.load(f)

            doc_id = str(doc["id"])
            title = doc["title"]
            content = doc["content"]
            url = doc["url"]

            # Give title words extra weight by repeating them 3 times
            full_text = f"{title} {title} {title} {content}"
            tokens = tokenize(full_text)

            # Save document metadata & word count (needed later for BM25 ranking)
            doc_metadata[doc_id] = {
                "url": url,
                "title": title,
                "doc_length": len(tokens),
                "snippet": content[:220] + "...",
            }

            # Count word frequencies for this document
            for word in tokens:
                inverted_index[word][doc_id] += 1

            total_docs += 1
            print(f"Indexed Doc #{doc_id}: {title[:45]} ({len(tokens)} tokens)")

    # Package everything neatly into one JSON index file
    index_data = {
        "total_docs": total_docs,
        "avg_doc_length": (
            sum(d["doc_length"] for d in doc_metadata.values()) / total_docs
            if total_docs > 0
            else 0
        ),
        "documents": doc_metadata,
        "index": {word: dict(postings) for word, postings in inverted_index.items()},
    }

    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(
        f"\nSuccess! Indexed {len(inverted_index)} unique words across {total_docs} documents."
    )
    print(f"Saved index to '{INDEX_FILE}'.")


if __name__ == "__main__":
    build_inverted_index()
