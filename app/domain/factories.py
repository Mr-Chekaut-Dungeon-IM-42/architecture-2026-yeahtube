from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from app.domain.errors import DomainError
from app.domain.models import UserD
from app.domain.repositories import UserUniquenessChecker
from app.domain.value_objects import BoundedText, Email


@dataclass(slots=True)
class UserFactory:
    """Creates domain users enforcing invariants.

    Simple invariants:
      - username length
      - email format

    Complex invariants (DB-backed):
      - username uniqueness
      - email uniqueness

    NOTE: This factory does not create HTTP errors.
    """

    uniqueness: UserUniquenessChecker

    def register_new_user(
        self,
        *,
        username: str,
        email: str,
        created_at: date,
        is_moderator: bool = False,
    ) -> UserD:
        # Simple invariants via VOs (raise DomainValidationError -> InvariantViolation).
        username_vo = BoundedText(username, 3, 32)
        email_vo = Email(email)

        # Complex invariants via DIP.
        if self.uniqueness.username_exists(username_vo.value):
            raise DomainError("Username is already taken")
        if self.uniqueness.email_exists(email_vo.value):
            raise DomainError("Email is already registered")

        # id is unknown before persistence; in an anemic model we can use 0/None.
        # Here we use 0 to keep the type simple (int). Persistence assigns a real id.
        return UserD(
            id=0,
            username=username_vo,
            email=email_vo,
            created_at=created_at,
            is_moderator=is_moderator,
            is_deleted=False,
            is_banned=False,
        )
