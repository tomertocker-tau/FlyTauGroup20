from flask import Flask, render_template, request, redirect, url_for, session
from utils import db_cur, check_if_admin
from flask_session import Session
from datetime import date,timedelta
import secrets
import os
app = Flask(__name__)

app.config["SECRET_KEY"] = secrets.token_hex(32)

SESSION_DIR = os.path.join(os.path.dirname(__file__), "flask_session_data")
os.makedirs(SESSION_DIR, exist_ok=True)

app.config.update(
    SESSION_TYPE="filesystem",
    SESSION_FILE_DIR=SESSION_DIR,
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    SESSION_REFRESH_EACH_REQUEST=True,
)

Session(app)



@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        with db_cur() as cursor:
            cursor.execute(""""
            SELECT Customers.Email, Customers.UserPassword
            FROM Customers""")
            user = cursor.fetchone()
            if user and user["password"] == password:
                session.permanent = True
                session["email"] = user["email"]
                return redirect("/users_page")

            return render_template(
                "login.html",
                message="Incorrect login details"
            )
    return render_template("login.html")

@app.route('/signup')
def signup():
    if request.method == 'POST':
        First_name = request.form.get('First_name')
        Last_name = request.form.get('Last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        phones = request.form.getlist("phones")
        passport_num = request.form.get('passport_num')
        date_of_birth = request.form.get('date_of_birth')
        signup_date = str(date.today())
        with db_cur() as cursor:
            cursor.execute(""""
                   SELECT Customers.Email
                   FROM Customers""")
            user = cursor.fetchone()
            if user == email:
                return render_template(
                    "login.html",
                    message="You are already registered")
        if check_if_admin(email):
            return render_template(
                "signup.html",
                message="Admins are not allowed to order flights")
        return redirect("/login")
    return  render_template("signup.html")



@app.route('/login_admin')
def login_admin():
    if request.method == 'POST':
        id = request.form.get('ID')
        password = request.form.get('password')
        with db_cur() as cursor:
            cursor.execute(""""
            SELECT ManagerID, Managers.UserPassword
            FROM Managers""")
            user = cursor.fetchone()
            if user and user["password"] == password:
                session.permanent = True
                session["ID"] = user["ID"]
                return redirect("/managers_page")

            return render_template(
                "login_admin.html",
                message="Incorrect login details"
            )
    return render_template("login_admin.html")
@app.route('/')
def main():
    if request.method == 'POST':
        SourceField = request.form.get('SourceField')
        DestinationField = request.form.get('DestinationField')
        TakeOffDate = request.form.get('TakeOffDate')
        PassengersAmount = request.form.get('PassengersAmount')
        return redirect("/Users_Flight_Table.html")

    return render_template("homepage.html")

if __name__ == '__main__':
    app.run(debug=True)