import json
from datetime import date
from pathlib import Path
from urllib.request import urlopen


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


def count_conda(package, channel, path):
    """Download count for the Anaconda distribution."""
    conda_api = urlopen(f"https://api.anaconda.org/package/{channel}/{package}")
    conda_json = json.loads(conda_api.read())
    count = sum(entry["ndownloads"] for entry in conda_json["files"])
    archive = _read_archive(path)
    _append(archive, count)
    _write_archive(path, archive)
    return count


def count_pypi(package, path):
    """Download count for the PyPI distribution."""
    pypi_api = urlopen(f"https://pypistats.org/api/packages/{package}/overall")
    pypi_json = json.loads(pypi_api.read())
    archive = _read_archive(path)
    for data in pypi_json["data"]:
        if all([d["category"] != data["category"] or d["date"] != data["date"] for d in archive]):
            archive.append(data)
    archive.sort(key=lambda x: f"{x['category']}{x['date']}")
    _write_archive(path, archive)
    return sum(d["downloads"] for d in archive if d["category"] == "without_mirrors")


if __name__ == "__main__":
    archives = Path("archives").resolve(True)
    _write_archive(archives / "total.json", {
        "conda": count_conda("cobyqa", "conda-forge", archives / "conda.json"),
        "pypi": count_pypi("cobyqa", archives / "pypi.json"),
    })
