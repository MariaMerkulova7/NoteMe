from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField
from wtforms import SubmitField, DateField, TimeField
from wtforms.validators import DataRequired


class NewNotesForm(FlaskForm):
    title = StringField('Заметка', validators=[DataRequired()])
    text = TextAreaField('Содержание', validators=[DataRequired()])
    date_of_event = DateField('Дата события', validators=[DataRequired()])
    time_of_event = TimeField('Время события', validators=[DataRequired()])
    submit = SubmitField('Создать заметку')