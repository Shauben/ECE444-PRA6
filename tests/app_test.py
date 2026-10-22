import pytest
from sqlalchemy import inspect

from project.app import create_app
from project.models import Post, db


@pytest.fixture
def app(tmp_path):
    application = create_app(
        {
            "TESTING": True,
            "SECRET_KEY": "test-only-key",
            "USERNAME": "Shaurya",
            "PASSWORD": "Shaurya",
            "SQLALCHEMY_DATABASE_URI": f"sqlite:///{tmp_path / 'test.db'}",
        }
    )
    with application.app_context():
        db.create_all()
    yield application
    with application.app_context():
        db.session.remove()
        db.drop_all()
        db.engine.dispose()


@pytest.fixture
def client(app):
    return app.test_client()


def login(client, username="Shaurya", password="Shaurya"):
    return client.post(
        "/login",
        data={"username": username, "password": password},
        follow_redirects=True,
    )


def seed_post(app, title="Example title", text="Example body"):
    with app.app_context():
        post = Post(title=title, text=text)
        db.session.add(post)
        db.session.commit()
        return post.id


def test_homepage(client, app):
    """The database is ready and an empty homepage loads."""
    response = client.get("/")
    assert response.status_code == 200
    assert b"No entries yet. Add some!" in response.data
    with app.app_context():
        assert "post" in inspect(db.engine).get_table_names()


def test_login_logout(client):
    """Reject wrong credentials, accept correct ones, then clear the session."""
    assert b"Invalid username" in login(client, username="wrong").data
    assert b"Invalid password" in login(client, password="wrong").data
    with client.session_transaction() as session:
        assert not session.get("logged_in")

    assert b"You were logged in" in login(client).data
    with client.session_transaction() as session:
        assert session["logged_in"] is True

    response = client.get("/logout", follow_redirects=True)
    assert b"You were logged out" in response.data
    with client.session_transaction() as session:
        assert "logged_in" not in session


def test_add_post(client, app):
    """Only a logged-in user can save a post, and it appears on the page."""
    data = {"title": "<Hello>", "text": "<strong>My first post</strong>"}
    assert client.post("/add", data=data).status_code == 401
    with app.app_context():
        assert db.session.execute(db.select(Post)).scalars().all() == []

    login(client)
    response = client.post("/add", data=data, follow_redirects=True)
    assert response.status_code == 200
    assert b"&lt;Hello&gt;" in response.data
    assert b"<strong>My first post</strong>" in response.data
    assert b"No entries yet. Add some!" not in response.data
    with app.app_context():
        posts = db.session.execute(db.select(Post)).scalars().all()
        assert len(posts) == 1
        assert posts[0].title == "<Hello>"
        assert posts[0].text == data["text"]


def test_delete_access(client, app):
    """Deny deletion before/after login; allow it while logged in."""
    post_id = seed_post(app)
    response = client.get(f"/delete/{post_id}")
    assert response.status_code == 401
    assert response.get_json() == {"status": 0, "message": "Please log in."}
    with app.app_context():
        assert db.session.get(Post, post_id) is not None

    login(client)
    response = client.get(f"/delete/{post_id}")
    assert response.status_code == 200
    assert response.get_json()["status"] == 1
    with app.app_context():
        assert db.session.get(Post, post_id) is None

    another_id = seed_post(app, "Keep this post", "Logout blocks deletion")
    client.get("/logout")
    assert client.get(f"/delete/{another_id}").status_code == 401
    with app.app_context():
        assert db.session.get(Post, another_id) is not None


def test_search(client, app):
    """Search title/body without case sensitivity and exclude nonmatches."""
    response = client.get("/search/")
    assert response.status_code == 200
    assert b'name="query"' in response.data

    seed_post(app, "Python notes", "A Flask tutorial")
    seed_post(app, "Dinner plans", "Pasta tonight")
    for query in ["python", "PYTHON", "flask tutorial"]:
        response = client.get("/search/", query_string={"query": query})
        assert response.status_code == 200
        assert b"Python notes" in response.data
        assert b"Dinner plans" not in response.data

    response = client.get("/search/", query_string={"query": "basketball"})
    assert response.status_code == 200
    assert b"No matching entries." in response.data
    assert b"Python notes" not in response.data
    assert b"Dinner plans" not in response.data