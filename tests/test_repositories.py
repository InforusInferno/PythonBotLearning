import pytest
import sys
import os
from utils.repositories import StudyRepository, TriviaRepository, CustomTriviaRepository, ModerationRepository, LevelingRepository

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

@pytest.fixture
def temp_study_file(tmp_path):
    file_path = tmp_path / "study_stats.json"
    return str(file_path)

@pytest.fixture
def temp_trivia_file(tmp_path):
    file_path = tmp_path / "trivia_scores.json"
    return str(file_path)

@pytest.mark.asyncio
async def test_study_repository_add_time(temp_study_file):
    repo = StudyRepository(file_path=temp_study_file)

    await repo.add_study_time(user_id=123, minutes=30)
    assert await repo.get_study_time(123) == 30

    await repo.add_study_time(user_id=123, minutes=15)
    assert await repo.get_study_time(123) == 45

    await repo.add_study_time(user_id=456, minutes=60)
    assert await repo.get_study_time(456) == 60
    assert await repo.get_study_time(123) == 45

@pytest.mark.asyncio
async def test_trivia_repository_add_score(temp_trivia_file):
    repo = TriviaRepository(file_path=temp_trivia_file)

    guild_id =999
    user_id= 123

    await repo.add_score(guild_id=guild_id, user_id=user_id, points=1)
    scores = await repo.get_guild_scores(guild_id)
    assert str(user_id) in scores
    assert scores[str(user_id)] == 1

    await repo.add_score(guild_id=guild_id, user_id=user_id, points=2)
    scores = await repo.get_guild_scores(guild_id)
    assert scores[str(user_id)] == 3

    empty_scores = await repo.get_guild_scores(888)
    assert empty_scores == {}

@pytest.fixture
def temp_leveling_file(tmp_path):
    file_path = tmp_path / "xp_stats.json"
    return str(file_path)

@pytest.fixture
def temp_mod_file(tmp_path):
    file_path = tmp_path / "automod_settings.json"
    return str(file_path)

@pytest.mark.asyncio
async def test_leveling_repository(temp_leveling_file):
    repo = LevelingRepository(file_path=temp_leveling_file)
    guild_id = 999
    user_id = 123

    await repo.add_xp(guild_id, user_id, 15)
    assert await repo.get_xp(guild_id, user_id) == 15

    await repo.add_xp(guild_id, user_id, 20)
    assert await repo.get_xp(guild_id, user_id) == 35

    assert await repo.get_xp(888, 123) == 0

@pytest.mark.asyncio
async def test_moderation_repository(temp_mod_file):
    repo = ModerationRepository(file_path=temp_mod_file)
    guild_id = 999

    await repo.add_banned_word(guild_id, "badword")
    words = await repo.get_banned_words(guild_id)
    assert "badword" in words

    await repo.add_banned_word(guild_id, "BADWORD")
    words = await repo.get_banned_words(guild_id)
    assert len(words) == 1

    await repo.remove_banned_word(guild_id, "BadWord")
    words = await repo.get_banned_words(guild_id)
    assert "badword" not in words

@pytest.fixture
def temp_custom_trivia_file(tmp_path):
    file_path = tmp_path / "custom_trivia.json"
    return str(file_path)

@pytest.mark.asyncio
async def test_custom_trivia_repository(temp_custom_trivia_file):
    repo = CustomTriviaRepository(file_path=temp_custom_trivia_file)
    guild_id = 999

    await repo.add_question(
        guild_id,
        "What color is the sky?",
        "Blue",
        ["Green", "Red", "Yellow"],
        123
    )

    questions = await repo.get_questions(guild_id) 
    assert len(questions) == 1
    assert questions[0]["question"] == "What color is the sky?"
    assert questions[0]["correct_answer"] == "Blue"
    assert questions[0]["incorrect_answers"] == ["Green", "Red", "Yellow"]

    empty_questions = await repo.get_questions(888)
    assert empty_questions == []