#!/usr/bin/env python3
"""
TermOSINT v1.0 — Free Terminal OSINT Tool
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Enhanced with category/subcategory targeting, exact username matching,
and clean categorized output.

Install:  pip install -r requirements.txt
Usage:    python vasuki.py -cat st -subcat pro col soc -n "Name Surname" -u "username" -k "Keyword 1" -k "Keyword 2" --deep --max-depth 2
"""

import argparse
import json
import re
import sys
import textwrap
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime

import requests
import urllib3

urllib3.disable_warnings()

# ── Optional: rich for pretty terminal output ───────────────────────────────
try:
    from rich import box as RBOX
    from rich.console import Console
    from rich.panel import Panel
    from rich.progress import (
        BarColumn,
        Progress,
        SpinnerColumn,
        TextColumn,
        TimeElapsedColumn,
    )
    from rich.table import Table

    RICH = True
    console = Console()
except ImportError:
    RICH = False

    class _FB:
        def print(self, *a, **kw):
            print(*[re.sub(r"\[/?[^\]]*\]", "", str(x)) for x in a])

        def rule(self, t=""):
            c = re.sub(r"\[/?[^\]]*\]", "", str(t))
            print(f"\n── {c} " + "─" * max(0, 52 - len(c)))

    console = _FB()

# ── Optional: duckduckgo-search for web intel ──────────────────────────────
try:
    from ddgs import DDGS

    DDG = True
except ImportError:
    DDG = False

VERSION = "1.0.0"
TIMEOUT = 10
UA = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122 Safari/537.36"
)

# ── Global results store ──────────────────────────────────────────────────────
RESULTS: dict = {"deep": {"pdfs": [], "indian_dbs": [], "court_cases": []}}

