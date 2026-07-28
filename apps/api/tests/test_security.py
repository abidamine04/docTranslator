from app.security import decrypt_secret, encrypt_secret


def test_provider_secret_round_trip() -> None:
    encrypted = encrypt_secret("very-secret")
    assert encrypted
    assert encrypted != "very-secret"
    assert decrypt_secret(encrypted) == "very-secret"


def test_empty_provider_secret() -> None:
    assert encrypt_secret(None) is None
    assert decrypt_secret(None) is None

