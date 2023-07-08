from WebApp import app, db, mail
from flask import flash, redirect, render_template, url_for, request, jsonify, session
from WebApp.models import Supervisor, Student, Topic, PreferredTopic, Group
from flask_login import current_user, login_user, logout_user, login_required
from WebApp.forms import Registration_Form, RequestResetform, ResetPasswordForm, Login_Form
from werkzeug.security import generate_password_hash, check_password_hash
import networkx as nx
from collections import defaultdict
from datetime import timedelta, datetime
from flask_mail import Message
import matplotlib.pyplot as plt
import random

def generate_hash_password(obj,password):
    obj.password = generate_password_hash(password)

def check_hashed_password(obj, password):
    return check_password_hash(obj.password, password)

@app.route("/")
def home():
    return render_template("HomePage.html")

@app.route("/login", methods=["GET", "POST"])
def Login():
    Form = Login_Form()
    if current_user.is_authenticated:
        flash("Already loged In")
        if current_user.role == "student":
            return redirect(url_for("StudentView"))
        else:
            return redirect(url_for("SupervisorView"))

    if request.method == "GET":
        return render_template("Login.html", form=Form)
    else:
        if Form.validate_on_submit():
            email = Form.email.data
            password = Form.password.data
            remember_me = Form.remember.data

            supervisor = Supervisor.query.filter_by(supervisor_email=email).first()

            student = Student.query.filter_by(student_email=email).first()

            if supervisor and check_hashed_password(supervisor, password):
                login_user(supervisor, remember=remember_me)
                if current_user.supervisor_email == "admin@leicester.ac.uk":
                    flash("Logged in Successful as Admin")
                    return redirect(url_for("admin.index"))
                flash("Logged in successful as Supervisor")
                return redirect(url_for("SupervisorView"))
            
            elif student and check_hashed_password(student, password):
                login_user(student, remember=remember_me)
                flash("Logged in successfully as Student")
                return redirect(url_for("StudentView"))
            else:
                flash("Invalid Email-Address or password")
                return redirect(url_for("Login"))
        else:
            return render_template("Login.html", form=Form)
        
@app.route("/register", methods=["GET", "POST"])
def Register():
    Form = Registration_Form()
    if current_user.is_authenticated:
        return redirect(url_for("home"))

    if request.method == "GET":
        return render_template("Register.html", form=Form)
    else:
        Fname = Form.FirstName.data
        Lanme = Form.LastName.data
        email = Form.email.data
        password = Form.password.data

        if not (email.endswith("@student.le.ac.uk") or (email.endswith("@leicester.ac.uk")) ):
            Form.email.errors = ["Email address must be from '@leicester.ac.uk' or '@student.le.ac.uk' "]
            return render_template("Register.html",form=Form)

        if Form.validate_on_submit():
            if email.endswith("@leicester.ac.uk"):
                supervisor_obj = Supervisor(supervisor_Fname=Fname, supervisor_Lname=Lanme, supervisor_email=email)
                generate_hash_password(supervisor_obj,password)
                db.session.add(supervisor_obj)
                db.session.commit()
                flash("You have registered successfully")
                return redirect(url_for("Login"))
            
            elif email.endswith("@student.le.ac.uk"):
                student_obj = Student(student_Fname=Fname, student_Lname=Lanme, student_email=email)
                generate_hash_password(student_obj,password)
                db.session.add(student_obj)
                db.session.commit()
                flash("You have registered successfully")
                return redirect(url_for("Login"))
            
            else:
                flash("Enter Valid Email-Address")
                return render_template("Register.html", form=Form)
        else:
            return render_template("Register.html", form=Form)


@app.route("/logout")
def logout():
    if current_user.is_authenticated:
        logout_user()
        flash("Loged out successful")
        return redirect(url_for("home"))
    else:
        flash("Have to login first")
        return redirect(url_for("Login"))

