from redis.asyncio import Redis
from enum import Enum, auto
from typing import Optional, Dict, Any
from threading import Lock
from datetime import datetime
from dataclasses import dataclass
from config.redis_config import RedisConfig
import json
import logging

logger = logging.getLogger(__name__)


class EngineerState(Enum):
    IDLE = auto()
    THINKING = auto()
    WORKING = auto()
    ERROR = auto()
    QUESTION = auto()


@dataclass
class UsageStats:
    total_requests: int = 0
    total_tokens: int = 0
    total_cost: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    last_request_time: Optional[datetime] = None


class StateManager:
    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._state = EngineerState.IDLE
                    cls._instance.redis_client = None
        return cls._instance

    def __init__(self):
        if not hasattr(self, "_initialized"):
            self._usage_stats = UsageStats()
            self._initialized = True
            self._memory_cache = {}

    async def init_redis(self):
        """Initialize Redis connection with immediate fallback to in-memory cache"""
        if self.redis_client is not None:
            return

        # Default to in-memory cache
        self.redis_client = None
        logger.info("Using in-memory cache by default")

        # Try Redis connection in the background without blocking
        try:
            url = RedisConfig.get_connection_url()
            if RedisConfig.SSL:
                url = url.replace("redis://", "rediss://")

            redis_client = Redis.from_url(
                url,
                socket_timeout=1,  # Reduce timeout to 1 second
                decode_responses=True,
            )
            # Quick connection test
            await redis_client.ping()
            self.redis_client = redis_client
            logger.info("Connected to Redis server")
        except Exception as e:
            logger.warning(
                f"Redis connection failed: {e}. Continuing with in-memory cache."
            )

    @property
    def state(self) -> EngineerState:
        return self._state

    @state.setter
    def state(self, new_state: EngineerState):
        with self._lock:
            self._state = new_state

    async def get_cached_response(self, cache_key: str) -> Optional[Any]:
        """Get cached response from Redis if it exists"""
        if not self.redis_client:
            return None

        try:
            cached_data = await self.redis_client.get(cache_key)
            if cached_data:
                self._usage_stats.cache_hits += 1
                return json.loads(cached_data)
            self._usage_stats.cache_misses += 1
            return None
        except Exception as e:
            logger.error(f"Error getting cached response: {e}")
            return None

    async def cache_response(self, cache_key: str, response: Any) -> None:
        """Store response in Redis cache"""
        if not self.redis_client:
            return

        try:
            serialized = json.dumps(response)
            await self.redis_client.setex(cache_key, RedisConfig.CACHE_TTL, serialized)
        except Exception as e:
            logger.error(f"Error caching response: {e}")

    def update_usage_stats(self, tokens_used: int, cost: float) -> None:
        """Update usage statistics"""
        with self._lock:
            self._usage_stats.total_requests += 1
            self._usage_stats.total_tokens += tokens_used
            self._usage_stats.total_cost += cost
            self._usage_stats.last_request_time = datetime.now()

    def get_usage_stats(self) -> UsageStats:
        """Get current usage statistics"""
        with self._lock:
            return self._usage_stats

    async def clear_cache(self) -> None:
        """Clear the Redis cache"""
        if self.redis_client:
            try:
                await self.redis_client.flushdb()
            except Exception as e:
                logger.error(f"Error clearing cache: {e}")


def get_state_manager() -> StateManager:
    return StateManager()
