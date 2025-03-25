from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from flask_mysqldb import MySQL
from flask_sqlalchemy import SQLAlchemy
from authlib.integrations.flask_client import OAuth
from werkzeug.security import generate_password_hash, check_password_hash
import MySQLdb
import secrets

app = Flask(__name__)
app.secret_key = "your_secret_key"

# ---------------------------------------------------
# 1) Configure SQLAlchemy (ORM) and MySQL (raw SQL)
# ---------------------------------------------------
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:EddieOliver..1@localhost/linda_mama'
db = SQLAlchemy(app)

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
class User(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)  
    email = db.Column(db.String(120), unique=True, nullable=False)
    role = db.Column(db.String(20), nullable=False)  
    password_hash = db.Column(db.String(128))
    # New column for guardian accounts to store linked mother's email
    linked_mother = db.Column(db.String(120))  


class GuardianRequest(db.Model):
    __tablename__ = "guardian_requests"
    id = db.Column(db.Integer, primary_key=True)
    guardian_email = db.Column(db.String(120), nullable=False)
    mother_id = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(50), default="pending")
    guardian_name = db.Column(db.String(100), nullable=False)
    mother_email = db.Column(db.String(120), nullable=False)
    # New column to store the guardian's password hash from signup
    password_hash = db.Column(db.String(128), nullable=False)


