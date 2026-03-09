from dataclasses import dataclass
from datetime import datetime, timezone

import pytest

from video_bot.core.entities import User, UserRole
from video_bot.core.interfaces import IAccessRepository
from video_bot.core.use_cases import CheckAccessUseCase


@dataclass
class FakeAccessRepository(IAccessRepository):
    user: User | None

    async def get_user(self, telegram_id: int) -> User | None:
        return self.user

    async def upsert_user(self, telegram_id: int, role: UserRole) -> User:
        if self.user is None:
            raise RuntimeError("No user configured")
        return self.user

    async def deactivate_user(self, telegram_id: int) -> None:
        return None

    async def list_active_users(self) -> list[User]:
        return [self.user] if self.user is not None else []


@pytest.mark.asyncio
async def test_check_access_returns_superadmin() -> None:
    user = User(
        telegram_id=1,
        role=UserRole.SUPERADMIN,
        is_active=True,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    use_case = CheckAccessUseCase(FakeAccessRepository(user=user))

    result = await use_case.execute(telegram_id=1)

    assert result == user


@pytest.mark.asyncio
async def test_check_access_returns_none_for_inactive_user() -> None:
    user = User(
        telegram_id=2,
        role=UserRole.USER,
        is_active=False,
        created_at=datetime.now(tz=timezone.utc),
        updated_at=datetime.now(tz=timezone.utc),
    )
    use_case = CheckAccessUseCase(FakeAccessRepository(user=user))

    result = await use_case.execute(telegram_id=2)

    assert result is None


@pytest.mark.asyncio
async def test_check_access_returns_none_when_user_not_found() -> None:
    use_case = CheckAccessUseCase(FakeAccessRepository(user=None))

    result = await use_case.execute(telegram_id=99)

    assert result is None
