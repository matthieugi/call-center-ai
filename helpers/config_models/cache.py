from enum import Enum
from functools import cache

from pydantic import BaseModel, Field, SecretStr, ValidationInfo, field_validator

from persistence.icache import ICache


class ModeEnum(str, Enum):
    MEMORY = "memory"
    REDIS = "redis"


class MemoryModel(BaseModel, frozen=True):
    max_size: int = Field(default=100, ge=10)

    @cache
    def instance(self) -> ICache:
        from persistence.memory import (
            MemoryCache,
        )

        return MemoryCache(self)


class RedisModel(BaseModel, frozen=True):
    database: int = Field(default=0, ge=0)
    host: str
    password: SecretStr
    port: int = 6379
    ssl: bool = True

    @cache
    def instance(self) -> ICache:
        from persistence.redis import (
            RedisCache,
        )

        return RedisCache(self)


class CacheModel(BaseModel):
    memory: MemoryModel | None = MemoryModel()  # Object is fully defined by default
    mode: ModeEnum = ModeEnum.MEMORY
    redis: RedisModel | None = None

    @field_validator("redis")
    @classmethod
    def _validate_sqlite(
        cls,
        redis: RedisModel | None,
        info: ValidationInfo,
    ) -> RedisModel | None:
        if not redis and info.data.get("mode", None) == ModeEnum.REDIS:
            raise ValueError("Redis config required")
        return redis

    @field_validator("memory")
    @classmethod
    def _validate_memory(
        cls,
        memory: MemoryModel | None,
        info: ValidationInfo,
    ) -> MemoryModel | None:
        if not memory and info.data.get("mode", None) == ModeEnum.MEMORY:
            raise ValueError("Memory config required")
        return memory

    def instance(self) -> ICache:
        if self.mode == ModeEnum.MEMORY:
            assert self.memory
            return self.memory.instance()

        assert self.redis
        return self.redis.instance()
