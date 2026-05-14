from __future__ import annotations

from dataclasses import asdict
from datetime import date, datetime

from sqlalchemy.orm import Session

from app.cqs.commands import (
    AddChannelStrikeCommand,
    BanUserCommand,
    CreatePlaylistCommand,
    CreateVideoCommand,
    CreateVideoWithCommentCommand,
    DeactivateVideoCommand,
    DeletePlaylistCommand,
    DeleteVideoCommand,
    DemonetizeVideoCommand,
    RegisterUserCommand,
    ResolveReportCommand,
    SoftDeleteUserCommand,
    UpdatePlaylistCommand,
    UpdateUserCommand,
    UpdateVideoCommand,
)
from app.cqs.queries import (
    GetAllUsersQuery,
    GetChannelsReportsAnalyticsQuery,
    GetCurrentUserInfoQuery,
    GetDetailedReportsQuery,
    GetPlaylistQuery,
    GetProblematicUsersQuery,
    GetReportsQuery,
    GetUserAverageViewTimeQuery,
    GetUserByIdQuery,
    GetUserCredibilityQuery,
    GetUserFavoriteCreatorQuery,
    GetUserPlaylistsQuery,
    GetUserReactionsCountQuery,
    GetUserRecommendationsQuery,
    GetUserYearlyViewsQuery,
    GetVideoByIdQuery,
    GetVideoCommentsQuery,
    GetVideoStatsQuery,
)
from app.db.models import Channel, Comment, Playlist, User, Video
from app.domain.errors import ForbiddenError, GoneError, NotFoundError, UnauthorizedError, ValidationError
from app.domain.factories import UserFactory
from app.infrastructure.mappers.orm_domain import (
    channel_to_domain,
    comment_to_domain,
    playlist_to_domain,
    user_to_domain,
    video_to_domain,
)
from app.infrastructure.repositories.user_uniqueness import SqlAlchemyUserUniquenessChecker
from app.repositories.admin import AdminRepository
from app.repositories.auth import AuthRepository
from app.repositories.playlist import PlaylistRepository
from app.repositories.user import UserRepository
from app.repositories.video import VideoRepository
from app.schemas.schemas import (
    ChannelAnalyticsListResponse,
    ChannelAnalyticsResponse,
    ChannelInfo,
    ChannelStrikeResponse,
    CommentResponse,
    DetailedReportResponse,
    DetailedReportsListResponse,
    ProblematicUserResponse,
    ProblematicUsersListResponse,
    ReportResolveResponse,
    ReportResponse,
    ReportsListResponse,
    ReportStats,
    ReporterInfo,
    Token,
    UserBanResponse,
    UserCredibilityResponse,
    UserDetailedResponse,
    UserOut,
    VideoCommentsResponse,
    VideoDeactivateResponse,
    VideoDemonetizeResponse,
    VideoInfo,
    VideoResponse,
    VideoStatsResponse,
    VideoWithCommentResponse,
)
from app.utils.auth import create_access_token, get_password_hash, verify_password


# ---- Command handlers (mutate state) ----


class RegisterUserCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: RegisterUserCommand) -> int:
        checker = SqlAlchemyUserUniquenessChecker(self._db)
        factory = UserFactory(uniqueness=checker)

        factory.register_new_user(
            username=cmd.username,
            email=cmd.email,
            created_at=date.today(),
            is_moderator=False,
        )

        hashed_password = get_password_hash(cmd.password)

        try:
            new_user = AuthRepository.create_user(
                db=self._db,
                username=cmd.username,
                email=cmd.email,
                hashed_password=hashed_password,
            )
            self._db.commit()
            return int(new_user.id)
        except Exception:
            self._db.rollback()
            raise


class LoginUserCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, username: str, password: str) -> Token:
        user = AuthRepository.get_user_by_username(self._db, username)
        if not user:
            raise UnauthorizedError("Incorrect username")
        if not verify_password(password, user.hashed_password):
            raise UnauthorizedError("Incorrect password")
        if user.is_banned:
            raise ForbiddenError("User account is banned")
        if user.is_deleted:
            raise ForbiddenError("User account is deleted")

        access_token = create_access_token(
            data={"user_id": user.id, "username": user.username, "is_moderator": user.is_moderator}
        )
        return Token(access_token=access_token, token_type="bearer")


class UpdateUserCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: UpdateUserCommand) -> None:
        user = UserRepository.get_by_id(self._db, cmd.user_id, for_update=True)
        if not user:
            raise NotFoundError("User not found")
        if user.is_deleted:
            raise GoneError("User has been deleted")

        if cmd.username and UserRepository.exists_by_username(self._db, cmd.username, cmd.user_id):
            raise ValidationError("Username already exists")
        if cmd.email and UserRepository.exists_by_email(self._db, cmd.email, cmd.user_id):
            raise ValidationError("Email already exists")

        if cmd.username:
            user.username = cmd.username
        if cmd.email:
            user.email = cmd.email
        if cmd.is_moderator is not None:
            user.is_moderator = cmd.is_moderator

        self._db.commit()


class SoftDeleteUserCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: SoftDeleteUserCommand) -> None:
        user = UserRepository.get_by_id(self._db, cmd.user_id)
        if not user:
            raise NotFoundError("User not found")
        if user.is_deleted:
            raise GoneError("User already deleted")
        user.is_deleted = True
        self._db.commit()


class CreateVideoCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: CreateVideoCommand) -> int:
        channel = self._db.get(Channel, cmd.channel_id)
        if not channel:
            raise NotFoundError("Channel not found")
        video = Video(
            title=cmd.title,
            description=cmd.description,
            uploaded_at=date.today(),
            channel_id=cmd.channel_id,
            is_active=cmd.is_active if cmd.is_active is not None else True,
            is_monetized=cmd.is_monetized if cmd.is_monetized is not None else False,
        )
        created = VideoRepository.create(self._db, video)
        return int(created.id)


class UpdateVideoCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: UpdateVideoCommand) -> None:
        video = VideoRepository.get_by_id(self._db, cmd.video_id, for_update=True)
        if not video:
            raise NotFoundError("Video not found")
        if cmd.title is not None:
            video.title = cmd.title
        if cmd.description is not None:
            video.description = cmd.description
        if cmd.is_active is not None:
            video.is_active = cmd.is_active
        if cmd.is_monetized is not None:
            video.is_monetized = cmd.is_monetized
        self._db.commit()


class DeleteVideoCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: DeleteVideoCommand) -> None:
        video = VideoRepository.get_by_id(self._db, cmd.video_id)
        if not video:
            raise NotFoundError("Video not found")
        VideoRepository.delete(self._db, video)


class CreateVideoWithCommentCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: CreateVideoWithCommentCommand) -> int:
        channel = self._db.get(Channel, cmd.channel_id)
        if not channel:
            raise NotFoundError("Channel not found")
        author = self._db.get(User, channel.owner_id)
        if not author:
            raise NotFoundError("Channel owner not found")
        if author.is_deleted:
            raise GoneError("Channel owner has been deleted")
        if author.is_banned:
            raise ForbiddenError("Channel owner is banned")

        video = Video(
            title=cmd.title,
            description=cmd.description,
            uploaded_at=date.today(),
            channel_id=cmd.channel_id,
            is_active=cmd.is_active if cmd.is_active is not None else True,
            is_monetized=cmd.is_monetized if cmd.is_monetized is not None else False,
        )
        self._db.add(video)
        self._db.flush()
        comment = Comment(
            comment_text=cmd.initial_comment,
            user_id=author.id,
            video_id=video.id,
            commented_at=date.today(),
        )
        self._db.add(comment)
        self._db.commit()
        return int(video.id)


class CreatePlaylistCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: CreatePlaylistCommand) -> int:
        if not PlaylistRepository.get_user(self._db, cmd.user_id):
            raise NotFoundError("User not found")
        playlist = PlaylistRepository.create(self._db, cmd.name, cmd.user_id)
        return int(playlist.id)


class UpdatePlaylistCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: UpdatePlaylistCommand) -> None:
        playlist = PlaylistRepository.get_by_id(self._db, cmd.playlist_id, cmd.user_id)
        if not playlist:
            raise NotFoundError("Playlist not found")
        PlaylistRepository.update(self._db, playlist, cmd.name)


class DeletePlaylistCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: DeletePlaylistCommand) -> None:
        playlist = PlaylistRepository.get_by_id(self._db, cmd.playlist_id, cmd.user_id)
        if not playlist:
            raise NotFoundError("Playlist not found")
        PlaylistRepository.delete(self._db, playlist)


class DeactivateVideoCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: DeactivateVideoCommand) -> None:
        video = AdminRepository.get_video_by_id(self._db, cmd.video_id)
        if not video:
            raise NotFoundError("Video not found")
        if not video.is_active:
            raise ValidationError("Video is already inactive")
        video.is_active = False
        self._db.commit()


class DemonetizeVideoCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: DemonetizeVideoCommand) -> None:
        video = AdminRepository.get_video_by_id(self._db, cmd.video_id)
        if not video:
            raise NotFoundError("Video not found")
        if not video.is_monetized:
            raise ValidationError("Video is already not monetized")
        video.is_monetized = False
        self._db.commit()


class BanUserCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: BanUserCommand) -> None:
        user = AdminRepository.get_user_by_id(self._db, cmd.user_id)
        if not user:
            raise NotFoundError("User not found")
        if user.is_banned:
            raise ValidationError("User is already banned")
        user.is_banned = True
        self._db.commit()


class AddChannelStrikeCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: AddChannelStrikeCommand) -> None:
        channel = AdminRepository.get_channel_by_id(self._db, cmd.channel_id)
        if not channel:
            raise NotFoundError("Channel not found")
        AdminRepository.add_channel_strike(self._db, channel.id, video_id=None)
        self._db.commit()


class ResolveReportCommandHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle(self, cmd: ResolveReportCommand) -> None:
        report = AdminRepository.get_report_by_id(self._db, cmd.report_id)
        if not report:
            raise NotFoundError("Report not found")
        if report.is_resolved:
            raise ValidationError("Report is already resolved")
        report.is_resolved = True
        self._db.commit()


# ---- Query handlers (read-only) ----


class AuthQueryHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle_current_user(self, q: GetCurrentUserInfoQuery) -> UserOut:
        user = self._db.get(User, q.user_id)
        if not user:
            raise NotFoundError("User not found")
        return UserOut(
            id=user.id,
            username=user.username,
            email=user.email,
            is_moderator=user.is_moderator,
            is_banned=user.is_banned,
            created_at=user.created_at,
        )


class UserQueryHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle_get_all(self, q: GetAllUsersQuery) -> list[UserDetailedResponse]:
        users = UserRepository.get_all_active(self._db)
        return [UserDetailedResponse.model_validate(u) for u in users]

    def handle_get_by_id(self, q: GetUserByIdQuery) -> UserDetailedResponse:
        user = UserRepository.get_by_id(self._db, q.user_id)
        if not user:
            raise NotFoundError("User not found")
        if user.is_deleted:
            raise GoneError("User has been deleted")
        d_user = user_to_domain(user)
        return UserDetailedResponse(
            id=d_user.id,
            username=d_user.username.value,
            email=d_user.email.value,
            created_at=d_user.created_at,
            is_moderator=d_user.is_moderator,
            is_deleted=d_user.is_deleted,
        )

    def handle_recommendations(self, q: GetUserRecommendationsQuery) -> list[VideoResponse]:
        self.handle_get_by_id(GetUserByIdQuery(user_id=q.user_id))
        vids = UserRepository.get_recommendations(self._db, q.user_id, q.limit)
        return [VideoResponse.model_validate(v) for v in vids]

    def handle_yearly_views(self, q: GetUserYearlyViewsQuery) -> dict:
        self.handle_get_by_id(GetUserByIdQuery(user_id=q.user_id))
        year = q.year if q.year is not None else datetime.now().year
        total = UserRepository.get_yearly_view_count(self._db, q.user_id, year) or 0
        return {"user_id": q.user_id, "total_views": int(total), "year": year}

    def handle_favorite_creator(self, q: GetUserFavoriteCreatorQuery) -> dict:
        self.handle_get_by_id(GetUserByIdQuery(user_id=q.user_id))
        year = q.year if q.year is not None else datetime.now().year
        result = UserRepository.get_favorite_creator(self._db, q.user_id, year)
        if not result:
            return {
                "user_id": q.user_id,
                "year": year,
                "favorite_creator": None,
                "message": "No views found for this year",
            }
        channel_name, view_count = result
        return {
            "user_id": q.user_id,
            "year": year,
            "favorite_creator": channel_name,
            "videos_watched": int(view_count or 0),
        }

    def handle_reactions_count(self, q: GetUserReactionsCountQuery) -> dict:
        self.handle_get_by_id(GetUserByIdQuery(user_id=q.user_id))
        year = q.year if q.year is not None else datetime.now().year
        comments_count, reacts_count = UserRepository.get_yearly_reaction_counts(
            self._db, q.user_id, year
        )
        total = int((comments_count or 0) + (reacts_count or 0))
        return {"user_id": q.user_id, "year": year, "total_reactions": total}

    def handle_average_view_time(self, q: GetUserAverageViewTimeQuery) -> dict:
        self.handle_get_by_id(GetUserByIdQuery(user_id=q.user_id))
        avg = UserRepository.get_avg_view_percentage(self._db, q.user_id)
        if avg is None:
            return {"user_id": q.user_id, "average_view_percents": 0.0}
        return {
            "user_id": q.user_id,
            "average_view_percents": round(float(avg) * 100.0, 2),
        }

    def handle_credibility(self, q: GetUserCredibilityQuery) -> UserCredibilityResponse:
        self.handle_get_by_id(GetUserByIdQuery(user_id=q.user_id))
        result = UserRepository.get_credibility_data(self._db, q.user_id)
        u_id, username, total, approved = result
        total, approved = (total or 0), (approved or 0)
        score = (approved / total * 100) if total > 0 else 0
        return UserCredibilityResponse(
            user_id=u_id,
            username=username,
            total_reports=total,
            approved_reports=approved,
            credibility_score=round(score, 2),
        )


class VideoQueryHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle_get_video(self, q: GetVideoByIdQuery) -> VideoResponse:
        video = VideoRepository.get_by_id(self._db, q.video_id)
        if not video:
            raise NotFoundError("Video not found")
        d_video = video_to_domain(video)
        return VideoResponse(
            id=d_video.id,
            title=d_video.title.value,
            description=d_video.description.value if d_video.description else None,
            channel_id=d_video.channel_id,
            uploaded_at=d_video.uploaded_at,
            is_active=d_video.is_active,
            is_monetized=d_video.is_monetized,
        )

    def handle_stats(self, q: GetVideoStatsQuery) -> VideoStatsResponse:
        video = VideoRepository.get_by_id(self._db, q.video_id)
        if not video:
            raise NotFoundError("Video not found")
        total_views, likes, dislikes, total_comments = VideoRepository.get_stats(self._db, q.video_id)
        d_video = video_to_domain(video)
        return VideoStatsResponse(
            video_id=q.video_id,
            title=d_video.title.value,
            total_views=total_views or 0,
            likes=likes or 0,
            dislikes=dislikes or 0,
            total_comments=total_comments,
        )

    def handle_comments(self, q: GetVideoCommentsQuery) -> VideoCommentsResponse:
        video = VideoRepository.get_by_id(self._db, q.video_id)
        if not video:
            raise NotFoundError("Video not found")
        d_video = video_to_domain(video)
        skip = (q.page - 1) * q.limit
        total_count, comments = VideoRepository.get_comments(self._db, q.video_id, skip, q.limit)
        return VideoCommentsResponse(
            video_id=q.video_id,
            title=d_video.title.value,
            comments=[
                CommentResponse(
                    id=comment_to_domain(comment).id,
                    comment_text=comment_to_domain(comment).comment_text.value,
                    commented_at=comment_to_domain(comment).commented_at,
                    user_id=comment_to_domain(comment).user_id,
                    username=username,
                )
                for comment, username in comments
            ],
            total_comments=total_count,
            page=q.page,
            limit=q.limit,
            total_pages=(total_count + q.limit - 1) // q.limit,
        )


class PlaylistQueryHandler:
    def __init__(self, db: Session):
        self._db = db

    def handle_user_playlists(self, q: GetUserPlaylistsQuery) -> list[dict]:
        if not PlaylistRepository.get_user(self._db, q.user_id):
            raise NotFoundError("User not found")
        playlists = PlaylistRepository.get_all_by_user(self._db, q.user_id)
        return [
            {
                "id": (d := playlist_to_domain(p)).id,
                "name": d.name.value,
                "created_at": d.created_at,
                "author_id": d.author_id,
            }
            for p in playlists
        ]

    def handle_get_playlist(self, q: GetPlaylistQuery) -> dict:
        playlist = PlaylistRepository.get_by_id(self._db, q.playlist_id, q.user_id)
        if not playlist:
            raise NotFoundError("Playlist not found")
        d_playlist = playlist_to_domain(playlist)
        return {
            "id": d_playlist.id,
            "name": d_playlist.name.value,
            "created_at": d_playlist.created_at,
            "author_id": d_playlist.author_id,
        }


