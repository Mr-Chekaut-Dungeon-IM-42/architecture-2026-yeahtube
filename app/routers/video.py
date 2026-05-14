from fastapi import APIRouter, Query, status

from app.cqs.commands import (
    CreateVideoCommand,
    CreateVideoWithCommentCommand,
    DeleteVideoCommand,
    UpdateVideoCommand,
)
from app.cqs.handlers import (
    CreateVideoCommandHandler,
    CreateVideoWithCommentCommandHandler,
    DeleteVideoCommandHandler,
    UpdateVideoCommandHandler,
    VideoQueryHandler,
)
from app.cqs.queries import GetVideoByIdQuery, GetVideoCommentsQuery, GetVideoStatsQuery
from app.db.session import DBDep
from app.schemas.schemas import (
    VideoCreate,
    VideoResponse,
    VideoStatsResponse,
    VideoUpdate,
    VideoWithCommentCreate,
    VideoWithCommentResponse,
)

router = APIRouter(tags=["video"], prefix="/video")

@router.get("/{video_id}", response_model=VideoResponse)
async def get_video(video_id: int, db: DBDep):
    return VideoQueryHandler(db).handle_get_video(GetVideoByIdQuery(video_id=video_id))

@router.post("/", status_code=status.HTTP_201_CREATED, response_model=VideoResponse)
async def create_video(video_data: VideoCreate, db: DBDep):
    handler = CreateVideoCommandHandler(db)
    video_id = handler.handle(
        CreateVideoCommand(
            title=video_data.title,
            description=video_data.description,
            channel_id=video_data.channel_id,
            is_active=video_data.is_active,
            is_monetized=video_data.is_monetized,
        )
    )
    return VideoQueryHandler(db).handle_get_video(GetVideoByIdQuery(video_id=video_id))

@router.patch("/{video_id}", response_model=VideoResponse)
async def update_video(video_id: int, video_data: VideoUpdate, db: DBDep):
    UpdateVideoCommandHandler(db).handle(
        UpdateVideoCommand(
            video_id=video_id,
            title=video_data.title,
            description=video_data.description,
            is_active=video_data.is_active,
            is_monetized=video_data.is_monetized,
        )
    )
    return VideoQueryHandler(db).handle_get_video(GetVideoByIdQuery(video_id=video_id))

@router.delete("/{video_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_video(video_id: int, db: DBDep):
    DeleteVideoCommandHandler(db).handle(DeleteVideoCommand(video_id=video_id))
    return None

@router.get("/{video_id}/stats", response_model=VideoStatsResponse)
async def get_video_stats(video_id: int, db: DBDep):
    return VideoQueryHandler(db).handle_stats(GetVideoStatsQuery(video_id=video_id))

@router.get("/{video_id}/comments")
async def get_video_comments(
    video_id: int,
    db: DBDep,
    page: int = Query(1, ge=1, description="Page number, starting from 1"),
    limit: int = Query(10, ge=1, le=100, description="Number of items per page")
):
    return VideoQueryHandler(db).handle_comments(
        GetVideoCommentsQuery(video_id=video_id, page=page, limit=limit)
    )

@router.post("/with-comment", status_code=status.HTTP_201_CREATED, response_model=VideoWithCommentResponse)
async def create_video_with_comment(video_data: VideoWithCommentCreate, db: DBDep):
    video_id, comment_id = CreateVideoWithCommentCommandHandler(db).handle(
        CreateVideoWithCommentCommand(
            title=video_data.title,
            description=video_data.description,
            channel_id=video_data.channel_id,
            initial_comment=video_data.initial_comment,
            is_active=video_data.is_active,
            is_monetized=video_data.is_monetized,
        )
    )
    video = VideoQueryHandler(db).handle_get_video(GetVideoByIdQuery(video_id=video_id))
    return VideoWithCommentResponse(
        video=video,
        comment_id=comment_id,
        comment_text=video_data.initial_comment,
    )