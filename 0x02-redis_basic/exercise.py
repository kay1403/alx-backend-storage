#!/usr/bin/env python3
"""This module provides a Cache class for interacting with Redis.
It supports storing values, retrieving them with optional conversion,
tracking function call counts, and recording function call history.
"""

import redis
import uuid
from typing import Union, Callable, Optional
from functools import wraps


def count_calls(method: Callable) -> Callable:
    """Decorator that counts how many times a method is called."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        key = method.__qualname__
        self._redis.incr(key)
        return method(self, *args, **kwargs)
    return wrapper


def call_history(method: Callable) -> Callable:
    """Decorator that stores the history of inputs and outputs for a function."""
    @wraps(method)
    def wrapper(self, *args, **kwargs):
        key = method.__qualname__
        input_key = f"{key}:inputs"
        output_key = f"{key}:outputs"
        self._redis.rpush(input_key, str(args))
        result = method(self, *args, **kwargs)
        self._redis.rpush(output_key, str(result))
        return result
    return wrapper


def replay(method: Callable):
    """Display the history of calls of a particular function."""
    r = method.__self__._redis
    key = method.__qualname__
    inputs = r.lrange(f"{key}:inputs", 0, -1)
    outputs = r.lrange(f"{key}:outputs", 0, -1)
    print(f"{key} was called {len(inputs)} times:")
    for i, o in zip(inputs, outputs):
        print(f"{key}(*{i.decode('utf-8')}) -> {o.decode('utf-8')}")


class Cache:
    """Cache class to interact with Redis for storing and retrieving data."""
    def __init__(self):
        """Initialize the Redis client and flush the database."""
        self._redis = redis.Redis()
        self._redis.flushdb()

    @call_history
    @count_calls
    def store(self, data: Union[str, bytes, int, float]) -> str:
        """Store data in Redis using a randomly generated key."""
        key = str(uuid.uuid4())
        self._redis.set(key, data)
        return key

    def get(self,
            key: str,
            fn: Optional[Callable] = None) -> Union[str, bytes, int, float, None]:
        """Retrieve data from Redis and optionally convert it using fn."""
        value = self._redis.get(key)
        if value is None:
            return None
        return fn(value) if fn else value

    def get_str(self, key: str) -> str:
        """Retrieve a string from Redis."""
        return self.get(key, fn=lambda d: d.decode("utf-8"))

    def get_int(self, key: str) -> int:
        """Retrieve an integer from Redis."""
        return self.get(key, fn=int)
