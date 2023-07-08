from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, EmailField, SubmitField, BooleanField
from wtforms.validators import DataRequired, Email, EqualTo, Length, InputRequired,StopValidation,ValidationError
from WebApp.models import Student, Supervisor
from werkzeug.security import check_password_hash
import re

class Registration_Form(FlaskForm):
    FirstName = StringField('FirstName', validators=[InputRequired(message='FirstName must be required')], id='fname', render_kw={"placeholder":' ','autocomplete':'off','class':'form__input'})
    LastName = StringField('LastName', validators=[InputRequired(message='LastName must be required')], id='lname', render_kw={"placeholder":' ','autocomplete':'off','class':'form__input'})
    email = EmailField('Email-address',validators=[InputRequired(message='E-mail address is required'),Email(check_deliverability=True,granular_message=True)], id="email", render_kw={"placeholder":' ','autocomplete':'off','class':'form__input'})
    password = PasswordField('Password',validators=[InputRequired("Password is required"), Length(min=5, max=25)],id='password',render_kw={"placeholder":' ','autocomplete':'off','aria-autocomplete':"none",'class':'pwfield form__input'})
    confirm_password = PasswordField('Confirm password',validators=[InputRequired(),Length(min=5, max=25),EqualTo('password')], id='confirm_password',render_kw={"placeholder":' ','autocomplete':'off','aria-autocomplete':"none",'class':'pwfield form__input'})
    submit = SubmitField('Register', render_kw={"class":"submit_button"})

    def validate_email(self, email):
        check_student_email = Student.query.filter_by(student_email=email.data).first()
        check_supervisor_email = Supervisor.query.filter_by(supervisor_email=email.data).first()

        if check_student_email or check_supervisor_email:
            raise ValidationError("Email is already registered, please Login or register with another Email.")
    
    def validate_password(form,password):
        if re.search('[^A-Za-z0-9 ]', password.data):
            raise ValidationError("Password does not contain special characters")

class Login_Form(FlaskForm):
    email = EmailField('Email-address',validators=[InputRequired(message='E-mail address is required'),Email(check_deliverability=False,granular_message=True)], id="email", render_kw={"placeholder":' ','autocomplete':'off','class':'form__input'})
    password = PasswordField('Password',validators=[InputRequired("Password is required")],id='password',render_kw={"placeholder":" ",'autocomplete':'off','class':'pwfield form__input'})
    remember = BooleanField("Remember", id="remember_me")
    submit = SubmitField('Login', render_kw={"class":"submit_button"})

    def validate_email(self,email):
        email = email.data
        if email.endswith("@student.le.ac.uk"):
            student = Student.query.filter_by(student_email=email).first()
            if student is None:
                raise StopValidation("Couldn't find your Account. Enter registered Email address")
        elif email.endswith('@leicester.ac.uk'):
            supervisor = Supervisor.query.filter_by(supervisor_email=email).first()
            if supervisor is None:
                raise StopValidation("Couldn't find your Account. Enter registered Email address")
        else:
            raise StopValidation("Enter Valid Email address")

    def validate_password(self,password):
        check_student_pwd = Student.query.filter_by(student_email=self.email.data).first()
        check_supervisor_pwd = Supervisor.query.filter_by(supervisor_email=self.email.data).first()
        
        if not (check_student_pwd or check_supervisor_pwd ):
            raise StopValidation("")
        
        if check_student_pwd:
            if check_password_hash(check_student_pwd.password,password.data) == False:
                raise StopValidation("Wrong password. Try again or Click Reset My Password below to change.")
        else:
            if check_password_hash(check_supervisor_pwd.password,password.data) == False:
                raise StopValidation("Wrong password. Try again or Click Reset My Password below to change.")  
        
class RequestResetform(FlaskForm):
    email = EmailField('Email-address',validators=[InputRequired(message='E-mail address is required'),Email(check_deliverability=True,granular_message=True)], id="email", render_kw={"placeholder":' ','autocomplete':'off','class':'form__input'})
    submit = SubmitField('Send Link',render_kw={"class":"submit_button"})
    
    def validate_email(self, email):
        email = email.data
        if email.endswith("@student.le.ac.uk"):
            student = Student.query.filter_by(student_email=email).first()
            if student is None:
                raise ValidationError("Couldn't find your Account. Enter registered Email address")
        elif email.endswith('@leicester.ac.uk'):
            supervisor = Supervisor.query.filter_by(supervisor_email=email).first()
            if supervisor is None:
                raise ValidationError("Couldn't find your Account. Enter registered Email address")
        else:
            raise ValidationError("Enter Valid Email address")

class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password',validators=[InputRequired("Password is required"), Length(min=5, max=25)],id='password',render_kw={"placeholder":' ','autocomplete':'off','aria-autocomplete':"none",'class':'pwfield form__input'})
    confirm_password = PasswordField('Confirm password',validators=[InputRequired(),Length(min=5, max=25),EqualTo('password')], id='confirm_password',render_kw={"placeholder":' ','autocomplete':'off','aria-autocomplete':"none",'class':'pwfield form__input'})
    submit = SubmitField('Reset Password', render_kw={"class":"submit_button"})

    def validate_password(form,password):
        if re.search('[^A-Za-z0-9 ]', password.data):
            raise ValidationError("Password does not contain special characters")