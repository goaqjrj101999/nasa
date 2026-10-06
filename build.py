#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
import hashlib
import html
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "_site"
CONFIG_PATH = ROOT / "config.json"


class TextExtractor(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []

    def handle_data(self, data: str) -> None:
        self.parts.append(data)

    def text(self) -> str:
        return " ".join(self.parts)


@dataclass
class Post:
    title: str
    link: str
    published: datetime | None
    excerpt: str
    post_id: str


def load_config() -> dict:
    with CONFIG_PATH.open("r", encoding="utf-8") as f:
        cfg = json.load(f)

    required = ["blog_id", "site_title", "site_description", "site_url"]
    missing = [k for k in required if not str(cfg.get(k, "")).strip()]
    if missing:
        raise SystemExit(f"config.json 필수 항목이 비어 있습니다: {', '.join(missing)}")

    if cfg["blog_id"] == "YOUR_NAVER_BLOG_ID":
        raise SystemExit("config.json의 blog_id를 실제 네이버 블로그 ID로 바꿔주세요.")
    if "YOUR_GITHUB_USERNAME" in cfg["site_url"]:
        raise SystemExit("config.json의 site_url을 실제 GitHub Pages 주소 또는 개인 도메인으로 바꿔주세요.")

    cfg["site_url"] = cfg["site_url"].rstrip("/") + "/"
    cfg["max_posts"] = max(1, int(cfg.get("max_posts", 30)))
    cfg["excerpt_chars"] = max(80, int(cfg.get("excerpt_chars", 260)))
    return cfg


def fetch_rss(blog_id: str) -> bytes:
    url = f"https://rss.blog.naver.com/{urllib.parse.quote(blog_id)}.xml"
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; NaverBlogIndexHub/1.0; +https://github.com/)",
            "Accept": "application/rss+xml, application/xml, text/xml;q=0.9, */*;q=0.8",
        },
        method="GET",
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as resp:
            data = resp.read()
            if not data:
                raise RuntimeError("RSS 응답이 비어 있습니다.")
            return data
    except Exception as e:
        raise RuntimeError(f"네이버 RSS를 가져오지 못했습니다: {url}\n{e}") from e


def strip_html(value: str) -> str:
    parser = TextExtractor()
    try:
        parser.feed(value or "")
        text = parser.text()
    except Exception:
        text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text


