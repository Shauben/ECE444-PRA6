from project.app import app
from project.models import db

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    print("Database tables created (existing data preserved).")
