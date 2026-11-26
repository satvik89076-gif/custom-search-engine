import re
from flask import Flask, render_template_string, request
from indexer import tokenize
from search import SearchEngine

app = Flask(__name__)
engine = SearchEngine()


def highlight_snippet(snippet, query):
    """Wraps matching query words in <mark> tags for bold/yellow highlighting."""
    tokens = set(tokenize(query))
    if not tokens:
        return snippet

    pattern = re.compile(
        r"\b(" + "|".join(re.escape(t) for t in tokens) + r")\b", re.IGNORECASE
    )
    return pattern.sub(r"<mark>\1</mark>", snippet)


HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ query + ' - ' if query else '' }}MiniGoogle Search</title>
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; }
        body { background: #ffffff; color: #202124; }
        
        /* Home Centered View */
        .home-container {
            display: flex; flex-direction: column; align-items: center; justify-content: center;
            height: 85vh; padding: 20px;
        }
        .logo { font-size: 4.2rem; font-weight: 700; letter-spacing: -2px; margin-bottom: 28px; user-select: none; }
        .logo span:nth-child(1) { color: #4285F4; }
        .logo span:nth-child(2) { color: #EA4335; }
        .logo span:nth-child(3) { color: #FBBC05; }
        .logo span:nth-child(4) { color: #4285F4; }
        .logo span:nth-child(5) { color: #34A853; }
        .logo span:nth-child(6) { color: #EA4335; }
        .logo small { font-size: 1rem; color: #5f6368; font-weight: 400; letter-spacing: 0; margin-left: 6px; }

        .search-box {
            display: flex; align-items: center; width: 100%; max-width: 584px;
            border: 1px solid #dfe1e5; border-radius: 24px; padding: 10px 20px;
            box-shadow: 0 1px 6px rgba(32,33,36,0.08); transition: box-shadow 0.2s;
        }
        .search-box:hover, .search-box:focus-within { box-shadow: 0 1px 8px rgba(32,33,36,0.2); border-color: rgba(223,225,229,0); }
        .search-box input {
            flex: 1; border: none; outline: none; font-size: 16px; color: #202124; background: transparent;
        }
        .search-btn {
            margin-top: 24px; background: #f8f9fa; border: 1px solid #f8f9fa;
            border-radius: 4px; color: #3c4043; font-size: 14px; padding: 10px 20px; cursor: pointer;
        }
        .search-btn:hover { border: 1px solid #dadce0; box-shadow: 0 1px 1px rgba(0,0,0,0.1); }
        .stats-footer { margin-top: 22px; font-size: 13px; color: #70757a; }

        /* Results Top Bar View */
        .top-bar {
            display: flex; align-items: center; padding: 20px 32px;
            border-bottom: 1px solid #ebebeb; gap: 28px; flex-wrap: wrap;
        }
        .logo-small { font-size: 1.6rem; font-weight: 700; text-decoration: none; letter-spacing: -1px; }
        .logo-small span:nth-child(1) { color: #4285F4; }
        .logo-small span:nth-child(2) { color: #EA4335; }
        .logo-small span:nth-child(3) { color: #FBBC05; }
        .logo-small span:nth-child(4) { color: #4285F4; }
        .logo-small span:nth-child(5) { color: #34A853; }
        .logo-small span:nth-child(6) { color: #EA4335; }

        .results-container { max-width: 680px; margin-left: 165px; padding: 16px 20px 60px; }
        @media (max-width: 850px) { .results-container { margin-left: 0; } }

        .meta-bar { font-size: 14px; color: #70757a; margin-bottom: 22px; }
        .result-card { margin-bottom: 28px; }
        .result-url { font-size: 13px; color: #202124; margin-bottom: 4px; word-break: break-all; }
        .result-title {
            display: inline-block; font-size: 20px; color: #1a0dab;
            text-decoration: none; margin-bottom: 6px; line-height: 1.3;
        }
        .result-title:hover { text-decoration: underline; }
        .result-snippet { font-size: 14px; color: #4d5156; line-height: 1.58; }
        .result-snippet mark { background: #fef08a; color: #202124; font-weight: 600; padding: 0 2px; border-radius: 2px; }
        
        .score-badges { margin-top: 8px; display: flex; gap: 8px; flex-wrap: wrap; }
        .badge {
            font-size: 11px; padding: 3px 8px; border-radius: 12px;
            background: #f1f3f4; color: #3c4043; font-family: monospace;
        }
        .badge-primary { background: #e8f0fe; color: #1967d2; font-weight: 600; }
    </style>
</head>
<body>

{% if not query %}
    <div class="home-container">
        <div class="logo">
            <span>G</span><span>o</span><span>o</span><span>g</span><span>l</span><span>e</span><small>Mini</small>
        </div>
        <form action="/" method="GET" style="width: 100%; display: flex; flex-direction: column; align-items: center;">
            <div class="search-box">
                <input type="text" name="q" placeholder="Search indexed web pages (e.g. cryptography, artificial intelligence, python)..." autofocus required>
            </div>
            <button type="submit" class="search-btn">MiniGoogle Search</button>
        </form>
        <div class="stats-footer">
            Index loaded: <strong>{{ total_docs }}</strong> crawled pages &bull; <strong>{{ vocab_size }}</strong> unique terms &bull; BM25 + PageRank Engine
        </div>
    </div>
{% else %}
    <div class="top-bar">
        <a href="/" class="logo-small">
            <span>G</span><span>o</span><span>o</span><span>g</span><span>l</span><span>e</span>
        </a>
        <form action="/" method="GET" style="flex: 1; max-width: 584px;">
            <div class="search-box">
                <input type="text" name="q" value="{{ query }}" required>
            </div>
        </form>
    </div>

    <div class="results-container">
        <div class="meta-bar">
            Found {{ results|length }} ranked results ({{ latency }} ms)
        </div>

        {% if results %}
            {% for r in results %}
            <div class="result-card">
                <div class="result-url">{{ r.url }}</div>
                <a href="{{ r.url }}" target="_blank" class="result-title">{{ r.title }}</a>
                <div class="result-snippet">{{ r.highlighted_snippet | safe }}</div>
                <div class="score-badges">
                    <span class="badge badge-primary">Total Score: {{ r.score }}</span>
                    <span class="badge">BM25 Relevance: {{ r.bm25 }}</span>
                    <span class="badge">PageRank Authority: {{ r.pagerank }}</span>
                </div>
            </div>
            {% endfor %}
        {% else %}
            <p style="font-size: 16px; color: #4d5156;">No indexed documents matched <strong>{{ query }}</strong>. Try searching for <em>computer science</em>, <em>cryptography</em>, <em>information theory</em>, or <em>python</em>.</p>
        {% endif %}
    </div>
{% endif %}

</body>
</html>
"""


@app.route("/")
def home():
    query = request.args.get("q", "").strip()
    if not query:
        return render_template_string(
            HTML_TEMPLATE,
            query="",
            total_docs=engine.total_docs,
            vocab_size=len(engine.index),
        )

    results, latency = engine.search(query, top_k=10)
    for r in results:
        r["highlighted_snippet"] = highlight_snippet(r["snippet"], query)

    return render_template_string(
        HTML_TEMPLATE,
        query=query,
        results=results,
        latency=latency,
    )


if __name__ == "__main__":
    print("\n=== MiniGoogle Web UI Running ===")
    print("Open in your browser: http://127.0.0.1:5000\n")
    app.run(debug=False, port=5000)
