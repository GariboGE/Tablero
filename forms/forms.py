from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, FileField, IntegerField, FloatField
from wtforms.validators import DataRequired, NumberRange, Optional


class LoginForm(FlaskForm):
    username = StringField('Usuario', validators=[DataRequired()])
    password = PasswordField('Contraseña', validators=[DataRequired()])


class CSVForm(FlaskForm):
    csv = FileField('Attach .csv', validators=[DataRequired()], render_kw={"accept": ".csv"})


class EmptyForm(FlaskForm):
    """Form vacío — solo para validación CSRF en acciones sin campos propios."""
    pass


class MetaForm(FlaskForm):
    sucursal = StringField('Sucursal', validators=[DataRequired()])
    mes = IntegerField('Mes', validators=[DataRequired(), NumberRange(min=1, max=12)])
    anio = IntegerField('Año', validators=[DataRequired(), NumberRange(min=2020, max=2099)])
    monto = FloatField('Monto (MXN)', validators=[DataRequired(), NumberRange(min=0)])


class RecipienteForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired()])
    nombre = StringField('Nombre', validators=[Optional()])
