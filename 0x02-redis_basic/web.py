#!/usr/bin/env python3
"""This module implements a simple caching mechanism for web pages
using Redis, with automatic expiration and access tracking.
"""

import redis
import requests
from typing import Callable
from functools import wraps


r = redis.Redis()


def count_url_access(method: Callable) -> Callable:
    """Decorator that counts URL accesses and caches responses."""
    @wraps(method)
    def wrapper(url: str) -> str:
        count_key = f"count:{url}"
        cache_key = f"cache:{url}"

        r.incr(count_key)
        cached = r.get(cache_key)
        if cached:
            return cached.decode("utf-8")

        result = method(url)
        r.setex(cache_key, 10, result)
        return result
    return wrapper


@count_url_access
def get_page(url: str) -> str:
    """Fetches the HTML content of a URL, caches it, and counts access."""
    response = requests.get(url)
    return response.text
