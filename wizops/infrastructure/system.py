from __future__ import annotations

import os
import shutil
import socket
import subprocess
from pathlib import Path

from wizops.application.models import SystemStatus


def _cmd(args: list[str]) -> str:
    try:
        return subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=1.5,
        ).stdout.strip()
    except Exception:
        return ""


def probe_system(
    collectors_active: int,
) -> SystemStatus:

    load1 = (
        os.getloadavg()[0]
        if hasattr(os, "getloadavg")
        else 0.0
    )

    mem_total = None
    mem_avail = None

    try:
        info = {}

        for line in Path("/proc/meminfo").read_text().splitlines():
            key, value = line.split(":", 1)
            info[key] = int(value.strip().split()[0]) * 1024

        mem_total = info.get("MemTotal")
        mem_avail = info.get("MemAvailable")

    except Exception:
        pass

    docker = _cmd(["docker", "ps", "-q"]).splitlines()

    loaded = _cmd(["ollama", "ps"]).splitlines()

    nvidia = _cmd([
        "nvidia-smi",
        "--query-gpu=memory.used,memory.total",
        "--format=csv,noheader,nounits",
    ])

    gpu_used = None
    gpu_total = None

    if nvidia:
        try:
            gpu_used, gpu_total = [
                float(x.strip())
                for x in nvidia.splitlines()[0].split(",")[:2]
            ]
        except Exception:
            pass

    disk = shutil.disk_usage("/")

    return SystemStatus(
        load1=load1,
        mem_total=mem_total or 0,
        mem_avail=mem_avail or 0,
        gpu_used=gpu_used,
        gpu_total=gpu_total,
        disk_used=disk.used,
        disk_total=disk.total,
        hostname=socket.gethostname(),
        container_count=len(docker),
        loaded_models=max(0, len(loaded) - 1),
        collectors_active=collectors_active,
    )
