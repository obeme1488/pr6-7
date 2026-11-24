
from flask import Flask, request, render_template_string, redirect, url_for, abort

app = Flask(__name__)

BASE_TEMPLATE = """
<!DOCTYPE html>
<html lang="uk">
<head>
    <meta charset="UTF-8">
    <title>{{ title }}</title>
</head>
<body>
    <h1>{{ title }}</h1>
    <nav>
        <a href="{{ url_for('index') }}">Головна</a> |
        <a href="{{ url_for('post_list') }}">Публікації</a> |
        <a href="{{ url_for('search') }}">Пошук</a>
    </nav>
    <hr>
    {{ content | safe }}
</body>
</html>
"""

posts_db = [
    {"id": 1, "title": "Вступ до Python", "content": "Python — потужна мова...", "author": "Іван"},
    {"id": 2, "title": "Flask для початківців", "content": "Flask — мікрофреймворк...", "author": "Марія"},
    {"id": 3, "title": "REST API", "content": "REST — архітектурний стиль...", "author": "Петро"}
]

next_id = 4


@app.route("/")
def index():
    content = "<p>Вітаємо на головній сторінці!</p>"
    return render_template_string(BASE_TEMPLATE, title="Головна", content=content)


@app.route("/posts")
def post_list():
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 10, type=int)

    content = "<h2>Список публікацій</h2>"

    start = (page - 1) * per_page
    posts = posts_db[start:start + per_page]

    for post in posts:
        content += f"<p><a href='/posts/{post['id']}'>{post['title']}</a></p>"

    return render_template_string(BASE_TEMPLATE, title="Публікації", content=content)


@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    for post in posts_db:
        if post["id"] == post_id:
            content = f"<h2>{post['title']}</h2><p>{post['content']}</p><p>Автор: {post['author']}</p>"
            return render_template_string(BASE_TEMPLATE, title="Публікація", content=content)

    abort(404)


@app.route("/posts/create", methods=["GET", "POST"])
def post_create():
    global next_id

    if request.method == "POST":
        title = request.form.get("title")
        content = request.form.get("content")
        author = request.form.get("author")

        if title and content and author:
            posts_db.append({
                "id": next_id,
                "title": title,
                "content": content,
                "author": author
            })

            next_id += 1
            return redirect(url_for("post_list"))

    content = """
    <h2>Створити публікацію</h2>
    <form method="POST">
        <p>Назва: <input name="title" required></p>
        <p>Автор: <input name="author" required></p>
        <p>Текст: <textarea name="content" required></textarea></p>
        <button type="submit">Створити</button>
    </form>
    """

    return render_template_string(BASE_TEMPLATE, title="Створення", content=content)


@app.route("/search")
def search():
    q = request.args.get("q", "")
    content = "<h2>Результати пошуку</h2>"

    for post in posts_db:
        if q and q.lower() in post["title"].lower():
            content += f"<p>{post['title']}</p>"

    return render_template_string(BASE_TEMPLATE, title="Пошук", content=content)


@app.route("/archive/<int:year>/<int:month>")
def archive(year, month):
    content = f"<p>Архів за {month} місяць {year} року</p>"
    return render_template_string(BASE_TEMPLATE, title="Архів", content=content)


@app.route("/user/<string:username>")
def user_profile(username):
    content = f"<p>Профіль користувача: {username}</p>"
    return render_template_string(BASE_TEMPLATE, title="Профіль", content=content)


if __name__ == "__main__":
    app.run(debug=True, port=5000)

