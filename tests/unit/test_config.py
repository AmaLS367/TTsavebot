from pathlib import Path

from video_bot import config


def test_load_settings_reads_values_from_dotenv(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "BOT_TOKEN=test-token",
                "SUPERADMINS=1, 2",
                "DOWNLOADS_DIR=tmp-downloads",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(config, "DEFAULT_ENV_FILE", env_file)
    monkeypatch.delenv("BOT_TOKEN", raising=False)
    monkeypatch.delenv("SUPERADMINS", raising=False)
    monkeypatch.delenv("DOWNLOADS_DIR", raising=False)

    settings = config.load_settings()

    assert settings.bot_token == "test-token"
    assert settings.superadmins == (1, 2)
    assert settings.downloads_dir == Path("tmp-downloads")


def test_load_settings_does_not_override_existing_environment(tmp_path: Path, monkeypatch) -> None:
    env_file = tmp_path / ".env"
    env_file.write_text(
        "\n".join(
            [
                "BOT_TOKEN=file-token",
                "SUPERADMINS=99",
            ]
        ),
        encoding="utf-8",
    )

    monkeypatch.setattr(config, "DEFAULT_ENV_FILE", env_file)
    monkeypatch.setenv("BOT_TOKEN", "env-token")
    monkeypatch.setenv("SUPERADMINS", "42")

    settings = config.load_settings()

    assert settings.bot_token == "env-token"
    assert settings.superadmins == (42,)