@app.route('/ResetPassword', methods=["POST", "GET"])
def reset_password():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    Form = RequestResetform()
    if request.method == "GET":
        return render_template('ForgetPassword.html', form=Form)

    else:
        user_email = Form.email.data
        model = None
        if user_email.endswith("@student.le.ac.uk"):
            model = Student()
        elif user_email.endswith("@leicester.ac.uk"):
            model = Supervisor()
        else:
            Form.email.errors = ["Enter Valid Email-Address"]
            return render_template('ForgetPassword.html', form=Form)

        if Form.validate_on_submit():
            if user_email.endswith("@student.le.ac.uk"):
                user = model.query.filter_by(student_email=user_email).first()
            else:
                user = model.query.filter_by(supervisor=user_email).first()
            if send_reset_email(user):
                flash('An email has been sent with instructions to reset your password.', "warning")
                return redirect(url_for('Login'))
            else:
                flash("Error in Sending Emails at this time, Please come back later")
                return redirect(url_for('home'))
        return render_template('ForgetPassword.html', form=Form)

def send_reset_email(user):
    role = user.role
    if role == "student":
        user = Student.query.filter_by(student_email=user.student_email).first()
        token = user.reset_token()
        username = user.student_Fname + " "+ user.student_Lname
        email = user.student_email
    else:
        user = Supervisor.query.filter_by(supervisor_email=user.supervisor_email).first()
        token = user.reset_token()
        username = user.supervisor_Fname + " "+ user.supervisor_Lname
        email = user.supervisor_email

    try:
        msg = Message(subject="Reset Password Link", sender=('University of Leicester', 'saikiri99@gmail.com'), recipients=[email])
        msg.html = render_template("EmailTemplate.html", token=token, username=username, email=email)
        mail.send(msg)
        return True
    except:
        return False


@app.route('/Reset_Password_Link/<token>', methods=["POST", "GET"])
def reset_token(token):
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    
    Form = ResetPasswordForm()
    user = None
    try:
        if Student.verify_reset_token(token):
            user = Student.verify_reset_token(token)
        elif Supervisor.verify_reset_token(token):
            user = Supervisor.verify_reset_token(token)
        else:
            user = None
    except:
        flash("Token is expired or Invalid")
        return redirect(url_for('reset_password'))
    
    if not user:
        flash("Token is Expired or Invalid, Please re-enter your Email-Address to get new Link", 'warning')
        return redirect(url_for('reset_password'))
    
    if request.method == "GET":
        return render_template("ForgetPasswordLink.html", form=Form)
    else:
        if Form.validate_on_submit():
            new_password = Form.password.data
            hash_password = generate_password_hash(new_password)
            user.password = hash_password
            db.session.commit()
            flash("Your password has been updated! you are now able to log in", "info")
            return redirect(url_for('home'))
        else:
            return render_template("ForgetPasswordLink.html", form=Form)
    
@app.route("/StudentView")
@app.route("/StudentView_Edit_Priority/<int:priority>")
@login_required
def StudentView(priority=None):
    topics = Topic.query.all()
    selected_topic_ids = [topic.topic_id for topic in current_user.preferred_topics]
    not_selected_topics = Topic.query.filter(~(Topic.id.in_(selected_topic_ids))).all()
    deadline = app.config['DEFAULT_DEADLINE']
    if priority == None:
        return render_template("StudentView.html", project_topics = topics, deadline=deadline)
    else:
        return render_template("StudentView.html", project_topics = not_selected_topics, deadline=deadline)

@app.route("/SupervisorView")
def SupervisorView():
    topics = Topic.query.all()
    return render_template("SupervisorView.html", project_topics = topics)

