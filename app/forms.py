from flask_wtf import Form
from wtforms import StringField, BooleanField, PasswordField, validators

class LoginForm(Form):
    login = StringField('login', [validators.DataRequired()])
    password = PasswordField('password', [validators.DataRequired()])
    remember_me = BooleanField('remember_me', default=False)

