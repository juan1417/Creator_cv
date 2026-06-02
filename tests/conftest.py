"""Pytest fixtures for the Creator CV test suite."""

from __future__ import annotations

import pytest
from app import create_app
from creator_cv.extensions import db
from creator_cv.models import User


@pytest.fixture
def app():
    app = create_app()
    app.config.update(TESTING=True, WTF_CSRF_ENABLED=False, SQLALCHEMY_DATABASE_URI="sqlite:///:memory:")
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def user(app):
    with app.app_context():
        u = User(email="test@example.com", full_name="Test User")
        u.set_password("supersecret")
        db.session.add(u)
        db.session.commit()
        return u.id
