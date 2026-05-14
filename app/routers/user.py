from fastapi import APIRouter, status

from app.cqs.commands import SoftDeleteUserCommand, UpdateUserCommand
from app.cqs.handlers import SoftDeleteUserCommandHandler, UpdateUserCommandHandler, UserQueryHandler
from app.cqs.queries import (
    GetAllUsersQuery,
    GetUserAverageViewTimeQuery,
    GetUserByIdQuery,
    GetUserCredibilityQuery,
    GetUserFavoriteCreatorQuery,
    GetUserReactionsCountQuery,
    GetUserRecommendationsQuery,
    GetUserYearlyViewsQuery,
)
from app.db.session import DBDep
from app.schemas.schemas import (
    UserCredibilityResponse,
    UserDetailedResponse,
    UserUpdate,
    VideoResponse,
)

router = APIRouter(tags=["user"], prefix="/user")

@router.get("/", response_model=dict[str, list[UserDetailedResponse]])
async def get_all_users(db: DBDep):
    return {"users": UserQueryHandler(db).handle_get_all(GetAllUsersQuery())}

@router.patch("/{user_id}", response_model=UserDetailedResponse)
async def update_user(user_id: int, user_data: UserUpdate, db: DBDep):
    UpdateUserCommandHandler(db).handle(
        UpdateUserCommand(
            user_id=user_id,
            username=user_data.username,
            email=str(user_data.email) if user_data.email is not None else None,
            is_moderator=user_data.is_moderator,
        )
    )
    return UserQueryHandler(db).handle_get_by_id(GetUserByIdQuery(user_id=user_id))

@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def soft_delete_user(user_id: int, db: DBDep):
    SoftDeleteUserCommandHandler(db).handle(SoftDeleteUserCommand(user_id=user_id))
    return None

@router.get("/{user_id}/recommendations", response_model=dict[str, list[VideoResponse]])
async def get_recommendations(user_id: int, db: DBDep, limit: int = 20):
    return {
        "videos": UserQueryHandler(db).handle_recommendations(
            GetUserRecommendationsQuery(user_id=user_id, limit=limit)
        )
    }

@router.get("/{user_id}/views")
async def get_user_year_views(user_id: int, db: DBDep):
    return UserQueryHandler(db).handle_yearly_views(GetUserYearlyViewsQuery(user_id=user_id))

@router.get("/{user_id}/favoriteCreator")
async def get_user_favorite_creator(user_id: int, db: DBDep):
    return UserQueryHandler(db).handle_favorite_creator(
        GetUserFavoriteCreatorQuery(user_id=user_id)
    )

@router.get("/{user_id}/reactions")
async def get_user_year_reactions(user_id: int, db: DBDep):
    return UserQueryHandler(db).handle_reactions_count(
        GetUserReactionsCountQuery(user_id=user_id)
    )

@router.get("/{user_id}/averageViewTime")
async def get_user_avg_view_time(user_id: int, db: DBDep):
    return UserQueryHandler(db).handle_average_view_time(
        GetUserAverageViewTimeQuery(user_id=user_id)
    )

@router.get("/{user_id}/credibility", response_model=UserCredibilityResponse)
async def get_user_credibility(user_id: int, db: DBDep):
    return UserQueryHandler(db).handle_credibility(GetUserCredibilityQuery(user_id=user_id))