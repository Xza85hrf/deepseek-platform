import os
from dotenv import load_dotenv

load_dotenv()

class RedisConfig:
    """Configuration for Redis connection"""
    
    HOST = os.getenv('REDIS_HOST', 'localhost')
    PORT = int(os.getenv('REDIS_PORT', 6379))
    DB = int(os.getenv('REDIS_DB', 0))
    PASSWORD = os.getenv('REDIS_PASSWORD', None)
    SSL = os.getenv('REDIS_SSL', 'false').lower() == 'true'
    TIMEOUT = int(os.getenv('REDIS_TIMEOUT', 5))
    CACHE_TTL = int(os.getenv('REDIS_CACHE_TTL', 3600))  # 1 hour default
    
    @classmethod
    def get_connection_url(cls) -> str:
        """Get Redis connection URL"""
        if cls.PASSWORD:
            return f"redis://:{cls.PASSWORD}@{cls.HOST}:{cls.PORT}/{cls.DB}"
        return f"redis://{cls.HOST}:{cls.PORT}/{cls.DB}"
