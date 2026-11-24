
from flask import Flask, request, jsonify, g
from datetime import datetime
from functools import wraps
import time

app = Flask(__name__)

students_db = {}
next_id = 1


class APIError(Exception):
    def __init__(self, message, status_code=400, details=None):
        self.message = message
        self.status_code = status_code
        self.details = details or {}


class StudentSerializer:
    @staticmethod
    def serialize(student, fields=None):
        result = student.copy()

        if "created_at" in result:
            result["created_at"] = result["created_at"][:19].replace("T", " ")

        result["passed"] = result["gpa"] >= 60

        if fields is not None:
            result = {key: value for key, value in result.items() if key in fields}

        return result

    @staticmethod
    def deserialize(data):
        if not isinstance(data, dict):
            raise APIError("Очікується JSON-об'єкт", 400)

        required = ["name", "group", "email", "gpa"]
        missing = [field for field in required if field not in data]

        if missing:
            raise APIError("Відсутні обов'язкові поля", 400, {"fields": missing})

        name = str(data["name"]).strip()
        group = str(data["group"]).strip()
        email = str(data["email"]).strip()

        if not name or not group or not email:
            raise APIError("Поля не можуть бути порожніми", 400)

        if "@" not in email:
            raise APIError("Некоректний email", 400)

        try:
            if isinstance(data["gpa"], bool):
                raise ValueError
            gpa = float(data["gpa"])
        except (ValueError, TypeError):
            raise APIError("Середній бал повинен бути числом", 400)

        if not 0 <= gpa <= 100:
            raise APIError("Середній бал повинен бути від 0 до 100", 400)

        return {
            "name": name,
            "group": group,
            "email": email,
            "gpa": gpa
        }

    @staticmethod
    def serialize_list(students, fields=None):
        return [StudentSerializer.serialize(s, fields) for s in students]


@app.before_request
def log_request():
    g.start_time = time.time()
    print(f"{datetime.now()} | {request.method} | {request.url}")


@app.after_request
def add_headers(response):
    start = getattr(g, "start_time", time.time())
    response.headers["X-Request-Time"] = str(round(time.time() - start, 4))
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response


def require_api_key(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        api_key = request.headers.get("X-API-Key")

        if api_key != "secret-api-key-123":
            raise APIError("Невірний API-ключ", 401)

        return f(*args, **kwargs)
    return wrapper


@app.route("/api/v2/students", methods=["GET"])
def get_students_v2():
    fields_text = request.args.get("fields")
    search = request.args.get("search", "").lower()
    sort = request.args.get("sort", "name")
    order = request.args.get("order", "asc")

    fields = fields_text.split(",") if fields_text else None

    allowed_fields = ["id", "name", "group", "email", "gpa", "created_at", "passed"]

    if fields and any(field not in allowed_fields for field in fields):
        raise APIError("Невідоме поле", 400)

    if sort not in ("name", "group", "gpa"):
        raise APIError("Невірне поле сортування", 400)

    if order not in ("asc", "desc"):
        raise APIError("Невірний порядок сортування", 400)

    students = list(students_db.values())

    if search:
        students = [
            s for s in students
            if search in s["name"].lower() or search in s["group"].lower()
        ]

    students.sort(key=lambda s: s[sort], reverse=(order == "desc"))

    return jsonify({
        "count": len(students),
        "students": StudentSerializer.serialize_list(students, fields)
    }), 200


@app.route("/api/v2/students", methods=["POST"])
@require_api_key
def create_student_v2():
    global next_id

    data = request.get_json(silent=True)
    student_data = StudentSerializer.deserialize(data)

    for student in students_db.values():
        if student["email"] == student_data["email"]:
            raise APIError("Такий email вже існує", 400)

    student = {
        "id": next_id,
        **student_data,
        "created_at": datetime.now().isoformat()
    }

    students_db[next_id] = student
    next_id += 1

    return jsonify(StudentSerializer.serialize(student)), 201


@app.errorhandler(APIError)
def handle_api_error(error):
    return jsonify({
        "error": error.message,
        "status": error.status_code,
        "details": error.details,
        "timestamp": datetime.now().isoformat()
    }), error.status_code


@app.errorhandler(404)
def not_found(error):
    return jsonify({"error": "Ресурс не знайдено", "status": 404}), 404


if __name__ == "__main__":
    test_students = [
        {"name": "Іваненко О.", "group": "КІ-21", "email": "ivan@kpi.ua", "gpa": 85.5},
        {"name": "Петренко М.", "group": "КІ-21", "email": "petro@kpi.ua", "gpa": 92.0},
        {"name": "Коваль Л.", "group": "КІ-22", "email": "koval@kpi.ua", "gpa": 95.1}
    ]

    for data in test_students:
        students_db[next_id] = {
            **data,
            "id": next_id,
            "created_at": datetime.now().isoformat()
        }
        next_id += 1

    app.run(debug=True, port=5006)

