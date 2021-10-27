import pytest

from emo.assets.domain.entity import (Asset, AssetTtileException,
                                      EmptyOwnerException)
from emo.shared.domain import AssetId, DomainId, IdTypeException, UserId
from tests.assets.domain import valid_asset


@pytest.mark.unit
class TestAsset:
    class TestModel:
        invalid_titles = [
            "",
            ".a2c",
            "c/sc",
            "this title is too long and should now be allowed",
            "  ",
            "#2sd",
            "*invalid initial char",
        ]

        @pytest.mark.parametrize("title", invalid_titles)
        def test_invalid_titles(self, valid_asset, title):
            valid_asset["title"] = title
            with pytest.raises(AssetTtileException):
                Asset(**valid_asset)

        valid_titles = [
            "Asset",
            "a2",
            "My asset",
            "0's",
            "à ú",
            "Is this?",
            "sds[sd]",
            "sd¡",
        ]

        @pytest.mark.parametrize("title", valid_titles)
        def test_valid_titles(self, valid_asset, title):
            valid_asset["title"] = title
            a = Asset(**valid_asset)
            assert a.title == title

        def test_valid_user_ids(self, valid_asset):
            valid_asset["owners_id"] = [UserId("3232"), UserId("11112")]
            a = Asset(**valid_asset)
            assert a.owners_id == valid_asset["owners_id"]

        def test_owners_cannot_be_empty(self, valid_asset):
            valid_asset["owners_id"] = []
            with pytest.raises(EmptyOwnerException):
                Asset(**valid_asset)

        invalid_uids = [
            [DomainId("1232")],
            [233343],
            ["", ""],
            [""],
            [UserId("3232"), UserId("11112"), ""],
            [UserId("3232"), UserId("11112"), AssetId("assetID")],
        ]

        @pytest.mark.parametrize("owners_id", invalid_uids)
        def test_invalid_user_ids(self, valid_asset, owners_id):
            valid_asset["owners_id"] = owners_id
            with pytest.raises(IdTypeException):
                Asset(**valid_asset)