# ── Platform Registry (unchanged) ──────────────────────────────────────────
PLATFORMS = {
    "Twitter/X": {"url": "https://twitter.com/{u}", "cat": "Social"},
    "Instagram": {"url": "https://www.instagram.com/{u}/", "cat": "Social"},
    "TikTok": {"url": "https://www.tiktok.com/@{u}", "cat": "Social"},
    "Snapchat": {"url": "https://www.snapchat.com/add/{u}", "cat": "Social"},
    "Pinterest": {"url": "https://www.pinterest.com/{u}/", "cat": "Social"},
    "Tumblr": {"url": "https://{u}.tumblr.com", "cat": "Social"},
    "Mastodon": {"url": "https://mastodon.social/@{u}", "cat": "Social"},
    "Bluesky": {"url": "https://bsky.app/profile/{u}.bsky.social", "cat": "Social"},
    "VK": {"url": "https://vk.com/{u}", "cat": "Social"},
    "Telegram": {"url": "https://t.me/{u}", "cat": "Social"},
    "Threads": {"url": "https://www.threads.net/@{u}", "cat": "Social"},
    "LinkedIn": {"url": "https://www.linkedin.com/in/{n}/", "cat": "Professional"},
    "GitHub": {
        "url": "https://github.com/{n}",
        "cat": "Professional",
        "api": "https://api.github.com/users/{n}",
    },
    "GitLab": {"url": "https://gitlab.com/{u}", "cat": "Professional"},
    "Bitbucket": {"url": "https://bitbucket.org/{u}/", "cat": "Professional"},
    "Dev.to": {"url": "https://dev.to/{u}", "cat": "Professional"},
    "Hashnode": {"url": "https://hashnode.com/@{u}", "cat": "Professional"},
    "Medium": {"url": "https://medium.com/@{u}", "cat": "Professional"},
    "Keybase": {"url": "https://keybase.io/{u}", "cat": "Professional"},
    "AngelList": {"url": "https://angel.co/u/{u}", "cat": "Professional"},
    "Xing": {"url": "https://www.xing.com/profile/{u}", "cat": "Professional"},
    "HackerNews": {
        "url": "https://news.ycombinator.com/user?id={u}",
        "cat": "Tech",
        "api": "https://hacker-news.firebaseio.com/v0/user/{u}.json",
    },
    "Product Hunt": {"url": "https://www.producthunt.com/@{u}", "cat": "Tech"},
    "npmjs": {"url": "https://www.npmjs.com/~{u}", "cat": "Tech"},
    "PyPI": {"url": "https://pypi.org/user/{u}/", "cat": "Tech"},
    "Replit": {"url": "https://replit.com/@{u}", "cat": "Tech"},
    "CodePen": {"url": "https://codepen.io/{u}", "cat": "Tech"},
    "Hugging Face": {"url": "https://huggingface.co/{u}", "cat": "Tech"},
    "Docker Hub": {"url": "https://hub.docker.com/u/{u}/", "cat": "Tech"},
    "SourceForge": {"url": "https://sourceforge.net/u/{u}/", "cat": "Tech"},
    "JSFiddle": {"url": "https://jsfiddle.net/user/{u}/", "cat": "Tech"},
    "Twitch": {"url": "https://www.twitch.tv/{u}", "cat": "Gaming"},
    "Steam": {"url": "https://steamcommunity.com/id/{u}", "cat": "Gaming"},
    "Roblox": {"url": "https://www.roblox.com/user.aspx?username={u}", "cat": "Gaming"},
    "Behance": {"url": "https://www.behance.net/{u}", "cat": "Creative"},
    "Dribbble": {"url": "https://dribbble.com/{u}", "cat": "Creative"},
    "DeviantArt": {"url": "https://www.deviantart.com/{u}", "cat": "Creative"},
    "ArtStation": {"url": "https://www.artstation.com/{u}", "cat": "Creative"},
    "Flickr": {"url": "https://www.flickr.com/people/{u}/", "cat": "Creative"},
    "Unsplash": {"url": "https://unsplash.com/@{u}", "cat": "Creative"},
    "500px": {"url": "https://500px.com/p/{u}", "cat": "Creative"},
    "SoundCloud": {"url": "https://soundcloud.com/{u}", "cat": "Music"},
    "Last.fm": {"url": "https://www.last.fm/user/{u}", "cat": "Music"},
    "Bandcamp": {"url": "https://{u}.bandcamp.com", "cat": "Music"},
    "WordPress": {"url": "https://{u}.wordpress.com", "cat": "Blogging"},
    "Blogger": {"url": "https://{u}.blogspot.com", "cat": "Blogging"},
    "Substack": {"url": "https://{u}.substack.com", "cat": "Blogging"},
    "Ghost": {"url": "https://{u}.ghost.io", "cat": "Blogging"},
    "About.me": {"url": "https://about.me/{u}", "cat": "Blogging"},
    "Write.as": {"url": "https://write.as/{u}", "cat": "Blogging"},
    "Patreon": {"url": "https://www.patreon.com/{u}", "cat": "Support"},
    "Buy Me Coffee": {"url": "https://www.buymeacoffee.com/{u}", "cat": "Support"},
    "Ko-fi": {"url": "https://ko-fi.com/{u}", "cat": "Support"},
    "Gumroad": {"url": "https://gumroad.com/{u}", "cat": "Support"},
    "Reddit": {
        "url": "https://www.reddit.com/user/{u}",
        "cat": "Forums",
        "api": "https://www.reddit.com/user/{u}/about.json",
    },
    "Quora": {"url": "https://www.quora.com/profile/{u}", "cat": "Forums"},
    "Gravatar": {"url": "https://en.gravatar.com/{u}", "cat": "Forums"},
    "Disqus": {"url": "https://disqus.com/by/{u}/", "cat": "Forums"},
}


# ── HTTP session ─────────────────────────────────────────────────────────────
def _session() -> requests.Session:
    s = requests.Session()
    s.headers.update({"User-Agent": UA, "Accept-Language": "en-US,en;q=0.9"})
    return s


SESSION = _session()


