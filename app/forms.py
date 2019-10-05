from flask_wtf import FlaskForm
from wtforms import TextField, PasswordField, DateField, IntegerField, SelectField
from wtforms.validators import Required, Email, EqualTo, Length

class RegisterForm(FlaskForm):
    name = TextField('Username', validators=[Required(), Length(min=3, max=25)])
    email = TextField('Email', validators=[Required(), Length(min=6, max=40)])
    password = PasswordField('Password',
                                validators=[Required(), Length(min=6, max=40)])
    confirm = PasswordField(
                'Repeat Password',
                [Required(), EqualTo('password', message='Passwords must match')])

class LoginForm(FlaskForm):
    email = TextField('email', validators=[Required()])
    password = PasswordField('Password', validators=[Required()])

class SearchForm(FlaskForm):
    search_term = TextField('search_term', validators=[Required()])