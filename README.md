# ECE444 PRA6: Flaskr TDD and deployment reference

This is a runnable reference for the activities in
https://github.com/shuruizUofT/flaskr-tdd/blob/main/README.md.
It includes the final SQLAlchemy version, search, login-protected deletion,
JavaScript, Bootstrap, PostgreSQL configuration, and 17 pytest cases.
Understand and adapt the code before submitting your own repository.

## 1. Run locally (macOS / Linux)

Extract this archive. Open a terminal in the ECE444-PRA6 folder (the folder
containing requirements.txt). Use Python 3.12 if available; this reference
was tested with Python 3.12.

```bash
python3 -m venv env
source env/bin/activate
python -m pip install -r requirements.txt
python -m pytest -v
python create_db.py
python -m flask --app project.app run --port 5001
```

Visit http://127.0.0.1:5001. Local demo login: admin / admin.
Stop the server with Ctrl+C. The test database is temporary and isolated;
pytest does not erase the local app database or a configured PostgreSQL database.

Manually verify: log in, add two different posts, search by a word in the title
and another in the body, delete one post, log out, and check that the posting
form and delete buttons disappear. Refresh to confirm the deletion persists.
Automated Flask tests do not execute JavaScript, so do the browser check too.

## 2. Understand the files

| File | Job |
| --- | --- |
| project/app.py | Application configuration, routes, login decorator, HTML sanitizer |
| project/models.py | SQLAlchemy extension and Post table (id, title, text) |
| project/templates/ | Jinja HTML pages and shared layout |
| project/static/main.js | Calls the deletion endpoint and reloads after success |
| tests/app_test.py | Fixtures, helpers, and automated test cases |
| create_db.py | Creates missing tables without dropping existing data |
| requirements.txt | Dependencies installed locally and by Render |

Request flow: browser sends a request -> Flask route runs -> SQLAlchemy reads or
writes a database row -> Flask returns rendered HTML or JSON -> browser displays it.
The database stores rows, not HTML pages. Jinja builds HTML from the row values.

| Route | Method | Behavior |
| --- | --- | --- |
| / | GET | Show newest posts first |
| /login | GET / POST | Show login form / check credentials and set session |
| /logout | GET | Remove logged_in from session |
| /add | POST | Insert a post; reject unauthenticated requests with 401 |
| /delete/<id> | GET | Return JSON; require login; delete existing row |
| /search/ | GET | Match query against title or body, ignoring case |

GET deletion follows the course tutorial for compatibility. A production design
would use POST or DELETE plus CSRF protection. This remains a classroom demo
with one configured account, rather than a production user-management system.

## 3. TDD: practice the red-green-refactor cycle

TDD means write a behavior test first, run it and see it fail for the intended
reason, implement that behavior, then improve the design while keeping tests green.
Running a finished solution's tests demonstrates correctness, but does not by
itself demonstrate that you developed the feature using TDD.

For the complete tutorial progression, build a separate working copy in its
README order: Hello World test -> database -> posting/login -> deletion ->
SQLAlchemy -> search tests -> login-required tests. This archive is the final
reference, so the initial Hello World assertion and raw SQLite schema are
intentionally absent after those tutorial stages have been replaced.

For a short, concrete exercise using this reference:

1. In a separate copy, remove the /search/ route and its function from app.py.
2. Keep the search tests and run:
   `python -m pytest -v -k search`.
   They should fail because the route returns 404.
3. Implement a GET /search/ route, read request.args, select matching posts,
   and render search.html. Use the final reference only after trying it yourself.
4. Rerun the search tests, then the full suite.
5. Refactor duplicated code if useful and rerun the suite.

Similarly, removing only @login_required from delete_entry makes the protection
tests fail: an unauthenticated request wrongly deletes a real seeded post.
Restore the decorator and rerun. Do not deploy the deliberately broken copy.

## 4. Explain your tests to the TA

The tests use Arrange -> Act -> Assert. Example: create a post, attempt deletion
without logging in, then assert 401 AND verify the post still exists in the DB.

| Tests | What they prove |
| --- | --- |
| index, database, empty_db | Home loads, the table exists, empty state is shown |
| login_logout | Login creates session state and logout removes it |
| invalid_login (2 cases) | Wrong username/password show errors and grant no session |
| messages | Logged-in posting persists data and displays the new post |
| add_requires_login | An unauthenticated POST cannot insert a database row |
| delete_requires_login | A denied delete returns 401 and preserves the row |
| delete_message | Logged-in deletion returns success and actually removes the row |
| logout_revokes_delete_access | Previous login grants no access after logout |
| search_page | Search form loads without a query |
| search_matches_title_and_body (3 cases) | Title/body matching ignores case and excludes nonmatches |
| search_no_matches | A nonmatching query returns an empty result message |
| html_is_sanitized | Basic formatting survives but script markup is removed |

Important explanations:

- A fixture prepares a known starting state. The app fixture configures a fresh
  SQLite file under pytest's tmp_path, creates tables, yields the app to the test,
  then removes sessions and drops those test tables after the test.
- The config is supplied BEFORE db.init_app. Changing the URI after initialization
  does not redirect an already-created SQLAlchemy engine.
