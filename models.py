from __future__ import annotations

from pydantic import BaseModel
from typing import Optional


class ScrapedArticle(BaseModel):
    url: str
    headline: Optional[str] = None
    text: Optional[str] = None
    source: Optional[str] = None
    date: Optional[str] = None
    is_paywalled: bool = False
    scrape_error: Optional[str] = None


class ArticleAnalysis(BaseModel):
    category: str  # "client", "competitor", or "industry"
    sentiment: str  # "Positive", "Negative", "Neutral"
    summary: str
    headline: str
    source: str
    date: str
    geographic_location: Optional[str] = None
    competitor_name: Optional[str] = None


class AnalyzedArticle(BaseModel):
    url: str
    scraped: ScrapedArticle
    analysis: Optional[ArticleAnalysis] = None
    analysis_error: Optional[str] = None


class ClientConfig(BaseModel):
    client_name: str
    keywords: list[str]
    competitors: list[str]
    markets: list[str]
    industry_keywords: list[str]
