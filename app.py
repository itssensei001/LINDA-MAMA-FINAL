from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
import secrets
import os
from datetime import datetime, timedelta
import random
from flask_socketio import SocketIO
from flask_mail import Mail, Message
import re
import logging

app = Flask(__name__)
app.secret_key = "your_secret_key"
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:EddieOliver..1@localhost/linda_mama'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Configure Flask-Mail for actual email sending
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False
app.config['MAIL_USERNAME'] = 'oliedd003@gmail.com'
app.config['MAIL_PASSWORD'] = 'izstwblikkwnegfl'  # App password from Google
app.config['MAIL_DEFAULT_SENDER'] = 'oliedd003@gmail.com'
app.config['MAIL_DEBUG'] = True
app.config['MAIL_SUPPRESS_SEND'] = False  # Enable actual email sending
app.config['MAIL_MAX_EMAILS'] = 5
app.config['TESTING'] = False
mail = Mail(app)

# Make datetime available in all templates
@app.context_processor
def inject_datetime():
    return {'datetime': datetime}

# ---------------------------------------------------
# 1) Configure SQLAlchemy (ORM) and MySQL (raw SQL)
# ---------------------------------------------------
db = SQLAlchemy(app)
migrate = Migrate(app, db)

app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = 'root'
app.config['MYSQL_PASSWORD'] = 'EddieOliver..1'
app.config['MYSQL_DB'] = 'linda_mama'
mysql = MySQL(app)

# ---------------------------------------------------
# 2) Configure Google OAuth
# ---------------------------------------------------
oauth = OAuth(app)
google = oauth.register(
    name='google',
    client_id="944644137951-fktmua0vvs3d4imfh2nl5iirv7uhft5d.apps.googleusercontent.com",
    client_secret="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",
    authorize_url="https://accounts.google.com/o/oauth2/auth",
    access_token_url="https://oauth2.googleapis.com/token",
    userinfo_endpoint="https://openidconnect.googleapis.com/v1/userinfo",
    jwks_uri="https://www.googleapis.com/oauth2/v3/certs",
    redirect_uri="http://127.0.0.1:5000/google/callback",
    client_kwargs={"scope": "openid email profile"}
)

# ---------------------------------------------------
# 3) SQLAlchemy Models
# ---------------------------------------------------
class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    full_name = db.Column(db.String(100), nullable=False)  
    role = db.Column(db.String(20), nullable=False)  # 'mother', 'guardian', 'doctor'
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    verification_token = db.Column(db.String(100), unique=True, nullable=True)
    
    # Relationships
    mother_profile = db.relationship('MotherProfile', backref='user', uselist=False)
    doctor_profile = db.relationship('DoctorProfile', backref='user', uselist=False)
    guardian_requests = db.relationship('GuardianRequest', backref='guardian', foreign_keys='GuardianRequest.guardian_id')
    guardian_approvals = db.relationship('GuardianApproval', backref='guardian', foreign_keys='GuardianApproval.guardian_id')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class GuardianRequest(db.Model):
    __tablename__ = "guardian_requests"
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mother_email = db.Column(db.String(100), nullable=False)
    request_date = db.Column(db.DateTime, default=datetime.utcnow)
    status = db.Column(db.String(20), default='pending')  # pending, approved, rejected

class GuardianApproval(db.Model):
    __tablename__ = "guardian_approvals"
    id = db.Column(db.Integer, primary_key=True)
    guardian_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    mother_id = db.Column(db.Integer, db.ForeignKey('mother_profiles.user_id'), nullable=False)
    approval_date = db.Column(db.DateTime, default=datetime.utcnow)

class HealthMetric(db.Model):
    __tablename__ = "health_metrics"
    id = db.Column(db.Integer, primary_key=True)
    mother_id = db.Column(db.Integer, db.ForeignKey('mother_profiles.user_id'), nullable=False)
    date_recorded = db.Column(db.DateTime, default=datetime.utcnow)
    weight = db.Column(db.Float)
    blood_pressure = db.Column(db.String(20))
    heart_rate = db.Column(db.Integer)
    blood_sugar = db.Column(db.Float)
    body_temperature = db.Column(db.Float)

class Appointment(db.Model):
    __tablename__ = "appointments"
    id = db.Column(db.Integer, primary_key=True)
    mother_id = db.Column(db.Integer, db.ForeignKey('mother_profiles.user_id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.user_id'), nullable=True)
    date = db.Column(db.Date, nullable=False)
    time = db.Column(db.Time, nullable=False)
    appointment_type = db.Column(db.String(50))
    status = db.Column(db.String(20), default='scheduled')  # scheduled, completed, cancelled

class ForumCategory(db.Model):
    __tablename__ = "forum_categories"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    posts = db.relationship('ForumPost', backref='category', lazy=True)

class ForumPost(db.Model):
    __tablename__ = "forum_posts"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('forum_categories.id'), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text, nullable=False)
    post_date = db.Column(db.DateTime, default=datetime.utcnow)
    comments = db.relationship('ForumComment', backref='post', lazy=True)

