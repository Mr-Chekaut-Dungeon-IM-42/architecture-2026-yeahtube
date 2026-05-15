from datetime import date

from sqlalchemy.orm import Session

from app.db.models import User
from app.domain.errors import (
    ForbiddenError,
    UnauthorizedError,
)
from app.domain.factories import UserFactory
from app.infrastructure.repositories.user_uniqueness import SqlAlchemyUserUniquenessChecker
from app.repositories.auth import AuthRepository
from app.presentation.schemas.schemas import Token, UserLogin, UserOut, UserRegister
from app.utils.auth import create_access_token, get_password_hash, verify_password


class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> UserOut:
        checker = SqlAlchemyUserUniquenessChecker(db)
        factory = UserFactory(uniqueness=checker)

        _domain_user = factory.register_new_user(
            username=user_data.username,
            email=user_data.email,
            created_at=date.today(),
            is_moderator=False,
        )

        hashed_password = get_password_hash(user_data.password)

        try:
            new_user = AuthRepository.create_user(
                db=db,
                username=_domain_user.username.value,
                email=_domain_user.email.value,
                hashed_password=hashed_password,
            )
            response = UserOut(
                id=new_user.id,
                username=new_user.username,
                email=new_user.email,
                is_moderator=new_user.is_moderator,
                is_banned=new_user.is_banned,
                created_at=new_user.created_at,
            )
            db.commit()
            return response
        except Exception:
            db.rollback()
            raise

    @staticmethod
    def login_user(db: Session, credentials: UserLogin) -> Token:
        user = AuthRepository.get_user_by_username(db, credentials.username)

        if not user:
            raise UnauthorizedError("Incorrect username")

        if not verify_password(credentials.password, user.hashed_password):
            raise UnauthorizedError("Incorrect password")

        if user.is_banned:
            raise ForbiddenError("User account is banned")

        if user.is_deleted:
            raise ForbiddenError("User account is deleted")

        access_token = create_access_token(
            data={
                "user_id": user.id,
                "username": user.username,
                "is_moderator": user.is_moderator,
            }
        )

        return Token(access_token=access_token, token_type="bearer")

    @staticmethod
    def get_user_info(user: User) -> UserOut:
        return UserOut(
            id=user.id,
            username=user.username,
            email=user.email,
            is_moderator=user.is_moderator,
            is_banned=user.is_banned,
            created_at=user.created_at,
        )
