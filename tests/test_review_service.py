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
    expected_doc = {
        "_id": "review_id_xyz",
        "author_name": "nasser",
        "content": "Excellent outil de transcription.",
        "rating": 5,
        "plan": "pro",
    }
    review_repo.create = AsyncMock(return_value=expected_doc)

    result = await review_service.submit(
        user=USER,
        content="Excellent outil de transcription.",
        rating=5,
        review_repo=review_repo,
    )

    assert result == expected_doc
    review_repo.create.assert_awaited_once_with(
        user_id="user_id_abc",
        author_name="nasser",
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
            content="Deuxième avis.",
            rating=3,
            review_repo=review_repo,
        )

    review_repo.create.assert_not_called()


async def test_list_public_delegates_to_repo():
    review_repo = MagicMock()
    avis = [{"_id": "r1", "rating": 5}, {"_id": "r2", "rating": 4}]
    review_repo.get_visible = AsyncMock(return_value=avis)

    result = await review_service.list_public(review_repo=review_repo)

    assert result == avis
    review_repo.get_visible.assert_awaited_once()
