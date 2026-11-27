"""Verify approved evaluation inputs without editing them.

Run before and after each evaluation: python eval/verify_frozen_inputs.py.
Hashes use UTF-8 bytes with LF endings, matching the Git blobs in the lock.
"""
import argparse
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK = ROOT / "eval/frozen-inputs-20261127.json"


def verify(root, manifest):
    errors = []
    for name, entry in manifest["files"].items():
        content = (root / name).read_bytes().replace(b"\r\n", b"\n")
        actual = hashlib.sha256(content).hexdigest()
        if actual != entry["sha256_lf"]:
            errors.append(f"{name}: SHA256 mismatch, expected {entry['sha256_lf']}, got {actual}")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", type=Path, default=LOCK)
    args = parser.parse_args()
    manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
    errors = verify(ROOT, manifest)
    for error in errors:
        print(error)
    if errors:
        return 1
    print(f"Frozen benchmark and metric match {manifest['source_commit']} ({len(manifest['files'])} files).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
