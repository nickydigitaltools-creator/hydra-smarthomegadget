#!/usr/bin/env python3
"""
Hydra Zero-Key Daily Content Generator
=======================================
Requires ZERO API keys. Runs entirely locally using Ollama.
Reads keywords from queue.json, generates articles via local LLM,
writes HTML files, updates RSS feeds, and marks keywords as published.

Usage:
    python3 scripts/hydra_zero_key_generator.py

Dependencies (all free, no keys):
    pip install requests
    # Ollama must be running: `ollama serve` with model pulled
    # e.g. `ollama pull llama3.2:1b` or `ollama pull phi3`
"""

import os
import re
import json
import datetime
import textwrap
import requests
import xml.etree.ElementTree as ET
from pathlib import Path

# ─── Configuration ────────────────────────────────────────────────────────────
BASE_DIR    = Path(__file__).resolve().parent.parent
QUEUE_FILE  = BASE_DIR / "queue.json"
OLLAMA_URL  = "http://localhost:11434/api/generate"
# Use the smallest/fastest model available on the runner.
# Options: "llama3.2:1b", "phi3", "mistral", "gemma:2b"
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:1b")

# Cross-linking map (Thematic Ring Architecture)
CROSS_LINK_MAP = {
    "site1-aitoolpicks":        ("https://sidehustlestack.io",     "Side Hustle Stack",     "side hustle tools for freelancers"),
    "site2-sidehustlestack":    ("https://learnsmartpicks.com",    "Learn Smart Picks",     "online courses to build new skills"),
    "site3-smarthomegadget":    ("https://parentingtechguide.com", "Parenting Tech Guide",  "smart tech for parents and families"),
    "site4-financeappreviews":  ("https://remotetravelpicks.com",  "Remote Travel Picks",   "budgeting tools for digital nomads"),
    "site5-parentingtechguide": ("https://diytoolsreviewed.com",   "DIY Tools Reviewed",    "DIY home improvement projects"),
    "site6-diytoolsreviewed":   ("https://smarthomegadgetpro.com", "Smart Home Gadget Pro", "smart home upgrades after renovation"),
    "site7-learnsmartpicks":    ("https://privacytoolsrated.com",  "Privacy Tools Rated",   "staying safe online while learning"),
    "site8-privacytoolsrated":  ("https://aitoolpicks.com",        "AI Tool Picks",         "AI productivity tools"),
    "site9-fitnesstechreviews": ("https://financeappreviews.net",  "Finance App Reviews",   "budgeting for health and fitness"),
    "site10-remotetravelpicks": ("https://privacytoolsrated.com",  "Privacy Tools Rated",   "VPN security while traveling"),
}

SITE_META = {
    "site1-aitoolpicks":        {"domain": "aitoolpicks.com",        "logo": "🤖 AI Tool Picks"},
    "site2-sidehustlestack":    {"domain": "sidehustlestack.io",     "logo": "💼 Side Hustle Stack"},
    "site3-smarthomegadget":    {"domain": "smarthomegadgetpro.com", "logo": "🏠 Smart Home Gadget Pro"},
    "site4-financeappreviews":  {"domain": "financeappreviews.net",  "logo": "💰 Finance App Reviews"},
    "site5-parentingtechguide": {"domain": "parentingtechguide.com", "logo": "👶 Parenting Tech Guide"},
    "site6-diytoolsreviewed":   {"domain": "diytoolsreviewed.com",   "logo": "🔧 DIY Tools Reviewed"},
    "site7-learnsmartpicks":    {"domain": "learnsmartpicks.com",    "logo": "🎓 Learn Smart Picks"},
    "site8-privacytoolsrated":  {"domain": "privacytoolsrated.com",  "logo": "🔐 Privacy Tools Rated"},
    "site9-fitnesstechreviews": {"domain": "fitnesstechreviews.io",  "logo": "💪 Fitness Tech Reviews"},
    "site10-remotetravelpicks": {"domain": "remotetravelpicks.com",  "logo": "✈️ Remote Travel Picks"},
}


# ─── Utility Functions ────────────────────────────────────────────────────────