# ── Helper functions (unchanged) ──────────────────────────────────────────
def fuzzy_match(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    a_tokens = set(a.lower().split())
    b_tokens = set(b.lower().split())
    overlap = len(a_tokens & b_tokens)
    total = len(a_tokens | b_tokens)
    return round(overlap / total, 2) if total else 0.0


def _detail_str(d: dict) -> str:
    parts = []
    if d.get("display_name"):
        parts.append(f"Name: {d['display_name']}")
    if d.get("bio"):
        parts.append(f"Bio: {d['bio'][:60]}")
    if d.get("location"):
        parts.append(f"📍 {d['location']}")
    if d.get("email"):
        parts.append(f"📧 {d['email']}")
    if d.get("blog"):
        parts.append(f"🌐 {d['blog']}")
    if d.get("company"):
        parts.append(f"🏢 {d['company']}")
    if d.get("repos"):
        parts.append(f"Repos: {d['repos']}")
    if d.get("followers"):
        parts.append(f"Followers: {d['followers']}")
    if d.get("karma"):
        parts.append(f"Karma: {d['karma']}")
    if d.get("cake_day"):
        parts.append(f"Since: {d['cake_day']}")
    if d.get("about"):
        parts.append(f"About: {d['about'][:60]}")
    return "\n".join(parts)


# ── Platform checker (unchanged) ──────────────────────────────────────────
def check_platform(
    platform_name: str, info: dict, username: str, target_name: str = ""
) -> tuple:
    u = username
    n = platform_name  # Note: we'll override with target_name later
    url = info["url"].replace("{u}", u).replace("{n}", target_name)
    found = False
    details = {}
    confidence = 0.0

    if platform_name == "GitHub" and "api" in info:
        try:
            r = SESSION.get(info["api"].replace("{u}", u), timeout=TIMEOUT)
            if r.status_code == 200:
                d = r.json()
                found = True
                details = {
                    k: v
                    for k, v in {
                        "display_name": d.get("name"),
                        "bio": (d.get("bio") or "")[:80],
                        "location": d.get("location"),
                        "email": d.get("email"),
                        "blog": d.get("blog"),
                        "company": d.get("company"),
                        "repos": d.get("public_repos"),
                        "followers": d.get("followers"),
                        "joined": (d.get("created_at") or "")[:10],
                    }.items()
                    if v
                }
                if target_name and details.get("display_name"):
                    confidence = fuzzy_match(target_name, details["display_name"])
        except Exception:
            pass
        return platform_name, url, found, details, confidence

    if platform_name == "HackerNews" and "api" in info:
        try:
            r = SESSION.get(info["api"].replace("{u}", u), timeout=TIMEOUT)
            if r.status_code == 200 and r.json():
                d = r.json()
                found = True
                details = {
                    "karma": d.get("karma"),
                    "about": re.sub(r"<[^>]+>", "", d.get("about") or "")[:100],
                }
                if (
                    target_name
                    and details.get("about")
                    and target_name.lower() in details["about"].lower()
                ):
                    confidence = 0.6
        except Exception:
            pass
        return platform_name, url, found, details, confidence

    if platform_name == "Reddit" and "api" in info:
        try:
            r = SESSION.get(
                info["api"].replace("{u}", u),
                timeout=TIMEOUT,
                headers={"User-Agent": "termosint/2.0"},
            )
            if r.status_code == 200:
                data = r.json().get("data", {})
                if data.get("name"):
                    found = True
                    created = data.get("created_utc", 0)
                    details = {
                        "karma": data.get("total_karma"),
                        "cake_day": datetime.utcfromtimestamp(created).strftime(
                            "%Y-%m-%d"
                        )
                        if created
                        else "?",
                        "verified": data.get("verified"),
                    }
                    confidence = 0.8 if data.get("name") == u else 0.5
        except Exception:
            pass
        return platform_name, url, found, details, confidence

    try:
        r = SESSION.head(url, timeout=TIMEOUT, verify=False, allow_redirects=True)
        if r.status_code == 200:
            found = True
        elif r.status_code == 405:
            r = SESSION.get(url, timeout=TIMEOUT, verify=False, allow_redirects=True)
            if r.status_code == 200:
                found = True
    except Exception:
        pass
    if found and target_name:
        confidence = 0.3
    return platform_name, url, found, details, confidence


# ── Platform scanner ──────────────────────────────────────────────────────
def scan_platforms(username: str, target_name: str = "", workers: int = 25) -> list:
    console.rule(
        f"[cyan]Scanning {len(PLATFORMS)} platforms  →  [bold]@{username}[/bold][/cyan]"
    )
    found_list = []

    if RICH:
        # Clean progress bar – no extra prints
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as prog:
            task = prog.add_task("[cyan]Checking platforms…", total=len(PLATFORMS))
            with ThreadPoolExecutor(max_workers=workers) as ex:
                futures = {
                    ex.submit(
                        check_platform, p_name, p_info, username, target_name
                    ): p_name
                    for p_name, p_info in PLATFORMS.items()
                }
                for fut in as_completed(futures):
                    prog.advance(task)
                    try:
                        p_name, url, found, details, conf = fut.result()
                        if found:
                            found_list.append(
                                {
                                    "platform": p_name,
                                    "url": url,
                                    "cat": PLATFORMS[p_name]["cat"],
                                    "details": details,
                                    "confidence": conf,
                                }
                            )
                    except Exception:
                        pass
    else:
        # Fallback without Rich – silent scan (no print lines)
        with ThreadPoolExecutor(max_workers=workers) as ex:
            futures = {
                ex.submit(check_platform, p_name, p_info, username, target_name): p_name
                for p_name, p_info in PLATFORMS.items()
            }
            for fut in as_completed(futures):
                try:
                    p_name, url, found, details, conf = fut.result()
                    if found:
                        found_list.append(
                            {
                                "platform": p_name,
                                "url": url,
                                "cat": PLATFORMS[p_name]["cat"],
                                "details": details,
                                "confidence": conf,
                            }
                        )
                except Exception:
                    pass

    RESULTS["platforms"] = found_list
    return found_list


# ── New: Exact username match scanner (separate category) ──────────────
def scan_exact_username(username: str, workers: int = 15) -> list:
    """Scan for exact username matches on a curated list of platforms."""
    matches = []
    # Use a subset of platforms where exact username is common
    exact_platforms = {
        "GitHub": "https://github.com/{u}",
        "GitLab": "https://gitlab.com/{u}",
        "Twitter/X": "https://x.com/{u}",
        "Instagram": "https://www.instagram.com/{u}/",
        "Reddit": "https://www.reddit.com/user/{u}",
        "HackerNews": "https://news.ycombinator.com/user?id={u}",
        "Medium": "https://medium.com/@{u}",
        "Dev.to": "https://dev.to/{u}",
        "Hashnode": "https://hashnode.com/@{u}",
        "PyPI": "https://pypi.org/user/{u}/",
        "npmjs": "https://www.npmjs.com/~{u}",
        "Docker Hub": "https://hub.docker.com/u/{u}/",
    }

    def check_exact(p_name: str, url_template: str) -> tuple:
        url = url_template.replace("{u}", username)
        try:
            r = SESSION.head(url, timeout=5, verify=False, allow_redirects=True)
            if r.status_code == 200:
                return p_name, url, True
            elif r.status_code == 405:
                r = SESSION.get(url, timeout=5, verify=False, allow_redirects=True)
                if r.status_code == 200:
                    return p_name, url, True
        except:
            pass
        return p_name, url, False

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {
            ex.submit(check_exact, p_name, url_template): p_name
            for p_name, url_template in exact_platforms.items()
        }
        for fut in as_completed(futures):
            try:
                p_name, url, found = fut.result()
                if found:
                    matches.append({"platform": p_name, "url": url})
            except:
                pass

    RESULTS["username_matches"] = matches
    return matches


# ── Modified: Deep web dorking with dynamic college search ─────────────
def deep_web_search(
    name: str,
    username: str,
    keywords_list: list = None,
    country: str = "",
    subcats: list = None,
    max_depth: int = 2,
) -> dict:
    if not DDG:
        console.print(
            "[yellow]⚠  Install duckduckgo-search for deep searches.[/yellow]"
        )
        return {}

    dorks = []
    subcat_set = set(subcats) if subcats else {"all"}

    # === COLLEGE KEYWORD DETECTION ===
    dtu_keywords = {"dtu", "nsut", "igdtuw"}
    ipu_colleges = {
        "usap",
        "usbas",
        "usbt",
        "usct",
        "usem",
        "ushss",
        "usict",
        "uslls",
        "usms",
        "usmc",
        "usmphs",
        "usar",
        "usdi",
        "mait",
        "msit",
        "bpit",
        "bvcoe",
        "vips-tc",
        "adgitm",
        "gtbit",
        "dtc",
        "ambedkar institute of technology",
        "igit",
        "b.m. institute of engineering",
        "dias",
        "rdias",
        "jims rohini",
        "bhai parmanand institute of business studies",
        "bcips",
        "fairfield institute",
        "vips law",
        "army college of medical sciences",
        "vardhman mahavir medical college",
        "dr. b.r. sur homoeopathic college",
        "institute of hotel management & catering",
        "dspsr",
    }

    # ── Keyword‑specific dorks with site‑specific fallback ──
    if keywords_list:
        for kw in keywords_list:
            kw_lower = kw.lower()
            queries = [f'"{name}" + "{kw}"']  # generic
            if kw_lower in dtu_keywords:
                queries.append(f'"{name}" site:resulthubdtu.com')
            elif kw_lower in ipu_colleges:
                queries.append(f'"{name}" site:ipuranklist.com')
            # Add all queries under the same label
            for q in queries:
                dorks.append((q, f"Keyword: {kw}"))

    # ── Standard subcategory dorks ──────────────────────────────────────
    subcat_dorks = {
        "soc": (
            "Social Sites",
            [
                f'"{name}" site:instagram.com OR site:facebook.com OR site:x.com',
            ],
        ),
        "case": (
            "Court Cases (Indian Kanoon)",
            [
                f'"{name}" site:indiankanoon.org',
            ],
        ),
        "pro": (
            "Professional Sites",
            [
                f'"{name}" site:linkedin.com/in OR site:github.com OR site:wellfound.com',
            ],
        ),
        "file": (
            "Kaagaz (Scribd)",
            [
                f'"{name}" site:scribd.com',
            ],
        ),
        "col": (
            "College (IPU/DTU)",
            [
                f'"{name}" site:ipuranklist.com OR site:resulthubdtu.com',
            ],
        ),
        "cus": (
            "Custom Sites",
            [
                f'"{name}" site:iascivillist.dopt.gov.in OR site:haryanapolice.gov.in OR site:delhi.gov.in OR site:joinindianarmy.nic.in',
            ],
        ),
    }

    if "all" in subcat_set:
        for sc, (label, qs) in subcat_dorks.items():
            for q in qs:
                dorks.append((q, label))
    else:
        for sc in subcat_set:
            if sc in subcat_dorks:
                label, qs = subcat_dorks[sc]
                for q in qs:
                    dorks.append((q, label))

    # ── Generic dorks for files (kept from original) ────────────────────
    dorks.append((f'"{name}" + "pdf"', "PDFs with name"))
    dorks.append((f'"{name}" "doc" OR "docx"', "Word docs"))
    dorks.append((f'"{name}" + "enrollment number"', "Enrollment numbers"))

    # ── Execute all dorks ──────────────────────────────────────────────
    all_hits = {}
    if RICH:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
            TimeElapsedColumn(),
            console=console,
            transient=False,
        ) as progress:
            task = progress.add_task("[cyan]Dorking…", total=len(dorks))
            for q, label in dorks:
                progress.update(task, description=f"[cyan]→ {label}")
                hits = _ddg_query(q, max_r=8)
                if hits:
                    all_hits.setdefault(label, []).extend(hits)
                progress.advance(task)
                time.sleep(0.6)
    else:
        for q, label in dorks:
            hits = _ddg_query(q, max_r=8)
            if hits:
                all_hits.setdefault(label, []).extend(hits)
            time.sleep(0.6)

    RESULTS["deep"]["dorks"] = all_hits
    return all_hits