def parse_pubdate(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        dt = parsedate_to_datetime(value)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def extract_post_id(link: str, title: str) -> str:
    parsed = urllib.parse.urlparse(link)
    query = urllib.parse.parse_qs(parsed.query)
    for key in ("logNo", "logno"):
        if key in query and query[key]:
            return re.sub(r"[^0-9A-Za-z_-]", "", query[key][0])
    m = re.search(r"/(\d{6,})(?:[/?#]|$)", parsed.path)
    if m:
        return m.group(1)
    return hashlib.sha1(f"{link}|{title}".encode("utf-8")).hexdigest()[:12]


def parse_rss(xml_bytes: bytes, max_posts: int, excerpt_chars: int) -> list[Post]:
    root = ET.fromstring(xml_bytes)
    posts: list[Post] = []

    for item in root.findall(".//item")[:max_posts]:
        title = (item.findtext("title") or "제목 없음").strip()
        link = (item.findtext("link") or "").strip()
        if not link.startswith("http"):
            continue
        desc = item.findtext("description") or ""
        excerpt = strip_html(desc)
        if len(excerpt) > excerpt_chars:
            excerpt = excerpt[:excerpt_chars].rstrip() + "…"
        published = parse_pubdate(item.findtext("pubDate"))
        posts.append(
            Post(
                title=title,
                link=link,
                published=published,
                excerpt=excerpt,
                post_id=extract_post_id(link, title),
            )
        )

    # 날짜가 있는 항목은 최신순. RSS 순서가 이미 최신순이어도 안전하게 유지.
    posts.sort(key=lambda p: p.published or datetime.min.replace(tzinfo=timezone.utc), reverse=True)
    return posts


def esc(s: str) -> str:
    return html.escape(s, quote=True)


def base_head(cfg: dict, title: str, canonical: str, description: str) -> str:
    verification = ""
    token = str(cfg.get("google_site_verification", "")).strip()
    if token:
        verification = f'  <meta name="google-site-verification" content="{esc(token)}">\n'

    return f"""<!doctype html>
<html lang="ko">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width,initial-scale=1">
  <title>{esc(title)}</title>
  <meta name="description" content="{esc(description)}">
  <meta name="robots" content="index,follow,max-image-preview:large,max-snippet:-1,max-video-preview:-1">
  <link rel="canonical" href="{esc(canonical)}">
{verification}  <style>
    :root {{ color-scheme: light dark; --max: 920px; }}
    body {{ font-family: system-ui,-apple-system,BlinkMacSystemFont,"Segoe UI",sans-serif; margin:0; line-height:1.65; }}
    main {{ max-width:var(--max); margin:auto; padding:32px 20px 64px; }}
    header {{ margin-bottom:32px; }}
    h1 {{ line-height:1.25; }}
    .muted {{ opacity:.72; }}
    .post {{ padding:20px 0; border-top:1px solid color-mix(in srgb, currentColor 18%, transparent); }}
    .post:first-of-type {{ border-top:0; }}
    .post h2 {{ margin:0 0 6px; font-size:1.2rem; }}
    .post p {{ margin:8px 0; }}
    a {{ text-underline-offset:3px; }}
    nav a {{ margin-right:14px; }}
    footer {{ margin-top:40px; padding-top:20px; border-top:1px solid color-mix(in srgb, currentColor 18%, transparent); font-size:.92rem; opacity:.78; }}
    code {{ overflow-wrap:anywhere; }}
  </style>
</head>
"""


def render_posts(posts: Iterable[Post]) -> str:
    chunks: list[str] = []
    for p in posts:
        date_txt = p.published.astimezone().strftime("%Y-%m-%d") if p.published else "날짜 정보 없음"
        excerpt = f"<p>{esc(p.excerpt)}</p>" if p.excerpt else ""
        chunks.append(
            f"""<article class="post">
  <h2><a href="{esc(p.link)}">{esc(p.title)}</a></h2>
  <div class="muted">{esc(date_txt)}</div>
  {excerpt}
  <p><a href="{esc(p.link)}">네이버 블로그 원문 보기 →</a></p>
</article>"""
        )
    return "\n".join(chunks)


def build_index(cfg: dict, posts: list[Post], now: datetime) -> str:
    canonical = cfg["site_url"]
    ld_items = []
    for idx, p in enumerate(posts[:10], start=1):
        ld_items.append({"@type": "ListItem", "position": idx, "url": p.link, "name": p.title})
    ld = {
        "@context": "https://schema.org",
        "@type": "CollectionPage",
        "name": cfg["site_title"],
        "description": cfg["site_description"],
        "url": canonical,
        "mainEntity": {"@type": "ItemList", "itemListElement": ld_items},
    }
    head = base_head(cfg, cfg["site_title"], canonical, cfg["site_description"])
    return head + f"""<body>
<main>
  <header>
    <h1>{esc(cfg['site_title'])}</h1>
    <p>{esc(cfg['site_description'])}</p>
    <nav><a href="./">최신 글</a><a href="archive.html">전체 아카이브</a><a href="sitemap.xml">Sitemap</a></nav>
  </header>
  <section aria-label="최신 네이버 블로그 글">
    {render_posts(posts[:12]) if posts else '<p>표시할 RSS 글이 없습니다.</p>'}
  </section>
  <footer>
    마지막 자동 갱신: {esc(now.strftime('%Y-%m-%d %H:%M UTC'))}<br>
    이 페이지는 원문을 복제하지 않고 네이버 블로그 원문으로 연결하는 공개 인덱스입니다.
  </footer>
</main>
<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False, separators=(',', ':'))}</script>
</body>
</html>
"""


def build_archive(cfg: dict, posts: list[Post], now: datetime) -> str:
    canonical = urllib.parse.urljoin(cfg["site_url"], "archive.html")
    title = f"전체 아카이브 | {cfg['site_title']}"
    head = base_head(cfg, title, canonical, "네이버 블로그 최신 글 전체 아카이브")
    return head + f"""<body>
<main>
  <header>
    <h1>전체 아카이브</h1>
    <p class="muted">RSS에서 확인 가능한 최근 {len(posts)}개 게시글</p>
    <nav><a href="./">최신 글</a><a href="archive.html">전체 아카이브</a></nav>
  </header>
  <section>{render_posts(posts) if posts else '<p>표시할 RSS 글이 없습니다.</p>'}</section>
  <footer>마지막 자동 갱신: {esc(now.strftime('%Y-%m-%d %H:%M UTC'))}</footer>
</main>
</body>
</html>
"""


def build_sitemap(cfg: dict, now: datetime) -> str:
    today = now.date().isoformat()
    urls = [
        cfg["site_url"],
        urllib.parse.urljoin(cfg["site_url"], "archive.html"),
    ]
    rows = "\n".join(
        f"  <url><loc>{esc(u)}</loc><lastmod>{today}</lastmod></url>" for u in urls
    )
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">
{rows}
</urlset>
"""


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8", newline="\n")


def main() -> int:
    cfg = load_config()
    xml_bytes = fetch_rss(cfg["blog_id"])
    posts = parse_rss(xml_bytes, cfg["max_posts"], cfg["excerpt_chars"])
    now = datetime.now(timezone.utc)

    OUT.mkdir(parents=True, exist_ok=True)
    write_text(OUT / "index.html", build_index(cfg, posts, now))
    write_text(OUT / "archive.html", build_archive(cfg, posts, now))
    write_text(OUT / "sitemap.xml", build_sitemap(cfg, now))
    write_text(
        OUT / "robots.txt",
        f"User-agent: *\nAllow: /\nSitemap: {urllib.parse.urljoin(cfg['site_url'], 'sitemap.xml')}\n",
    )
    write_text(OUT / ".nojekyll", "")
    write_text(
        OUT / "status.json",
        json.dumps(
            {
                "generated_at": now.isoformat(),
                "blog_id": cfg["blog_id"],
                "rss_url": f"https://rss.blog.naver.com/{cfg['blog_id']}.xml",
                "post_count": len(posts),
            },
            ensure_ascii=False,
            indent=2,
        ),
    )

    print(f"완료: {len(posts)}개 글을 읽어 {OUT}에 사이트를 생성했습니다.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
