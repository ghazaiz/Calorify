"""Build and verify versioned Calorify source archives."""

import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import runpy
import subprocess
from zipfile import ZIP_DEFLATED, ZipFile, ZipInfo


ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = {"main.py", "requirements.txt", "README.md", "CHANGELOG.md", ".env.example"}
SOURCE_SUFFIXES = {
    "app": {".py", ".html", ".css", ".js", ".svg", ".png", ".jpg", ".webp", ".ico"},
    "deployment": {".py", ".sh", ".conf", ".service", ".timer", ".example"},
    "docs": {".md"},
}
MANIFEST = "release.json"


def allowed(name):
    path = PurePosixPath(name)
    if path.is_absolute() or path.as_posix() != name or "\\" in name or ":" in name or ".." in path.parts:
        return False
    if len(path.parts) == 1:
        return name in ROOT_FILES or name == MANIFEST
    return all(not part.startswith(".") and part != "__pycache__" for part in path.parts) and (
        path.suffix in SOURCE_SUFFIXES.get(path.parts[0], set())
    )


def digest(path):
    with path.open("rb") as data:
        return hashlib.file_digest(data, "sha256").hexdigest()


def build(output, clean):
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    dirty = bool(subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT))
    if clean and dirty:
        raise ValueError("A release must be built from a clean Git checkout.")
    version = runpy.run_path(str(ROOT / "app/version.py"))["APP_VERSION"]
    output.mkdir(parents=True, exist_ok=True)
    archive = output / f"calorify-{version}-{commit[:12]}.zip"
    files = [ROOT / name for name in ROOT_FILES]
    for folder in SOURCE_SUFFIXES:
        files.extend(path for path in (ROOT / folder).rglob("*") if path.is_file())
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for path in sorted(files):
            name = path.relative_to(ROOT).as_posix()
            if allowed(name):
                if path.is_symlink() or not path.resolve().is_relative_to(ROOT):
                    raise ValueError(f"Unexpected linked file in release: {name}")
                bundle.writestr(ZipInfo(name), path.read_bytes(), compress_type=ZIP_DEFLATED)
        bundle.writestr(ZipInfo(MANIFEST), json.dumps({"version": version, "commit": commit, "dirty": dirty}) + "\n")
    archive.with_suffix(".zip.sha256").write_text(digest(archive) + "\n", encoding="ascii")
    print(archive)


def unpack(archive, destination, clean):
    checksum = archive.with_suffix(".zip.sha256").read_text(encoding="ascii").strip()
    if digest(archive) != checksum:
        raise ValueError("Release checksum mismatch.")
    with ZipFile(archive) as bundle:
        names = bundle.namelist()
        if len(set(names)) != len(names) or not all(allowed(name) for name in names):
            raise ValueError("Unexpected release archive contents.")
        manifest = json.loads(bundle.read(MANIFEST))
        if not re.fullmatch(r"\d+\.\d+\.\d+", manifest["version"]) or not re.fullmatch(r"[0-9a-f]{40}", manifest["commit"]):
            raise ValueError("Invalid release provenance.")
        if clean and manifest.get("dirty") is not False:
            raise ValueError("Production requires an archive built from a clean Git checkout.")
        if destination.exists():
            raise ValueError("Unpack into a new directory.")
        bundle.extractall(destination)
    print(f"{manifest['version']} {manifest['commit']}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    pack = commands.add_parser("build")
    pack.add_argument("output", type=Path)
    extract = commands.add_parser("unpack")
    extract.add_argument("archive", type=Path)
    extract.add_argument("destination", type=Path)
    for command in (pack, extract):
        command.add_argument("--require-clean", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "build":
            build(args.output, args.require_clean)
        else:
            unpack(args.archive, args.destination, args.require_clean)
    except (ValueError, OSError) as error:
        parser.exit(1, f"{error}\n")
