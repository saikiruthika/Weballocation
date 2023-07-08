from flask import Flask, redirect, url_for, request, flash, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, current_user
from flask_wtf.csrf import CSRFProtect
from flask_mail import Mail
from flask_admin import Admin, AdminIndexView, expose
from flask_admin.menu import MenuLink
from flask_mail import Mail, Message
import datetime
import sched
import time
from flask_admin.base import BaseView
from collections import defaultdict
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)
my_login_manager = LoginManager(app)
app.config.from_object('WebApp.config.Development_Config')
db = SQLAlchemy(app)
migrate = Migrate(app,db)
csrf = CSRFProtect(app)
mail = Mail(app)

class AdminSecureIndexView(AdminIndexView):
    def is_accessible(self):
        
        
        return current_user.is_authenticated and current_user.role == "supervisor" and current_user.supervisor_email == 'admin@leicester.ac.uk'

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            flash("Access Denied, Please login as admin")
            return redirect(url_for('Login', next=request.url))
        else:
            flash("Access Denied, You are not an Admin")
            return redirect(url_for('home')) 
        
    @expose('/')
    def index(self):
        num_students = Student.query.count()
        num_supervisors = Supervisor.query.count()
        num_topics = Topic.query.count()
        groups = Group.query.all()
        return self.render('admin/index.html',
                           num_students=num_students,
                           num_supervisors=num_supervisors,
                           num_topics=num_topics,
                           groups = groups,
                           student_db = Student,
                           supervisor_db = Supervisor
                           )


admin = Admin(app, name = 'Admin Dashboard', template_mode = 'bootstrap4', index_view=AdminSecureIndexView(url="/StudentAllocation-Admin-Dashboard"))
admin.add_link(MenuLink(name='Go to Website', endpoint='home'))

from WebApp.models import Supervisor, Student, Topic, Group
import WebApp.routes

my_login_manager.session_protection = "strong"
my_login_manager.login_view = 'Login'
my_login_manager.login_message = "Please Login to Continue"

@my_login_manager.user_loader
def load_user(id):
    if id.startswith("student-"):
        student = Student.query.get(id[8:])
        if student:
            return student
        
    elif id.startswith("supervisor-"):
        supervisor = Supervisor.query.get(id[11:])
        if supervisor:
            return supervisor
    return None

def send_email(to_address, subject, body, name):
    msg = Message(subject=subject, sender=('University Of Leicester', 'saikiri99@gmail.com'), recipients=[to_address])
    msg.html = render_template("EmailTemplate.html", msg='remainder', username=name, remainder_text=body)
    mail.send(msg)

scheduler = sched.scheduler(time.time, time.sleep)
def schedule_email_reminders():
    deadline = datetime.datetime.strptime(app.config['DEFAULT_DEADLINE'], '%Y-%m-%d').date()
    reminder_date = deadline - datetime.timedelta(days=1)
    students_without_topic = Student.query.filter(~Student.preferred_topics.any(),Student.reminder_sent == False).all()
    for student in students_without_topic:
        now = datetime.datetime.now()
        time_until_reminder =  (reminder_date - now.date()).days * 24 * 60 * 60 - now.time().hour * 60 * 60 - now.time().minute * 60 - now.time().second
        scheduler.enter(time_until_reminder, 1, send_email, argument=(student.student_email, 'Reminder: Select a Topic', 'Please select a topic before the deadline - {}'.format(app.config['DEFAULT_DEADLINE']),student.student_Fname))
        student.reminder_sent = True
        db.session.commit()

    willing_supervisors = Supervisor.query.filter_by(willing_to_supervise=True, number_of_topics_to_supervise=0, reminder_sent=False).all()
    for staf in willing_supervisors:
        now = datetime.datetime.now()
        time_until_reminder =  (reminder_date - now.date()).days * 24 * 60 * 60 - now.time().hour * 60 * 60 - now.time().minute * 60 - now.time().second
        scheduler.enter(time_until_reminder, 1, send_email, argument=(staf.supervisor_email, 'Reminder: Select a Topic', 'Please select a topic before the deadline - {}'.format(app.config['DEFAULT_DEADLINE']),staf.supervisor_Fname))
        staf.reminder_sent = True
        db.session.commit()
        print(staf.reminder_sent)
    scheduler.run()


with app.app_context():
    db.create_all()
    db.session.commit()
    schedule_email_reminders()
    # deadlinedate = app.config['DEFAULT_DEADLINE']
    # deadlinetime = '05:40:00'
    # deadline_datetime_str = deadlinedate + ' ' + deadlinetime
    # deadline_datetime = datetime.datetime.strptime(deadline_datetime_str, "%Y-%m-%d %H:%M:%S")
    # trigger_time = deadline_datetime - datetime.timedelta(days=1)

    # sc = BackgroundScheduler()
    # sc.add_job(func=send_email, args=('saikiri99@gmail.com', 'Testing Scheduler', 'Yah ! Its worked fine', 'Flask Application'),  trigger='date', run_date=trigger_time)
    # sc.start()
import WebApp.admin
if __name__ == "__main__":
    app.run()