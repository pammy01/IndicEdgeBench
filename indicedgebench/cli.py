"""Command line: `python -m indicedgebench <command> ...`"""

from __future__ import annotations

import argparse
import json
import logging

from .config import load_config


def main(argv=None):
    p = argparse.ArgumentParser(prog="indicedgebench", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("info", help="print hardware/software fingerprint and data access status")
    for name, help_ in [("download", "download all GGUF files in a config"),
                        ("prepare", "freeze the sampled item set for a config"),
                        ("run", "run the full sweep, then write the report")]:
        sp = sub.add_parser(name, help=help_)
        sp.add_argument("config")
        if name == "run":
            sp.add_argument("--force", action="store_true", help="re-run configs that already finished")
            sp.add_argument("--models", nargs="*", help="only these model names")
            sp.add_argument("--quants", nargs="*", help="only these quant labels")
    sp = sub.add_parser("report", help="(re)build summary.csv, plots and REPORT.md for a run directory")
    sp.add_argument("run_dir")

    args = p.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s", datefmt="%H:%M:%S")

    if args.cmd == "info":
        from . import sysinfo
        from .data import get_hf_token

        info = sysinfo.collect()
        info["hf_token"] = "found (MILU enabled)" if get_hf_token() else "missing (fallback set will be used)"
        print(json.dumps(info, indent=2))
    elif args.cmd == "download":
        from .runner import download

        download(load_config(args.config))
    elif args.cmd == "prepare":
        from .runner import prepare

        print(prepare(load_config(args.config)))
    elif args.cmd == "run":
        from .report import report
        from .runner import run

        run_dir = run(load_config(args.config), args.force, args.models, args.quants)
        print(report(run_dir))
    elif args.cmd == "report":
        from .report import report

        print(report(args.run_dir))


if __name__ == "__main__":
    main()
