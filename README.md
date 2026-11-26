# MiniGoogle: Full-Stack Search Engine from Scratch 🔍🌐

A custom, end-to-end search engine built from scratch in Python—featuring a BFS web crawler, an inverted index with stop-word filtering, Google's PageRank link-analysis algorithm, BM25 probabilistic relevance scoring, and a Google-inspired Flask web interface.

---

## 🏗️ System Architecture

```text
[ Seed URLs ] ──► [ Web Crawler (BFS) ] ──► [ Inverted Indexer ]
                                                    │
[ Web Search UI ] ◄── [ BM25 + PageRank Scorer ] ◄──┴── [ PageRank Graph Engine ]