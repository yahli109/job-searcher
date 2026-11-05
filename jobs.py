"""Check company career pages, filter by keywords, alert on jobs not seen before."""
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).parent
SEEN = ROOT / "seen.json"


def get(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (job-searcher)"})
    with urllib.request.urlopen(req, timeout=30) as r:
        return r.read().decode("utf-8", "replace")


class Links(HTMLParser):
    """Collects (text, href) for every <a> on a page."""

    def __init__(self):
        super().__init__()
        self.links, self._href, self._text = [], None, []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self._href, self._text = dict(attrs).get("href"), []

    def handle_data(self, data):
        if self._href is not None:
            self._text.append(data)

    def handle_endtag(self, tag):
        if tag == "a":
            if self._href:
                self.links.append((" ".join("".join(self._text).split()), self._href))
            self._href = None


def ats(url):
    """('greenhouse'|'lever'|'ashby', slug) for a hosted job-board link, else ('html', None)."""
    u = urllib.parse.urlparse(url)
    slug = u.path.strip("/").split("/")[0]
    for host, kind in (("greenhouse.io", "greenhouse"), ("lever.co", "lever"), ("ashbyhq.com", "ashby")):
        if u.netloc.endswith(host) and slug:
            return kind, slug
    return "html", None


def fetch_jobs(url):
    """Return [(title, job_url)] for one careers page link."""
    kind, slug = ats(url)
    if kind == "greenhouse":
        data = json.loads(get(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs"))
        return [(j["title"], j["absolute_url"]) for j in data["jobs"]]
    if kind == "lever":
        data = json.loads(get(f"https://api.lever.co/v0/postings/{slug}?mode=json"))
        return [(j["text"], j["hostedUrl"]) for j in data]
    if kind == "ashby":
        data = json.loads(get(f"https://api.ashbyhq.com/posting-api/job-board/{slug}"))
        return [(j["title"], j["jobUrl"]) for j in data["jobs"]]
    # ponytail: any other page = every link on it; JS-rendered pages return nothing, add a headless browser if one matters
    p = Links()
    p.feed(get(url))
    return [(t, urllib.parse.urljoin(url, h)) for t, h in p.links if t]


def matches(title, keywords):
    """No keywords = every role matches."""
    t = title.lower()
    return not keywords or any(k in t for k in keywords)


def notify(lines):
    """One Telegram message per job."""
    token, chat = os.environ.get("TELEGRAM_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat):
        if os.environ.get("GITHUB_ACTIONS"):
            sys.exit("TELEGRAM_TOKEN / TELEGRAM_CHAT_ID secrets are missing")
        print("\n\n".join(lines))  # local dry run
        return
    for text in lines:
        data = urllib.parse.urlencode({"chat_id": chat, "text": text}).encode()
        urllib.request.urlopen(f"https://api.telegram.org/bot{token}/sendMessage", data, timeout=30)
        time.sleep(1.1)  # Telegram allows ~1 message/sec per chat


def main():
    cfg = json.loads((ROOT / "config.json").read_text("utf-8"))
    keywords = [k.lower() for k in cfg["keywords"]]
    first_run = not SEEN.exists()
    seen = set() if first_run else set(json.loads(SEEN.read_text("utf-8")))
    new, failed = [], []

    for c in cfg["companies"]:
        try:
            jobs = fetch_jobs(c["url"])
        except Exception as e:
            print(f"!! {c['name']}: {e}", file=sys.stderr)
            failed.append(c["name"])
            continue
        print(f"{c['name']}: {len(jobs)} jobs")
        for title, url in jobs:
            if url not in seen and matches(title, keywords):
                new.append(f"{c['name']}: {title}\n{url}")
                seen.add(url)

    print(f"{len(new)} new matching jobs")
    if first_run:
        print("first run: recorded current jobs as the baseline, no alerts sent")
    elif new:
        notify(new)  # raises on failure, so seen.json is only saved after a successful alert
    SEEN.write_text(json.dumps(sorted(seen), indent=1, ensure_ascii=False), "utf-8")
    if failed:
        sys.exit(f"failed companies: {', '.join(failed)}")  # red run = GitHub emails you


if __name__ == "__main__":
    main()
