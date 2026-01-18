from flask import Flask, render_template, request, redirect, url_for, session
''''from utils import *'''''
from flask_session import Session
from datetime import date,timedelta, datetime
import secrets
import os
from dummies import *

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



@app.route('/login_new', methods=['GET', 'POST'])
def login_new():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        if check_login(email, password):
                session.permanent = True
                session["email"] = email
                return render_template("users_page.html")

        return render_template(
                "login_new.html",
                message="Incorrect login details"
            )
    return render_template("login_new.html")

@app.route('/signup_new', methods=['GET', 'POST'])
def signup_new():
    if request.method == 'POST':
        phone_count = request.form.get('phone_count', type=int)
        if phone_count and not request.form.getlist("phones"):
            return render_template(
                "signup_new.html",
                phone_count=phone_count)

        First_name = request.form.get('First_name')
        Last_name = request.form.get('Last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        phones = request.form.getlist("phones")
        passport_num = request.form.get('passport_num')
        date_of_birth = request.form.get('date_of_birth')
        signup_date = str(date.today())
        if customer_exists(email):
                return render_template(
                    "login_new.html",
                    message="You are already registered"
                )
        if check_if_admin(email):
            return render_template(
                "signup_new.html",
                message="Admins are not allowed to order flights")
        return render_template("login_new.html")
    return  render_template("signup_new.html")

@app.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    if request.method == 'POST':
        id = request.form.get('ID')
        password = request.form.get('password')
        if check_admin_login(id, password):
                session.permanent = True
                session["ID"]=id
                return render_template("managers_page.html")

        return render_template(
                "login_admin.html",
                message="Incorrect login details"
            )
    return render_template("login_admin.html")
@app.route('/', methods=['GET', 'POST'])
def homepagenew():
    if request.method == 'POST':
        SourceField = request.form.get('SourceField')
        DestinationField = request.form.get('DestinationField')
        TakeOffDate = request.form.get('TakeOffDate')
        PassengersAmount = request.form.get('PassengersAmount')
        return render_template("Users_Flight_Table.html")

    return render_template("homepagenew.html")

@app.route('/users_page', methods=['GET', 'POST'])
def flights():
    if request.method == 'GET':
        return render_template("users_page.html")

    if request.method == 'POST':
        origin = request.form.get('origin')
        destination = request.form.get('destination')
        departure_date = request.form.get('departure_date')
        passengers = request.form.get('passengers')

        return render_template(
            "Users_Flight_Table.html",
            origin=origin,
            destination=destination,
            departure_date=departure_date,
            passengers=passengers
        )

@app.route("/users_page", methods=['GET','POST'])
def filter_history():
    if 'email' not in session:
        return render_template("login_new.html")
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


if __name__ == '__main__':
    app.run(debug=True)