def _ddg_query(q: str, max_r: int = 6) -> list:
    if not DDG:
        return []
    try:
        ddgs = DDGS()
        return list(ddgs.text(q, max_results=max_r))
    except Exception as e:
        if "Ratelimit" in str(e):
            time.sleep(3)
        return []


# ── Recursive enrichment (removed heading) ─────────────────────────────
def recursive_enrich(
    platform_results: list, name: str, username: str, max_depth: int = 2
) -> dict:
    # Removed console.rule line
    enriched = {}
    emails, locations, companies, blogs = set(), set(), set(), set()
    for p in platform_results:
        d = p.get("details", {})
        if d.get("email"):
            emails.add(d["email"])
        if d.get("location"):
            locations.add(d["location"])
        if d.get("company"):
            companies.add(d["company"])
        if d.get("blog"):
            blogs.add(d["blog"])

    if emails:
        console.print(f"[cyan]Found {len(emails)} email addresses — searching…[/cyan]")
        for email in emails:
            hits = _ddg_query(f'"{email}"', max_r=4)
            if hits:
                enriched[f"Email: {email}"] = hits
            time.sleep(0.4)
    if locations:
        console.print(f"[cyan]Locations: {', '.join(locations)} — searching…[/cyan]")
        for loc in locations:
            hits = _ddg_query(f'"{name}" "{loc}"', max_r=4)
            if hits:
                enriched[f"Location: {loc}"] = hits
            time.sleep(0.4)
    if companies:
        console.print(f"[cyan]Companies: {', '.join(companies)} — searching…[/cyan]")
        for comp in companies:
            hits = _ddg_query(f'"{name}" "{comp}"', max_r=4)
            if hits:
                enriched[f"Company: {comp}"] = hits
            time.sleep(0.4)
    RESULTS["deep"]["recursive"] = enriched
    return enriched