@app.route("/selectedpreferences", methods = ["POST"])
def selectedpreferences():
    data = request.get_json()
    datas = data.items()
    id = PreferredTopic.query.filter_by(student_id = current_user.id).all()

    if not id:
        for data in datas:
            topics = Topic.query.get(int(data[0]))
            store_data =  PreferredTopic(topic_id=data[0], priority=data[1], student_id=current_user.id,topic_name= topics.name)
            db.session.add(store_data)    
        db.session.commit()

    else:
        for data,already_data in zip(datas, current_user.preferred_topics):
            topics = Topic.query.get(int(data[0]))
            already_data.topic_id = data[0]
            already_data.priority = data[1]
            already_data.topic_name = topics.name
            db.session.add(already_data)
        db.session.commit()

    response_data = {"message": "success", "redirect":"/profile"}
    return jsonify(response_data)
         
@app.route('/supervisortopics', methods=["POST"])
def supervisortopics():
    req_data = request.get_json()
    data = req_data["selectedTopics"]
    supervisor_obj = Supervisor.query.get(current_user.id)
    if len(data) > 0:
        for topic_ids in data:
            topic_obj = Topic.query.get(int(topic_ids))
            if topic_obj.supervisors_id != None and supervisor_obj not in topic_obj.supervisors_id:
                topic_obj.supervisors_id.append(supervisor_obj)  
                db.session.add(topic_obj)
        supervisor_obj.willing_to_supervise = True
        supervisor_obj.number_of_topics_to_supervise = int(req_data["noOfTopics"])
        db.session.add(supervisor_obj)
        db.session.commit()
    
    else:
        all_topics = Topic.query.all()
        for topics in all_topics:
            if topics.supervisors_id != None and supervisor_obj in topics.supervisors_id:
                topics.supervisors_id.remove(supervisor_obj)
                db.session.commit()

        supervisor_obj.willing_to_supervise = False
        supervisor_obj.number_of_topics_to_supervise = 0
        db.session.add(supervisor_obj)
        db.session.commit()

    response_data = {"message": "success", "redirect":"/profile"}
    return jsonify(response_data)

@app.route("/remove-topics", methods=["POST"])
def remove_topics():
    req_data = request.get_json()
    tp_id = int(req_data['topic_data'])
    supervisor_obj = Supervisor.query.get(current_user.id)
    topic_to_remove = Topic.query.get(tp_id)
    if supervisor_obj in topic_to_remove.supervisors_id:
        topic_to_remove.supervisors_id.remove(supervisor_obj)
        db.session.commit()
    return jsonify({"msg":"success"})

@app.route("/profile")
def Profile():
    if current_user.is_authenticated:
        if current_user.role == "supervisor":
            t = Topic.query.all()
            return render_template("Profile.html", supervisor_topics=t)
        else:
            preferred_topics = [(topic.topic_name,topic.priority) for topic in current_user.preferred_topics.order_by(PreferredTopic.priority.asc())]
            return render_template("Profile.html", preferred_topics=preferred_topics)
    else:
        flash("You have to login")
        return redirect(url_for("Login"))


@app.route("/preferences_edit", methods=["POST"])
def preferences_edit():
    data = request.get_json()
    priority_to_change = int(data['priority_to_edit'])
    return jsonify({"msg": "done", "redirect":"/StudentView_Edit_Priority/{}".format(priority_to_change)})


@app.route("/changepriority", methods=["POST"])
def change_priority():
    data = request.get_json()
    data = list(data.items())
    topics = Topic.query.get(int(data[0][0]))
    priority_to_change = int(data[0][1])
    preferred_topic = PreferredTopic.query.filter_by(student_id=current_user.id, priority=priority_to_change).first()
    if preferred_topic:
        preferred_topic.topic_id = topics.id
        preferred_topic.topic_name = topics.name
        db.session.commit()
    return jsonify({"msg":"success", "redirect":"/profile"})


