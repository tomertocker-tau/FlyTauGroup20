from flask import Flask, render_template, request, redirect, url_for, session
from utils import db_cur, check_if_admin, get_customer_history
from flask_session import Session
from datetime import date,timedelta, datetime
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
                return render_template("users_page.html")

            return render_template(
                "login.html",
                message="Incorrect login details"
            )
    return render_template("login.html")

@app.route('/signup', methods=['GET', 'POST'])
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
        return render_template("login.html")
    return  render_template("signup.html")



@app.route('/login_admin', methods=['GET', 'POST'])
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
                return render_template("managers_page.html")

            return render_template(
                "login_admin.html",
                message="Incorrect login details"
            )
    return render_template("login_admin.html")
@app.route('/', methods=['GET', 'POST'])
def homepage():
    if request.method == 'POST':
        SourceField = request.form.get('SourceField')
        DestinationField = request.form.get('DestinationField')
        TakeOffDate = request.form.get('TakeOffDate')
        PassengersAmount = request.form.get('PassengersAmount')
        return render_template("Users_Flight_Table.html")

    return render_template("homepage.html")

@app.route('/flights', methods=['GET', 'POST'])
def users_page():
    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        departure_date = request.form.get('departure_date')
        passengers = request.form.get('passengers')
        return render_template("Users_Flight_Table.html")

    return render_template("users_page.html")

@app.route("/flight-history", methods=['GET','POST'])
def filter_history():
    if 'email' not in session:
        return render_template("login.html")
    user_email = session.get("email")
    if request.method == 'POST':
        status = request.args.get("status")
        return render_template("users_page.html",orders=get_customer_history(user_email, status))

    return render_template("users_page.html",orders=get_customer_history(user_email))

@app.route('/manage_order', methods=['GET', 'POST'])
def manage_order():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        email = request.form.get('email')
        order = get_order(order_id,email)
        flight_time_str = order["TakeOffTime"]
        format_string = "%Y-%m-%d %H:%M:%S"
        flight_time = datetime.strptime(flight_time_str, format_string)
        current_time = datetime.now()
        time_diff = current_time - flight_time
        is_cancellable = (time_diff > timedelta(hours=36)) & (order["OrderStatus"] != "Cancelled")

        return render_template("booking_details.html", order=get_order(order_id, email), show_cancel_button=is_cancellable)

    return render_template("manage_order.html")


def get_order(order_id, email):
    return {"Order_ID": "0123", "ClassType" : "business", "NumSeats" : 5, "SourceField": "London", "DestinationField": "Paris", "TakeOffTime": "2000-10-1 14:20:00", "OrderPrice": "200$", "OrderStatus": "active"}


if __name__ == '__main__':
    app.run(debug=True)