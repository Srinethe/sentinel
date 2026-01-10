import pytest
import os
from unittest.mock import patch
from app.config import Settings, get_settings


def test_settings_loads_from_env(monkeypatch):
    """Test that Settings loads environment variables correctly"""
    monkeypatch.setenv("ANTHROPIC_API_KEY", "test-anthropic-key")
    monkeypatch.setenv("OPENAI_API_KEY", "test-openai-key")
    
    settings = Settings()
    assert settings.anthropic_api_key == "test-anthropic-key"
    assert settings.openai_api_key == "test-openai-key"
    assert settings.app_name == "Project Sentinel"
    assert settings.debug is True


def test_settings_defaults():
    """Test that Settings has correct defaults"""
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test-key",
        "OPENAI_API_KEY": "test-key"
    }):
        settings = Settings()
        assert settings.app_name == "Project Sentinel"
        assert settings.debug is True


def test_get_settings_cached():
    """Test that get_settings uses LRU cache"""
    with patch.dict(os.environ, {
        "ANTHROPIC_API_KEY": "test-key",
        "OPENAI_API_KEY": "test-key"
    }):
        settings1 = get_settings()
        settings2 = get_settings()
        # Should return same instance due to caching
        assert settings1 is settings2