def slugify(text: str) -> str:
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s_]+", "-", text)
    return text[:80]


def ollama_generate(prompt: str, expect_json: bool = False) -> str:
    """Send a prompt to the local Ollama API and return the response text."""
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.7, "num_predict": 2048},
    }
    if expect_json:
        payload["format"] = "json"
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=300)
        resp.raise_for_status()
        return resp.json().get("response", "").strip()
    except requests.exceptions.ConnectionError:
        print("  [ERROR] Ollama is not running. Falling back to template content.")
        return ""
    except Exception as e:
        print(f"  [ERROR] Ollama call failed: {e}")
        return ""


def extract_json_safe(raw: str) -> dict:
    """Try to parse JSON from LLM output; fall back gracefully."""
    raw = raw.strip()
    # Strip markdown code fences if present
    raw = re.sub(r"^```(?:json)?", "", raw, flags=re.MULTILINE)
    raw = re.sub(r"```$", "", raw, flags=re.MULTILINE).strip()
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        # Try to extract the first {...} block
        match = re.search(r"\{.*\}", raw, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except Exception:
                pass
    return {}


# ─── Template Fallback ────────────────────────────────────────────────────────
# Used when Ollama is unavailable (e.g., first run before model is pulled)

def template_article(keyword: str, site_id: str) -> dict:
    """Generate a complete article using a deterministic template (no LLM needed)."""
    cross = CROSS_LINK_MAP[site_id]
    title = keyword.title()
    slug = slugify(keyword)
    meta = f"Looking for the best {keyword.lower()}? Our expert review compares top options to help you choose the right one for your needs and budget."

    body_html = f"""
<p>If you've been searching for the best {keyword.lower()}, you're in the right place. In this guide, we've done the heavy lifting — testing, comparing, and ranking the top options so you can make a confident decision.</p>

<h2>Why This Matters</h2>
<p>With so many options flooding the market, choosing the wrong product means wasted money and frustration. The right choice, however, can save you hours every week and genuinely improve your results.</p>

<h2>Top Picks at a Glance</h2>
<table class="comp-table">
  <thead>
    <tr><th>Product</th><th>Best For</th><th>Price</th><th>Action</th></tr>
  </thead>
  <tbody>
    <tr>
      <td><strong>Editor's Choice</strong></td>
      <td>Overall best value</td>
      <td>From $15/mo</td>
      <td><a href="AFF_LINK_IMPACT" class="aff-btn" rel="nofollow noopener" target="_blank">Check Price</a></td>
    </tr>
    <tr>
      <td><strong>Best Free Option</strong></td>
      <td>Beginners &amp; budget users</td>
      <td>Free</td>
      <td><a href="AFF_LINK_PARTNERSTACK" class="aff-btn" rel="nofollow noopener" target="_blank">Try Free</a></td>
    </tr>
    <tr>
      <td><strong>Premium Pick</strong></td>
      <td>Power users &amp; professionals</td>
      <td>From $49/mo</td>
      <td><a href="AFF_LINK_AMAZON" class="aff-btn" rel="nofollow noopener" target="_blank">View Details</a></td>
    </tr>
  </tbody>
</table>

<h2>Detailed Reviews</h2>
<h3>1. Editor's Choice — Best Overall</h3>
<p>After extensive testing, this option consistently delivers the best combination of performance, ease of use, and value. It's our top recommendation for most users. The interface is intuitive, customer support is responsive, and the results speak for themselves.</p>
<p><strong>Pros:</strong> Reliable performance, excellent support, great value for money.<br>
<strong>Cons:</strong> Advanced features have a slight learning curve.</p>
<p><a href="AFF_LINK_IMPACT" rel="nofollow noopener" target="_blank">Get started with our top pick →</a></p>

<h3>2. Best Free Option — Great for Beginners</h3>
<p>If you're just starting out or working with a tight budget, this free option covers all the core features you need. It lacks some of the premium capabilities, but for most everyday use cases, it performs admirably.</p>
<p><strong>Pros:</strong> Completely free to start, lightweight, easy setup.<br>
<strong>Cons:</strong> Limited integrations and advanced features.</p>
<p><a href="AFF_LINK_PARTNERSTACK" rel="nofollow noopener" target="_blank">Try the free option here →</a></p>

<h2>Frequently Asked Questions</h2>
<div class="faq-item">
  <div class="faq-q">Is the free version good enough for most users?</div>
  <div class="faq-a">For basic needs, yes. The free tier handles the core use cases well. However, if you need advanced features, integrations, or priority support, upgrading is worthwhile.</div>
</div>
<div class="faq-item">
  <div class="faq-q">How did you test these products?</div>
  <div class="faq-a">Our editorial team spent over 40 hours testing each product in real-world scenarios, evaluating performance, ease of use, customer support, and overall value.</div>
</div>
<div class="faq-item">
  <div class="faq-q">Are these affiliate links?</div>
  <div class="faq-a">Yes. Some links on this page are affiliate links. If you purchase through them, we may earn a small commission at no extra cost to you. This helps fund our testing process.</div>
</div>

<h2>Conclusion</h2>
<p>Choosing the right tool for <em>{keyword.lower()}</em> doesn't have to be complicated. Our top pick delivers the best all-round experience for most users, while the free option is a solid starting point if you're on a budget. Take advantage of free trials before committing to a paid plan.</p>
<p>If you're also interested in {cross[2]}, our friends at <a href="{cross[0]}" rel="noopener" target="_blank">{cross[1]}</a> have an excellent guide worth checking out.</p>
"""
    return {"title": title, "meta_description": meta, "slug": slug, "body_html": body_html}


# ─── Article HTML Builder ─────────────────────────────────────────────────────

def build_full_html(article: dict, site_id: str) -> str:
    meta = SITE_META[site_id]
    logo = meta["logo"]
    logo_text = logo.split(" ", 1)[1] if " " in logo else logo
    domain = meta["domain"]
    today = datetime.date.today().strftime("%B %d, %Y")
    slug = article["slug"]

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{article['title']} | {logo_text}</title>
  <meta name="description" content="{article['meta_description']}" />
  <link rel="canonical" href="https://{domain}/articles/{slug}.html" />
  <link rel="alternate" type="application/rss+xml" title="{logo_text} RSS" href="/rss.xml" />
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "Article",
    "headline": "{article['title']}",
    "datePublished": "{datetime.date.today().isoformat()}",
    "author": {{"@type": "Organization", "name": "{logo_text}"}},
    "publisher": {{"@type": "Organization", "name": "{logo_text}"}}
  }}
  </script>
  <link rel="stylesheet" href="../assets/css/style.css" />
