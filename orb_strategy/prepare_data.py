"""Download free 1-minute US index data and cut it down to regular-hours sessions.

Source: github.com/FutureSharks/financial-data (Oanda CFD minute bars, UTC, mid prices,
2005 - May 2020) for SPX500_USD, NAS100_USD and US2000_USD.

Usage:  python prepare_data.py [data_dir]
Writes  <data_dir>/<SYMBOL>.pkl  (1-minute bars, 09:30-15:59 America/New_York).
"""
from __future__ import annotations

import glob
import subprocess
import sys
from pathlib import Path

import pandas as pd

REPO = "https://github.com/FutureSharks/financial-data.git"
SUBDIR = "pyfinancialdata/data/currencies/oanda"
SYMBOLS = ["SPX500_USD", "NAS100_USD", "US2000_USD"]


def fetch(data_dir: Path) -> Path:
    clone = data_dir / "fd"
    if not clone.exists():
        subprocess.run(["git", "clone", "--filter=blob:none", "--no-checkout", "--depth", "1",
                        REPO, str(clone)], check=True)
        subprocess.run(["git", "sparse-checkout", "init", "--cone"], cwd=clone, check=True)
        subprocess.run(["git", "sparse-checkout", "set", *[f"{SUBDIR}/{s}" for s in SYMBOLS]],
                       cwd=clone, check=True)
        subprocess.run(["git", "checkout", "master"], cwd=clone, check=True)
    return clone / SUBDIR


def load_rth(sym_dir: Path) -> pd.DataFrame:
    files = sorted(glob.glob(str(sym_dir / "*" / "*.csv")))
    df = pd.concat((pd.read_csv(f) for f in files), ignore_index=True)
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.drop_duplicates("time").set_index("time").sort_index()
    df.index = df.index.tz_convert("America/New_York")
    df = df.between_time("09:30", "15:59")[["open", "high", "low", "close", "volume"]]
    return df[df.index.dayofweek < 5]


if __name__ == "__main__":
    data_dir = Path(sys.argv[1] if len(sys.argv) > 1 else "data")
    data_dir.mkdir(parents=True, exist_ok=True)
    src = fetch(data_dir)
    for sym in SYMBOLS:
        df = load_rth(src / sym)
        df.to_pickle(data_dir / f"{sym}.pkl")
        print(sym, len(df), df.index[0], df.index[-1])
