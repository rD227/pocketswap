# SPDX-License-Identifier: GPL-3.0-only
# Copyright (C) 2026 xvsu
import hashlib
import importlib.util
import json
from pathlib import Path
import shutil
import stat
import tempfile
import unittest
import zipfile

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("build_release", ROOT / "tools" / "build_release.py")
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="pocketswap-release-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)

    def fixture(self):
        root = self.base / "source"
        root.mkdir()
        shutil.copytree(ROOT / "module", root / "module")
        for name in ("LICENSE", "README.md", "CHANGELOG.md"):
            shutil.copyfile(ROOT / name, root / name)
        return root

    def test_matching_assets_and_installable_zip(self):
        output = self.base / "dist"
        props = builder.read_properties(ROOT / "module")
        tag = f"v{props['version']}"
        target = builder.build(output=output, expected_tag=tag)
        metadata = json.loads((output / "update.json").read_text())
        self.assertEqual(metadata["version"], props["version"])
        self.assertEqual(metadata["versionCode"], int(props["versionCode"]))
        self.assertEqual(metadata["zipUrl"], f"{builder.REPOSITORY}/releases/download/{tag}/pocketswap.zip")
        self.assertEqual(metadata["changelog"], f"{builder.REPOSITORY}/releases/download/{tag}/changelog.md")
        self.assertEqual({p.name for p in output.iterdir()}, {"pocketswap.zip", "update.json", "changelog.md", "SHA256SUMS"})
        with zipfile.ZipFile(target) as archive:
            self.assertIsNone(archive.testzip())
            self.assertIn("module.prop", archive.namelist())
            self.assertIn("service.sh", archive.namelist())
            self.assertIn("skip_mount", archive.namelist())
            self.assertFalse(any(name.startswith("module/") for name in archive.namelist()))
            self.assertEqual(archive.read("LICENSE"), (ROOT / "LICENSE").read_bytes())
            self.assertEqual(archive.read("README.md"), builder.normalized_text((ROOT / "README.md").read_bytes(), "README.md"))
            for entry in archive.infolist():
                if entry.filename != "LICENSE":
                    self.assertNotIn(b"\r", archive.read(entry))
                if entry.filename.endswith(".sh"):
                    self.assertEqual(stat.S_IMODE(entry.external_attr >> 16), 0o755)
            zip_props = dict(line.split("=", 1) for line in archive.read("module.prop").decode().splitlines())
            self.assertEqual(zip_props["version"], metadata["version"])
            self.assertEqual(int(zip_props["versionCode"]), metadata["versionCode"])
            self.assertEqual(zip_props["updateJson"], builder.UPDATE_URL)
        for line in (output / "SHA256SUMS").read_text().splitlines():
            checksum, name = line.split("  ")
            self.assertEqual(checksum, hashlib.sha256((output / name).read_bytes()).hexdigest())

    def test_repeat_build_is_identical(self):
        first, second = self.base / "first", self.base / "second"
        builder.build(output=first)
        builder.build(output=second)
        for name in ("pocketswap.zip", "update.json", "changelog.md", "SHA256SUMS"):
            self.assertEqual((first / name).read_bytes(), (second / name).read_bytes())

    def test_tag_mismatch_stops_before_output(self):
        output = self.base / "dist"
        with self.assertRaisesRegex(ValueError, "must match module version"):
            builder.build(output=output, expected_tag="v0.0.0")
        self.assertFalse(output.exists())

    def test_license_mismatch_rejected(self):
        root = self.fixture()
        with (root / "module" / "LICENSE").open("ab") as handle:
            handle.write(b"\nchanged\n")
        with self.assertRaisesRegex(ValueError, "LICENSE differs"):
            builder.build(root=root)

    def test_missing_current_changelog_rejected(self):
        root = self.fixture()
        (root / "CHANGELOG.md").write_text("# No current release\n")
        with self.assertRaisesRegex(ValueError, "missing from CHANGELOG"):
            builder.build(root=root)

    def test_missing_update_endpoint_rejected(self):
        root = self.fixture()
        prop = root / "module" / "module.prop"
        prop.write_text("\n".join(line for line in prop.read_text().splitlines() if not line.startswith("updateJson=")) + "\n")
        with self.assertRaisesRegex(ValueError, "stable release endpoint"):
            builder.build(root=root)

    def test_output_inside_module_rejected(self):
        root = self.fixture()
        output = root / "module" / "generated"
        with self.assertRaisesRegex(ValueError, "outside module source"):
            builder.build(root=root, output=output)
        self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