# ── GitHub enrichment (unchanged) ──────────────────────────────────────
def enrich_github(username: str) -> dict:
    data = {}
    try:
        r = SESSION.get(
            f"https://api.github.com/users/{username}/repos?per_page=6&sort=stars",
            timeout=TIMEOUT,
        )
        if r.status_code == 200:
            data["top_repos"] = [
                {
                    "name": rp["name"],
                    "stars": rp["stargazers_count"],
                    "lang": rp.get("language"),
                    "url": rp["html_url"],
                }
                for rp in r.json()[:6]
            ]
    except Exception:
        pass
    try:
        r2 = SESSION.get(
            f"https://api.github.com/users/{username}/orgs", timeout=TIMEOUT
        )
        if r2.status_code == 200:
            data["orgs"] = [o["login"] for o in r2.json()]
    except Exception:
        pass
    return data


# ── Display functions (modified: only headings) ──────────────────────────
def display_platforms(found: list) -> None:
    """Display platform profiles in the new line-by-line format (no 'Found X' line)."""
    if not found:
        return
    # We'll output later as part of the overall results, so we don't print here.
    # The main display function will handle it.
    pass


def display_deep_results(deep: dict) -> None:
    """Print deep results in the requested line-by-line format per category."""
    if not deep:
        return
    # The main display function will handle it in a structured way.
    pass


