import os
from dotenv import load_dotenv
from flask import Flask,render_template, redirect,request, session,url_for, jsonify
from flask_session import Session
from functools import wraps
from werkzeug.security import check_password_hash, generate_password_hash
import sqlite3


app = Flask(__name__)

# load_dotenv()

# app.secret_key = os.environ.get('SECRET_KEY')



app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)



@app.after_request
def after_request(response):
    """Ensure responses aren't cached"""
    response.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    response.headers["Expires"] = 0
    response.headers["Pragma"] = "no-cache"
    return response


def login_required(f):
    """
    Decorate routes to require login.

    # http://flask.pocoo.org/docs/0.12/patterns/viewdecorators/
    # """

    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            return redirect("/login")
        return f(*args, **kwargs)
    return decorated_function



@app.route("/", methods=["POST", "GET"])
@login_required
def home():
    user_id = session["user_id"]

    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    user = cursor.execute("SELECT username FROM USERS WHERE id = ?", (user_id,)).fetchone()[0]
    connected_users = cursor.execute("SELECT DISTINCT sender FROM messages WHERE  receiver = ? UNION SELECT DISTINCT receiver FROM messages WHERE sender = ?",(user, user)).fetchall()


    connection.close()
  
    return render_template("home.html", user=user, connected_users=connected_users)



@app.route("/chat", methods=["POST", "GET"])
@login_required
def chat():
    user_id = session["user_id"]
    alert=""
    conversation_partner = session.get("conversation_partner", "")
    
    
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    user = cursor.execute("SELECT username FROM USERS WHERE id = ?", (user_id,)).fetchone()[0]
    all_user = cursor.execute("SELECT username FROM USERS").fetchall()

    connection.close()
  

    if request.method == "POST" and "conversation_partner" in request.form:
        conversation_partner = request.form.get("conversation_partner")
        session["conversation_partner"] = conversation_partner


    if request.method == "POST" and "send_message" in request.form:

        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        message = request.form.get("message")

        partner_count = cursor.execute("SELECT COUNT(*) FROM users WHERE username = ?", (conversation_partner,)).fetchone()[0]

        if partner_count == 0:
            alert ="invalid receiver !!"
        elif len(conversation_partner) < 1:
            alert = "Choose Reciever!!"
        elif not message or len(message) < 1:
            alert= "write Message!!"
        else:
            cursor.execute("INSERT INTO messages (receiver, message, sender) VALUES (?, ?, ?)", (conversation_partner, message, user))
            alert=""
            connection.commit()
            connection.close()
            return redirect(url_for('chat'))


    return render_template("chat.html", user=user, conversation_partner=conversation_partner, all_user=all_user,  alert=alert)
    


@app.route('/update_messages')
@login_required
def update_messages():
    user_id = session["user_id"]
    
    conversation_partner = session.get("conversation_partner")
    
    connection = sqlite3.connect("database.db")
    cursor = connection.cursor()

    user = cursor.execute("SELECT username FROM USERS WHERE id = ?", (user_id,)).fetchone()[0]
    messages = cursor.execute("SELECT * FROM messages WHERE (sender = ? AND receiver = ?) OR (sender = ? AND receiver = ?)", (user, conversation_partner,conversation_partner,user)).fetchall()
    
    connection.close()
    
    return jsonify(messages)


@app.route("/logout", methods=["POST", "GET"])
@login_required
def logout():

    session.clear()
    return redirect("/login")



@app.route("/sign-up", methods=["GET", "POST"])
def sign_up():
    alert = ""

    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        password2 = request.form.get('password2')

        
        connection = sqlite3.connect('database.db')
        cursor = connection.cursor()

       
        user_in_database = cursor.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()

        if user_in_database:
            alert = "User already exists"
        elif len(username) < 4:
            alert = "Username must be greater than 4 characters."
        elif len(password) < 7:
            alert = "Password must be greater than 6 characters."
        elif password != password2:
            alert = "Passwords don't match."
        else:
           
            hashed = generate_password_hash(password)


            cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed))
            connection.commit()
            connection.close()


            alert = "User successfully registered"

            return redirect("/login")
        
            

    return render_template("sign_up.html", alert=alert)




@app.route("/login", methods=["POST", "GET"])
def login():
    session.clear()
    alert = ""

    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")


        connection = sqlite3.connect("database.db")
        cursor = connection.cursor()

        user_in_database = cursor.execute("SELECT * FROM users WHERE username = ?", (username,) ).fetchone()
        
        connection.commit()
        connection.close()


        if user_in_database:
            if check_password_hash(user_in_database[2], password):
                session["user_id"] = user_in_database[0]
                return redirect("/")
            else:
                alert = "Incorrect password"
        else:
            alert = "User does not exist"


    return render_template("login.html",alert=alert)



# if __name__ == "__main__":
#     app.run(host="0.0.0.0", port=5000)

