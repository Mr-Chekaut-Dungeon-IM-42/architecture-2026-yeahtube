from fastapi import APIRouter, Depends, status

from app.cqs.commands import RegisterUserCommand
from app.cqs.handlers import AuthQueryHandler, LoginUserCommandHandler, RegisterUserCommandHandler
from app.cqs.queries import GetCurrentUserInfoQuery
from app.db.models import User
from app.db.session import DBDep
from app.dependencies import get_current_user
from app.schemas.schemas import Token, UserLogin, UserOut, UserRegister

router = APIRouter(tags=["auth"], prefix="/auth")


@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def register(user_data: UserRegister, db: DBDep) -> UserOut:
    handler = RegisterUserCommandHandler(db)
    user_id = handler.handle(
        RegisterUserCommand(
            username=user_data.username,
            email=user_data.email,
            password=user_data.password,
        )
    )
    # Optional: commands may return only the created entity ID. We then query read-model.
    return AuthQueryHandler(db).handle_current_user(GetCurrentUserInfoQuery(user_id=user_id))


@router.post("/login", response_model=Token)
async def login(credentials: UserLogin, db: DBDep) -> Token:
    return LoginUserCommandHandler(db).handle(credentials.username, credentials.password)


@router.get("/me", response_model=UserOut)
async def get_current_user_info(
    current_user: User = Depends(get_current_user),
) -> UserOut:
    return UserOut(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_moderator=current_user.is_moderator,
        is_banned=current_user.is_banned,
        created_at=current_user.created_at,
    )