</head>
<body>
<header>
  <div class="container">
    <a class="logo" href="/">{logo}</a>
    <nav><a href="/">Home</a></nav>
  </div>
</header>
<div class="container article-wrap">
  <main class="article-body">
    <div class="breadcrumb"><a href="/">Home</a><span>›</span> Article</div>
    <h1>{article['title']}</h1>
    <div class="article-meta">Published: {today} · <em>Affiliate Disclosure: We may earn a commission from links at no extra cost to you.</em></div>
    {article['body_html']}
  </main>
  <aside class="sidebar">
    <div class="widget">
      <h4>Affiliate Disclosure</h4>
      <p style="font-size:0.85rem;color:#64748b;">If you purchase through our links, we may earn a commission at no extra cost to you. This funds our independent testing.</p>
    </div>
    <div class="widget">
      <h4>Subscribe via RSS</h4>
      <p style="font-size:0.85rem;color:#64748b;"><a href="/rss.xml">📡 RSS Feed</a> — Get new articles automatically.</p>
    </div>
  </aside>
</div>
<footer>
  <div class="container">
    <span>© {datetime.date.today().year} {logo_text}</span>
    <div class="footer-links">
      <a href="/privacy.html">Privacy</a>
      <a href="/disclaimer.html">Affiliate Disclaimer</a>
    </div>
  </div>
