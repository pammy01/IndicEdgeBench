"""Hardware/software fingerprint saved with every run, for reproducibility."""

from __future__ import annotations

import platform
import subprocess
import sys
from pathlib import Path

import psutil


def cpu_brand() -> str:
    try:
        import cpuinfo

        return cpuinfo.get_cpu_info().get("brand_raw") or platform.processor()
    except Exception:
        return platform.processor() or platform.machine()


def git_commit() -> str | None:
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"], cwd=Path(__file__).parent,
            stderr=subprocess.DEVNULL, text=True).strip()
    except Exception:
        return None


def collect() -> dict:
    try:
        import llama_cpp

        llama_version = llama_cpp.__version__
    except Exception:
        llama_version = None
    return {
        "os": f"{platform.system()} {platform.release()}",
        "machine": platform.machine(),
        "cpu": cpu_brand(),
        "physical_cores": psutil.cpu_count(logical=False),
        "logical_cores": psutil.cpu_count(logical=True),
        "ram_gb": round(psutil.virtual_memory().total / 2**30, 1),
        "python": sys.version.split()[0],
        "llama_cpp_python": llama_version,
        "git_commit": git_commit(),
    }
