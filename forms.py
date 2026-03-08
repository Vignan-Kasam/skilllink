from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, SubmitField, SelectField, TextAreaField, FileField
from wtforms.validators import DataRequired, Email, Length
from flask_wtf.file import FileField, FileAllowed
class LoginForm(FlaskForm):
    email = StringField("Email", validators=[DataRequired()])
    password = PasswordField("Password", validators=[DataRequired()])
    submit = SubmitField("Login")

class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired()])
    email = StringField("Email", validators=[DataRequired(), Email()])
    password = PasswordField("Password", validators=[DataRequired()])
    aadhar = StringField("Aadhar Number", validators=[DataRequired(), Length(min=12, max=12)])

    # ✅ Add Role Selection
    role = SelectField("Register As", choices=[
        ('client', 'Client'),
        ('worker', 'Worker')
    ], validators=[DataRequired()])

    skills = TextAreaField("Skills (Only for Workers)")
    
    # ✅ Govt ID Image Upload
    govt_id_image = FileField("Upload Govt Approved ID (Photo)")

    submit = SubmitField("Register")