def display_all_results(
    target_name: str,
    target_username: str,
    platform_results: list,
    deep_results: dict,
    username_matches: list,
    subcats: list,
) -> None:
    """Print only category headings (no detailed items)."""
    console.print(
        f"\n[bold cyan]Target Name → {target_name} @{target_username}[/bold cyan]\n"
    )

    # 1. Exact username matches heading (if any)
    if username_matches:
        console.print("[bold green]🐍 Exact Username Matches Found ✅[/bold green]\n")

    # 2. Deep results – only print category headings
    if deep_results:
        for label, hits in deep_results.items():
            if not hits or not isinstance(hits, list):
                continue
            # Determine emoji based on label
            emoji = "🐍"
            if "Social" in label:
                emoji = "🐍"
            elif "Court" in label:
                emoji = "⚖️"
            elif "Professional" in label:
                emoji = "💼"
            elif "Kaagaz" in label or "Scribd" in label:
                emoji = "📄"
            elif "College" in label or "IPU" in label:
                emoji = "🎓"
            elif "Custom" in label:
                emoji = "🔍"
            console.print(f"[bold green]{emoji} {label} Found ✅[/bold green]")
        console.print("")  # blank line after all headings


# ── Summary (unchanged) ──────────────────────────────────────────────────
def display_summary(name: str, username: str, found: list, deep: dict) -> None:
    total_deep = sum(len(v) for v in deep.values()) if deep else 0
    if RICH:
        lines = (
            f"[bold]Target:[/bold]          {name}  (@{username})\n"
            f"[bold]Profiles found:[/bold]  [green]{len(found)}[/green] / {len(PLATFORMS)} scanned\n"
            f"[bold]Deep hits:[/bold]       [yellow]{total_deep}[/yellow]\n"
            f"[bold]Report saved:[/bold]    [dim]see below[/dim]\n"
            f"[bold]Time:[/bold]            {datetime.now().strftime('%Y-%m-%d  %H:%M:%S')}"
        )
        console.print(
            Panel(
                lines,
                title="[bold cyan]📊  OSINT Summary[/bold cyan]",
                border_style="green",
            )
        )
    else:
        print(f"\n{'=' * 60}")
        print(f" OSINT Summary  |  {name} / @{username}")
        print(f"  Profiles : {len(found)} found  /  {len(PLATFORMS)} scanned")
        print(f"  Deep hits: {total_deep}")
        print(f"{'=' * 60}")


# ── Report export (modified JSON structure) ──────────────────────────
def save_report(
    name: str,
    username: str,
    platform_results: list,
    deep_results: dict,
    username_matches: list,
    subcats: list,
    filepath: str = None,
) -> str:
    if filepath is None:
        safe = re.sub(r"[^\w]", "_", username.lower() or name.lower())
        filepath = f"osint_{safe}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    # Build categorized JSON as requested – NO platforms field
    json_data = {
        "target_name": name,
        "target_username": username,
        "category": args.category,
        "subcategories": subcats,
        "username_matches": username_matches,
        # "platforms" field intentionally omitted
        "deep_results": {},
        "_meta": {
            "timestamp": datetime.now().isoformat(),
            "tool": f"TermOSINT v{VERSION}",
            "max_depth": args.max_depth,
        },
    }

    # Structure deep results by category (label)
    if deep_results:
        for label, hits in deep_results.items():
            if not isinstance(hits, list):
                continue
            if not hits:
                continue
            key = label.lower().replace(" ", "_").replace("(", "").replace(")", "")
            json_data["deep_results"][key] = []
            for hit in hits[:20]:
                json_data["deep_results"][key].append(
                    {
                        "title": hit.get("title", "Untitled")[:100],
                        "url": hit.get("href", "#"),
                        "snippet": hit.get("body", "No details")[:200],
                    }
                )

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, ensure_ascii=False)

    console.print(f"\n[green]💾  Report saved →  [bold]{filepath}[/bold][/green]")
    return filepath


