from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import sqlite3
import smtplib, ssl
from email.message import EmailMessage
from flask_bcrypt import Bcrypt

app = Flask(__name__)

bcrypt = Bcrypt(app)

app.secret_key = b'secret_key'

conn = sqlite3.connect('user_data.db')
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY,
        email TEXT,
        password TEXT
    )
''')
conn.commit()
conn.close()

@app.route('/')
def home():    
    return render_template('home.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        
        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, hashed_password))
        conn.commit()
        conn.close()
        
        return "You registered successfully"
    
    return render_template('register.html')



@app.route('/login', methods=['POST'])
def login():
    email = request.form['email']
    password = request.form['password']
    
    conn = sqlite3.connect('user_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email,)) 
    user = cursor.fetchone()
    
    if user and bcrypt.check_password_hash(user[2], password): 
        response_data = {"message": "Welcome " + email.split("@")[0].strip(), "success": True}
    else:
        update_password_link = '<a href="' + url_for('update_password') + '"style="color: DarkCyan;">update password</a>'
        failure_message = "Login failed, " + update_password_link
        response_data = {"message": failure_message, "success": False}

    
    conn.close()
    return jsonify(response_data)

@app.route("/update_password", methods=['GET', 'POST'])
def update_password():
    if request.method == 'POST':
        email = request.form['email']
        new_password = request.form['password']

        conn = sqlite3.connect('user_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE email = ?", (email,))
        user = cursor.fetchone()

        if user:
            hashed_password = bcrypt.generate_password_hash(new_password).decode('utf-8')
            cursor.execute("UPDATE users SET password = ? WHERE email = ?", (hashed_password, email))
            conn.commit()
            conn.close()

            sender_email = "salahlisahil055@gmail.com"  #intermediary email
            sender_password = "app_password" # app password of the mail right above
            receiver_email = email

            subject = f"Password update for {receiver_email}"
            body = f"Dear {receiver_email.split('@')[0].strip()},<br><br>" \
                "This is to inform you that your password has just been changed. If this change was not executed by you, " \
                f"please <a href='http://127.0.0.1:5000/update_password'>change your password from here</a>.<br><br>" \
                "Additionally, we would like to express our gratitude for your interest in our services.<br><br>" \
                "Regards,<br>TechCtrl"

            email_message = EmailMessage()
            email_message["From"] = sender_email
            email_message["To"] = receiver_email
            email_message["Subject"] = subject
            email_message.add_alternative(body, subtype='html')

            context = ssl.create_default_context()

            try:
                with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
                    smtp.login(sender_email, sender_password)
                    smtp.send_message(email_message)
                    print("Email sent successfully")
            except Exception as e:
                print("Email not sent: ", e)

            return "Password updated successfully and email sent. Check your inbox"
        else:
            return "Email not found in the database. Please, <a href='/register'>register</a> first"

    return render_template("update_password.html")



@app.route("/service")
def service():
    return render_template("service.html")

@app.route("/contact", methods=["GET","POST"])
def contact():
    if request.method == "POST":
        full_name = request.form.get("full_name")
        user_email = request.form.get("user_email")
        message = request.form.get("message")
        subject = request.form.get("subject")
        
        send_email(full_name, user_email, subject, message)
        flash("Email sent successfully!", "success")
        return redirect(url_for("contact"))

    return render_template("contact.html")

def send_email(full_name, user_email, subject, message):
    email_sender = "email_1" # This is an intermediary email which sends an email to the mail 'you assign'
    password = "app_password"  # This is the app password for the intermediary email above.
    email_receiver = "email_2" #This is the email 'you assign' and you will use this email to reply back to customers

    subject = subject +" " f"(by {full_name} [{user_email}])"
    body =  message

    email = EmailMessage()
    email["From"] = email_sender
    email["To"] = email_receiver
    email["Subject"] = subject
    email.set_content(body)

    context = ssl.create_default_context()

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465, context=context) as smtp:
            smtp.login(email_sender, password) 
            smtp.sendmail(email_sender, email_receiver, email.as_string())
            print("Email sent successfully")
    except Exception as e:
        print("Email not sent: ", e)

@app.route("/about")
def about():
    return render_template("about.html")

@app.route("/team")
def team():
    return render_template("team.html")



if __name__ == '__main__':
    app.run(debug=True)