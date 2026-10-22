import os
from functools import wraps
from pathlib import Path

import bleach
from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    redirect,
    render_template,
    request,
    session,
    url_for,
)

from project.models import Post, db


def login_required(function):
    @wraps(function)
    def decorated_function(*args, **kwargs):
        if not session.get("logged_in"):
            flash("Please log in.")
            return jsonify({"status": 0, "message": "Please log in."}), 401
        return function(*args, **kwargs)

    return decorated_function


def create_app(test_config=None):
    app = Flask(__name__)
    database_path = Path(__file__).resolve().parent / "flaskr.db"
    database_url = os.getenv("DATABASE_URL", f"sqlite:///{database_path}")
    if database_url.startswith("postgres://"):
        database_url = database_url.replace("postgres://", "postgresql://", 1)
    app.config.from_mapping(
        USERNAME=os.getenv("APP_USERNAME", "Shaurya"),
        PASSWORD=os.getenv("APP_PASSWORD", "Shaurya"),
        SECRET_KEY=os.getenv("SECRET_KEY", "local-classroom-demo-key"),
        SQLALCHEMY_DATABASE_URI=database_url,
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
    )
    if test_config is not None:
        app.config.update(test_config)
    db.init_app(app)

    @app.template_filter("clean_html")
    def clean_html(value):
        # Keep tutorial formatting while removing executable HTML/attributes.
        return bleach.clean(
            value,
            tags={"strong", "em", "b", "i", "p", "br", "ul", "ol", "li"},
            attributes={},
            strip=True,
        )

    @app.route("/")
    def index():
        entries = (
            db.session.execute(db.select(Post).order_by(Post.id.desc())).scalars().all()
        )
        return render_template("index.html", entries=entries)

    @app.route("/login", methods=["GET", "POST"])
    def login():
        error = None
        if request.method == "POST":
            if request.form.get("username") != app.config["USERNAME"]:
                error = "Invalid username"
            elif request.form.get("password") != app.config["PASSWORD"]:
                error = "Invalid password"
            else:
                session["logged_in"] = True
                flash("You were logged in")
                return redirect(url_for("index"))
        return render_template("login.html", error=error)

    @app.route("/logout")
    def logout():
        session.pop("logged_in", None)
        flash("You were logged out")
        return redirect(url_for("index"))

    @app.route("/add", methods=["POST"])
    def add_entry():
        if not session.get("logged_in"):
            abort(401)
        entry = Post(title=request.form["title"], text=request.form["text"])
        db.session.add(entry)
        db.session.commit()
        flash("New entry was successfully posted")
        return redirect(url_for("index"))

    # GET deletion matches the assigned tutorial's JavaScript/API.
    # In a production app, use POST/DELETE with CSRF protection instead.
    @app.route("/delete/<int:post_id>", methods=["GET"])
    @login_required
    def delete_entry(post_id):
        entry = db.session.get(Post, post_id)
        if entry is None:
            return jsonify({"status": 0, "message": "Post not found"}), 404
        db.session.delete(entry)
        db.session.commit()
        flash("The entry was deleted.")
        return jsonify({"status": 1, "message": "Post Deleted"})

    @app.route("/search/", methods=["GET"])
    def search():
        query = request.args.get("query", "").strip()
        entries = []
        if query:
            # Match the tutorial's case-insensitive substring behavior.
            posts = (
                db.session.execute(db.select(Post).order_by(Post.id.desc()))
                .scalars()
                .all()
            )
            entries = [
                post
                for post in posts
                if query.lower() in post.title.lower()
                or query.lower() in post.text.lower()
            ]
        return render_template("search.html", entries=entries, query=query)

    return app


app = create_app()
