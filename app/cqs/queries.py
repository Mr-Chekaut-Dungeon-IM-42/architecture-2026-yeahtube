from __future__ import annotations

from dataclasses import dataclass


# Queries are DTOs with no logic and never mutate state.


@dataclass(frozen=True, slots=True)
class GetCurrentUserInfoQuery:
    user_id: int


@dataclass(frozen=True, slots=True)
class GetAllUsersQuery:
    pass


@dataclass(frozen=True, slots=True)
class GetUserByIdQuery:
    user_id: int


@dataclass(frozen=True, slots=True)
class GetUserRecommendationsQuery:
    user_id: int
    limit: int = 20


@dataclass(frozen=True, slots=True)
class GetUserYearlyViewsQuery:
    user_id: int
    year: int | None = None


@dataclass(frozen=True, slots=True)
class GetUserFavoriteCreatorQuery:
    user_id: int
    year: int | None = None


@dataclass(frozen=True, slots=True)
class GetUserReactionsCountQuery:
    user_id: int
    year: int | None = None


@dataclass(frozen=True, slots=True)
class GetUserAverageViewTimeQuery:
    user_id: int


@dataclass(frozen=True, slots=True)
class GetUserCredibilityQuery:
    user_id: int


@dataclass(frozen=True, slots=True)
class GetVideoByIdQuery:
    video_id: int


@dataclass(frozen=True, slots=True)
class GetVideoStatsQuery:
    video_id: int


@dataclass(frozen=True, slots=True)
class GetVideoCommentsQuery:
    video_id: int
    page: int = 1
    limit: int = 10


@dataclass(frozen=True, slots=True)
class GetUserPlaylistsQuery:
    user_id: int


@dataclass(frozen=True, slots=True)
class GetPlaylistQuery:
    user_id: int
    playlist_id: int


@dataclass(frozen=True, slots=True)
class GetReportsQuery:
    resolved: bool | None = None
    skip: int = 0
    limit: int = 50


@dataclass(frozen=True, slots=True)
class GetDetailedReportsQuery:
    resolved: bool | None = None
    skip: int = 0
    limit: int = 50


@dataclass(frozen=True, slots=True)
class GetProblematicUsersQuery:
    min_reports: int = 3
    skip: int = 0
    limit: int = 50


@dataclass(frozen=True, slots=True)
class GetChannelsReportsAnalyticsQuery:
    min_reports: int = 1
    limit: int = 20