</footer>
</body>
</html>"""


# ─── LLM Article Generation ───────────────────────────────────────────────────

def generate_article_llm(keyword: str, site_id: str) -> dict:
    """Generate article content using the local Ollama LLM."""
    cross = CROSS_LINK_MAP[site_id]
    meta = SITE_META[site_id]
    logo_text = meta["logo"].split(" ", 1)[1] if " " in meta["logo"] else meta["logo"]

    prompt = textwrap.dedent(f"""
    You are an expert SEO content writer for "{logo_text}".
    Write a 900-word affiliate review article for the keyword: "{keyword}"

    Return ONLY a JSON object with these exact keys:
    - "title": SEO title under 60 characters
    - "meta_description": under 155 characters
    - "slug": URL slug (lowercase, hyphens only)
    - "body_html": complete HTML body (no html/head/body tags). Must include:
        * An engaging introduction paragraph
        * An H2 "Why This Matters" section
        * An H2 "Top Picks at a Glance" with a comparison table using placeholder hrefs: AFF_LINK_IMPACT, AFF_LINK_AMAZON, AFF_LINK_PARTNERSTACK and class="aff-btn" on the links
        * An H2 "Detailed Reviews" with 2 mini-reviews
        * An H2 "Frequently Asked Questions" with 3 Q&A items using class="faq-item", class="faq-q", class="faq-a"
        * An H2 "Conclusion" that naturally mentions {cross[1]} with a link to {cross[0]} in context of "{cross[2]}"

    Return ONLY the JSON. No explanation. No markdown fences.
    """).strip()

    raw = ollama_generate(prompt, expect_json=True)
    if not raw:
        print("  [FALLBACK] Using template article (Ollama unavailable).")
        return template_article(keyword, site_id)

    data = extract_json_safe(raw)
    if not data.get("body_html"):
        print("  [FALLBACK] LLM returned incomplete JSON. Using template.")
        return template_article(keyword, site_id)

    # Ensure slug is set
    if not data.get("slug"):
        data["slug"] = slugify(data.get("title", keyword))

    return data


# ─── Social Post Generation ───────────────────────────────────────────────────

def generate_social_posts_llm(title: str, url: str, site_id: str) -> dict:
    """Generate social posts using local LLM, with a template fallback."""
    prompt = textwrap.dedent(f"""
    Generate social media content for this article: "{title}"
    URL: {url}

    Return ONLY a JSON object with these keys:
    - "twitter": A tweet under 280 chars with 3 hashtags and the URL
    - "pinterest_text": A 10-word curiosity-driven pin overlay text
    - "pinterest_desc": A 500-char pin description with 5 hashtags
    - "reddit_title": A Reddit post title (no marketing language, sounds authentic)
    - "reddit_body": A 200-word authentic Reddit post with a soft link at the end

    Return ONLY the JSON. No explanation.
    """).strip()

    raw = ollama_generate(prompt, expect_json=True)
    if raw:
        data = extract_json_safe(raw)
        if data.get("twitter"):
            return data

    # Template fallback
    return {
        "twitter": f"Just published: {title} — everything you need to know before buying. {url} #Review #BuyingGuide #SaveMoney",
        "pinterest_text": f"Is {title.split()[0]} Worth It? Read This First.",
        "pinterest_desc": f"Before you spend money on {title.lower()}, read our in-depth review. We tested the top options and ranked them by value, features, and ease of use. Click to read the full breakdown. #{title.split()[0].replace(',','')} #ProductReview #BuyingGuide #SaveMoney #BestOf2025",
        "reddit_title": f"I spent 2 weeks testing {title.lower()} — here's what I found",
        "reddit_body": f"Hey everyone, I recently went down a rabbit hole researching {title.lower()} because I was tired of wasting money on products that didn't deliver. After about two weeks of testing, I put together a full breakdown of what actually works. The short version: the most expensive option isn't always the best, and there are some genuinely great free alternatives. If you're in the market for this, I wrote up my full findings here: {url} — happy to answer any questions in the comments.",
    }


# ─── RSS Feed Builder ─────────────────────────────────────────────────────────

def update_rss_feed(site_id: str, article: dict):
    """Add the new article to the site's RSS feed (creates it if missing)."""
    meta = SITE_META[site_id]
    domain = meta["domain"]
    logo_text = meta["logo"].split(" ", 1)[1] if " " in meta["logo"] else meta["logo"]
    rss_path = BASE_DIR / site_id / "rss.xml"
    article_url = f"https://{domain}/articles/{article['slug']}.html"
    pub_date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

    # Parse existing or create new
    if rss_path.exists():
        try:
            tree = ET.parse(rss_path)
            root = tree.getroot()
            channel = root.find("channel")
        except ET.ParseError:
            channel = None
    else:
        channel = None

    if channel is None:
        root = ET.Element("rss", version="2.0")
        channel = ET.SubElement(root, "channel")
        ET.SubElement(channel, "title").text = logo_text
        ET.SubElement(channel, "link").text = f"https://{domain}"
        ET.SubElement(channel, "description").text = f"Latest affiliate reviews from {logo_text}"
        ET.SubElement(channel, "language").text = "en-us"

    # Prepend new item (keep max 20 items)
    new_item = ET.Element("item")
    ET.SubElement(new_item, "title").text = article["title"]
    ET.SubElement(new_item, "link").text = article_url
    ET.SubElement(new_item, "description").text = article.get("meta_description", "")
    ET.SubElement(new_item, "pubDate").text = pub_date
    ET.SubElement(new_item, "guid").text = article_url

    # Insert at position 0 (after channel metadata tags)
    items = channel.findall("item")
    if len(items) >= 20:
        channel.remove(items[-1])

    # Find insertion index (after last non-item element)
    insert_idx = 0
    for i, child in enumerate(list(channel)):
        if child.tag != "item":
            insert_idx = i + 1
    channel.insert(insert_idx, new_item)

    tree = ET.ElementTree(root)
    ET.indent(tree, space="  ")
    tree.write(str(rss_path), encoding="unicode", xml_declaration=True)
    print(f"  ✓ RSS feed updated: {rss_path}")


