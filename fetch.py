import json
import traceback
import warnings
from datetime import date
from pathlib import Path

import condastats.cli
import pypistats


def _read_archive(path):
    try:
        with open(path, "r") as f:
            archive = json.load(f)
    except FileNotFoundError:
        archive = []
    return archive


def _write_archive(path, archive):
    with open(path, "w") as f:
        json.dump(archive, f, indent=4)


def _append(archive, count):
    today = date.today().strftime("%Y-%m-%d")
    if today not in {entry["date"] for entry in archive}:
        prev_count = sum(map(lambda d: d["downloads"], archive))
        archive.append({"date": today, "downloads": count - prev_count})


def count_conda(package, path):
    """Download count for the Anaconda distribution."""
    archive = _read_archive(path)
    try:
        count = int(condastats.cli.overall(package))
    except ValueError as exc:
        count = sum(map(lambda d: d["downloads"], archive))
        warnings.warn(f"Could not fetch conda download count: {exc}\n{traceback.format_exc()}", RuntimeWarning)
    _append(archive, count)
    _write_archive(path, archive)
    return count


def count_pypi(package, path):
    """Download count for the PyPI distribution."""
    df = pypistats.overall(package, total=True, format="pandas")
    archive = _read_archive(path)
    for _, data in df.iterrows():
        if data["category"] != "Total" and all([d["category"] != data["category"] or d["date"] != data["date"] for d in archive]):
            data_util = data.to_dict()
            data_util.pop("percent")
            archive.append(data_util)
    archive.sort(key=lambda x: f"{x['category']}{x['date']}")
    _write_archive(path, archive)
    return sum(d["downloads"] for d in archive if d["category"] == "without_mirrors")


if __name__ == "__main__":
    archives = Path("archives").resolve(True)
    _write_archive(archives / "total.json", {
        "conda": count_conda("cobyqa", archives / "conda.json"),
        "pypi": count_pypi("cobyqa", archives / "pypi.json"),
    })
