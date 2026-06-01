from auth import hash_password, verify_password


def test_hash_returns_bcrypt_string():
    h = hash_password("secret")
    assert h.startswith("$2b$")


def test_hash_differs_from_plaintext():
    assert hash_password("secret") != "secret"


def test_same_password_produces_different_hashes():
    # bcrypt uses a random salt each time
    assert hash_password("secret") != hash_password("secret")


def test_verify_correct_password():
    h = hash_password("correct")
    assert verify_password("correct", h) is True


def test_verify_wrong_password():
    h = hash_password("correct")
    assert verify_password("wrong", h) is False


def test_verify_empty_password_against_real_hash():
    h = hash_password("nonempty")
    assert verify_password("", h) is False