# ── Banner (UPDATED) ────────────────────────────────────────────────────
BANNER_TEXT = r"""
██╗   ██╗ █████╗ ███████╗██╗   ██╗██╗  ██╗██╗
██║   ██║██╔══██╗██╔════╝██║   ██║██║ ██╔╝██║
██║   ██║███████║███████╗██║   ██║█████╔╝ ██║
╚██╗ ██╔╝██╔══██║╚════██║██║   ██║██╔═██╗ ██║
 ╚████╔╝ ██║  ██║███████║╚██████╔╝██║  ██╗██║
  ╚═══╝  ╚═╝  ╚═╝╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═╝
"""


def banner():
    if RICH:
        console.print(
            Panel(
                f"[bold cyan]{BANNER_TEXT}[/bold cyan]\n"
                f"  [white]v{VERSION}[/white]  ·  [green]Free[/green]  ·  [green]No API Keys[/green]  ·  [green]Deep OSINT[/green]  ·  [bold cyan]Author - Preet Kapoor[/bold cyan]",
                border_style="bright_blue",
                padding=(0, 1),
            )
        )
    else:
        print(BANNER_TEXT)
        print(
            f"  TermOSINT v{VERSION}  |  Free · Deep OSINT  |  Author - Preet Kapoor\n"
        )


# ── CLI ──────────────────────────────────────────────────────────────────
def build_parser():
    custom_usage = """usage: vasuki.py [-h] [-cat {st,em,any}] [-subcat {soc,case,pro,file,col,cus,all}] [-n NAME] [-u USERNAME] [-e EMAIL] [-k KEYWORDS] [-o OUTPUT] [--no-web] [--workers WORKERS] [--deep] [--country COUNTRY] [--max-depth MAX_DEPTH]"""
    p = argparse.ArgumentParser(
        prog="vasuki.py",
        description="VASUKI — Free terminal OSINT with deep recursive dorking",
        usage=custom_usage,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent("""
        Examples:
          python vasuki.py -cat st -subcat pro col soc -n "Name Surname" -u "username" -k "keyword_1" -k "Keyword_2" --deep --max-depth 2
          python vasuki.py -cat em -subcat pro -n "John Doe" --deep          # username optional
          python vasuki.py -cat any -subcat all -n "Elon Musk" --deep

        ⚠  Use only on yourself or with explicit written permission.
        """),
    )
    p.add_argument(
        "-cat",
        "--category",
        choices=["st", "em", "any"],
        default="any",
        help="Category: st (Student), em (Employee), any (Anyone)",
    )
    p.add_argument(
        "-subcat",
        "--subcategories",
        nargs="*",  # accepts zero or more, default below
        choices=["soc", "case", "pro", "file", "col", "cus", "all"],
        default=["all"],  # ensures at least 'all' if nothing given
        help="Subcategories (space-separated): social sites, case(advocate_name, judge_name, case_number, party(A or B)_name), professional sites, file(docs,pdfs), college/university, custom search, all",
    )
    # -n is now required
    p.add_argument("-n", "--name", required=True, help="Target full name (compulsory)")
    # -u is now optional
    p.add_argument("-u", "--username", default="", help="Target username (optional)")
    p.add_argument("-e", "--email", default="", help="Known email address")
    p.add_argument(
        "-k",
        "--keywords",
        action="append",
        help="Extra keyword (can be used multiple times)",
    )
    p.add_argument("-o", "--output", default=None, help="Output JSON file path")
    p.add_argument("--no-web", action="store_true", help="Skip DuckDuckGo searches")
    p.add_argument("--workers", type=int, default=25, help="Thread count (default 25)")
    p.add_argument("--deep", action="store_true", help="Enable deep recursive searches")
    p.add_argument(
        "--country", default="", help="Prioritise country-specific sources (e.g., IN)"
    )
    p.add_argument(
        "--max-depth",
        type=int,
        default=2,
        help="Recursion depth for enrichment (default 2)",
    )
    return p


