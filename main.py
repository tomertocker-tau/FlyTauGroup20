from flask import Flask, render_template, request, redirect, url_for, session
from utils import db_cur
from datetime import date
app = Flask(__name__)


#session??


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
        email = request.form.get('email') #need to add the function that makes sure its not a manager email
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
        return redirect("/users_page")
    return  render_template("signup.html")

#add to the utils the function that inserts a new user information into the customers table
'''how to add the phones list to the costumers phones table
phones = request.form.getlist("phones")

for phone in phones:
    phone = phone.strip()
    if not phone:
        continue

    cursor.execute(
        "INSERT INTO user_phones (user_id, phone) VALUES (%s, %s)",
        (user_id, phone)
    )
'''

@app.route('/login-admin')
def login_admin():
    if request.method == 'POST':
        ID = request.form.get('ID')
        password = request.form.get('password')
        with db_cur() as cursor:
            cursor.execute(""""
            SELECT ManagerID, Managers.UserPassword
            FROM Managers""")
            user = cursor.fetchone()
            if user and user["password"] == password:
                session["ID"] = user["ID"]
                return redirect("/managers_page")

            return render_template(
                "login-admin.html", #the comment is probably because we didn't create this html yet
                message="Incorrect login details"
            )
    return render_template("login_admin.html")
@app.route('/')
def main():
    return render_template("homepage.html")

if __name__ == '__main__':
    app.run(debug=True)