import json
from datetime import date
from pathlib import Path

import condastats.cli
import pypistats
from github import Github


def _write_archive(path, counts):
    try:
        with open(path, "r") as f:
            archive = json.load(f)
    except FileNotFoundError:
        archive = []
    today = date.today().strftime("%Y-%m-%d")
    if today not in {entry["date"] for entry in archive}:
        prev_count = sum(map(lambda d: d["downloads"], archive))
        archive.append({"date": today, "downloads": counts - prev_count})
    with open(path, "w") as f:
        json.dump(archive, f, indent=4)


def count_github(user, package, path):
    """Download count for the GitHub repository."""
    repo = Github().get_repo(f"{user}/{package}")
    total = sum(sum(map(lambda d: d.download_count, release.get_assets())) for release in repo.get_releases())
    _write_archive(path, total)
    return total


def count_conda(package, path):
    """Download count for the Anaconda distribution."""
    total = int(condastats.cli.overall(package))
    _write_archive(path, total)
    return total


def count_pypi(package, path):
    """Download count for the PyPI distribution."""
    df = pypistats.overall(package, total=True, format="pandas")
    with open(path, "r") as f:
        archive = json.load(f)
    for _, data in df.iterrows():
        if data["category"] != "Total" and all([d["category"] != data["category"] or d["date"] != data["date"] for d in archive]):
            data_util = data.to_dict()
            data_util.pop("percent")
            archive.append(data_util)
    archive.sort(key=lambda x: f"{x['category']}{x['date']}")
    with open(path, "w") as f:
        json.dump(archive, f, indent=4)
    return sum(d["downloads"] for d in archive if d["category"] == "without_mirrors")


if __name__ == "__main__":
    archives = Path("archives").resolve(True)
    with open(archives / "total.json", "w") as f:
        json.dump({
            "github": count_github("cobyqa", "cobyqa", archives / "github.json"),
            "pypi": count_pypi("cobyqa", archives / "pypi.json"),
        }, f, indent=4)