# ── Main ──────────────────────────────────────────────────────────────────
def main():
    global args
    banner()
    args = build_parser().parse_args()
    username = args.username.lstrip("@") if args.username else ""
    name = args.name  # required
    keywords_list = args.keywords if args.keywords else []
    subcats = args.subcategories
    max_depth = args.max_depth

    if RICH:
        console.print(
            Panel(
                f"[bold]Target:[/bold]    [cyan]{name}[/cyan]"
                + (f"   (@{username})" if username else "")
                + (
                    f"\n[bold]Email:[/bold]     [cyan]{args.email}[/cyan]\n"
                    if args.email
                    else ""
                )
                + (
                    f"[bold]Keywords:[/bold] [cyan]{' '.join(keywords_list)}[/cyan]\n"
                    if keywords_list
                    else ""
                )
                + (f"[bold]Deep:[/bold]     [green]ON[/green]\n" if args.deep else "")
                + (
                    f"[bold]Country:[/bold]  [cyan]{args.country}[/cyan]\n"
                    if args.country
                    else ""
                )
                + (f"[bold]Category:[/bold] [cyan]{args.category}[/cyan]\n")
                + (f"[bold]Subcats:[/bold]  [cyan]{', '.join(subcats)}[/cyan]"),
                title="[bold]🎯  Target Info[/bold]",
                border_style="cyan",
            )
        )
    else:
        print(f"\nTarget: {name}" + (f"  (@{username})" if username else ""))
        if keywords_list:
            print(f"Keywords: {', '.join(keywords_list)}")
        print(f"Category: {args.category}")
        print(f"Subcats: {', '.join(subcats)}")

    # 1. Scan for exact username matches (only if username provided)
    username_matches = []
    if username:
        console.rule("[cyan]🔍 Scanning for exact username matches…[/cyan]")
        username_matches = scan_exact_username(username, args.workers)
        if username_matches:
            console.print(
                f"[green]✓ Found {len(username_matches)} exact username matches[/green]"
            )
        else:
            console.print("[dim]No exact username matches found[/dim]")

    # 2. Platform scan (only if username provided)
    found = []
    if username:
        found = scan_platforms(username, target_name=name, workers=args.workers)
        # GitHub enrichment (if found) – still runs but we don't display platform profiles
        gh = next((x for x in found if x["platform"] == "GitHub"), None)
        if gh:
            console.rule("[cyan]GitHub Enrichment[/cyan]")
            extra = enrich_github(username)
            if extra.get("top_repos"):
                RESULTS["github_repos"] = extra["top_repos"]
                if RICH:
                    t = Table(
                        title="🐙  Top GitHub Repos",
                        box=RBOX.SIMPLE_HEAD,
                        header_style="bold magenta",
                        border_style="bright_black",
                    )
                    t.add_column("Repo", style="cyan", width=28)
                    t.add_column("★ Stars", style="yellow", width=8)
                    t.add_column("Lang", style="green", width=14)
                    t.add_column("URL", style="blue")
                    for rp in extra["top_repos"]:
                        t.add_row(
                            rp["name"],
                            str(rp["stars"]),
                            rp.get("lang") or "—",
                            rp["url"],
                        )
                    console.print(t)
            if extra.get("orgs"):
                RESULTS["github_orgs"] = extra["orgs"]
                console.print(
                    f"  [green]Organizations: {', '.join(extra['orgs'])}[/green]"
                )
    else:
        console.print("[dim]No username provided, skipping platform scans.[/dim]")

    # 4. Deep dorking (always runs if --deep, regardless of username)
    deep_results = {}
    if args.deep and not args.no_web:
        deep_results = deep_web_search(
            name, username, keywords_list, args.country, subcats, max_depth
        )
        # Recursive enrichment (heading removed) – only if we have platform results (found list)
        if found:
            rec = recursive_enrich(found, name, username, max_depth)
            if rec:
                deep_results.update(rec)

    # 5. Display results – print the deep heading after the scan, replacing "Results"
    if args.deep and not args.no_web:
        console.rule("[cyan]🐍 After Deep Crawl , Here's what I found 🐍[/cyan]")

    # Now show the category headings only (no details)
    display_all_results(name, username, found, deep_results, username_matches, subcats)

    # 6. Summary and save
    display_summary(name, username, found, RESULTS.get("deep", {}))
    save_report(
        name,
        username,
        found,
        deep_results,
        username_matches,
        subcats,
        args.output,
    )


if __name__ == "__main__":
    main()
