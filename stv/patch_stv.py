#!/usr/bin/env python3
"""Patch a pristine Astra SuperStars ST-V ZIP into astrassu.zip."""

import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory
from zipfile import BadZipFile, ZIP_DEFLATED, ZipFile


ROOT = Path(__file__).resolve().parent
OUTPUT_NAME = "astrassu.zip"
ROM_NAMES = ("epr20825.13", *(f"mpr{20825 + n}.{n}" for n in range(1, 7)),
             "mpr20832.8", "mpr20833.9")
HASH_PATTERN = re.compile(r"[0-9a-f]{64}")


def load_hashes(path):
    manifest = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(manifest, dict) or manifest.get("format") != "astra-stv-xdelta-v1":
        raise ValueError(f"Unsupported hash manifest: {path}")
    files = manifest.get("files")
    if not isinstance(files, dict) or files.keys() != set(ROM_NAMES):
        raise ValueError(f"Hash manifest must list all nine ST-V ROMs: {path}")
    for name, entry in files.items():
        size = 0x100000 if name == ROM_NAMES[0] else 0x400000
        if not isinstance(entry, dict) or entry.get("size") != size:
            raise ValueError(f"Invalid ROM size in hash manifest: {name}")
        for key in ("source_sha256", "patched_sha256", "xdelta_sha256"):
            value = entry.get(key)
            if not isinstance(value, str) or not HASH_PATTERN.fullmatch(value):
                raise ValueError(f"Invalid {key} in hash manifest: {name}")
    return files


def validate_hash(data, expected, label):
    actual = hashlib.sha256(data).hexdigest()
    if actual != expected:
        raise ValueError(f"{label}: SHA-256 mismatch (expected {expected}, got {actual})")


def read_source_zip(path, hashes):
    members = {}
    roms = {}
    with ZipFile(path) as archive:
        for member in archive.infolist():
            name = member.filename.replace("\\", "/").rsplit("/", 1)[-1].lower()
            if member.is_dir() or name not in hashes:
                continue
            if name in members:
                raise ValueError(f"Duplicate ZIP entry for {name}")
            members[name] = member
        missing = hashes.keys() - members.keys()
        if missing:
            raise ValueError(f"Missing ROMs: {', '.join(sorted(missing))}")
        for name in ROM_NAMES:
            member = members[name]
            if member.file_size != hashes[name]["size"]:
                raise ValueError(f"{name}: expected {hashes[name]['size']} bytes, found {member.file_size}")
            data = archive.read(member)
            validate_hash(data, hashes[name]["source_sha256"], name)
            roms[name] = data
    return roms


def find_source(directory, explicit, hashes):
    if explicit is not None:
        return explicit, read_source_zip(explicit, hashes)
    candidates = sorted(
        (p for p in directory.iterdir()
         if p.is_file() and p.suffix.lower() == ".zip" and p.name.lower() != OUTPUT_NAME),
        key=lambda p: (p.name.lower() != "astrass.zip", p.name.lower()),
    )
    errors = []
    for candidate in candidates:
        try:
            return candidate, read_source_zip(candidate, hashes)
        except (OSError, ValueError, BadZipFile, RuntimeError) as exc:
            errors.append(f"  {candidate.name}: {exc}")
    if errors:
        raise ValueError("No matching pristine ST-V ZIP found:\n" + "\n".join(errors))
    raise ValueError(f"Place the pristine astrass.zip next to the script in {directory}, or pass its path.")


def patch_archive(directory, explicit):
    patches = directory / "xdeltas"
    hashes = load_hashes(patches / "hashes.json")
    xdelta = directory / "tools" / "xdelta.exe"
    if not xdelta.is_file():
        raise ValueError(f"xdelta executable is missing: {xdelta}")
    source, roms = find_source(directory, explicit, hashes)
    print(f"Validated {len(roms)} ROMs in {source}")

    output = directory / OUTPUT_NAME
    if source.resolve() == output.resolve():
        raise ValueError(f"Source ZIP cannot also be the output: {output}")
    build = directory / "build"
    build.mkdir(exist_ok=True)
    with TemporaryDirectory(prefix="stv-patch-", dir=build) as staging:
        staging = Path(staging)
        work = staging / "work"
        work.mkdir()
        for name in ROM_NAMES:
            patch = patches / f"{name}.xdelta"
            validate_hash(patch.read_bytes(), hashes[name]["xdelta_sha256"], patch.name)
            pristine, patched = staging / name, work / name
            pristine.write_bytes(roms[name])
            result = subprocess.run(
                [str(xdelta), "-d", "-s", str(pristine), str(patch), str(patched)],
                capture_output=True, text=True, errors="replace",
            )
            if result.returncode:
                detail = result.stderr.strip() or result.stdout.strip()
                raise ValueError(f"{name}: xdelta exited with code {result.returncode}: {detail}")
            validate_hash(patched.read_bytes(), hashes[name]["patched_sha256"], f"Patched {name}")
            print(f"Patched {name}")

        archive_path = staging / OUTPUT_NAME
        with ZipFile(archive_path, "w", compression=ZIP_DEFLATED) as archive:
            for name in ROM_NAMES:
                archive.write(work / name, arcname=name)
        final_work = build / "work"
        final_work.mkdir(exist_ok=True)
        for name in ROM_NAMES:
            (staging / name).replace(build / name)
            (work / name).replace(final_work / name)
        archive_path.replace(output)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source_zip", nargs="?", type=Path,
                        help="Pristine source ZIP. By default, search next to this script.")
    args = parser.parse_args()
    try:
        output = patch_archive(ROOT, args.source_zip)
    except (OSError, ValueError, BadZipFile, RuntimeError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1
    print(f"Created {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
