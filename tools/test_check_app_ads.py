"""Proves check_app_ads.py rejects every way app-ads.txt can go wrong.

    python3 -m unittest tools/test_check_app_ads.py
"""
import hashlib
import importlib.util
import pathlib
import shutil
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
SPEC = importlib.util.spec_from_file_location("check_app_ads", HERE / "check_app_ads.py")


class CheckAppAdsTest(unittest.TestCase):
    def setUp(self):
        self.module = importlib.util.module_from_spec(SPEC)
        SPEC.loader.exec_module(self.module)
        self.temp = pathlib.Path(tempfile.mkdtemp())
        shutil.copy(self.module.TARGET, self.temp / "app-ads.txt")
        shutil.copytree(self.module.SOURCES_DIR, self.temp / "sources")
        self.module.TARGET = self.temp / "app-ads.txt"
        self.module.SOURCES_DIR = self.temp / "sources"

    def tearDown(self):
        shutil.rmtree(self.temp)

    def run_check(self):
        return self.module.main([])

    def edit_target(self, change):
        path = self.module.TARGET
        path.write_bytes(change(path.read_bytes()))

    def edit_source(self, name, change, repin=True):
        path = self.module.SOURCES_DIR / name
        path.write_bytes(change(path.read_bytes()))
        if repin:
            self.module.SOURCE_SHA256[name] = hashlib.sha256(path.read_bytes()).hexdigest()

    def test_committed_files_pass(self):
        self.assertEqual(self.run_check(), 0)

    def test_one_character_typo_fails(self):
        self.edit_target(lambda b: b.replace(b"pubmatic.com, 160456", b"pubmatic.com, 160465", 1))
        self.assertEqual(self.run_check(), 1)

    def test_typo_in_cert_id_fails(self):
        self.edit_target(lambda b: b.replace(b"96cabb5fbdde37a7", b"96cabb5fbdde37a1", 1))
        self.assertEqual(self.run_check(), 1)

    def test_missing_line_fails(self):
        self.edit_target(lambda b: b.replace(b"unity.com, 2144453, DIRECT, 96cabb5fbdde37a7\n", b""))
        self.assertEqual(self.run_check(), 1)

    def test_extra_line_fails(self):
        self.edit_target(lambda b: b + b"example.com, 1, RESELLER\n")
        self.assertEqual(self.run_check(), 1)

    def test_duplicate_line_fails(self):
        self.edit_target(lambda b: b + b.split(b"\n")[5] + b"\n")
        self.assertEqual(self.run_check(), 1)

    def test_reordered_lines_fail(self):
        def swap(b):
            lines = b.split(b"\n")
            lines[0], lines[1] = lines[1], lines[0]
            return b"\n".join(lines)
        self.edit_target(swap)
        self.assertEqual(self.run_check(), 1)

    def test_crlf_fails(self):
        self.edit_target(lambda b: b.replace(b"\n", b"\r\n"))
        self.assertEqual(self.run_check(), 1)

    def test_bom_fails(self):
        self.edit_target(lambda b: b"\xef\xbb\xbf" + b)
        self.assertEqual(self.run_check(), 1)

    def test_missing_final_newline_fails(self):
        self.edit_target(lambda b: b.rstrip(b"\n"))
        self.assertEqual(self.run_check(), 1)

    def test_trailing_space_fails(self):
        self.edit_target(lambda b: b.replace(b"\n", b" \n", 1))
        self.assertEqual(self.run_check(), 1)

    def test_lowercase_relation_fails(self):
        self.edit_target(lambda b: b.replace(b"RESELLER", b"reseller", 1))
        self.assertEqual(self.run_check(), 1)

    def test_owner_domain_line_fails(self):
        self.edit_target(lambda b: b"OWNERDOMAIN=blogger.com\n" + b)
        self.assertEqual(self.run_check(), 1)

    def test_snapshot_edited_without_repinning_fails(self):
        self.edit_source("unity.txt", lambda b: b.replace(b"2144453", b"377470"), repin=False)
        self.assertEqual(self.run_check(), 1)

    def test_wrong_direct_account_fails_even_when_everything_agrees(self):
        # Core ID instead of the developer ID, written into the snapshot, re-pinned and regenerated.
        self.edit_source("unity.txt", lambda b: b.replace(b"unity.com, 2144453", b"unity.com, 377470"))
        self.assertEqual(self.module.main(["--write"]), 1)

    def test_new_certification_variant_fails(self):
        self.edit_source("unity.txt", lambda b: b + b"pubmatic.com, 160456, RESELLER\n")
        self.assertEqual(self.module.main(["--write"]), 1)

    def test_direct_and_reseller_for_same_account_fails(self):
        self.edit_source("unity.txt", lambda b: b + b"ironsrc.com, 631887, RESELLER\n")
        self.assertEqual(self.module.main(["--write"]), 1)

    def test_write_reproduces_the_committed_file(self):
        before = self.module.TARGET.read_bytes()
        self.assertEqual(self.module.main(["--write"]), 0)
        self.assertEqual(self.module.TARGET.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
