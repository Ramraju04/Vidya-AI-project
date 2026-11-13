from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
import sqlite3
import random
import requests
import os

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "dev_secret_key")


# Initialize DB
def init_db():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password TEXT NOT NULL,
        role TEXT NOT NULL
    )''')
    
    # Add user_details table for additional profile information
    c.execute('''CREATE TABLE IF NOT EXISTS user_details (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        grade TEXT,
        school TEXT,
        interests TEXT,
        language TEXT,
        bio TEXT,
        FOREIGN KEY (user_id) REFERENCES users (id)
    )''')
    
    conn.commit()
    conn.close()
def create_demo_user():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()

    c.execute("SELECT * FROM users WHERE email=?", ("demo@vidyaai.com",))
    user = c.fetchone()

    if not user:
        print("Creating demo user...")

        c.execute("""
            INSERT INTO users (name, email, password, role)
            VALUES (?, ?, ?, ?)
        """, (
            "Demo User",
            "demo@vidyaai.com",
            "Demo@123",
            "Student"
        ))

        user_id = c.lastrowid

        c.execute("""
            INSERT INTO user_details
            (user_id, grade, school, interests, language, bio)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            user_id,
            "",
            "",
            "",
            "English",
            "Demo Account"
        ))

        conn.commit()
        print("Demo user created successfully!")

    else:
        print("Demo user already exists.")

    conn.close()
# def create_demo_user():
#     conn = sqlite3.connect("database.db")
#     c = conn.cursor()

#     c.execute("SELECT * FROM users WHERE email=?", ("demo@vidyaai.com",))
#     user = c.fetchone()

#     if not user:
#         c.execute("""
#             INSERT INTO users (name, email, password, role)
#             VALUES (?, ?, ?, ?)
#         """, (
#             "Demo User",
#             "demo@vidyaai.com",
#             "Demo@123",
#             "Student"
#         ))

#         user_id = c.lastrowid

#         c.execute("""
#             INSERT INTO user_details
#             (user_id, grade, school, interests, language, bio)
#             VALUES (?, ?, ?, ?, ?, ?)
#         """, (
#             user_id,
#             "",
#             "",
#             "",
#             "English",
#             "Demo Account"
#         ))

#         conn.commit()

#     conn.close()
init_db()
create_demo_user()


# Send OTP Email
# def send_otp(email):
#     otp = str(random.randint(100000, 999999))
#     context = ssl.create_default_context()
#     with smtplib.SMTP_SSL('smtp.gmail.com', 465, context=context) as server:
#         server.login(EMAIL_ADDRESS, EMAIL_PASSWORD)
#         server.sendmail(EMAIL_ADDRESS, email, f"Subject: Your One-Time Password (OTP) for VidyAI++ Access\n\nBody: Dear User,\nYour One-Time Password (OTP) for accessing VidyAI++ is: {otp}\n\n Please use this OTP to proceed with your authentication. For security reasons, do not share this code with anyone.\nIf you did not request this OTP, please ignore this email.\n\nThank you,\nThe VidyAI++ Team")
#     return otp

def send_otp(email):
    otp = str(random.randint(100000, 999999))

    api_key = os.getenv("BREVO_API_KEY")
    sender_email = os.getenv("BREVO_SENDER_EMAIL")

    if not api_key or not sender_email:
        raise RuntimeError("Brevo configuration missing.")

    url = "https://api.brevo.com/v3/smtp/email"

    headers = {
        "accept": "application/json",
        "api-key": api_key,
        "content-type": "application/json"
    }

    payload = {
        "sender": {
            "name": "VidyaAI Team",
            "email": sender_email
        },
        "to": [{"email": email}],
        "subject": "Your VidyaAI OTP",
        "textContent": f"Your OTP is {otp}. Please do not share it with anyone."
    }

    try:
        response = requests.post(
            url,
            headers=headers,
            json=payload,
            timeout=20
        )
        response.raise_for_status()
        return otp

    except requests.RequestException as e:
        print("Brevo error:", str(e))
        raise RuntimeError("Unable to send OTP. Please try again.")


@app.route('/')
def home():
    return redirect('/login')

@app.route('/profile')
def profile():
    # Assuming you have a user_id from session or authentication
    user_id = session.get('user_id')
    
    # Query the database for user details
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row  # This allows accessing columns by name
    c = conn.cursor()
    
    # Query user details
    c.execute('SELECT * FROM user_details WHERE user_id = ?', (user_id,))
    user_details = c.fetchone()
    
    # If no details exist yet, provide an empty dict with default values
    if not user_details:
        user_details = {
            'bio': '',
            'grade': '',
            'school': '',
            'interests': '',
            'language': ''
        }
    else:
        # Convert Row object to dict
        user_details = dict(user_details)
    
    conn.close()
    
    return render_template('profile.html', user_details=user_details)

@app.route('/relatedvideos')
def relatedvideos():
    return render_template('relatedvideos.html')


@app.route('/resetpassword')
def forgotpassword():
    return render_template('resetpassword.html')

@app.route('/mentors')
def mentors():
    if 'user' not in session:
        return redirect('/login')
    return render_template('mentors.html')

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']
        role = request.form['role']

        if password != confirm_password:
            flash("Passwords do not match.")
            return redirect('/signup')

        
        try:
            otp = send_otp(email)
        except RuntimeError as e:
            flash(str(e))
            return redirect('/signup')

        session['temp_user'] = {
            'name': name,
            'email': email,
            'password': password,
            'role': role
        }
        session['otp'] = otp
        return render_template('verify.html')

    return render_template('signup.html')

@app.route('/Home')
def Home():
    if 'user' not in session:
        return redirect('/login')
    return render_template('Home.html')

@app.route("/contactus", methods=["GET", "POST"])
def contactus():
    if 'user' not in session:
        return redirect('/login')

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        message = request.form.get("message", "").strip()

        if not name or not email or not message:
            return render_template(
                "contactus.html",
                success=False,
                error="Please fill in all fields."
            )

        try:
            import requests
            import os

            api_key = os.getenv("BREVO_API_KEY")
            sender_email = os.getenv("BREVO_SENDER_EMAIL")
            receiver_email = os.getenv("CONTACT_RECEIVER_EMAIL")

            if not api_key or not sender_email or not receiver_email:
                raise ValueError("Email configuration is missing.")

            response = requests.post(
                "https://api.brevo.com/v3/smtp/email",
                headers={
                    "accept": "application/json",
                    "api-key": api_key,
                    "content-type": "application/json"
                },
                json={
                    "sender": {
                        "name": "VidyaAI++",
                        "email": sender_email
                    },
                    "to": [
                        {"email": receiver_email}
                    ],
                    "replyTo": {
                        "email": email,
                        "name": name
                    },
                    "subject": f"New Contact Message from {name}",
                    "textContent": (
                        f"Name: {name}\n"
                        f"Email: {email}\n\n"
                        f"Message:\n{message}"
                    )
                },
                timeout=20
            )

            response.raise_for_status()

            return render_template(
                "contactus.html",
                success=True
            )

        except Exception as e:
            app.logger.exception("Contact email failed")
            return render_template(
                "contactus.html",
                success=False,
                error="Unable to send your message. Please try again."
            )

    return render_template("contactus.html", success=False)



@app.route('/verify', methods=['GET', 'POST'])
def verify():
    if request.method == 'POST':
        entered_otp = request.form['otp']
        if entered_otp == session.get('otp'):
            user = session.get('temp_user')
            conn = sqlite3.connect('database.db')
            c = conn.cursor()
            try:
                c.execute("INSERT INTO users (name, email, password, role) VALUES (?, ?, ?, ?)",
                          (user['name'], user['email'], user['password'], user['role']))
                user_id = c.lastrowid
                # Initialize empty user details
                c.execute("INSERT INTO user_details (user_id, grade, school, interests, language, bio) VALUES (?, ?, ?, ?, ?, ?)",
                          (user_id, '', '', '', 'English', ''))
                conn.commit()
                flash("Account created successfully!")
            except sqlite3.IntegrityError:
                flash("Email already exists.")
                return redirect('/signup')
            finally:
                conn.close()
                session.pop('temp_user', None)
                session.pop('otp', None)
            return redirect('/login')
        else:
            flash("Invalid OTP")
            return render_template('verify.html')
    return redirect('/signup')


@app.route('/aboutus')
def aboutus():
    if 'user' not in session:
        return redirect('/login')
    return render_template('aboutus.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        conn = sqlite3.connect('database.db')
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
        user = c.fetchone()
        conn.close()

        if user:
            session['user'] = user
            return redirect('/Home')
        else:
            flash("Invalid email or password")
            return redirect('/login')
    return render_template('login.html')

@app.route('/main')
def main_page():
    if 'user' in session:
        return redirect('/Home')
    else:
        return redirect('/login')



@app.route('/edit-profile')
def edit_profile():
    if 'user' not in session:
        return redirect('/login')
    
    user_id = session['user'][0]
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    c = conn.cursor()
    
    # Get user details
    c.execute("SELECT * FROM user_details WHERE user_id=?", (user_id,))
    user_details = c.fetchone()
    
    conn.close()
    
    return render_template('edit_profile.html', user_details=user_details)

@app.route('/update-profile', methods=['POST'])
def update_profile():
    if 'user' not in session:
        return redirect('/login')
    
    user_id = session['user'][0]
    name = request.form['name']
    grade = request.form['grade']
    school = request.form['school']
    interests = request.form['interests']
    language = request.form['language']
    bio = request.form['bio']
    
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    
    # Update user name
    c.execute("UPDATE users SET name=? WHERE id=?", (name, user_id))
    
    # Update user details
    c.execute("""
        UPDATE user_details 
        SET grade=?, school=?, interests=?, language=?, bio=? 
        WHERE user_id=?
    """, (grade, school, interests, language, bio, user_id))
    
    conn.commit()
    
    # Update session user information
    c.execute("SELECT * FROM users WHERE id=?", (user_id,))
    updated_user = c.fetchone()
    session['user'] = updated_user
    
    conn.close()
    
    flash("Profile updated successfully!")
    return redirect('/profile')



@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')



if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
