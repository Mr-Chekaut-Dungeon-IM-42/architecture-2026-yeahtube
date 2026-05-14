# Application layer: use-case orchestration
# Moved from app/services/auth.py

from datetime import date

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db.models import User
from app.domain.errors import DomainError
from app.domain.factories import UserFactory
from app.infrastructure.repositories.user_uniqueness import SqlAlchemyUserUniquenessChecker
from app.repositories.auth import AuthRepository
from app.schemas.schemas import Token, UserLogin, UserOut, UserRegister
from app.utils.auth import create_access_token, get_password_hash, verify_password


class AuthService:
    @staticmethod
    def register_user(db: Session, user_data: UserRegister) -> UserOut:
        try:
            checker = SqlAlchemyUserUniquenessChecker(db)
            factory = UserFactory(uniqueness=checker)

            _domain_user = factory.register_new_user(
                username=user_data.username,
                email=user_data.email,
                created_at=date.today(),
                is_moderator=False,
            )

            hashed_password = get_password_hash(user_data.password)

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

        except DomainError as e:
            # DomainError -> HTTP is better handled by presentation handlers,
            # but we keep the current behavior for compatibility.
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=str(e),
            )
        except Exception as e:
            db.rollback()
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create user: {str(e)}",
            )

    @staticmethod
    def login_user(db: Session, credentials: UserLogin) -> Token:
        user = AuthRepository.get_user_by_username(db, credentials.username)

        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if not verify_password(credentials.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        if user.is_banned:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is banned",
            )

        if user.is_deleted:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User account is deleted",
            )

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
