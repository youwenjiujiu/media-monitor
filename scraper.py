from __future__ import annotations

import logging
import urllib.request
import ssl
from models import ScrapedArticle

logger = logging.getLogger(__name__)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

PAYWALL_MARKERS = [
    "paywall",
    "subscribe to read",
    "subscription required",
    "premium content",
    "register to continue",
    "sign in to read",
    "subscribers only",
]


def _detect_paywall(text: str | None, html: str | None) -> bool:
    if text and len(text) < 200:
        if html:
            html_lower = html.lower()
            return any(marker in html_lower for marker in PAYWALL_MARKERS)
    return False


def _fetch_html(url: str) -> str | None:
    """Download HTML with browser-like headers using urllib."""
    try:
        ctx = ssl.create_default_context()
        req = urllib.request.Request(url, headers=HEADERS)
        with urllib.request.urlopen(req, timeout=20, context=ctx) as resp:
            data = resp.read()
            # Try utf-8 first, fall back to latin-1
            try:
                return data.decode("utf-8")
            except UnicodeDecodeError:
                return data.decode("latin-1")
    except Exception as e:
        logger.warning(f"urllib fetch failed for {url}: {e}")
        return None


def _scrape_with_trafilatura(url: str, html: str | None = None) -> ScrapedArticle | None:
    try:
        import trafilatura

        # Use provided HTML or let trafilatura fetch
        if html is None:
            html = trafilatura.fetch_url(url)
        if not html:
            return None

        result = trafilatura.bare_extraction(
            html,
            url=url,
            include_comments=False,
            include_tables=False,
        )
        if not result or not result.get("text"):
            return None

        is_paywalled = _detect_paywall(result.get("text"), html)

        return ScrapedArticle(
            url=url,
            headline=result.get("title"),
            text=result.get("text"),
            source=result.get("sitename"),
            date=result.get("date"),
            is_paywalled=is_paywalled,
        )
    except Exception as e:
        logger.warning(f"trafilatura failed for {url}: {e}")
        return None


def _scrape_with_newspaper(url: str, html: str | None = None) -> ScrapedArticle | None:
    try:
        from newspaper import Article

        article = Article(url)
        if html:
            article.download(input_html=html)
        else:
            article.download()
        article.parse()

        if not article.text:
            return None

        date_str = None
        if article.publish_date:
            date_str = article.publish_date.strftime("%Y-%m-%d")

        source = None
        if hasattr(article, "meta_data") and article.meta_data:
            og = article.meta_data.get("og", {})
            if isinstance(og, dict):
                source = og.get("site_name")
        source = source or article.source_url

        return ScrapedArticle(
            url=url,
            headline=article.title,
            text=article.text,
            source=source,
            date=date_str,
            is_paywalled=False,
        )
    except Exception as e:
        logger.warning(f"newspaper4k failed for {url}: {e}")
        return None


def scrape_article(url: str) -> ScrapedArticle:
    url = url.strip()

    # Fetch HTML once with browser headers
    html = _fetch_html(url)

    # Try trafilatura with our HTML
    article = _scrape_with_trafilatura(url, html)
    if article and article.text and len(article.text) > 100:
        return article

    # Also try trafilatura's own fetcher
    article = _scrape_with_trafilatura(url, None)
    if article and article.text and len(article.text) > 100:
        return article

    # Fallback to newspaper4k
    article = _scrape_with_newspaper(url, html)
    if article and article.text and len(article.text) > 100:
        return article

    # Everything failed — check paywall
    if html and any(m in html.lower() for m in PAYWALL_MARKERS):
        return ScrapedArticle(
            url=url,
            is_paywalled=True,
            scrape_error="Article appears to be behind a paywall.",
        )

    return ScrapedArticle(
        url=url,
        scrape_error="Failed to extract article content from this URL.",
    )


def scrape_articles(urls: list[str]) -> list[ScrapedArticle]:
    results = []
    for url in urls:
        if not url.strip():
            continue
        logger.info(f"Scraping: {url}")
        article = scrape_article(url)
        results.append(article)
    return results
