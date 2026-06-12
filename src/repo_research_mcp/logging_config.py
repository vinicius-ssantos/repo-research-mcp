from __future__ import annotations

import contextvars
import json
import logging
import uuid

_request_id: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")

_EXTRA_FIELDS = ("tool", "repository", "duration_ms", "result_count", "error_type", "request_id")


def new_request_id() -> str:
    rid = str(uuid.uuid4())[:8]
    _request_id.set(rid)
    return rid


def get_request_id() -> str:
    return _request_id.get()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        data: dict[str, object] = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        rid = get_request_id()
        if rid:
            data["request_id"] = rid
        for key in _EXTRA_FIELDS:
            if hasattr(record, key) and key != "request_id":
                data[key] = getattr(record, key)
        if record.exc_info:
            data["exc"] = self.formatException(record.exc_info)
        return json.dumps(data)


def configure_logging(fmt: str = "json") -> None:
    handler = logging.StreamHandler()
    if fmt == "json":
        handler.setFormatter(JsonFormatter())
    logging.basicConfig(level=logging.WARNING, handlers=[handler], force=True)
