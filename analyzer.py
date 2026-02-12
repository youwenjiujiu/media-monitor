from __future__ import annotations

import logging
import time
from openai import OpenAI
from models import ScrapedArticle, ArticleAnalysis, AnalyzedArticle, ClientConfig
from config import OPENAI_API_KEY, OPENAI_MODEL

logger = logging.getLogger(__name__)

MAX_TEXT_LENGTH = 12000


def _build_system_prompt(config: ClientConfig) -> str:
    return f"""You are a media monitoring analyst for a PR agency. Your client is {config.client_name}.

Client keywords: {', '.join(config.keywords)}
Competitors: {', '.join(config.competitors)}
Target markets: {', '.join(config.markets)}
Industry keywords: {', '.join(config.industry_keywords)}

Analyze the given news article and classify it:
- category: "client" if it directly mentions the client, "competitor" if it mentions a competitor, or "industry" for general industry news
- sentiment: "Positive", "Negative", or "Neutral" from the client's perspective
- summary: 2-3 sentence summary of the article's key points relevant to the client
- headline: the article's headline
- source: the publication/media outlet name
- date: publication date in YYYY-MM-DD format (use today's date if unknown)
- geographic_location: primary geographic focus (e.g. "Singapore", "Hong Kong", "Global")
- competitor_name: if category is "competitor", which competitor is mentioned (must match one from the list exactly); null otherwise"""


def analyze_article(
    client: OpenAI, article: ScrapedArticle, config: ClientConfig
) -> AnalyzedArticle:
    if article.scrape_error or not article.text:
        return AnalyzedArticle(
            url=article.url,
            scraped=article,
            analysis_error=article.scrape_error or "No article text available.",
        )

    text = article.text[:MAX_TEXT_LENGTH]

    user_content = f"URL: {article.url}\n"
    if article.headline:
        user_content += f"Headline: {article.headline}\n"
    if article.source:
        user_content += f"Source: {article.source}\n"
    if article.date:
        user_content += f"Date: {article.date}\n"
    user_content += f"\nArticle text:\n{text}"

    try:
        completion = client.beta.chat.completions.parse(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": _build_system_prompt(config)},
                {"role": "user", "content": user_content},
            ],
            response_format=ArticleAnalysis,
        )

        analysis = completion.choices[0].message.parsed

        return AnalyzedArticle(
            url=article.url,
            scraped=article,
            analysis=analysis,
        )
    except Exception as e:
        logger.error(f"OpenAI analysis failed for {article.url}: {e}")
        return AnalyzedArticle(
            url=article.url,
            scraped=article,
            analysis_error=str(e),
        )


def analyze_articles(
    articles: list[ScrapedArticle], config: ClientConfig
) -> list[AnalyzedArticle]:
    client = OpenAI(api_key=OPENAI_API_KEY)
    results = []

    for i, article in enumerate(articles):
        logger.info(f"Analyzing ({i+1}/{len(articles)}): {article.url}")
        result = analyze_article(client, article, config)
        results.append(result)

        # Rate limit: 0.5s between calls
        if i < len(articles) - 1:
            time.sleep(0.5)

    return results
