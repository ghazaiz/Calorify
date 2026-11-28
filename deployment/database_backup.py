"""Create or restore a verified SQLite snapshot without overwriting files."""

import argparse
from contextlib import closing
import os
from pathlib import Path
import sqlite3
from tempfile import NamedTemporaryFile


def verify(connection):
    if connection.execute("PRAGMA integrity_check").fetchall() != [("ok",)]:
        raise ValueError("SQLite integrity check failed.")
    if connection.execute("PRAGMA foreign_key_check").fetchone() is not None:
        raise ValueError("SQLite foreign-key check failed.")
    tables = {row[0] for row in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
    if not {"users", "profiles", "meals"} <= tables:
        raise ValueError("The database is missing Calorify tables.")


def read_only(path):
    return sqlite3.connect(path.resolve(strict=True).as_uri() + "?mode=ro", uri=True, timeout=15)


def copy_database(source, destination):
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")
    with NamedTemporaryFile(dir=destination.parent, prefix=".calorify-", delete=False) as temporary:
        path = Path(temporary.name)
    try:
        with closing(read_only(source)) as original, closing(sqlite3.connect(path, timeout=15)) as copy:
            original.backup(copy)
            verify(copy)
        # Publishing by hard link is atomic and fails if another process created the destination.
        os.link(path, destination)
    finally:
        path.unlink(missing_ok=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("snapshot", "restore", "verify"))
    parser.add_argument("source", type=Path)
    parser.add_argument("destination", type=Path, nargs="?")
    args = parser.parse_args()
    try:
        if args.command == "verify":
            if args.destination:
                parser.error("verify takes only a source")
            with closing(read_only(args.source)) as connection:
                verify(connection)
        else:
            if not args.destination:
                parser.error("snapshot and restore require a new destination")
            copy_database(args.source, args.destination)
    except (ValueError, OSError, sqlite3.Error) as error:
        parser.exit(1, f"{error}\n")
    print(f"Verified {args.destination or args.source}")
