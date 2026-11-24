# локальная версия API
from pathlib import Path

from flask import Flask, jsonify, request

from models import Project, Task, db

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///taskflow.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db.init_app(app)

ALLOWED_STATUSES = {"open", "in_progress", "done"}


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


def task_to_dict(task):
    return {
        "id": task.id,
        "title": task.title,
        "status": task.status,
        "project_id": task.project_id,
    }


def error(message, status):
    return jsonify({"error": message}), status


@app.get("/tasks")
def get_tasks():
    tasks = Task.query.order_by(Task.id).all()
    return jsonify([task_to_dict(task) for task in tasks])


@app.get("/tasks/<int:task_id>")
def get_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        return error("task not found", 404)
    return jsonify(task_to_dict(task))


@app.post("/tasks")
def create_task():
    data = request.get_json(silent=True)
    if not data or not isinstance(data.get("title"), str):
        return error("title is required", 400)

    title = data["title"].strip()
    status = data.get("status", "open")
    project_id = data.get("project_id")
    if not title:
        return error("title is required", 400)
    if status not in ALLOWED_STATUSES:
        return error("invalid status", 400)
    if project_id is None or db.session.get(Project, project_id) is None:
        return error("project not found", 400)

    task = Task(title=title, status=status, project_id=project_id)
    db.session.add(task)
    db.session.commit()
    return jsonify(task_to_dict(task)), 201


@app.put("/tasks/<int:task_id>")
def update_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        return error("task not found", 404)

    data = request.get_json(silent=True)
    if not data:
        return error("JSON body is required", 400)

    if "title" in data:
        if not isinstance(data["title"], str) or not data["title"].strip():
            return error("title must not be empty", 400)
        task.title = data["title"].strip()

    if "status" in data:
        if data["status"] not in ALLOWED_STATUSES:
            return error("invalid status", 400)
        task.status = data["status"]

    if "project_id" in data:
        if db.session.get(Project, data["project_id"]) is None:
            return error("project not found", 400)
        task.project_id = data["project_id"]

    db.session.commit()
    return jsonify(task_to_dict(task))


@app.delete("/tasks/<int:task_id>")
def delete_task(task_id):
    task = db.session.get(Task, task_id)
    if task is None:
        return error("task not found", 404)

    db.session.delete(task)
    db.session.commit()
    return "", 204


if __name__ == "__main__":
    app.run(debug=True)