- client is Flask's test client: it simulates HTTP requests without starting a
  real network server. These route + database checks are integration tests in
  the strict sense, although the PRA refers to the suite as unit tests.
- follow_redirects=True follows the response from login/post/logout to the home
  page, letting assertions inspect the resulting page and flashed message.
- response.data is bytes; b"..." is a bytes literal used for comparisons.
- A 200 means success; 302 is a redirect; 401 denies unauthenticated access;
  404 means the route or requested post does not exist.
- @login_required wraps the route and checks session before allowing deletion.
  @wraps preserves the wrapped function's identity for Flask routing.
- Flask's default session is stored in a signed client cookie. SECRET_KEY protects
  its integrity; signing does not encrypt cookie contents.
- SQLAlchemy maps Post objects to database rows. add/delete stage changes;
  commit writes the transaction. SQLite is a local file; deployed PostgreSQL is
  a separate database service.
- Gunicorn runs the Flask app in deployment. project.app:app means import the
  module project/app.py and serve its variable named app.
- Search tests create both matching and nonmatching posts, so they catch an
  implementation that mistakenly returns every post.
- Deletion tests seed a real post and inspect the DB afterward: checking only
  a JSON success flag would not prove that deletion worked.

## 5. Put it in your own GitHub repo

Create an empty repository in GitHub, e.g. ECE444-PRA6. Do not initialize it
with another README if you will push this folder. From this project folder:

```bash
git init
git add .
git commit -m "Add Flaskr app, tests, and deployment configuration"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/ECE444-PRA6.git
git push -u origin main
```

Replace YOUR_USERNAME with yours. Do not commit database URLs, passwords,
.env files, virtual environments, or database files. .gitignore covers local files.
The final-reference commit is not a historical record of incremental TDD work;
if your TA expects intermediate stages, do the tutorial progression yourself.

## 6. Deploy on Render with PostgreSQL

Sign in to Render with your UofT account, as directed by the PRA.
Create a PostgreSQL database and a Python Web Service connected to your repo.
Choose the free option when available; check the current dashboard's limits.
Put the database and web service in the same region.

Web service settings for THIS archive:

| Setting | Value |
| --- | --- |
| Branch | main |
| Root directory | Leave blank if requirements.txt is at repo root |
| Build command | pip install -r requirements.txt |
| Start command | python create_db.py && gunicorn project.app:app --bind 0.0.0.0:$PORT |

Add environment variables before the first successful deployment:

| Variable | Value |
| --- | --- |
| DATABASE_URL | Your Render PostgreSQL INTERNAL database URL |
| SECRET_KEY | Generate a random value locally; keep it private |
| APP_USERNAME | Your chosen demo login name |
| APP_PASSWORD | Your chosen demo login password |
| PYTHON_VERSION | A supported full Python 3.12.x version matching your environment |

Generate SECRET_KEY locally using:

```bash
python -c 'import secrets; print(secrets.token_hex(32))'
```

Copy that generated value into Render, not into source control. The start command
creates missing tables against DATABASE_URL before Gunicorn starts. create_all()
does not erase existing posts and does not perform schema migrations.
psycopg2-binary provides the PostgreSQL driver.

Because table creation runs on Render, this reference does not need you to set
the external DB URL locally. The tutorial's alternative is to use the external
URL locally with create_db.py. On macOS the syntax would be
`export DATABASE_URL='YOUR_EXTERNAL_URL'`, followed by `python create_db.py` and
`unset DATABASE_URL`; its `$env:DATABASE_URL=...` example is PowerShell syntax.
Never paste actual URLs containing passwords into a public README or screenshot.

After deployment, open the onrender.com URL. Repeat the browser checks from
section 1 using your deployed login credentials, and confirm posts survive a
service restart/redeploy. That persistence checks the PostgreSQL connection.
Add your public app URL to this README before your final push.

Official reference: https://render.com/docs/deploy-flask
SQLAlchemy configuration reference:
https://flask-sqlalchemy.palletsprojects.com/en/stable/config/

## 7. Final checks and submission

```bash
python -m pytest -v
python -m black --check project tests create_db.py
python -m flake8 .
```

Show the TA your live app, passing tests, and your own search/access-control tests.
Be ready to explain the files and behavior above. Submit your own GitHub repo
link to Quercus. The handout requires in-person attendance and evaluation before
your PRA ends. Grading: activities 2 points; understanding/explanation 3 points.

## Differences from the tutorial's final snippets

- Application factory creates independently configured test apps; models live
  separately to avoid circular imports.
- Shared templates reduce repeated markup; the delete button triggers JavaScript
  instead of clicking anywhere on a post.
- Search filtering happens in Python in the route rather than inside Jinja;
  matching behavior is the same for this small demo.
- Test assertions verify actual stored data and rejected access.
- Missing post deletion returns 404 rather than claiming success.
- Basic body HTML is sanitized before the safe filter. The tutorial's strong
  formatting example still works; arbitrary executable markup is removed.
- Credentials/key can be configured in the environment for deployment.
- The start command creates tables, avoiding a separate local remote-DB setup.

Local verification: 17 pytest cases passed on Python 3.12. Formatting and lint
checks passed. Live Render/PostgreSQL deployment and browser JavaScript checks
must still be completed in your account; they have not been verified here.
