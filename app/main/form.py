"""
This module contains the form classes for the feed.
"""

from flask_wtf import FlaskForm
from wtforms import (
    RadioField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TextAreaField,
    widgets,
)
from wtforms.validators import DataRequired, Length


class MultiCheckboxField(SelectMultipleField):
    """
    A multiple-checkbox field.
    """

    widget = widgets.ListWidget(prefix_label=False)
    option_widget = widgets.CheckboxInput()


class PostForm(FlaskForm):
    """
    A form for creating a new blog post.
    Example data:
    {
        "project_name": "Hello World",
        "description": "This is my first blog post!",
        "language": "python",
        "code": "print('Hello, World!')",
        "tags": ["example", "tutorial"]
        "feedback": ["code_quality", "performance"],
        "visibility": "public"
        "submit": "Publish Post"
    }

    """

    project_name = StringField(
        "Project Name", validators=[DataRequired(), Length(max=100)]
    )
    description = TextAreaField(
        "Description", validators=[DataRequired(), Length(max=5000)]
    )

    # Choices are (value, label)
    language = RadioField(
        "Language",
        choices=[
            ("python", "Python"),
            ("javascript", "JavaScript"),
            ("rust", "Rust"),
            ("go", "Go"),
            ("java", "Java"),
            ("cpp", "C++"),
            ("csharp", "C#"),
        ],
        validators=[DataRequired()],
    )

    code = TextAreaField("Code", validators=[DataRequired(), Length(max=5000)])
    tags = StringField("Tags", validators=[Length(max=200)])

    feedback = MultiCheckboxField(
        "Feedback Type",
        choices=[
            ("code_quality", "Code Quality"),
            ("performance", "Performance"),
            ("architecture", "Architecture"),
            ("security", "Security"),
        ],
    )

    visibility = RadioField(
        "Visibility",
        choices=[("public", "Public"), ("unlisted", "Unlisted")],
        default="public",
    )
    submit = SubmitField("Publish Post")


class BattleForm(FlaskForm):
    """
    Form for creating a new coding battle.
    """

    title = StringField("Battle Title", validators=[DataRequired(), Length(max=100)])
    description = TextAreaField(
        "Description", validators=[DataRequired(), Length(max=5000)]
    )

    time_limit = RadioField(
        "Time limit",
        choices=[
            ("30 min", "30 min"),
            ("1 hour", "1 hour"),
            ("3 hours", "3 hours"),
            ("24 hours", "24 hours"),
            ("Custom", "Custom"),
        ],
        default="1 hour",
        validators=[DataRequired()],
    )

    language = RadioField(
        "Language",
        choices=[
            ("python", "Python"),
            ("javascript", "Javascript"),
            ("typescript", "Typescript"),
            ("rust", "Rust"),
            ("go", "Go"),
            ("java", "Java"),
            ("csharp", "C#"),
            ("cpp", "C++"),
            ("php", "PHP"),
            ("ruby", "Ruby"),
            ("swift", "Swift"),
            ("kotlin", "Kotlin"),
        ],
        validators=[DataRequired()],
    )

    difficulty = RadioField(
        "Difficulty",
        choices=[
            ("Beginner", "Beginner"),
            ("Intermediate", "Intermediate"),
            ("Advanced", "Advanced"),
            ("Expert", "Expert"),
        ],
        default="Intermediate",
        validators=[DataRequired()],
    )

    visibility = RadioField(
        "Visibility",
        choices=[("public", "Public"), ("private", "Private")],
        default="public",
        validators=[DataRequired()],
    )

    tags = StringField("Tags", validators=[Length(max=200)])

    submit = SubmitField("Create Battle")
