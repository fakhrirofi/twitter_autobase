from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, IntegerField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, EqualTo

class LoginForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    remember_me = BooleanField("Remember Me")
    submit = SubmitField("Sign In")

class RegisterForm(FlaskForm):
    username = StringField("Username", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    password2 = PasswordField("Repeat password", validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField("Register")

class SetConfig(FlaskForm):
    consumer_key = StringField("CONSUMER KEY", validators=[DataRequired()])
    consumer_secret = StringField("CONSUMER SECRET", validators=[DataRequired()])
    access_key = StringField("ACCESS KEY", validators=[DataRequired()])
    access_secret = StringField("ACCESS SECRET", validators=[DataRequired()])
    env_name = StringField("ENVIRONT NAME", validators=[DataRequired()])
