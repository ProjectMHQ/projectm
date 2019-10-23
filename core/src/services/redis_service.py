from flask import json

from core.src.services.abstracts import RedisServiceAbstract


class RedisServiceBase(RedisServiceAbstract):
    @staticmethod
    def _redis_to_json(data: bytes) -> dict:
        return json.loads(data.decode())

    @staticmethod
    def _json_to_redis(data: dict) -> bytes:
        return json.dumps(data).encode()
