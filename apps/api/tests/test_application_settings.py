from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.application_settings import get_application_settings
from app.db import Base


def test_application_settings_persist_in_database() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        settings = get_application_settings(session)
        settings.max_upload_mb = 321
        settings.default_target_language = "fr"
        settings.translation_system_prompt = "Translate {source} to {target}."
        session.commit()

    with Session(engine) as session:
        settings = get_application_settings(session)
        assert settings.max_upload_mb == 321
        assert settings.default_target_language == "fr"
        assert settings.translation_system_prompt == "Translate {source} to {target}."


def test_environment_values_are_only_first_run_seeds() -> None:
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        first = get_application_settings(session)
        first.max_page_count = 42
        session.commit()
        assert get_application_settings(session).max_page_count == 42
