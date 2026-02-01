from app import db
from app.models import User

CORRECT_LANGUAGES = {
    "python",
    "javascript",
    "typescript",
    "rust",
    "go",
    "java",
    "csharp",
    "cpp",
    "php",
    "ruby",
    "swift",
    "kotlin",
}


def check_data(request) -> bool | str:
    form = (
        "project_name",
        "description",
        "language",
        "code",
        "tags",
        # "feedback",
        "visibility",
    )
    form = {el: request.form.get(el) for el in form}

    for el in form:  # checking if any data is null
        if not request.form.get(el):
            return f"{el}: can't be null"
    # checking all parametrs
    if len(form["project_name"]) > 100:
        return "Project name must be less than 100 symbols length"
    if len(form["description"]) > 5000:
        return "Description length mus be less than 5000 symbols"
    if request.form.get("language") not in CORRECT_LANGUAGES:
        return f"Incorrect language: {request.form.get('language')}"
    if (ln := len(form["code"])) > 5000:
        return f"Sorry, but your code too long: {ln}/5000"
    if len(form["tags"].split("#")) > 5:
        return f"Too many tags: {len(form['tags'].split('#'))}/5"
    if form["visibility"] not in ("public", "unlisted"):
        return f"Invalid visibility: {form['visibility']}"
    return True
