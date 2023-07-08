from flask_login import UserMixin
from WebApp import app,db
from itsdangerous import URLSafeSerializer as serializer
import time
from sqlalchemy.ext.mutable import MutableList
from sqlalchemy.event import listens_for

class Supervisor(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    supervisor_Fname = db.Column(db.String(50), nullable=False)
    supervisor_Lname = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    supervisor_email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(100), default='supervisor', nullable=False)
    topics = db.relationship('Topic', backref='supervisor', lazy='dynamic')
    willing_to_supervise = db.Column(db.Boolean, default=True, nullable=False)
    number_of_topics_to_supervise = db.Column(db.Integer, default=0)
    reminder_sent = db.Column(db.Boolean, default=False, nullable=False)
    # groups_allocated_to_supervise = db.Column(db.String(200), nullable=False, default='Not Yet Allocated')

    def reset_token(self,expires_sec=1800):
        s = serializer(app.config['SECRET_KEY'], salt=app.config['SUPERVISOR_SALT_KEY'])
        supervisor_details = {'user_id':self.id, 'user_email':self.supervisor_email}
        expiration_time = int(time.time()) + expires_sec
        supervisor_details['expiration_time'] = expiration_time
        token = s.dumps(supervisor_details)
        return token
    
    @staticmethod
    def verify_reset_token(token):
        s = serializer(app.config['SECRET_KEY'], salt=app.config['SUPERVISOR_SALT_KEY'])
        try:
            load_reset_token = s.loads(token)
        except:
            return False
        
        if 'expiration_time' in load_reset_token and load_reset_token['expiration_time'] >= int(time.time()):    
            id =  Supervisor.query.get(load_reset_token['user_id'])
            return id
        else:
            return False

    def get_id(self):
        return "supervisor-{}".format(self.id)
    
    # def __repr__(self):
    #     return self.supervisor_email

class PreferredTopic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'))
    priority = db.Column(db.Integer)
    student_id = db.Column(db.Integer, db.ForeignKey('student.id'))
    topic_name = db.Column(db.String(200), nullable=True)


class Topic(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'))
    supervisors_id = db.Column(MutableList.as_mutable(db.PickleType), default=[])
    preferred_topics = db.relationship('PreferredTopic', backref='topic', lazy='dynamic')

    def __repr__(self):
        return self.name

class Student(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    student_Fname = db.Column(db.String(50), nullable=False)
    student_Lname = db.Column(db.String(50), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    student_email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(100), default='student', nullable=False)
    group_allocation = db.Column(db.String(200), nullable=False, default='Not Yet Allocated')
    preferred_topics = db.relationship('PreferredTopic', backref='student', lazy='dynamic')
    reminder_sent = db.Column(db.Boolean, default=False, nullable=False)

    def reset_token(self,expires_sec=1800):
        s = serializer(app.config['SECRET_KEY'], salt=app.config['STUDENT_SALT_KEY'])
        student_details = {'user_id':self.id, 'user_email':self.student_email}
        expiration_time = int(time.time()) + expires_sec
        student_details['expiration_time'] = expiration_time
        token = s.dumps(student_details)
        return token

    @staticmethod
    def verify_reset_token(token):
        s = serializer(app.config['SECRET_KEY'], salt=app.config['STUDENT_SALT_KEY'])
        try:
            load_reset_token = s.loads(token)
        except:
            return False
        
        if 'expiration_time' in load_reset_token and load_reset_token['expiration_time'] >= int(time.time()):    
            id =  Student.query.get(load_reset_token['user_id'])
            return id
        else:
            return False
        
    def get_priority(self, topic):
        """Get the priority of a preferred topic for a student"""
        preferred_topic = self.preferred_topics.filter_by(topic=topic).first()
        if preferred_topic:
            return preferred_topic.priority
        else:
            return None
        
    def get_id(self):
        return "student-{}".format(self.id)
    

# class StudentGroup(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     student_id = db.Column(db.Integer, db.ForeignKey('student.id'), nullable=False)
#     group_id = db.Column(db.Integer, db.ForeignKey('group.id'), nullable=False)
#     topic_id = db.Column(db.Integer, db.ForeignKey('topic.id'), nullable=False)
#     supervisor_id = db.Column(db.Integer, db.ForeignKey('supervisor.id'), nullable=False)

@listens_for(Topic.name, 'set')
def topic_name_changed_listener(target, value, oldvalue, initiator):
    if value != oldvalue:
        for preferred_topic in target.preferred_topics:
            preferred_topic.topic_name = value


class Group(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    topic = db.Column(db.String(50), nullable=False)
    students = db.Column(db.JSON, nullable=False)
    supervisors = db.Column(db.JSON, nullable=False)

    def __init__(self, topic, students, supervisors):
        self.topic = topic
        self.students = students
        self.supervisors = supervisors






