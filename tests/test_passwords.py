"""Unit tests for password hashing and legacy-hash upgrades."""

import hashlib
import unittest

from security.passwords import hash_password, verify_password


class PasswordUtilityTests(unittest.TestCase):
    def test_pbkdf2_hash_verifies_correct_password(self):
        stored = hash_password("correct horse battery staple")
        valid, needs_upgrade = verify_password("correct horse battery staple", stored)
        self.assertTrue(valid)
        self.assertFalse(needs_upgrade)

    def test_pbkdf2_hash_rejects_wrong_password(self):
        stored = hash_password("correct horse battery staple")
        valid, _ = verify_password("wrong password", stored)
        self.assertFalse(valid)

    def test_hash_uses_a_different_salt_each_time(self):
        first = hash_password("same password")
        second = hash_password("same password")
        self.assertNotEqual(first, second)
        self.assertTrue(verify_password("same password", first)[0])
        self.assertTrue(verify_password("same password", second)[0])

    def test_legacy_sha256_is_accepted_but_requires_upgrade(self):
        legacy = hashlib.sha256("old password".encode("utf-8")).hexdigest()
        valid, needs_upgrade = verify_password("old password", legacy)
        self.assertTrue(valid)
        self.assertTrue(needs_upgrade)

    def test_legacy_sha256_rejects_wrong_password(self):
        legacy = hashlib.sha256("old password".encode("utf-8")).hexdigest()
        valid, _ = verify_password("incorrect", legacy)
        self.assertFalse(valid)

    def test_empty_password_is_rejected_when_hashing(self):
        with self.assertRaises(ValueError):
            hash_password("")


if __name__ == "__main__":
    unittest.main()
