"""
Basic tests for the Portfolio Flask app.
Run: pytest tests/ -v
"""
import pytest
import os
os.environ.setdefault("DATABASE_URL", "sqlite:///:memory:")
os.environ.setdefault("SECRET_KEY", "test-secret")

from app import app, db, Project


@pytest.fixture
def client():
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["WTF_CSRF_ENABLED"] = False
    with app.test_client() as c:
        with app.app_context():
            db.create_all()
            yield c
            db.drop_all()


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert b"ok" in r.data


def test_index(client):
    r = client.get("/")
    assert r.status_code == 200


def test_projects_page(client):
    r = client.get("/projects")
    assert r.status_code == 200


def test_api_projects(client):
    r = client.get("/api/projects")
    assert r.status_code == 200
    assert r.json is not None


def test_create_project(client):
    r = client.post("/projects/new", data={
        "title": "Test Project",
        "description": "A test project description",
        "tech_stack": "Python, Flask",
        "category": "Web",
        "github_url": "",
        "live_url": "",
    }, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        p = Project.query.filter_by(title="Test Project").first()
        assert p is not None


def test_edit_project(client):
    with app.app_context():
        p = Project(title="Old Title", description="desc", tech_stack="", category="Web")
        db.session.add(p)
        db.session.commit()
        pid = p.id

    r = client.post(f"/projects/{pid}/edit", data={
        "title": "New Title",
        "description": "Updated description",
        "tech_stack": "Flask",
        "category": "Web",
        "github_url": "",
        "live_url": "",
    }, follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        updated = Project.query.get(pid)
        assert updated.title == "New Title"


def test_delete_project(client):
    with app.app_context():
        p = Project(title="To Delete", description="desc", tech_stack="", category="Web")
        db.session.add(p)
        db.session.commit()
        pid = p.id

    r = client.post(f"/projects/{pid}/delete", follow_redirects=True)
    assert r.status_code == 200
    with app.app_context():
        assert Project.query.get(pid) is None


def test_contact_form(client):
    r = client.post("/contact", data={
        "name": "Test User",
        "email": "test@example.com",
        "subject": "Hello",
        "body": "This is a test message",
    }, follow_redirects=True)
    assert r.status_code == 200
