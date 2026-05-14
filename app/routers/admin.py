from fastapi import APIRouter, Depends

from app.cqs.commands import (
    AddChannelStrikeCommand,
    BanUserCommand,
    DeactivateVideoCommand,
    DemonetizeVideoCommand,
    ResolveReportCommand,
)
from app.cqs.handlers import (
    AddChannelStrikeCommandHandler,
    AdminQueryHandler,
    BanUserCommandHandler,
    DeactivateVideoCommandHandler,
    DemonetizeVideoCommandHandler,
    ResolveReportCommandHandler,
)
from app.cqs.queries import (
    GetChannelsReportsAnalyticsQuery,
    GetDetailedReportsQuery,
    GetProblematicUsersQuery,
    GetReportsQuery,
)
from app.db.session import DBDep
from app.dependencies import require_admin
from app.repositories.admin import AdminRepository
from app.schemas.schemas import (
    ChannelAnalyticsListResponse,
    ChannelStrikeResponse,
    DetailedReportsListResponse,
    ProblematicUsersListResponse,
    ReportResolveResponse,
    ReportsListResponse,
    UserBanResponse,
    VideoDeactivateResponse,
    VideoDemonetizeResponse,
)

router = APIRouter(
    tags=["admin"], prefix="/admin", dependencies=[Depends(require_admin)]
)


@router.patch("/video/{video_id}/deactivate", response_model=VideoDeactivateResponse)
async def deactivate_video(video_id: int, db: DBDep) -> VideoDeactivateResponse:
    DeactivateVideoCommandHandler(db).handle(DeactivateVideoCommand(video_id=video_id))
    video = AdminQueryHandler(db).get_video_by_id(video_id)
    return VideoDeactivateResponse(
        message="Video deactivated successfully",
        video_id=video.id,
        title=video.title,
        is_active=video.is_active,
    )


@router.patch("/video/{video_id}/demonetize", response_model=VideoDemonetizeResponse)
async def demonetize_video(video_id: int, db: DBDep) -> VideoDemonetizeResponse:
    DemonetizeVideoCommandHandler(db).handle(DemonetizeVideoCommand(video_id=video_id))
    video = AdminQueryHandler(db).get_video_by_id(video_id)
    return VideoDemonetizeResponse(
        message="Video demonetized successfully",
        video_id=video.id,
        title=video.title,
        is_monetized=video.is_monetized,
    )


@router.post("/user/{user_id}/ban", response_model=UserBanResponse)
async def ban_user(user_id: int, db: DBDep) -> UserBanResponse:
    BanUserCommandHandler(db).handle(BanUserCommand(user_id=user_id))
    user = AdminQueryHandler(db).get_user_by_id(user_id)
    return UserBanResponse(
        message="User banned successfully",
        user_id=user.id,
        username=user.username,
        is_banned=user.is_banned,
    )


@router.post("/channel/{channel_id}/strike", response_model=ChannelStrikeResponse)
async def add_channel_strike(channel_id: int, db: DBDep) -> ChannelStrikeResponse:
    AddChannelStrikeCommandHandler(db).handle(AddChannelStrikeCommand(channel_id=channel_id))
    channel = AdminQueryHandler(db).get_channel_by_id(channel_id)
    strikes = AdminRepository.get_channel_strikes_count(db, channel_id)
    penalty_message = ""
    if strikes >= 3:
        penalty_message = " Channel has reached 3 strikes and may face additional penalties."
    return ChannelStrikeResponse(
        message=f"Strike added to channel successfully.{penalty_message}",
        channel_id=channel.id,
        channel_name=channel.name,
        strikes=strikes,
    )


@router.get("/reports", response_model=ReportsListResponse)
async def get_all_reports(
    db: DBDep, resolved: bool | None = None, skip: int = 0, limit: int = 50
) -> ReportsListResponse:
    return AdminQueryHandler(db).handle_reports(
        GetReportsQuery(resolved=resolved, skip=skip, limit=limit)
    )


@router.patch("/report/{report_id}/resolve", response_model=ReportResolveResponse)
async def resolve_report(report_id: int, db: DBDep) -> ReportResolveResponse:
    ResolveReportCommandHandler(db).handle(ResolveReportCommand(report_id=report_id))
    report = AdminRepository.get_report_by_id(db, report_id)
    assert report is not None
    return ReportResolveResponse(
        message="Report resolved successfully",
        report_id=report.id,
        is_resolved=report.is_resolved,
        video_id=report.video_id,
    )


@router.get("/reports/detailed", response_model=DetailedReportsListResponse)
async def get_reports_with_details(
    db: DBDep, resolved: bool | None = None, skip: int = 0, limit: int = 50
) -> DetailedReportsListResponse:
    return AdminQueryHandler(db).handle_detailed_reports(
        GetDetailedReportsQuery(resolved=resolved, skip=skip, limit=limit)
    )


@router.get("/users/problematic", response_model=ProblematicUsersListResponse)
async def get_problematic_users(
    db: DBDep, min_reports: int = 3, skip: int = 0, limit: int = 50
) -> ProblematicUsersListResponse:
    return AdminQueryHandler(db).handle_problematic_users(
        GetProblematicUsersQuery(min_reports=min_reports, skip=skip, limit=limit)
    )


@router.get(
    "/analytics/channels-reports-stats", response_model=ChannelAnalyticsListResponse
)
async def get_channels_with_reports_analytics(
    db: DBDep, min_reports: int = 1, limit: int = 20
) -> ChannelAnalyticsListResponse:
    return AdminQueryHandler(db).handle_channels_reports_analytics(
        GetChannelsReportsAnalyticsQuery(min_reports=min_reports, limit=limit)
    )
