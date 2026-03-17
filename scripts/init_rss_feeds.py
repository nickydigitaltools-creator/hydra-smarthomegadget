#!/usr/bin/env python3
"""
Initializes a base rss.xml file for each of the 10 Hydra sites.
Run this once during setup. The daily generator will append new items.
"""

from pathlib import Path
import datetime

BASE_DIR = Path(__file__).resolve().parent.parent

SITES = [
    {"dir": "site1-aitoolpicks",        "domain": "aitoolpicks.com",        "name": "AI Tool Picks",          "desc": "Best AI productivity tools reviewed and compared"},
    {"dir": "site2-sidehustlestack",    "domain": "sidehustlestack.io",     "name": "Side Hustle Stack",      "desc": "Best tools for freelancers and side hustlers"},
    {"dir": "site3-smarthomegadget",    "domain": "smarthomegadgetpro.com", "name": "Smart Home Gadget Pro",  "desc": "Best smart home devices reviewed"},
    {"dir": "site4-financeappreviews",  "domain": "financeappreviews.net",  "name": "Finance App Reviews",    "desc": "Best personal finance apps reviewed"},
    {"dir": "site5-parentingtechguide", "domain": "parentingtechguide.com", "name": "Parenting Tech Guide",   "desc": "Best baby and kids tech products reviewed"},
    {"dir": "site6-diytoolsreviewed",   "domain": "diytoolsreviewed.com",   "name": "DIY Tools Reviewed",     "desc": "Best power tools and home improvement gear"},
    {"dir": "site7-learnsmartpicks",    "domain": "learnsmartpicks.com",    "name": "Learn Smart Picks",      "desc": "Best online courses and learning platforms"},
    {"dir": "site8-privacytoolsrated",  "domain": "privacytoolsrated.com",  "name": "Privacy Tools Rated",    "desc": "Best VPNs, password managers, and security tools"},
    {"dir": "site9-fitnesstechreviews", "domain": "fitnesstechreviews.io",  "name": "Fitness Tech Reviews",   "desc": "Best fitness trackers, apps, and wellness gadgets"},
    {"dir": "site10-remotetravelpicks", "domain": "remotetravelpicks.com",  "name": "Remote Travel Picks",    "desc": "Best gear and tools for digital nomads"},
]

RSS_TEMPLATE = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0" xmlns:atom="http://www.w3.org/2005/Atom">
  <channel>
    <title>{name}</title>
    <link>https://{domain}</link>
    <description>{desc}</description>
    <language>en-us</language>
    <lastBuildDate>{date}</lastBuildDate>
    <atom:link href="https://{domain}/rss.xml" rel="self" type="application/rss+xml" />
  </channel>
</rss>
"""

pub_date = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S +0000")

for site in SITES:
    rss_path = BASE_DIR / site["dir"] / "rss.xml"
    if rss_path.exists():
        print(f"[SKIP] {site['dir']}/rss.xml already exists.")
        continue
    content = RSS_TEMPLATE.format(
        name=site["name"],
        domain=site["domain"],
        desc=site["desc"],
        date=pub_date,
    )
    with open(rss_path, "w") as f:
        f.write(content)
    print(f"[OK] Created {site['dir']}/rss.xml")

print("\nAll RSS feeds initialized.")
