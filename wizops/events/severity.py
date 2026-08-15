from __future__ import annotations
import json
import re

SEVERITIES = ("TRACE", "DEBUG", "INFO", "WARN", "ERROR", "FATAL")

_KEY_VALUE_LEVEL = re.compile(r'(?:^|\s)level=(TRACE|DEBUG|INFO|WARN|WARNING|ERROR|FATAL|PANIC)(?:\s|$)', re.I)

_EXPLICIT = (
    ("FATAL", re.compile(r"(?:^|[\s:\-\[\]])(?:FATAL|PANIC)(?:$|[\s:\-\[\]])", re.I)),
    ("ERROR", re.compile(r"(?:^|[\s:\-\[\]])ERROR(?:$|[\s:\-\[\]])", re.I)),
    ("WARN", re.compile(r"(?:^|[\s:\-\[\]])WARN(?:ING)?(?:$|[\s:\-\[\]])", re.I)),
    ("DEBUG", re.compile(r"(?:^|[\s:\-\[\]])DEBUG(?:$|[\s:\-\[\]])", re.I)),
    ("TRACE", re.compile(r"(?:^|[\s:\-\[\]])TRACE(?:$|[\s:\-\[\]])", re.I)),
)
_FATAL_SIGNALS = re.compile(r"\b(segfault|segmentation fault|fatal error|panic)\b", re.I)
_ERROR_SIGNALS = re.compile(
    r"\b(authenticationerror|permission denied|out of memory|cuda allocation failure|"
    r"request failed|pipeline failed|file embedding failed|execution error|"
    r"invalid_api_key|incorrect api key|401 unauthorized|403 forbidden|"
    r"connection refused|uncaught exception|unhandled exception)\b", re.I
)
_WARN_SIGNALS = re.compile(r"\b(unhealthy|deprecated|timed out|timeout|retrying)\b", re.I)

def _json_severity(text: str) -> str | None:
    stripped=text.lstrip()
    if not stripped.startswith("{"):
        return None
    try:
        value=json.loads(stripped)
    except (json.JSONDecodeError, TypeError):
        return None
    marker=value.get("s") if isinstance(value, dict) else None
    return {"F":"FATAL","E":"ERROR","W":"WARN","I":"INFO","D":"DEBUG"}.get(marker)

def parse_severity(text: str) -> str:
    structured=_json_severity(text)
    if structured:
        return structured
    kv_level=_KEY_VALUE_LEVEL.search(text)
    if kv_level:
        level=kv_level.group(1).upper()
        return {"WARNING":"WARN","PANIC":"FATAL"}.get(level, level)
    for severity, pattern in _EXPLICIT:
        if pattern.search(text):
            return severity
    if _FATAL_SIGNALS.search(text):
        return "FATAL"
    if _ERROR_SIGNALS.search(text):
        return "ERROR"
    if _WARN_SIGNALS.search(text):
        return "WARN"
    return "INFO"
