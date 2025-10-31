from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, DateField, FileField
from wtforms.validators import DataRequired


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])


class CSVForm(FlaskForm):
    csv = FileField('Attach .csv', validators=[DataRequired()], render_kw={"accept": ".csv"})
