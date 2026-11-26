from collections import deque
import json
import os
import time
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import requests

# Create a folder to store our crawled pages
DATA_DIR = "crawled_data"
os.makedirs(DATA_DIR, exist_ok=True)


class WebCrawler:
    def __init__(self, seed_urls, max_pages=15):
        self.queue = deque(seed_urls)  # URLs waiting to be visited (FIFO queue)
        self.visited = set()  # Keep track of already visited URLs
        self.max_pages = max_pages  # Safety limit
        self.graph = {}  # Maps URL -> list of outgoing URLs

    def is_valid_url(self, url):
        """Checks if URL is valid HTTP/HTTPS and not a static media file."""
        parsed = urlparse(url)
        if parsed.scheme not in ["http", "https"]:
            return False
        skip_extensions = (
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".pdf",
            ".zip",
            ".svg",
            ".mp4",
            ".css",
            ".js",
        )
        if any(parsed.path.lower().endswith(ext) for ext in skip_extensions):
            return False
        return True

    def crawl(self):
        print(f"Starting crawl with limit: {self.max_pages} pages...\n")
        doc_id = 0

        # Standard desktop browser User-Agent so websites don't block the request
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
                " (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            ),
            "Accept-Language": "en-US,en;q=0.9",
        }

        while self.queue and len(self.visited) < self.max_pages:
            current_url = self.queue.popleft()

            if current_url in self.visited:
                continue

            try:
                response = requests.get(current_url, headers=headers, timeout=8)

                if response.status_code != 200:
                    print(f"Skipped ({response.status_code} status): {current_url}")
                    continue

                content_type = response.headers.get("Content-Type", "")
                if "text/html" not in content_type:
                    continue

                # Mark as visited
                self.visited.add(current_url)
                doc_id += 1

                # Parse HTML content
                soup = BeautifulSoup(response.text, "html.parser")

                # Extract page title
                title = (
                    soup.title.string.strip()
                    if soup.title and soup.title.string
                    else current_url
                )

                # Remove scripts, styles, and navigation bars
                for element in soup(["script", "style", "nav", "footer", "header"]):
                    element.extract()

                # Get clean body text
                text_content = soup.get_text(separator=" ", strip=True)

                # Extract outgoing links for the web graph
                outgoing_links = []
                for a_tag in soup.find_all("a", href=True):
                    full_url = urljoin(current_url, a_tag["href"])
                    full_url = full_url.split("#")[0]  # Remove section anchors

                    if self.is_valid_url(full_url):
                        outgoing_links.append(full_url)
                        if full_url not in self.visited:
                            self.queue.append(full_url)

                # Save outgoing links for PageRank graph
                self.graph[current_url] = outgoing_links

                # Save document metadata to disk
                doc_data = {
                    "id": doc_id,
                    "url": current_url,
                    "title": title,
                    "content": text_content,
                    "links": outgoing_links,
                }

                with open(
                    os.path.join(DATA_DIR, f"doc_{doc_id}.json"),
                    "w",
                    encoding="utf-8",
                ) as f:
                    json.dump(doc_data, f, indent=2, ensure_ascii=False)

                print(
                    f"[{doc_id}/{self.max_pages}] Crawled: {title[:50]}... ->"
                    f" ({current_url})"
                )

                # Short delay to avoid rate limits
                time.sleep(0.5)

            except Exception as e:
                print(f"Failed to crawl {current_url}: {e}")

        # Save web graph for PageRank
        with open(os.path.join(DATA_DIR, "web_graph.json"), "w", encoding="utf-8") as f:
            json.dump(self.graph, f, indent=2)

        print(f"\nCrawling complete! Saved {doc_id} documents to '{DATA_DIR}/'.")


if __name__ == "__main__":
    # Starter Seed URLs
    seeds = [
        "https://en.wikipedia.org/wiki/Computer_science",
        "https://en.wikipedia.org/wiki/Search_engine",
        "https://docs.python.org/3/tutorial/index.html",
    ]

    crawler = WebCrawler(seed_urls=seeds, max_pages=15)
    crawler.crawl()
