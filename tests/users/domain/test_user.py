import pytest

from kpm.shared.domain import DomainId, IdTypeException
from kpm.shared.domain.model import RootAggState, UserId
from kpm.shared.domain.time_utils import now_utc_millis
from kpm.users.domain.events import UserReminderAdded, UserRemoved
from kpm.users.domain.model import Reminder, User, generate_referral_code
from tests.users.domain import active_user, valid_user, user


@pytest.mark.unit
class TestUser:
    class TestModel:
        def test_constructor_should_create_instance(self, active_user):
            u = User(**active_user)

            assert u.id == active_user["id"]
            assert u.username == active_user["username"]
            assert u.salt == active_user["salt"]
            assert u.password_hash == active_user["password_hash"]
            assert u.email == active_user["email"]

        def test_new_user_needs_validation(self, valid_user):
            u = User(**valid_user)
            assert u.is_disabled()
            assert u.is_pending_validation()

        def test_id_shall_be_class_userid(self, active_user):
            active_user["id"] = 3324
            with pytest.raises(IdTypeException) as _:
                User(**active_user)

            active_user["id"] = DomainId("232")
            with pytest.raises(IdTypeException) as _:
                User(**active_user)

            active_user["id"] = UserId("232")
            assert isinstance(User(**active_user).id, UserId)

        @pytest.mark.parametrize(
            "username",
            [
                "test",
                "Test",
                "this_is_an_user",
                "Ts",
            ],
        )
        def test_valid_usernames(self, active_user, username):
            active_user["username"] = username
            u = User(**active_user)
            assert u.username == username.lower()

        @pytest.mark.parametrize(
            "username",
            [
                "spa ces",
                "",
                "no-dash",
                "odd'chars",
                "oddajkshdajksdhaskjdhsakjdhasdkljashdkjs",
            ],
        )
        def test_invalid_usernames(self, active_user, username):
            active_user["username"] = username

            with pytest.raises(ValueError):
                u = User(**active_user)

        @pytest.mark.parametrize(
            "email",
            [
                "test@fmai.cos",
                "tes-t-test-test_test.test@fmai.cos",
                "test@barcelona.barcelona",
                "test-test@gmail.com",
                "test.test@gmail.com",
                "a@a.co",
                "Test@C.co",
                "test@Com.cSo",
                "test+valid@gmail.com",
                "  testvalid@gmail.com",
                "  testvalid@gmail.com   ",
                "testvalid@gmail.com     ",
            ],
        )
        def test_valid_emails(self, active_user, email):
            active_user["email"] = email
            u = User(**active_user)
            assert u.email == email.lower().strip()

        @pytest.mark.parametrize(
            "email",
            [
                "asd",
                "@gmail.com",
                "s d@gmail.com",
                "test@gmail",
                "test@.com",
                "te`st@gmail.com",
                "';test@gmail.com",
            ],
        )
        def test_invalid_emails(self, active_user, email):
            active_user["email"] = email
            with pytest.raises(ValueError) as _:
                User(**active_user)

        def test_abiguous_characters_referral_code(self):
            ambiguous_characters = ["I", "l", "1", "0", "O", "S", "5"]
            for i in range(100000):
                code = generate_referral_code()
                for char in ambiguous_characters:
                    assert char not in code

        def test_add_reminders(self, user):
            r1 = Reminder(title="one", time=123, frequency=2323)
            r2 = Reminder(title="two", time=1277)
            mod_ts = now_utc_millis()+100
            user.add_reminder(r1, mod_ts)
            user.add_reminder(r2, mod_ts)
            assert set(user.reminders) == {r1, r2}

            result_events = [
                UserReminderAdded(aggregate_id=user.id.id, title="one", time=123, frequency=2323, related_user=None, timestamp=mod_ts),
                UserReminderAdded(aggregate_id=user.id.id, title="two", time=1277, frequency=0, related_user=None, timestamp=mod_ts)
            ]
            print(user.events)
            for event in result_events:
                assert event in user.events

        def test_double_add_reminders_does_not_duplicate(self, user):
            r1 = Reminder(title="one", time=123, frequency=2323)
            r1_upd = Reminder(title="one", time=123, frequency=2323)

            user.add_reminder(r1, now_utc_millis()+100)
            # When
            user.add_reminder(r1_upd, now_utc_millis()+1000)
            # Then
            assert user.reminders == [r1]

        def test_last_reminder_is_kept(self, user):
            r1 = Reminder(title="one", time=123, frequency=2323)
            user.add_reminder(r1, now_utc_millis()+100)
            # When
            r1_v2 = Reminder(title="one", time=123, frequency=2)
            user.add_reminder(r1_v2, now_utc_millis()+1000)
            # Then
            assert user.reminders == [r1_v2]
            assert user.reminders[0].frequency == r1_v2.frequency

        def test_remove_reminders(self, user):
            # When there were no reminders
            r1 = Reminder(title="one", time=123, frequency=2323)
            user.remove_reminder(r1, now_utc_millis()+100)
            assert len(user.reminders) == 0

            # Given
            user.add_reminder(r1, now_utc_millis() + 100)
            assert len(user.reminders) == 1
            # When
            user.remove_reminder(r1, now_utc_millis()+1000)
            # Then
            assert len(user.reminders) == 0

    class TestActions:
        def test_user_disable(self, active_user):
            u = User(**active_user)
            assert not u.is_disabled()
            u.disable()
            assert u.is_disabled()

        def test_user_remove(self, active_user):
            u = User(**active_user)
            assert not u.is_disabled()
            u.remove(by=UserId(id="sdsds"), reason="GDPR")
            assert u.state == RootAggState.REMOVED
            removal_events = [
                e for e in u.events if isinstance(e, UserRemoved)
            ]
            assert len(removal_events) == 1
            ev = removal_events[0]
            assert ev.aggregate_id == u.id.id
            assert ev.by == "sdsds"
            assert ev.reason == "GDPR"

        def test_user_remove_id_string(self, active_user):
            u = User(**active_user)
            assert not u.is_disabled()
            u.remove(by="sdsds", reason="GDPR")
            assert u.state == RootAggState.REMOVED

        def test_user_remove_value_error(self, active_user):
            u = User(**active_user)
            assert not u.is_disabled()

            with pytest.raises(ValueError):
                u.remove(reason="GDPR")

            with pytest.raises(ValueError):
                u.remove()

            with pytest.raises(ValueError):
                u.remove(by="sdsds")
