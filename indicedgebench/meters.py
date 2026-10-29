"""Resource meters: peak memory (sampled) and energy (measured or estimated).

Energy sources, best first:
  * Linux + Intel/AMD: RAPL package counter (/sys/class/powercap/intel-rapl:0/energy_uj) -> "rapl"
  * everywhere else (Windows, macOS): process CPU-seconds x per-core share of TDP -> "estimated"
The method is recorded next to every number so estimated and measured values are never mixed silently.
"""

from __future__ import annotations

import platform
import threading
import time
from pathlib import Path

import psutil

RAPL_FILE = Path("/sys/class/powercap/intel-rapl:0/energy_uj")
RAPL_MAX_FILE = Path("/sys/class/powercap/intel-rapl:0/max_energy_range_uj")


def default_tdp_watts() -> float:
    """Rough sustained package power under all-core load."""
    if platform.system() == "Darwin" and platform.machine() == "arm64":
        return 20.0  # Apple M-series base chips, CPU cluster under load
    return 45.0  # Intel 12th-gen H-series base power


class PeakMemorySampler:
    """Samples this process's RSS in a background thread; also uses OS peak counters when present."""

    def __init__(self, interval_s: float = 0.02):
        self.proc = psutil.Process()
        self.interval_s = interval_s
        self.peak = 0
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.is_set():
            self.peak = max(self.peak, self.proc.memory_info().rss)
            time.sleep(self.interval_s)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join()

    @property
    def peak_mb(self) -> float:
        peak = self.peak
        os_peak = getattr(self.proc.memory_info(), "peak_wset", None)  # Windows peak working set
        if os_peak:
            peak = max(peak, os_peak)
        return peak / 2**20


class EnergyMeter:
    """Energy over a code region: `with EnergyMeter(tdp, cores) as m: ...; m.joules`."""

    def __init__(self, tdp_watts: float | None, n_cores: int):
        self.tdp = tdp_watts or default_tdp_watts()
        self.n_cores = max(1, n_cores)
        self.proc = psutil.Process()
        self.method = "rapl" if self._rapl_readable() else "estimated"
        self.joules = 0.0
        self.wall_s = 0.0
        self.cpu_s = 0.0

    @staticmethod
    def _rapl_readable() -> bool:
        try:
            int(RAPL_FILE.read_text())
            return True
        except Exception:
            return False

    def _cpu_seconds(self) -> float:
        t = self.proc.cpu_times()
        return t.user + t.system

    def __enter__(self):
        self._t0 = time.perf_counter()
        self._c0 = self._cpu_seconds()
        if self.method == "rapl":
            self._e0 = int(RAPL_FILE.read_text())
        return self

    def __exit__(self, *exc):
        self.wall_s = time.perf_counter() - self._t0
        self.cpu_s = self._cpu_seconds() - self._c0
        if self.method == "rapl":
            e1 = int(RAPL_FILE.read_text())
            if e1 < self._e0:  # counter wrapped
                e1 += int(RAPL_MAX_FILE.read_text())
            self.joules = (e1 - self._e0) / 1e6
        else:
            # Each fully-busy core is charged an equal share of package TDP.
            self.joules = self.cpu_s * self.tdp / self.n_cores
