from pathlib import Path

from flask import Flask, jsonify

from models import Task, db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)


def init_database():
    with app.app_context():
        db.create_all()
        script = Path(__file__).with_name("schema.sql").read_text(
            encoding="utf-8"
        )
        connection = db.engine.raw_connection()
        try:
            connection.executescript(script)
            connection.commit()
        finally:
            connection.close()


init_database()


@app.get("/tasks")
def get_tasks():
    tasks = Task.query.order_by(Task.id).all()
    return jsonify([
        {
            "id": task.id,
            "title": task.title,
            "status": task.status,
            "project_id": task.project_id,
        }
        for task in tasks
    ])


if __name__ == "__main__":
    app.run(debug=True)
