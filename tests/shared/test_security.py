import pytest

from emo.shared.security import *


def test_salt():
    s = generate_salt()
    assert isinstance(s, str)


def test_salt_password():
    sp = salt_password("password,", "salt")
    assert isinstance(sp, str)
    assert sp.split(",")[0] == "password"
    assert sp.split(",")[1] == "salt"
    assert len(sp.split(",")) == 2


def test_hash():
    assert isinstance(hash_password("password"), str)
    assert len(hash_password("password")) == 60


def test_password_verify():
    assert verify_password(
        "password", "$2b$12$Hzgp1lAu1tA5O1Qizcjei.KXMhl9Z5.uejg5RePR9whnDuAqTbCQi"
    )