# ---------------------------------------------------
# 4) Routes
# ---------------------------------------------------
@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':  
        full_name = request.form.get('full_name', '').strip()
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        role = request.form.get('role', '').strip()
        mother_email = request.form.get('mother_email', None)

        if not role:
            flash("Please select a role!", "danger")
            return redirect(url_for('signup'))
        if password != confirm_password:
            flash("Passwords do not match!", "danger")
            return redirect(url_for('signup'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT * FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        if existing_user:
            flash("Email already exists. Please use a different email or login.", "danger")
            cursor.close()
            return redirect(url_for('signup'))

        if role == "guardian":
            if not mother_email:
                flash("Please enter the mother's email.", "danger")
                cursor.close()
                return redirect(url_for("signup"))

            cursor.execute("SELECT id FROM users WHERE email = %s AND role = 'mother'", (mother_email,))
            mother = cursor.fetchone()
            if not mother:
                flash("No such user (mother) exists. Please enter a registered mother's email.", "danger")
                cursor.close()
                return redirect(url_for("signup"))

            mother_id = mother[0]
            guardian_email = email  
            guardian_name = full_name  
            status = "pending"

            # Insert into guardian_requests table along with the guardian's password hash
            cursor.execute("""
                INSERT INTO guardian_requests 
                    (guardian_email, mother_id, status, guardian_name, mother_email, password_hash)
                VALUES (%s, %s, %s, %s, %s, %s)
            """, (guardian_email, mother_id, status, guardian_name, mother_email, hashed_password))
            mysql.connection.commit()
            cursor.close()

            flash("Guardian request sent! Wait for approval.", "success")
            return redirect(url_for("login"))

        # Otherwise, sign up as mother/doctor
        cursor.execute("""
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
        """, (full_name, email, hashed_password, role))
        mysql.connection.commit()
        cursor.close()

        flash("Signup successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('signup.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'GET':
        return render_template('login.html')
    try:
        if request.content_type == "application/json":
            data = request.get_json()
            email = data.get('email')
            password = data.get('password')
        else:
            email = request.form.get('email')
            password = request.form.get('password')

        if not email or not password:
            return {"success": False, "message": "Email and password are required!"}, 400

        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id, full_name, password_hash, role FROM users WHERE email = %s", (email,))
        user = cursor.fetchone()
        cursor.close()

        if user and check_password_hash(user[2], password):
            session['user_id'] = user[0]
            session['full_name'] = user[1]
            session['role'] = user[3]
            session['email'] = email

            role_redirects = {
                "doctor": "/doctor_dashboard",
                "mother": "/mother_dashboard",
                "guardian": "/guardian_dashboard",
                "father": "/guardian_dashboard",
            }
            return {"success": True, "redirect_url": role_redirects.get(user[3], "/login")}

        return {"success": False, "message": "Invalid email or password!"}, 401

    except Exception as e:
        print("Login error:", e)
        return {"success": False, "message": f"An error occurred: {str(e)}"}, 500


@app.route('/mother_dashboard')
def mother_dashboard():
    if 'user_id' not in session or session['role'] != 'mother':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    mother_id = session['user_id']
    cursor = mysql.connection.cursor()
    cursor.execute("""
        SELECT id, guardian_email, guardian_name 
        FROM guardian_requests
        WHERE mother_id = %s AND status = 'pending'
    """, (mother_id,))
    guardian_requests = cursor.fetchall()
    cursor.close()

    return render_template('mother_dashboard.html', guardian_requests=guardian_requests)


@app.route("/google_login")
def google_login():
    email = session.get("temp_email")
    if email:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT id FROM users WHERE email = %s", (email,))
        existing_user = cursor.fetchone()
        cursor.close()
        prompt_value = "none" if existing_user else "consent"
    else:
        prompt_value = "consent"

    nonce = secrets.token_urlsafe(16)
    session["nonce"] = nonce
    return google.authorize_redirect(
        url_for("google_callback", _external=True),
        nonce=nonce,
        prompt=prompt_value
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

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT id, role FROM users WHERE email = %s", (email,))
    user = cursor.fetchone()

    if user:
        session["user_id"] = user[0]
        session["role"] = user[1]
        flash("Login successful!", "success")
        return redirect(url_for(f"{user[1]}_dashboard"))
    else:
        placeholder_password = generate_password_hash("google_user", method="pbkdf2:sha256")
        cursor.execute("""
            INSERT INTO users (full_name, email, password_hash, role)
            VALUES (%s, %s, %s, %s)
        """, (full_name, email, placeholder_password, "mother"))
        mysql.connection.commit()
        flash("Sign up successful! Please complete your profile.", "success")
        return redirect(url_for("mother_dashboard"))
    cursor.close()


@app.route('/doctor_dashboard')
def doctor_dashboard():
    if 'user_id' not in session or session.get('role') != 'doctor':
        return redirect(url_for('login'))
    return render_template('doctor_dashboard.html', user_name=session['full_name'])


@app.route('/guardian_dashboard')
def guardian_dashboard():
    if 'user_id' not in session or session['role'] != 'guardian':
        flash("Unauthorized access!", "danger")
        return redirect(url_for('login'))

    user_email = session.get("email")
    if not user_email:
        flash("No guardian email found in session!", "danger")
        return redirect(url_for('login'))

    cursor = mysql.connection.cursor()
    cursor.execute("SELECT linked_mother FROM users WHERE email = %s", (user_email,))
    result = cursor.fetchone()
    if not result:
        flash("No linked mother found!", "danger")
        cursor.close()
        return redirect(url_for('login'))

    mother_email = result[0]
    cursor.execute("SELECT trimester, week FROM pregnancy_data WHERE email = %s", (mother_email,))
    mother_data = cursor.fetchone()

    cursor.execute("SELECT date, time, type FROM appointments WHERE mother_email = %s", (mother_email,))
    appointments = cursor.fetchall()
    cursor.close()

    return render_template("guardian_dashboard.html", mother_data=mother_data, appointments=appointments)


@app.route('/approve_guardian/<int:request_id>', methods=['POST'])
def approve_guardian(request_id):
    try:
        request_entry = GuardianRequest.query.get(request_id)
        if not request_entry:
            return jsonify({"error": "Request not found"}), 404

        # Use the guardian's password from the guardian_requests table
        new_guardian = User(
            full_name=request_entry.guardian_name,
            email=request_entry.guardian_email,
            password_hash=request_entry.password_hash,
            role="guardian",
            linked_mother=request_entry.mother_email  # Set linked mother
        )
        db.session.add(new_guardian)
        db.session.delete(request_entry)
        db.session.commit()
        return jsonify({"success": True}), 200
    except Exception as e:
        print("Approve guardian error:", e)
        return jsonify({"error": str(e)}), 500


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


@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({"success": True})


if __name__ == "__main__":
    app.run(debug=True)
