from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services import review_service
from app.services.review_service import AlreadyReviewed

USER = {
    "_id": "user_id_abc",
    "email": "nasser@example.com",
    "plan": "pro",
}


async def test_submit_ok():
    review_repo = MagicMock()
    review_repo.find_by_user_id = AsyncMock(return_value=None)
    created_at = datetime.now(timezone.utc)
    expected_doc = {
        "_id": "review_id_xyz",
        "first_name": "Nasser",
        "company": "Voclaire",
        "content": "Excellent outil de transcription.",
        "rating": 5,
        "plan": "pro",
        "created_at": created_at,
    }
    review_repo.create = AsyncMock(return_value=expected_doc)

    result = await review_service.submit(
        user=USER,
        first_name="Nasser",
        company="Voclaire",
        content="Excellent outil de transcription.",
        rating=5,
        review_repo=review_repo,
    )

    assert result.id == "review_id_xyz"
    assert result.first_name == "Nasser"
    assert result.company == "Voclaire"
    assert result.content == "Excellent outil de transcription."
    assert result.rating == 5
    assert result.plan == "pro"
    assert result.created_at == created_at
    review_repo.create.assert_awaited_once_with(
        user_id="user_id_abc",
        first_name="Nasser",
        company="Voclaire",
        plan="pro",
        content="Excellent outil de transcription.",
        rating=5,
    )


async def test_submit_already_reviewed():
    review_repo = MagicMock()
    review_repo.find_by_user_id = AsyncMock(
        return_value={"_id": "review_existant", "rating": 4}
    )

    with pytest.raises(AlreadyReviewed):
        await review_service.submit(
            user=USER,
            first_name="Nasser",
            company="Voclaire",
            content="Deuxième avis.",
            rating=3,
            review_repo=review_repo,
        )

    review_repo.create.assert_not_called()


async def test_list_public_delegates_to_repo():
    review_repo = MagicMock()
    created_at = datetime.now(timezone.utc)
    avis = [
        {
            "_id": "r1",
            "first_name": "Nasser",
            "company": "Voclaire",
            "content": "Top.",
            "rating": 5,
            "plan": "pro",
            "created_at": created_at,
        },
        {
            "_id": "r2",
            "first_name": "Zeinab",
            "company": "Acme",
            "content": "Très pratique.",
            "rating": 4,
            "plan": "free",
            "created_at": created_at,
        },
    ]
    review_repo.get_visible = AsyncMock(return_value=avis)

    result = await review_service.list_public(review_repo=review_repo)

    assert [r.id for r in result] == ["r1", "r2"]
    assert [r.first_name for r in result] == ["Nasser", "Zeinab"]
    assert [r.company for r in result] == ["Voclaire", "Acme"]
    review_repo.get_visible.assert_awaited_once()
