from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, TextAreaField
from flask_wtf.file import FileField
from wtforms.validators import DataRequired


class NovelForm(FlaskForm):
    title = StringField('Заголовок', validators=[DataRequired()])
    content = TextAreaField("Содержание")
    submit = SubmitField('Применить')
    immage = FileField()
    document = FileField()
