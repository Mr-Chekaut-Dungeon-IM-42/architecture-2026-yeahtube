import pytest

from app.cqs.commands import SoftDeleteUserCommand, UpdateUserCommand
from app.cqs.handlers import SoftDeleteUserCommandHandler, UpdateUserCommandHandler
from app.domain.errors import GoneError, NotFoundError, ValidationError


class _FakeDB:
    def __init__(self):
        self.commits = 0

    def commit(self):
        self.commits += 1


class _User:
    def __init__(self, *, is_deleted: bool = False):
        self.is_deleted = is_deleted
        self.username = "old"
        self.email = "old@example.com"
        self.is_moderator = False


def test_soft_delete_user_not_found(monkeypatch):
    monkeypatch.setattr("app.cqs.handlers.UserRepository.get_by_id", lambda db, user_id: None)

    with pytest.raises(NotFoundError):
        SoftDeleteUserCommandHandler(_FakeDB()).handle(SoftDeleteUserCommand(user_id=1))


def test_soft_delete_user_gone(monkeypatch):
    monkeypatch.setattr(
        "app.cqs.handlers.UserRepository.get_by_id", lambda db, user_id: _User(is_deleted=True)
    )

    with pytest.raises(GoneError):
        SoftDeleteUserCommandHandler(_FakeDB()).handle(SoftDeleteUserCommand(user_id=1))


def test_update_user_validates_uniqueness(monkeypatch):
    user = _User(is_deleted=False)
    monkeypatch.setattr(
        "app.cqs.handlers.UserRepository.get_by_id", lambda db, user_id, for_update=False: user
    )
    monkeypatch.setattr(
        "app.cqs.handlers.UserRepository.exists_by_username",
        lambda db, username, exclude_id=None: True,
    )

    with pytest.raises(ValidationError):
        UpdateUserCommandHandler(_FakeDB()).handle(
            UpdateUserCommand(user_id=1, username="taken")
        )
