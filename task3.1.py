
from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

students_db = {}
next_id = 1


def validate_student(data, student_id=None, partial=False):
    if not isinstance(data, dict):
        return "Очікується JSON-об'єкт"

    if not partial:
        if not data.get("name") or not data.get("group"):
            return "Ім'я та група обов'язкові"

        if not data.get("email") or "@" not in str(data["email"]):
            return "Некоректний email"

        if "gpa" not in data:
            return "Потрібно вказати середній бал"

    if "name" in data:
        if not isinstance(data["name"], str) or not data["name"].strip():
            return "Ім'я не може бути порожнім"

    if "group" in data:
        if not isinstance(data["group"], str) or not data["group"].strip():
            return "Група не може бути порожньою"

    if "gpa" in data:
        if isinstance(data["gpa"], bool) or not isinstance(data["gpa"], (int, float)):
            return "Середній бал повинен бути числом"
        if not 0 <= data["gpa"] <= 100:
            return "Середній бал повинен бути від 0 до 100"

    if "email" in data:
        email = data["email"]
        if not isinstance(email, str) or "@" not in email or not email.strip():
            return "Некоректний email"

        for student in students_db.values():
            if student["email"] == email and student["id"] != student_id:
                return "Такий email вже існує"

    return None


@app.route("/api/students", methods=["GET"])
def get_students():
    group = request.args.get("group")
    min_gpa = request.args.get("min_gpa", type=float)
    sort_by = request.args.get("sort_by", "name")
    order = request.args.get("order", "asc")
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    if sort_by not in ("name", "gpa", "group"):
        return jsonify({"error": "Некоректне поле сортування"}), 400

    if order not in ("asc", "desc") or page < 1 or per_page < 1:
        return jsonify({"error": "Некоректні параметри"}), 400

    students = list(students_db.values())

    if group:
        students = [s for s in students if s["group"] == group]

    if min_gpa is not None:
        students = [s for s in students if s["gpa"] >= min_gpa]

    students.sort(
        key=lambda s: s[sort_by],
        reverse=(order == "desc")
    )

    count = len(students)
    start = (page - 1) * per_page
    students = students[start:start + per_page]

    return jsonify({
        "count": count,
        "page": page,
        "per_page": per_page,
        "students": students
    }), 200


@app.route("/api/students", methods=["POST"])
def create_student():
    global next_id

    data = request.get_json(silent=True)
    error = validate_student(data)

    if error:
        return jsonify({"error": error}), 400

    student = {
        "id": next_id,
        "name": data["name"],
        "group": data["group"],
        "email": data["email"],
        "gpa": data["gpa"],
        "created_at": datetime.now().isoformat()
    }

    students_db[next_id] = student
    next_id += 1

    return jsonify(student), 201


@app.route("/api/students/<int:student_id>", methods=["GET"])
def get_student(student_id):
    student = students_db.get(student_id)

    if student is None:
        return jsonify({"error": "Студента не знайдено"}), 404

    return jsonify(student), 200


@app.route("/api/students/<int:student_id>", methods=["PUT"])
def update_student(student_id):
    if student_id not in students_db:
        return jsonify({"error": "Студента не знайдено"}), 404

    data = request.get_json(silent=True)
    error = validate_student(data, student_id)

    if error:
        return jsonify({"error": error}), 400

    students_db[student_id] = {
        "id": student_id,
        "name": data["name"],
        "group": data["group"],
        "email": data["email"],
        "gpa": data["gpa"],
        "created_at": students_db[student_id]["created_at"]
    }

    return jsonify(students_db[student_id]), 200


@app.route("/api/students/<int:student_id>", methods=["PATCH"])
def patch_student(student_id):
    if student_id not in students_db:
        return jsonify({"error": "Студента не знайдено"}), 404

    data = request.get_json(silent=True)
    error = validate_student(data, student_id, partial=True)

    if error:
        return jsonify({"error": error}), 400

    for field in ("name", "group", "email", "gpa"):
        if field in data:
            students_db[student_id][field] = data[field]

    return jsonify(students_db[student_id]), 200


@app.route("/api/students/<int:student_id>", methods=["DELETE"])
def delete_student(student_id):
    if student_id not in students_db:
        return jsonify({"error": "Студента не знайдено"}), 404

    del students_db[student_id]
    return "", 204


@app.route("/api/students/stats", methods=["GET"])
def students_stats():
    students = list(students_db.values())
    total = len(students)

    avg_gpa = 0
    if total > 0:
        avg_gpa = round(sum(s["gpa"] for s in students) / total, 2)

    groups = {}
    for student in students:
        group = student["group"]
        groups[group] = groups.get(group, 0) + 1

    top_students = sorted(
        students,
        key=lambda s: s["gpa"],
        reverse=True
    )[:3]

    return jsonify({
        "total": total,
        "avg_gpa": avg_gpa,
        "groups": groups,
        "top_students": top_students
    }), 200


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Ресурс не знайдено", "status": 404}), 404


@app.errorhandler(400)
def bad_request(error):
    return jsonify({"error": "Некоректний запит", "status": 400}), 400


@app.errorhandler(422)
def unprocessable(error):
    return jsonify({"error": "Помилка валідації", "status": 422}), 422


if __name__ == "__main__":
    test_students = [
        {"name": "Іваненко О.", "group": "КІ-21", "email": "ivan@kpi.ua", "gpa": 85.5},
        {"name": "Петренко М.", "group": "КІ-21", "email": "petro@kpi.ua", "gpa": 92.0},
        {"name": "Сидоренко А.", "group": "КІ-22", "email": "syd@kpi.ua", "gpa": 78.3},
        {"name": "Коваль Л.", "group": "КІ-22", "email": "koval@kpi.ua", "gpa": 95.1}
    ]

    for s in test_students:
        students_db[next_id] = {
            **s,
            "id": next_id,
            "created_at": datetime.now().isoformat()
        }
        next_id += 1

    app.run(debug=True, port=5005)