class AdminQueryHandler:
    def __init__(self, db: Session):
        self._db = db

    def get_video_by_id(self, video_id: int):
        video = AdminRepository.get_video_by_id(self._db, video_id)
        if not video:
            raise NotFoundError("Video not found")
        return video

    def get_user_by_id(self, user_id: int):
        user = AdminRepository.get_user_by_id(self._db, user_id)
        if not user:
            raise NotFoundError("User not found")
        return user

    def get_channel_by_id(self, channel_id: int):
        channel = AdminRepository.get_channel_by_id(self._db, channel_id)
        if not channel:
            raise NotFoundError("Channel not found")
        return channel

    def handle_reports(self, q: GetReportsQuery) -> ReportsListResponse:
        reports = AdminRepository.get_all_reports(self._db, q.resolved, q.skip, q.limit)
        return ReportsListResponse(
            reports=[
                ReportResponse(
                    id=report.id,
                    reason=report.reason,
                    created_at=report.created_at,
                    is_resolved=report.is_resolved,
                    reporter_id=report.reporter_id,
                    video_id=report.video_id,
                )
                for report in reports
            ],
            count=len(reports),
            skip=q.skip,
            limit=q.limit,
        )

    def handle_detailed_reports(self, q: GetDetailedReportsQuery) -> DetailedReportsListResponse:
        results = AdminRepository.get_reports_with_details(self._db, q.resolved, q.skip, q.limit)
        return DetailedReportsListResponse(
            reports=[
                DetailedReportResponse(
                    id=report.id,
                    reason=report.reason,
                    created_at=report.created_at,
                    is_resolved=report.is_resolved,
                    reporter=ReporterInfo(id=report.reporter_id, username=username),
                    video=VideoInfo(id=report.video_id, title=title),
                )
                for report, username, title in results
            ],
            count=len(results),
            skip=q.skip,
            limit=q.limit,
        )

    def handle_problematic_users(self, q: GetProblematicUsersQuery) -> ProblematicUsersListResponse:
        results = AdminRepository.get_problematic_users(self._db, q.min_reports, q.skip, q.limit)
        return ProblematicUsersListResponse(
            users=[
                ProblematicUserResponse(
                    id=user_id,
                    username=username,
                    email=email,
                    is_banned=is_banned,
                    reports_created=reports_count,
                )
                for user_id, username, email, is_banned, reports_count in results
            ],
            count=len(results),
            min_reports_threshold=q.min_reports,
        )

    def handle_channels_reports_analytics(
        self, q: GetChannelsReportsAnalyticsQuery
    ) -> ChannelAnalyticsListResponse:
        results = AdminRepository.get_channels_with_reports_analytics(self._db, q.min_reports, q.limit)

        analytics: list[ChannelAnalyticsResponse] = []
        for (
            channel_id,
            channel_name,
            strikes,
            owner_username,
            total_reports,
            reported_videos_count,
            unique_reporters,
            resolved_percentage,
        ) in results:
            # simple risk heuristic
            risk_level = "LOW"
            if total_reports >= 10 or strikes >= 3:
                risk_level = "HIGH"
            elif total_reports >= 3 or strikes >= 1:
                risk_level = "MEDIUM"

            analytics.append(
                ChannelAnalyticsResponse(
                    channel=ChannelInfo(
                        id=channel_id,
                        name=channel_name,
                        strikes=strikes,
                        owner_username=owner_username,
                    ),
                    report_stats=ReportStats(
                        total_reports=int(total_reports or 0),
                        reported_videos_count=int(reported_videos_count or 0),
                        unique_reporters=int(unique_reporters or 0),
                        resolved_percentage=float(resolved_percentage or 0.0),
                    ),
                    risk_level=risk_level,
                )
            )

        return ChannelAnalyticsListResponse(
            analytics=analytics,
            count=len(analytics),
            min_reports_threshold=q.min_reports,
        )
