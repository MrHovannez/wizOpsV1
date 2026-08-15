import json
import re
from datetime import datetime

def clean_timestamp(value: str | None) -> str:
    return (value or "").replace("Z", "")


def human_size(size: int) -> str:
    units = ["B", "KB", "MB", "GB", "TB"]
    value = float(size)

    for unit in units:
        if value < 1024 or unit == units[-1]:
            if unit == "B":
                return f"{int(value)} {unit}"
            return f"{value:.1f} {unit}"
        value /= 1024

_ANSI=re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
_LEVEL=re.compile(r'^time=\S+\s+level=\w+\s+source=\S+\s+msg=(?:"([^"]*)"|(\S.*?))(?=\s+\w+=|$)')
_GIN=re.compile(r'^\[GIN\]\s+\S+\s+-\s+\S+\s+\|\s+(\d+)\s+\|\s+([^|]+)\|\s+([^|]+)\|\s+(\S+)\s+"([^"]+)"')
SEVS=("ATTENTION",None,"TRACE","DEBUG","INFO","WARN","ERROR","FATAL")
COLORS={"FATAL":"bold white on #d000ff","ERROR":"bold #ff416c","WARN":"bold #ffb000","INFO":"#00d9ff","DEBUG":"dim","TRACE":"dim"}

def local_timestamp(value: str, fmt="%Y-%m-%d %H:%M:%S") -> str:
    """Convert a stored UTC ISO8601 timestamp to local system time."""
    if not value:
        return ""
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return dt.astimezone().strftime(fmt)
    except Exception:
        return value

def clean(value: str) -> str:
    return _ANSI.sub("", str(value or "")).replace("\r", "")

def summary(message, limit=190):
    text=clean(message).replace("\n"," ↵ ")
    m=_LEVEL.match(text)
    if m:
        text=(m.group(1) or m.group(2) or "").strip()
        raw=clean(message)
        if " error=" in raw:
            err=raw.split(" error=",1)[1].strip().strip('"').replace("\\n"," · ")
            text+=f" — {err}"
    else:
        m=_GIN.match(text)
        if m:
            status,latency,client,method,path=m.groups()
            text=f"{method} {path} → {status} in {latency.strip()} from {client.strip()}"
        elif text.startswith("{"):
            try:
                obj=json.loads(text); msg=obj.get("msg") or obj.get("message")
                if msg: text=str(msg)
            except Exception: pass
    return text if len(text)<=limit else text[:limit-1]+"…"

def pretty_raw(raw):
    raw=clean(raw)
    try: return json.dumps(json.loads(raw),indent=2,ensure_ascii=False)
    except Exception: return raw