class ForumComment(db.Model):
    __tablename__ = "forum_comments"
    id = db.Column(db.Integer, primary_key=True)
    post_id = db.Column(db.Integer, db.ForeignKey('forum_posts.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    comment_date = db.Column(db.DateTime, default=datetime.utcnow)

class Message(db.Model):
    __tablename__ = "messages"
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    receiver_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    message_type = db.Column(db.String(20), default='user')  # user, doctor, ai

class MotherProfile(db.Model):
    __tablename__ = "mother_profiles"
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    due_date = db.Column(db.Date, nullable=True)
    current_week = db.Column(db.Integer, nullable=True)
    trimester = db.Column(db.String(20), nullable=True)
    weight = db.Column(db.Float)
    blood_pressure = db.Column(db.String(20))
    sugar_levels = db.Column(db.Float)
    age = db.Column(db.String(20))
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctor_profiles.id'), nullable=True)
    last_visit_date = db.Column(db.DateTime, nullable=True)
    height = db.Column(db.Float)
    bmi = db.Column(db.Float)
    
    # Guardian approvals - mothers who approved this guardian
    approvals_received = db.relationship('GuardianApproval', backref='mother', foreign_keys='GuardianApproval.mother_id')
    # Health metrics
    health_metrics = db.relationship('HealthMetric', backref='mother', lazy=True)
    # Appointments
    appointments = db.relationship('Appointment', backref='mother', lazy=True)

class DoctorProfile(db.Model):
    __tablename__ = "doctor_profiles"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    specialty = db.Column(db.String(100))
    hospital = db.Column(db.String(150))
    
    # Appointments scheduled with this doctor
    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

class Notification(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    notification_type = db.Column(db.String(50))
    related_id = db.Column(db.Integer)  # ID of related record (e.g., guardian request)

# ---------------------------------------------------
# 4) Routes
# ---------------------------------------------------
@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        full_name = request.form.get('full_name')
        role = request.form.get('role')
        
        # Use email as username
        username = email
        
        # Check if user already exists - FIRST CHECK
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('Account already exists. Please login instead.')
            return redirect(url_for('login'))
        
        # Check email domain - SECOND CHECK
        if not (email.endswith('@gmail.com') or email.endswith('@yahoo.com')):
            flash('Email must be a Gmail or Yahoo address.')
            return redirect(url_for('signup'))
        
        # Validate password - THIRD CHECK
        password_regex = re.compile(r'^(?=.*\d)(?=.*[!@#$%^&*\.])[a-zA-Z0-9!@#$%^&*\.]{6,}$')
        if not password_regex.match(password):
            flash('Password must be at least 6 characters long and include at least 1 number and 1 symbol.')
            return redirect(url_for('signup'))
        
        # Create verification token
        verification_token = secrets.token_urlsafe(32)
        
        # Create new user with username field set
        new_user = User(
            username=username,
            email=email,
            full_name=full_name,
            role=role,
            verification_token=verification_token
        )
        new_user.set_password(password)
        
        db.session.add(new_user)
        db.session.commit()
        
        # Try to send email, but also provide direct verification link
        verification_url = url_for('verify_email', token=verification_token, _external=True)
        try:
            email_sent = send_verification_email(new_user)
            if email_sent:
                flash(f'Account created! Please check your email to verify your account. You must verify your email before logging in.')
            else:
                # Email sending failed, provide direct verification link
                flash(f'Email could not be sent. Please click this link to verify your account: <a href="{verification_url}" class="verification-link">Verify Account</a>', 'verification')
        except Exception as e:
            print(f"Error in signup: {str(e)}")
            # Provide direct verification link on error
            flash(f'Account created! Click this link to verify your account: <a href="{verification_url}" class="verification-link">Verify Account</a>', 'verification')
        
        return redirect(url_for('login'))
    
    return render_template('signup.html')

def send_verification_email(user):
    token = user.verification_token
    verification_url = url_for('verify_email', token=token, _external=True)

    try:
        msg = Message(
            subject='Verify your email for Linda Mama Health System',
            recipients=[user.email]
        )
        msg.body = f'Hello {user.full_name},\n\nPlease verify your email by clicking on the following link: {verification_url}\n\nThank you,\nLinda Mama Health System Team'
        msg.html = f'''
        <h1>Welcome to Linda Mama Health System!</h1>
        <p>Hello {user.full_name},</p>
        <p>Please verify your email by clicking on the following link:</p>
        <p><a href="{verification_url}">Verify Your Email</a></p>
        <p>Or copy and paste this URL into your browser:</p>
        <p>{verification_url}</p>
        <p>Thank you,<br>Linda Mama Health System Team</p>
        '''
        
        # Print diagnostic information
        print(f"Attempting to send email to: {user.email}")
        print(f"Verification URL: {verification_url}")
        
    mail.send(msg)
        print(f"Email sent successfully to {user.email}")
        return True
    except Exception as e:
        print(f"Failed to send email to {user.email}: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

@app.route('/verify-email/<token>')
def verify_email(token):
    user = User.query.filter_by(verification_token=token).first()
    if user:
        user.is_verified = True
        user.verification_token = None
        db.session.commit()
        flash('Your account has been verified! You can now login.')
    else:
        flash('Invalid or expired verification link.')
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        user = User.query.filter_by(email=email).first()
        
        if not user:
            flash('No account found with that email address.', 'login_error')
            return redirect(url_for('login'))
            
        if not user.check_password(password):
            flash('Invalid password. Please try again.', 'login_error')
            return redirect(url_for('login'))
            
        if not user.is_verified:
            flash('Please verify your email before logging in.', 'login_error')
            return redirect(url_for('login'))
        
        login_user(user)
        return redirect(url_for(f'{user.role}_dashboard'))
    
    return render_template('login.html')

@app.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user()
    return jsonify({"success": True})

@app.route('/mother_dashboard')
@login_required
def mother_dashboard():
    if current_user.role != 'mother':
        return redirect(url_for('login'))

    # Fetch the mother's profile
    mother_profile = MotherProfile.query.filter_by(user_id=current_user.id).first()

    if not mother_profile:
        # Create a new mother profile instead of redirecting
        mother_profile = MotherProfile(user_id=current_user.id)
        db.session.add(mother_profile)
        db.session.commit()
        flash("Welcome! Your profile has been created.")

    # Fetch latest health metrics
    latest_metrics = HealthMetric.query.filter_by(mother_id=current_user.id).order_by(HealthMetric.date_recorded.desc()).first()
    
    # Get upcoming appointments
    appointments = Appointment.query.filter_by(
        mother_id=current_user.id, 
        status='scheduled'
    ).order_by(Appointment.date).limit(3).all()
    
    # Get pending guardian requests
    guardian_requests_query = GuardianRequest.query.filter_by(
        mother_email=current_user.email,
        status='pending'
    ).all()
    
    # Convert guardian requests to serializable dictionaries
    guardian_requests = []
    for request in guardian_requests_query:
        guardian = User.query.get(request.guardian_id)
        guardian_requests.append({
            'id': request.id,
            'guardian_id': request.guardian_id,
            'guardian_name': guardian.full_name if guardian else 'Unknown',
            'request_date': request.request_date.strftime('%Y-%m-%d')
        })
    
    return render_template(
        'mother/mother_dashboard.html',
        mother_profile=mother_profile,
        metrics=latest_metrics,
        appointments=appointments,
        guardian_requests=guardian_requests
    )

@app.route("/google_login")
def google_login():
    # Set up nonce for security
    nonce = secrets.token_urlsafe(16)
    session["nonce"] = nonce
    
    # Redirect to Google authentication
    return google.authorize_redirect(
        url_for("google_callback", _external=True),
        nonce=nonce,
        prompt="consent"  # Always show consent screen
    )

@app.route("/google_callback")
def google_callback():
    token = google.authorize_access_token()
    if token is None:
        flash("Google login failed!", "danger")
        return redirect(url_for("login"))

    nonce = session.pop("nonce", None)
    if nonce is None:
        flash("Login failed: missing nonce", "danger")
        return redirect(url_for("login"))

    user_info = google.parse_id_token(token, nonce)
    email = user_info["email"]
    full_name = user_info.get("name", "Google User")

    # Check if user already exists
    existing_user = User.query.filter_by(email=email).first()
    
    if existing_user:
        # User exists - log them in
        login_user(existing_user)
        
        # Check if guardian has approval
        if existing_user.role == "guardian":
            approval = GuardianApproval.query.filter_by(guardian_id=existing_user.id).first()
            if not approval:
                flash("Your guardian request is still pending approval")
                return redirect(url_for("login"))
                
        flash("Login successful!", "success")
        return redirect(url_for(f"{existing_user.role}_dashboard"))
    else:
        # New user - get role from session
        role = session.pop("google_signup_role", None)
        
        if not role:
            flash("Please select a role before signing up with Google")
            return redirect(url_for("signup_with_google"))
        
        # Create the new user with the selected role
        new_user = User(
            username=email,
            email=email,
            full_name=full_name,
            role=role
        )
        new_user.set_password(secrets.token_urlsafe(16))  # Random secure password
        db.session.add(new_user)
        db.session.commit()
        
        # Handle role-specific setup
        if role == "mother":
            mother_profile = MotherProfile(user_id=new_user.id)
            db.session.add(mother_profile)
            
        elif role == "doctor":
            specialty = session.pop("doctor_specialty", "")
            hospital = session.pop("doctor_hospital", "")
            doctor_profile = DoctorProfile(
                user_id=new_user.id,
                specialty=specialty,
                hospital=hospital
            )
            db.session.add(doctor_profile)
            
        elif role == "guardian":
            mother_email = session.pop("guardian_mother_email", "")
            guardian_request = GuardianRequest(
                guardian_id=new_user.id,
                mother_email=mother_email
            )
            db.session.add(guardian_request)
            
            # Create notification for mother
            mother = User.query.filter_by(email=mother_email, role="mother").first()
            if mother:
                notification = Notification(
                    user_id=mother.id,
                    content=f"{full_name} wants to be your guardian",
                    notification_type="guardian_request",
                    related_id=guardian_request.id
                )
                db.session.add(notification)
        
        db.session.commit()
        
        # Log in the new user
        login_user(new_user)
        
        # For guardians, show waiting page
        if role == "guardian":
            flash("Your guardian request has been sent. Please wait for approval.")
            return render_template('login.html')
            
        flash("Sign up successful!", "success")
        return redirect(url_for(f"{role}_dashboard"))

@app.route('/doctor_dashboard')
@login_required
def doctor_dashboard():
    if current_user.role != 'doctor':
        return redirect(url_for('login'))
    
    # Ensure doctor profile exists
    if not hasattr(current_user, 'doctor_profile') or not current_user.doctor_profile:
        doctor_profile = DoctorProfile(user_id=current_user.id)
        db.session.add(doctor_profile)
        db.session.commit()
        current_user.doctor_profile = doctor_profile

    # Fetch patients assigned to the doctor, joining with User to get full name
    patients = db.session.query(MotherProfile, User).join(
        User, User.id == MotherProfile.user_id
    ).filter(MotherProfile.doctor_id == current_user.doctor_profile.id).all()
    
    # Create a separate list of patient-user mappings for JavaScript
    patient_user_map = []
    for patient, user in patients:
        patient_user_map.append({
            'patient_id': patient.id,
            'user_id': user.id,
            'name': user.full_name
        })
    
    # Fetch the doctor's upcoming appointments
    upcoming_appointments = db.session.query(
        Appointment, User, MotherProfile
    ).join(
        MotherProfile, Appointment.mother_id == MotherProfile.user_id
    ).join(
        User, User.id == MotherProfile.user_id
    ).filter(
        Appointment.doctor_id == current_user.id,
        Appointment.status == 'scheduled'
    ).order_by(
        Appointment.date, Appointment.time
    ).all()
    
    # Format the appointments for the template
    formatted_appointments = []
    for appt, user, profile in upcoming_appointments:
        formatted_appointments.append({
            'id': appt.id,
            'date': appt.date,
            'time': appt.time,
            'patient_name': user.full_name,
            'patient_id': profile.id,
            'appointment_type': appt.appointment_type
        })

    return render_template(
        'doctor/doctor_dashboard.html', 
        doctor_name=current_user.full_name, 
        patients=patients,
        patient_user_map=patient_user_map,
        appointments=formatted_appointments
    )

@app.route('/guardian_dashboard')
@login_required
def guardian_dashboard():
    if current_user.role != 'guardian':
        return redirect(url_for('login'))

    # Get the mother this guardian is approved for
    approval = GuardianApproval.query.filter_by(guardian_id=current_user.id).first()
    
    if not approval:
        return "Your guardian request is still pending approval"
    
    mother = User.query.get(approval.mother_id)
    mother_profile = MotherProfile.query.filter_by(user_id=mother.id).first()
    
    # Get mother's latest health metrics
    latest_metrics = HealthMetric.query.filter_by(mother_id=mother.id).order_by(HealthMetric.date_recorded.desc()).first()
    
    # Get mother's upcoming appointments
    appointments = Appointment.query.filter_by(
        mother_id=mother.id, 
        status='scheduled'
    ).order_by(Appointment.date).limit(1).all()
    
    return render_template(
        'guardian/guardian_dashboard.html',
        mother=mother,
        mother_profile=mother_profile,
        metrics=latest_metrics,
        appointments=appointments,
        now=datetime.utcnow
    )

@app.route('/approve_guardian/<int:request_id>/<action>')
@login_required
def approve_guardian(request_id, action):
    if current_user.role != 'mother':
        flash('Permission denied')
        return redirect(url_for('mother_dashboard'))
    
    guardian_request = GuardianRequest.query.get_or_404(request_id)
    
    if guardian_request.mother_email != current_user.email:
        flash('Permission denied')
        return redirect(url_for('mother_dashboard'))
    
    if action == 'approve':
        # Create approval record
        approval = GuardianApproval(
            guardian_id=guardian_request.guardian_id,
            mother_id=current_user.id
        )
        db.session.add(approval)
        guardian_request.status = 'approved'
        flash('Guardian approved')
    elif action == 'deny':
        guardian_request.status = 'rejected'
        flash('Guardian request denied')
    
        db.session.commit()
    return redirect(url_for('mother_dashboard'))

@app.route('/deny_guardian/<int:request_id>', methods=['POST'])
def deny_guardian(request_id):
    try:
        request_entry = GuardianRequest.query.get(request_id)
        if not request_entry:
            return jsonify({"error": "Request not found"}), 404

        db.session.delete(request_entry)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        print("Deny guardian error:", e)
        return jsonify({"error": str(e)}), 500

@app.route('/get_guardian_requests', methods=['GET'])
def get_guardian_requests():
    if 'user_id' not in session or session['role'] != 'mother':
        return {"success": False, "message": "Unauthorized access!"}, 403

    mother_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT id, guardian_email, guardian_name
        FROM guardian_requests
        WHERE mother_id = %s AND status = 'pending'
    """, (mother_id,))
    guardian_requests = cursor.fetchall()
    cursor.close()

    requests_list = [{"id": req[0], "guardian_email": req[1], "guardian_name": req[2]} for req in guardian_requests]
    return {"success": True, "guardian_requests": requests_list}

@app.route('/submit_health_metrics', methods=['POST'])
@login_required
def submit_health_metrics():
    try:
        data = request.get_json()
        if not data:
            return jsonify({"success": False, "error": "No data provided"}), 400

        current_week = int(data.get('current_week'))
        height = float(data.get('height'))  # Get height
        weight = float(data.get('weight'))  # Get weight
        bmi = float(data.get('bmi'))  # Get BMI
        due_date = datetime.now() + timedelta(weeks=(40 - current_week))  # Calculate due date
        formatted_due_date = due_date.date()  # Format for storage

        # Check if a MotherProfile already exists for the current user
        mother_profile = MotherProfile.query.filter_by(user_id=current_user.id).first()

        if mother_profile:
            # Update the existing profile
            mother_profile.weight = weight
            mother_profile.height = height  # Update height
            mother_profile.bmi = bmi  # Update BMI
            mother_profile.blood_pressure = data.get('blood_pressure')
            mother_profile.sugar_levels = data.get('blood_sugar')
            mother_profile.age = data.get('age')
            mother_profile.current_week = current_week
            mother_profile.trimester = data.get('trimester')
            mother_profile.due_date = formatted_due_date
        else:
            # Create a new MotherProfile instance if it doesn't exist
            mother_profile = MotherProfile(
                user_id=current_user.id,
                weight=weight,
                height=height,  # Store height
                bmi=bmi,  # Store BMI
                blood_pressure=data.get('blood_pressure'),
                sugar_levels=data.get('blood_sugar'),
                age=data.get('age'),
                current_week=current_week,
                trimester=data.get('trimester'),
                due_date=formatted_due_date
            )
            db.session.add(mother_profile)

        # Commit the changes to the database
        db.session.commit()

        return jsonify({"success": True, "metrics": data})
    except Exception as e:
        print("Error saving health metrics:", e)
        return jsonify({"success": False, "error": str(e)}), 500

# Move these lines near line 35, right after db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Fetch latest health metrics as JSON (for AJAX updates)
@app.route('/api/health_metrics/latest')
@login_required
def get_latest_metrics():
    mother_id = current_user.id
    
    # For guardians, get the associated mother's ID
    if current_user.role == 'guardian':
        approval = GuardianApproval.query.filter_by(guardian_id=current_user.id).first()
        if not approval:
            return {"error": "No approved mother found"}, 403
        mother_id = approval.mother_id
    
    # Get latest metrics
    latest = HealthMetric.query.filter_by(mother_id=mother_id).order_by(HealthMetric.date_recorded.desc()).first()
    
    if latest:
        return {
            "weight": latest.weight,
            "blood_pressure": latest.blood_pressure,
            "heart_rate": latest.heart_rate,
            "blood_sugar": latest.blood_sugar,
            "body_temperature": latest.body_temperature,
            "date_recorded": latest.date_recorded.strftime('%Y-%m-%d %H:%M:%S')
        }
    else:
        return {"error": "No health metrics found"}, 404

# Forum post creation
@app.route('/api/forum/post', methods=['POST'])
@login_required
def create_forum_post():
    data = request.json
    
    new_post = ForumPost(
        user_id=current_user.id,
        category_id=data.get('category_id'),
        title=data.get('title'),
        content=data.get('content')
    )
    
    db.session.add(new_post)
    db.session.commit()
    
    return {"success": True, "post_id": new_post.id}

# Message sending API (for doctor chat and AI assistant)
@app.route('/api/messages/send', methods=['POST'])
@login_required
def send_message():
    data = request.json
    receiver_id = data.get('receiver_id')
    content = data.get('content')
    message_type = data.get('message_type', 'user')  # Default to 'user'
    
    # Special handling for doctor-patient communication
    if current_user.role == 'doctor':
        # Check if receiver_id might be a mother's profile ID instead of User.id
        # First try to see if it's a valid user ID
        receiver_user = User.query.get(receiver_id)
        if not receiver_user:
            # It might be a mother profile ID, try to get the associated user
            mother_profile = MotherProfile.query.get(receiver_id)
            if mother_profile:
                receiver_id = mother_profile.user_id
    
    # Special handling for mother-doctor communication
    elif current_user.role == 'mother':
        # If receiver_id is a DoctorProfile ID, convert to User.id
        receiver_user = User.query.get(receiver_id)
        if not receiver_user:
            # It might be a doctor profile ID
            doctor_profile = DoctorProfile.query.get(receiver_id)
            if doctor_profile:
                receiver_id = doctor_profile.user_id
    
    # Final validation of receiver ID
    if not receiver_id or not User.query.get(receiver_id):
        return {"success": False, "error": "Invalid receiver ID"}, 400

    new_message = Message(
        sender_id=current_user.id,
        receiver_id=receiver_id,
        content=content,
        message_type=message_type
    )

    db.session.add(new_message)
    db.session.commit()

    return {"success": True, "message_id": new_message.id}

# Get conversation history
@app.route('/api/messages/conversation/<int:other_user_id>')
@login_required
def get_conversation(other_user_id):
    messages = Message.query.filter(
        ((Message.sender_id == current_user.id) & (Message.receiver_id == other_user_id)) |
        ((Message.sender_id == other_user_id) & (Message.receiver_id == current_user.id))
    ).order_by(Message.timestamp).all()
    
    conversation = []
    for msg in messages:
        conversation.append({
            "id": msg.id,
            "sender_id": msg.sender_id,
            "content": msg.content,
            "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "is_sender": msg.sender_id == current_user.id
        })
    
    return {"conversation": conversation}

# Route to fetch notifications
@app.route('/api/notifications')
@login_required
def get_notifications():
    notifications = Notification.query.filter_by(
        user_id=current_user.id,
        is_read=False
    ).order_by(Notification.timestamp.desc()).all()
    
    result = []
    for notif in notifications:
        result.append({
            "id": notif.id,
            "content": notif.content,
            "timestamp": notif.timestamp.strftime('%Y-%m-%d %H:%M:%S'),
            "type": notif.notification_type,
            "related_id": notif.related_id
        })
    
    return {"notifications": result}

# Mark notification as read
@app.route('/api/notifications/read/<int:notification_id>', methods=['POST'])
@login_required
def mark_notification_read(notification_id):
    notification = Notification.query.get_or_404(notification_id)
    
    if notification.user_id != current_user.id:
        return {"error": "Permission denied"}, 403
    
    notification.is_read = True
    db.session.commit()
    
    return {"success": True}

@app.route('/settings.html')
@login_required
def settings():
    if current_user.role != 'mother':
        return redirect(url_for('login'))
    return render_template('mother/settings.html')

@app.route('/health_monitoring.html')
@login_required
def health_monitoring():
    if current_user.role != 'mother':
        return redirect(url_for('login'))
    return render_template('mother/health_monitoring.html')

@app.route('/mealplan_and_nutrition.html')
@login_required
def mealplan_and_nutrition():
    if current_user.role != 'mother':
        return redirect(url_for('login'))
    return render_template('mother/mealplan_and_nutrition.html')

@app.route('/comm_and_support.html')
@login_required
def comm_and_support():
    if current_user.role != 'mother':
        return redirect(url_for('login'))
    return render_template('mother/comm_and_support.html')

@app.route("/signup_with_google", methods=["GET", "POST"])
def signup_with_google():
    if request.method == "POST":
        role = request.form.get("role")
        
        # Validate the role
        if role not in ["mother", "doctor", "guardian"]:
            flash("Invalid role selected")
            return redirect(url_for("signup_with_google"))
        
        # Store the selected role in session
        session["google_signup_role"] = role
        
        # If guardian, collect mother's email
        if role == "guardian":
            mother_email = request.form.get("mother_email")
            if not mother_email:
                flash("Mother's email is required for guardian signup")
                return redirect(url_for("signup_with_google"))
            session["guardian_mother_email"] = mother_email
        
        # If doctor, collect specialty and hospital
        if role == "doctor":
            specialty = request.form.get("specialty")
            hospital = request.form.get("hospital")
            if not specialty or not hospital:
                flash("Specialty and hospital are required for doctor signup")
                return redirect(url_for("signup_with_google"))
            session["doctor_specialty"] = specialty
            session["doctor_hospital"] = hospital
        
        # Now redirect to Google OAuth
        return redirect(url_for("google_login"))
        
    return render_template("signup_with_google.html")

def assign_patients_to_doctors():
    # Get all doctors and mothers
    doctors = DoctorProfile.query.all()
    mothers = User.query.filter_by(role='mother').all()

    # Create a dictionary to hold doctor assignments
    doctor_assignments = {doctor.id: [] for doctor in doctors}

    for mother in mothers:
        # Randomly select a doctor
        available_doctors = [doctor for doctor in doctors if len(doctor_assignments[doctor.id]) < 5]
        
        if available_doctors:
            selected_doctor = random.choice(available_doctors)
            doctor_assignments[selected_doctor.id].append(mother)
            mother.doctor_id = selected_doctor.id  # Assign the doctor to the mother

    # Commit changes to the database
    db.session.commit()

@app.before_request
def setup():
    # Call the assignment function
    assign_patients_to_doctors()

@app.route('/api/patient_info/<int:patient_id>')
@login_required
def get_patient_info(patient_id):
    if current_user.role != 'doctor':
        return jsonify({"error": "Unauthorized access"}), 403
    
    # Fetch the patient's profile
    patient = MotherProfile.query.get_or_404(patient_id)
    
    # Get associated user information
    user = User.query.get(patient.user_id)
    if not user:
        return jsonify({"error": "User not found for this patient"}), 404
    
    # Fetch chat history between doctor and mother
    chat_history = Message.query.filter(
        db.or_(
            db.and_(Message.sender_id == current_user.id, Message.receiver_id == user.id),
            db.and_(Message.sender_id == user.id, Message.receiver_id == current_user.id)
        )
    ).order_by(Message.timestamp).all()

    # Prepare chat messages
    chat_messages = []
    for msg in chat_history:
        chat_messages.append({
            "id": msg.id,
            "content": msg.content,
            "sender_id": msg.sender_id,
            "is_from_doctor": msg.sender_id == current_user.id,
            "timestamp": msg.timestamp.strftime('%Y-%m-%d %H:%M:%S')
        })

    # Get latest health metrics
    latest_metrics = HealthMetric.query.filter_by(mother_id=user.id)\
        .order_by(HealthMetric.date_recorded.desc()).first()
    
    # Get upcoming appointments
    upcoming_appointments = Appointment.query.filter_by(
        mother_id=user.id,
        status='scheduled'
    ).order_by(Appointment.date).limit(3).all()
    
    # Format appointments
    formatted_appointments = []
    for appt in upcoming_appointments:
        doctor_name = "Not assigned"
        if appt.doctor_id:
            doctor = User.query.get(appt.doctor_id)
            if doctor:
                doctor_name = doctor.full_name
                
        formatted_appointments.append({
            "id": appt.id,
            "date": appt.date.strftime('%Y-%m-%d'),
            "time": appt.time.strftime('%H:%M'),
            "type": appt.appointment_type,
            "doctor_name": doctor_name,
            "status": appt.status
        })

    return jsonify({
        "user_id": user.id,
        "full_name": user.full_name,
        "email": user.email,
        "current_week": patient.current_week,
        "trimester": patient.trimester,
        "due_date": patient.due_date.strftime('%Y-%m-%d') if patient.due_date else None,
        "weight": patient.weight,
        "blood_pressure": patient.blood_pressure,
        "chat_history": chat_messages,
        "metrics": {
            "weight": latest_metrics.weight if latest_metrics else patient.weight,
            "blood_pressure": latest_metrics.blood_pressure if latest_metrics else patient.blood_pressure,
            "blood_sugar": latest_metrics.blood_sugar if latest_metrics else patient.sugar_levels,
            "last_updated": latest_metrics.date_recorded.strftime('%Y-%m-%d') if latest_metrics else "Not recorded"
        } if latest_metrics or patient else {},
        "appointments": formatted_appointments
    })

@app.route('/api/schedule_appointment', methods=['POST'])
@login_required
def schedule_appointment():
    # Get data from request
    data = request.json
    print(f"Received appointment data: {data}")
    print(f"Current user: {current_user.id} ({current_user.role})")
    
    # Validate required data
    if not data.get('patientId'):
        return jsonify({'success': False, 'error': 'Patient ID is required'})
    
    if not data.get('date') or not data.get('time'):
        return jsonify({'success': False, 'error': 'Date and time are required'})
    
    try:
        # Get mother profile from patient ID
        mother_profile = MotherProfile.query.get(data['patientId'])
        
        if not mother_profile:
            print(f"Patient ID {data['patientId']} not found")
            return jsonify({'success': False, 'error': 'Patient not found'})
        
        # The mother_id should be the user_id of the mother
        mother_id = mother_profile.user_id
        print(f"Using mother_id (user_id): {mother_id}")
        
        # IMPORTANT: doctor_id in Appointment refers to doctor_profiles.user_id, NOT doctor_profiles.id
        # So we need to use current_user.id directly, not the doctor profile ID
        doctor_id = current_user.id
        print(f"Using doctor_id (user_id): {doctor_id}")
        
        # Parse date and time
        try:
            appointment_date = datetime.strptime(data['date'], '%Y-%m-%d').date()
            appointment_time = datetime.strptime(data['time'], '%H:%M').time()
        except ValueError as e:
            print(f"Date/time parsing error: {e}")
            return jsonify({'success': False, 'error': 'Invalid date or time format'})
        
        print(f"Creating appointment: mother_id={mother_id}, doctor_id={doctor_id}, date={appointment_date}, time={appointment_time}")
        
        # Create appointment
    appointment = Appointment(
            mother_id=mother_id,
            doctor_id=doctor_id,
            date=appointment_date,
            time=appointment_time,
            appointment_type=data.get('type', 'Check-up'),
            status='scheduled'
        )
        
        # Add to database
    db.session.add(appointment)
        
        # Check if any changes are pending
        print(f"Pending changes: {db.session.is_modified(appointment)}")
        
        # Commit to database
        try:
    db.session.commit()
            print(f"Appointment created with ID: {appointment.id}")
            return jsonify({'success': True, 'appointment_id': appointment.id})
        except Exception as e:
            db.session.rollback()
            print(f"Database error: {e}")
            
            # Check for foreign key errors
            error_msg = str(e).lower()
            if "foreign key constraint" in error_msg:
                if "doctor_id" in error_msg:
                    print(f"Foreign key error with doctor_id={doctor_id}")
                    # Try to find what's wrong
                    doctor_exists = DoctorProfile.query.filter_by(user_id=doctor_id).first()
                    print(f"Doctor with user_id={doctor_id} exists: {doctor_exists is not None}")
                
                if "mother_id" in error_msg:
                    print(f"Foreign key error with mother_id={mother_id}")
                    # Try to find what's wrong
                    mother_exists = MotherProfile.query.filter_by(user_id=mother_id).first()
                    print(f"Mother with user_id={mother_id} exists: {mother_exists is not None}")
            
            return jsonify({'success': False, 'error': f'Database error: {str(e)}'})
            
    except Exception as e:
        print(f"Unexpected error: {e}")
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})

@app.route('/update_dashboards', methods=['POST'])
@login_required
def update_dashboards():
    data = request.get_json()
    
    # Here you would typically broadcast the data to the relevant dashboards
    # For example, you could use Flask-SocketIO to emit the data to connected clients
    # Emit to all connected clients (mothers, guardians, doctors)
    socketio.emit('update_health_metrics', data, broadcast=True)

    return jsonify({"success": True})

@app.route('/check_email', methods=['POST'])
def check_email():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided', 'exists': False}), 400
            
        email = data.get('email')
        if not email:
            return jsonify({'error': 'No email provided', 'exists': False}), 400
            
        existing_user = User.query.filter_by(email=email).first()
        return jsonify({'exists': existing_user is not None})
    except Exception as e:
        print(f"Error in check_email: {e}")
        return jsonify({'error': str(e), 'exists': False}), 500

@app.route('/test_email/<email>')
def test_email(email):
    # Find the user
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': 'User not found with that email'}), 404
    
    # Ensure user has a verification token
    if not user.verification_token:
        user.verification_token = secrets.token_urlsafe(32)
        db.session.commit()
    
    # Attempt to send the email
    try:
        result = send_verification_email(user)
        if result:
            return jsonify({'success': True, 'message': 'Verification email sent successfully'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send verification email'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/email_test', methods=['GET', 'POST'])
def email_test():
    if request.method == 'POST':
        email = request.form.get('email')
        user = User.query.filter_by(email=email).first()
        
        if not user:
            return render_template('email_test.html', error="User not found with that email", config=app.config)
        
        # Ensure user has a verification token
        if not user.verification_token:
            user.verification_token = secrets.token_urlsafe(32)
            db.session.commit()
        
        # Attempt to send the email
        result = send_verification_email(user)
        if result:
            return render_template('email_test.html', success=f"Verification email sent to {email}", config=app.config)
        else:
            return render_template('email_test.html', error=f"Failed to send email to {email}", config=app.config)
    
    return render_template('email_test.html', config=app.config)

@app.route('/force_verify/<email>')
def force_verify(email):
    user = User.query.filter_by(email=email).first()
    
    if not user:
        return jsonify({'error': 'User not found with that email'}), 404
    
    # Force verify the user
    user.is_verified = True
    db.session.commit()
    
    return jsonify({
        'success': True, 
        'message': f'User {email} has been verified. You can now log in.',
        'redirect': url_for('login')
    })

# Doctor info for mother's dashboard
@app.route('/api/mother/doctor_info')
@login_required
def get_mother_doctor_info():
    if current_user.role != 'mother':
        return jsonify({"success": False, "error": "Unauthorized access"}), 403
    
    # Fetch the mother's profile
    mother_profile = MotherProfile.query.filter_by(user_id=current_user.id).first()
    
    if not mother_profile or not mother_profile.doctor_id:
        return jsonify({"success": False, "message": "No doctor assigned yet"})
    
    # Get the doctor's profile and user information
    doctor_profile = DoctorProfile.query.get(mother_profile.doctor_id)
    if not doctor_profile:
        return jsonify({"success": False, "message": "Doctor not found"})
    
    doctor_user = User.query.get(doctor_profile.user_id)
    if not doctor_user:
        return jsonify({"success": False, "message": "Doctor user not found"})
    
    return jsonify({
        "success": True,
        "doctor_id": doctor_user.id,  # Return user_id for messaging
        "doctor_name": doctor_user.full_name,
        "doctor_email": doctor_user.email,
        "doctor_specialty": doctor_profile.specialty if hasattr(doctor_profile, 'specialty') else "General"
    })

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
