from WebApp import admin, db
from WebApp.models import Supervisor, Student, Topic, PreferredTopic
from flask_admin.contrib.sqla import ModelView
import flask_login
from flask_login import current_user
from flask import redirect, url_for, request, flash
from flask_admin.base import BaseView
from flask_admin import expose


class BaseModelView(ModelView):
    page_size = 20
    
    def is_accessible(self):
        
        
        return current_user.is_authenticated and current_user.role == "supervisor" and current_user.supervisor_email == 'admin@leicester.ac.uk'

    def inaccessible_callback(self, name, **kwargs):
        if not current_user.is_authenticated:
            flash("Access Denied, Please login as admin")
            return redirect(url_for('Login', next=request.url))
        else:
            flash("Access Denied, You are not an Admin")
            return redirect(url_for('home'))

class StudentModelView(BaseModelView):
    column_searchable_list = ['student_email']
    column_exclude_list = ['password']
    column_list = ['student_Lname', 'student_email', 'Topics Selected', 'group_allocation' , 'reminder_sent']
    inline_models = [(PreferredTopic, dict(form_excluded_columns=["topic_name"]))]

    
    def __init__(self, model, session, *args, **kwargs):
        super().__init__(model, session, *args, **kwargs)
        self.column_formatters = {
            'Topics Selected': self._format_preferred_topics
        }
        self.column_formatters_with_defaults = True

    def _format_preferred_topics(self, view, context, model, name):
        preferred_topics = model.preferred_topics.all()
        sorted_topics = sorted(preferred_topics, key=lambda x: x.priority)
        formatted_topics = []
        for topic in sorted_topics:
            topic_name = topic.topic.name if topic.topic else topic.topic_name
            formatted_topics.append(f"Priority-{topic.priority}: {topic_name}")
        return ", ".join(formatted_topics)


class SupervisorModelView(BaseModelView):
    column_searchable_list = ['supervisor_email']
    column_exclude_list = ['password']


class TopicModelView(BaseModelView):
    page_size = 20
    can_export = True
    column_searchable_list = ['name']
    column_list = ["name","supervisors_id"]
    column_labels = {"supervisors_id": "Supervisors Email"}


admin.add_view(StudentModelView(Student, db.session))
admin.add_view(SupervisorModelView(Supervisor, db.session))
admin.add_view(TopicModelView(Topic, db.session))


class CustomView(BaseView):
    @expose('/')
    def index(self):
        return self.render('admin/custom.html')
    
admin.add_view(CustomView(name='Run Algorithm', endpoint='customview'))
