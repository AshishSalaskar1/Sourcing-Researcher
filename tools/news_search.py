import asyncio
import logging

from ddgs import DDGS

logger = logging.getLogger("supply_risk_radar.news_search")


async def search_public_news(query: str, limit: int = 5) -> dict:
    """Search recent public news articles with no signup or API key required."""

    def _search_news() -> list[dict]:
        logger.info("DDGS news search start query=%r limit=%s", query, limit)
        with DDGS() as ddgs:
            return ddgs.news(query, max_results=limit)

    def _search_text() -> list[dict]:
        logger.info("DDGS text search fallback start query=%r limit=%s", query, limit)
        with DDGS() as ddgs:
            return ddgs.text(query, max_results=limit)

    try:
        results = await asyncio.wait_for(asyncio.to_thread(_search_news), timeout=20)
        logger.info("DDGS news search returned %s results for query=%r", len(results), query)
        articles = [
            {
                "title": item.get("title", ""),
                "date": item.get("date", ""),
                "source": item.get("source", ""),
                "url": item.get("url", ""),
                "summary": item.get("body", ""),
            }
            for item in results
        ]
        return {
            "query": query,
            "count": len(articles),
            "articles": articles,
            "search_mode": "news",
        }
    except TimeoutError as exc:
        logger.exception("DDGS news search timed out for query=%r", query)
        raise RuntimeError(
            f"Public news search timed out for query '{query}' after 20 seconds"
        ) from exc
    except Exception as exc:
        logger.warning(
            "DDGS news search failed for query=%r, falling back to text search: %s",
            query,
            exc,
        )
        news_error = f"{type(exc).__name__}: {exc}"

    try:
        results = await asyncio.wait_for(asyncio.to_thread(_search_text), timeout=20)
        logger.info("DDGS text fallback returned %s results for query=%r", len(results), query)
        articles = [
            {
                "title": item.get("title", ""),
                "date": "",
                "source": "",
                "url": item.get("href", ""),
                "summary": item.get("body", ""),
            }
            for item in results
        ]
        return {
            "query": query,
            "count": len(articles),
            "articles": articles,
            "search_mode": "text_fallback",
            "warning": f"News search failed and text search was used instead: {news_error}",
        }
    except TimeoutError as exc:
        logger.exception("DDGS text fallback timed out for query=%r", query)
        return {
            "query": query,
            "count": 0,
            "articles": [],
            "search_mode": "unavailable",
            "warning": (
                f"News search failed ({news_error}) and text fallback timed out after 20 seconds: "
                f"{type(exc).__name__}: {exc}"
            ),
        }
    except Exception as exc:
        logger.exception("DDGS text fallback failed for query=%r", query)
        return {
            "query": query,
            "count": 0,
            "articles": [],
            "search_mode": "unavailable",
            "warning": (
                f"News search failed ({news_error}) and text fallback also failed: "
                f"{type(exc).__name__}: {exc}"
            ),
        }
