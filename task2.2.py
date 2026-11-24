
from flask import Flask, request, render_template_string, redirect, url_for, flash, abort

app = Flask(__name__)
app.secret_key = "blog-secret-key"

posts_db = [
    {"id": 1, "title": "Перша публікація", "content": "Зміст першої...",
     "author": "Іван", "created_at": "2025-01-15"},
    {"id": 2, "title": "Друга публікація", "content": "Зміст другої...",
     "author": "Марія", "created_at": "2025-01-20"}
]

LIST_TEMPLATE = """
<h1>Публікації</h1>
{% with messages = get_flashed_messages() %}
{% for message in messages %}
<p style="color:green;">{{ message }}</p>
{% endfor %}
{% endwith %}

{% for post in posts %}
<h2><a href="{{ url_for('post_detail', post_id=post.id) }}">{{ post.title }}</a></h2>
<p>{{ post.content }}</p>
<hr>
{% endfor %}
"""

DETAIL_TEMPLATE = """
<h1>{{ post.title }}</h1>
<p>{{ post.content }}</p>
<p>Автор: {{ post.author }}</p>
<p>Дата: {{ post.created_at }}</p>

{% with messages = get_flashed_messages() %}
{% for message in messages %}
<p style="color:green;">{{ message }}</p>
{% endfor %}
{% endwith %}

<a href="{{ url_for('post_edit', post_id=post.id) }}">Редагувати</a>
<a href="{{ url_for('post_delete', post_id=post.id) }}">Видалити</a>
<a href="{{ url_for('post_list') }}">Назад до списку</a>
"""

EDIT_TEMPLATE = """
<h1>Редагування публікації</h1>
{% with messages = get_flashed_messages() %}
{% for message in messages %}
<p style="color:red;">{{ message }}</p>
{% endfor %}
{% endwith %}

<form method="POST">
    <label>Заголовок:</label><br>
    <input type="text" name="title" value="{{ post.title }}" required><br><br>

    <label>Автор:</label><br>
    <input type="text" name="author" value="{{ post.author }}" required><br><br>

    <label>Зміст:</label><br>
    <textarea name="content" rows="8" cols="45" required>{{ post.content }}</textarea><br><br>

    <button type="submit">Зберегти зміни</button>
    <a href="{{ url_for('post_detail', post_id=post.id) }}">Скасувати</a>
</form>
"""

DELETE_CONFIRM_TEMPLATE = """
<!DOCTYPE html>
<html>
<head><title>Видалення</title></head>
<body>
    <h1>Підтвердження видалення</h1>
    <p>Ви дійсно бажаєте видалити публікацію
    "<strong>{{ post.title }}</strong>"?</p>

    <form method="POST">
        <button type="submit" style="color:red;">Так, видалити</button>
        <a href="{{ url_for('post_detail', post_id=post.id) }}">Скасувати</a>
    </form>
</body>
</html>
"""


@app.route("/posts")
def post_list():
    return render_template_string(LIST_TEMPLATE, posts=posts_db)


@app.route("/posts/<int:post_id>")
def post_detail(post_id):
    for post in posts_db:
        if post["id"] == post_id:
            return render_template_string(DETAIL_TEMPLATE, post=post)
    abort(404)


@app.route("/posts/<int:post_id>/edit", methods=["GET", "POST"])
def post_edit(post_id):
    post = next((p for p in posts_db if p["id"] == post_id), None)

    if post is None:
        abort(404)

    if request.method == "POST":
        title = request.form.get("title", "").strip()
        author = request.form.get("author", "").strip()
        content = request.form.get("content", "").strip()

        if not title or not author or not content:
            flash("Усі поля повинні бути заповнені")
            return render_template_string(EDIT_TEMPLATE, post=post), 400

        post["title"] = title
        post["author"] = author
        post["content"] = content

        flash("Публікацію успішно оновлено!")
        return redirect(url_for("post_detail", post_id=post_id))

    return render_template_string(EDIT_TEMPLATE, post=post)


@app.route("/posts/<int:post_id>/delete", methods=["GET", "POST"])
def post_delete(post_id):
    post = next((p for p in posts_db if p["id"] == post_id), None)

    if post is None:
        abort(404)

    if request.method == "POST":
        posts_db.remove(post)
        flash("Публікацію успішно видалено!")
        return redirect(url_for("post_list"))

    return render_template_string(DELETE_CONFIRM_TEMPLATE, post=post)


if __name__ == "__main__":
    app.run(debug=True, port=5004)

