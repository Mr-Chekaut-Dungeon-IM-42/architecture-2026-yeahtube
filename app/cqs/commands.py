from __future__ import annotations

from dataclasses import dataclass


# Commands are DTOs with no logic. A command may return only an identifier.


@dataclass(frozen=True, slots=True)
class RegisterUserCommand:
    username: str
    email: str
    password: str


@dataclass(frozen=True, slots=True)
class UpdateUserCommand:
    user_id: int
    username: str | None = None
    email: str | None = None
    is_moderator: bool | None = None


@dataclass(frozen=True, slots=True)
class SoftDeleteUserCommand:
    user_id: int


@dataclass(frozen=True, slots=True)
class CreateVideoCommand:
    title: str
    description: str | None
    channel_id: int
    is_active: bool | None = True
    is_monetized: bool | None = False


@dataclass(frozen=True, slots=True)
class UpdateVideoCommand:
    video_id: int
    title: str | None = None
    description: str | None = None
    is_active: bool | None = None
    is_monetized: bool | None = None


@dataclass(frozen=True, slots=True)
class DeleteVideoCommand:
    video_id: int


@dataclass(frozen=True, slots=True)
class CreateVideoWithCommentCommand:
    title: str
    description: str | None
    channel_id: int
    initial_comment: str
    is_active: bool | None = True
    is_monetized: bool | None = False


@dataclass(frozen=True, slots=True)
class CreatePlaylistCommand:
    user_id: int
    name: str


@dataclass(frozen=True, slots=True)
class UpdatePlaylistCommand:
    user_id: int
    playlist_id: int
    name: str


@dataclass(frozen=True, slots=True)
class DeletePlaylistCommand:
    user_id: int
    playlist_id: int


@dataclass(frozen=True, slots=True)
class DeactivateVideoCommand:
    video_id: int


@dataclass(frozen=True, slots=True)
class DemonetizeVideoCommand:
    video_id: int


@dataclass(frozen=True, slots=True)
class BanUserCommand:
    user_id: int


@dataclass(frozen=True, slots=True)
class AddChannelStrikeCommand:
    channel_id: int


@dataclass(frozen=True, slots=True)
class ResolveReportCommand:
    report_id: int