@app.route("/groupresult/<int:num_of_students>", methods=["POST", "GET"])
def group(num_of_students):
    students = Student.query.all()
    random.shuffle(students)
    g = nx.Graph()
    for student in students:
        stu_id = 'student_id' + ' ' + str(student.id)
        if not g.has_node(stu_id):
            g.add_node(stu_id, bipartite=0)
            for preferred_topic in student.preferred_topics:
                topic = preferred_topic.topic
                priority = preferred_topic.priority
                tp_id = 'topic_id' + ' ' + str(topic.id)
                if not g.has_node(tp_id):
                    g.add_node(tp_id, bipartite=1)
                # print(f"Adding edge from {student.student_Fname} to {topic.name} with priority {priority}")
                g.add_edge(stu_id, tp_id, weight=priority)

    num_students_per_group = num_of_students
    num_students_per_group = max(1, min(num_students_per_group, len(students)))
    components = list(nx.connected_components(g))
    # Grouping code below
    groups = {}
    assigned_students = set()
    unassigned_students = []
    supervisors_by_topic = {}
    for topic in Topic.query.all():
        supervisors_by_topic[topic.id] = topic.supervisors_id

    for component in components:
        # Filter out topic nodes
        student_nodes = [node for node in component if node.startswith('student_id')]
        students_in_component = [next(student for student in students if 'student_id' + ' ' + str(student.id) == node) for node in student_nodes]
        for student in students_in_component:
            if student.preferred_topics.count() == 0:
                unassigned_students.append(student)
                break
            if student in assigned_students:
                continue
            assigned = False
            # Prioritize assigning students to groups based on their first preferred topic and priority
            for preferred_topic in sorted(student.preferred_topics, key=lambda pt: pt.priority):
                topic = preferred_topic.topic

                if (topic.id, preferred_topic.priority) in groups:
                    group = groups[(topic.id, preferred_topic.priority)]
                    if len(group) < num_students_per_group:
                        group.append(student)
                        assigned_students.add(student)
                        assigned = True
                        break
                    
                else:
                    for tpc in groups.keys():
                        if tpc[0] == topic.id:
                            break
                    else:
                        group = []
                        group.append(student)
                        groups[(topic.id, preferred_topic.priority)] = group
                        assigned_students.add(student)
                        assigned = True
                        break

                if len(group) < num_students_per_group:
                    group.append(student)
                    assigned_students.add(student)
                    assigned = True
                    break

            if assigned:
                continue
            else:
                unassigned_students.append(student)

            for not_allocate_student in unassigned_students:
                if not_allocate_student.preferred_topics.count() != 0:
                    ls = []
                    for prefered_topic in not_allocate_student.preferred_topics:
                        ls.append(prefered_topic.topic_id)
                    for topics in groups:
                        if topics[0] in ls and len(groups[topics]) < num_students_per_group:
                            grp = groups[topics]
                            grp.append(not_allocate_student)
                            unassigned_students.remove(not_allocate_student)
                            break
    
    print(groups)
    Group.query.delete()
    for (topic_id, priority), students in groups.items():
        topic = Topic.query.get(topic_id)

        print(f"Group for topic '{topic.name}' and priority {priority}:")

        supervisor_ids = [supervisor.id for supervisor in topic.supervisors_id]
        if len(supervisor_ids) > 2:
            supervisor_ids = supervisor_ids[0:2]
        student_list = [stu_id.id for stu_id in students]
        for student in students:
            student_group_update = Student.query.get(student.id)
            student_group_update.group_allocation = topic.name
            db.session.commit()
            print(f"  - {student.student_Fname} {student.student_Lname}")
        new_group = Group(topic=topic.name, students=student_list,supervisors=supervisor_ids)
        db.session.add(new_group)
        db.session.commit()

    if len(unassigned_students) > 0:
        print("The following students were not assigned to any group:")
        for student in unassigned_students:
            stu = Student.query.get(student.id)
            stu.group_allocation = 'Not Yet Allocated'
            db.session.commit()
            print(f"  - {student.student_Fname} {student.student_Lname}")

    return jsonify({"msg":"Matching algorithm succed", "redirect":"/StudentAllocation-Admin-Dashboard"})