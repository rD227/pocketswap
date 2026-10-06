#!/usr/bin/env python3
# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 xvsu
"""Build the source-complete module and matching GitHub release assets."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import stat
import zipfile

ROOT = Path(__file__).resolve().parents[1]
REPOSITORY = "https://github.com/rD227/pocketswap"
UPDATE_URL = f"{REPOSITORY}/releases/latest/download/update.json"
FIXED_DATE = (2026, 10, 6, 0, 0, 0)


def read_properties(module: Path) -> dict[str, str]:
    props = {}
    for line in (module / "module.prop").read_text(encoding="utf-8").splitlines():
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        if key in props:
            raise ValueError(f"Duplicate property: {key}")
        props[key] = value
    if props.get("id") != "pocketswap":
        raise ValueError("Keep the published module id=pocketswap")
    if not re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+", props.get("version", "")):
        raise ValueError("version must use major.minor.patch")
    if not re.fullmatch(r"[1-9][0-9]*", props.get("versionCode", "")):
        raise ValueError("versionCode must be a positive integer")
    if props.get("updateJson") != UPDATE_URL:
        raise ValueError("updateJson does not match the stable release endpoint")
    return props


def normalized_text(data: bytes, name: str) -> bytes:
    data = data.replace(b"\r\n", b"\n")
    if b"\r" in data or b"\x00" in data:
        raise ValueError(f"Invalid text file: {name}")
    return data


def build(root: Path = ROOT, output: Path | None = None, expected_tag: str | None = None) -> Path:
    module = root / "module"
    props = read_properties(module)
    tag = f"v{props['version']}"
    if expected_tag is not None and expected_tag != tag:
        raise ValueError(f"Tag {expected_tag!r} must match module version {tag!r}")
    license_data = (root / "LICENSE").read_bytes()
    if (module / "LICENSE").read_bytes() != license_data:
        raise ValueError("Module LICENSE differs from the supplied root LICENSE")
    if b"GNU GENERAL PUBLIC LICENSE" not in license_data or b"Version 3, 29 June 2007" not in license_data:
        raise ValueError("Expected the complete supplied GNU GPL v3 LICENSE")
    changelog = normalized_text((root / "CHANGELOG.md").read_bytes(), "CHANGELOG.md")
    if f"## {props['version']}\n".encode() not in changelog:
        raise ValueError("Current version is missing from CHANGELOG.md")
    readme = normalized_text((root / "README.md").read_bytes(), "README.md")
    output = root / "dist" if output is None else output
    if output.resolve().is_relative_to(module.resolve()):
        raise ValueError("Output must be outside module source to avoid packaging generated assets")
    output.mkdir(parents=True, exist_ok=True)
    target = output / "pocketswap.zip"
    with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
        for item in sorted(module.rglob("*")):
            if item.is_symlink():
                raise ValueError(f"Symlink in module source: {item}")
            if not item.is_file():
                continue
            relative = item.relative_to(module).as_posix()
            # Repository docs are canonical; embed those exact docs in the ZIP.
            data = readme if relative == "README.md" else item.read_bytes()
            if item.name != "LICENSE":
                data = normalized_text(data, relative)
            info = zipfile.ZipInfo(relative, date_time=FIXED_DATE)
            info.create_system = 3
            mode = 0o755 if item.suffix == ".sh" or item.name == "update-binary" else 0o644
            info.external_attr = (stat.S_IFREG | mode) << 16
            info.compress_type = zipfile.ZIP_DEFLATED
            archive.writestr(info, data)
        info = zipfile.ZipInfo("CHANGELOG.md", date_time=FIXED_DATE)
        info.create_system = 3
        info.external_attr = (stat.S_IFREG | 0o644) << 16
        info.compress_type = zipfile.ZIP_DEFLATED
        archive.writestr(info, changelog)
    with zipfile.ZipFile(target) as archive:
        if archive.testzip() is not None or archive.read("LICENSE") != license_data:
            raise ValueError("ZIP verification failed")
    release_url = f"{REPOSITORY}/releases/download/{tag}"
    update = {
        "version": props["version"],
        "versionCode": int(props["versionCode"]),
        "zipUrl": f"{release_url}/pocketswap.zip",
        "changelog": f"{release_url}/changelog.md",
    }
    (output / "update.json").write_bytes((json.dumps(update, indent=2) + "\n").encode("utf-8"))
    (output / "changelog.md").write_bytes(changelog)
    assets = ("pocketswap.zip", "update.json", "changelog.md")
    checksums = "".join(f"{hashlib.sha256((output / name).read_bytes()).hexdigest()}  {name}\n" for name in assets)
    (output / "SHA256SUMS").write_bytes(checksums.encode("ascii"))
    return target


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=ROOT / "dist")
    parser.add_argument("--tag", help="Require this Git tag to match module.prop")
    args = parser.parse_args()
    try:
        print(build(output=args.output, expected_tag=args.tag))
    except (ValueError, OSError) as error:
        parser.exit(1, f"Build failed: {error}\n")


if __name__ == "__main__":
    main()