# ─── Main Execution ───────────────────────────────────────────────────────────

def main():
    print(f"\n{'='*60}")
    print(f"  Hydra Zero-Key Generator — {datetime.date.today()}")
    print(f"  Model: {OLLAMA_MODEL}")
    print(f"{'='*60}\n")

    # Load queue
    if not QUEUE_FILE.exists():
        print(f"[ERROR] queue.json not found at {QUEUE_FILE}")
        return

    with open(QUEUE_FILE) as f:
        queue = json.load(f)

    social_log_path = BASE_DIR / "social_queue.jsonl"
    today = datetime.date.today().isoformat()
    published_count = 0

    for site_id, site_queue in queue.items():
        # Find first pending keyword
        pending = [k for k in site_queue if k.get("status") == "pending"]
        if not pending:
            print(f"[{site_id}] No pending keywords. Skipping.")
            continue

        entry = pending[0]
        keyword = entry["keyword"]
        print(f"\n[{site_id}] Keyword: \"{keyword}\"")

        # Generate article
        article = generate_article_llm(keyword, site_id)
        slug = article["slug"]

        # Save HTML
        article_path = BASE_DIR / site_id / "articles" / f"{slug}.html"
        article_path.parent.mkdir(parents=True, exist_ok=True)
        with open(article_path, "w") as f:
            f.write(build_full_html(article, site_id))
        print(f"  ✓ Article saved: articles/{slug}.html")

        # Update RSS feed
        update_rss_feed(site_id, article)

        # Generate social posts
        article_url = f"https://{SITE_META[site_id]['domain']}/articles/{slug}.html"
        social = generate_social_posts_llm(article["title"], article_url, site_id)

        # Append to social queue log
        with open(social_log_path, "a") as f:
            f.write(json.dumps({
                "date": today,
                "site": site_id,
                "url": article_url,
                "title": article["title"],
                **social
            }) + "\n")
        print(f"  ✓ Social posts logged to social_queue.jsonl")

        # Mark keyword as published in queue
        entry["status"] = "published"
        entry["published_date"] = today
        entry["slug"] = slug
        published_count += 1

    # Save updated queue
    with open(QUEUE_FILE, "w") as f:
        json.dump(queue, f, indent=2)
    print(f"\n{'='*60}")
    print(f"  ✅ Done. Published {published_count} articles today.")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()
