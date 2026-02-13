"""
This module contains the form classes for the feed.
"""

from flask_wtf import FlaskForm
from wtforms import (RadioField, SelectMultipleField, StringField, SubmitField,
                     TextAreaField, widgets)
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
