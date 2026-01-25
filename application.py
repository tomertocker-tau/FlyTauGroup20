from flask import Flask, render_template, request, redirect, url_for, session, flash
from flask_session import Session
from datetime import date, timedelta, datetime
import secrets
import os



from utils import *
import calendar
from reports_utils import (
    get_average_occupancy_report,
    get_revenue_breakdown_report,
    get_employee_hours_report,
    get_cancellation_rate_report,
    get_plane_activity_report,
    get_summary_statistics
)
from sql_base import db_cur
application = Flask(__name__)

application.config["SECRET_KEY"] = secrets.token_hex(32)

SESSION_DIR = os.path.join(os.path.dirname(__file__), "flask_session_data")
os.makedirs(SESSION_DIR, exist_ok=True)

application.config.update(
    SESSION_TYPE="filesystem",
    SESSION_FILE_DIR=SESSION_DIR,
    SESSION_PERMANENT=True,
    PERMANENT_SESSION_LIFETIME=timedelta(minutes=30),
    SESSION_REFRESH_EACH_REQUEST=True,
)

Session(application)

@application.route("/setup_db")
def setup_db():
    try:
        with open('triviaDB.sql', 'r') as f:
            sql_script = f.read()
        with db_cur() as cursor:
            for result in cursor.execute(sql_script, multi=True):
                pass
        return "Success! Tables created from schema.sql."
    except Exception as e:
        return f"Error running SQL file: {str(e)}"

@application.route('/')
def homepagenew():
    """Homepage with search functionality"""
    session["on_search"] = False
    airports = get_all_fields()
    return render_template("homepagenew.html", airports=airports)

@application.route('/search_flights', methods=['GET', 'POST'])
def search_flights():
    """Handle flight search and show available flights"""
    airports = get_all_fields()
    if session.get("user_type", "user") == "customer":
        session["on_search"] = True
        return render_template("users_page.html", airports=airports)
    return render_template("homepagenew.html",airports=airports, on_search=True)


@application.route('/book_flight/<flight_id>/<class_type>')
def book_flight(flight_id, class_type):
    """Process flight selection and move to passenger details"""
    search_params = session.get('search_params')
    if not search_params:
        flash('Please search for flights first', 'error')
        return redirect(url_for('homepagenew'))

    flights = find_flights_by(flight_id=flight_id)
    flight = flights[0] if flights else {}

    passengers_count = search_params.get('passengers', 1)

    session['booking_data'] = {
        'flight_id': flight_id,
        'class_type': class_type,
        'passengers_count': passengers_count,
        'flight': flight
    }

    user_data = None
    if 'email' in session and session.get('user_type') == 'customer':
        user_email = session.get('email')
        user_data = get_assigned_customer(user_email)

    return render_template("booking_step1.html",
                           flight=flight,
                           class_type=class_type,
                           user_data=user_data,
                           passengers_count=passengers_count)



@application.route('/booking_step1_process', methods=['POST'])
def booking_step1_process():
    """Process passenger details form - with passport and birth date"""
    if 'booking_data' not in session:
        flash('Please start booking process again', 'error')
        return redirect(url_for('homepagenew'))

    session['booking_data'].update({
        'first_name': request.form.get('first_name'),
        'last_name': request.form.get('last_name'),
        'email': request.form.get('email'),
        'phone': request.form.get('phone').strip().split(','),
        'passport_number': request.form.get('passport_number'),
        'birth_date': request.form.get('birth_date')
    })

    email = request.form.get('email')
    is_registered = assigned_customer_exists(email)
    session['booking_data']['is_registered'] = is_registered
    if check_if_admin(email):
        flash("Admins not allowed to order", "error")
        return redirect(url_for('book_flight',
                                flight_id=session['booking_data']['flight_id'],
                                class_type=session['booking_data']['class_type']))

    return redirect(url_for('booking_step2'))


@application.route('/booking_step2')
def booking_step2():
    """Show seat selection page - only for selected class"""
    if 'booking_data' not in session:
        flash('Please start booking process again', 'error')
        return redirect(url_for('homepagenew'))

    booking_data = session['booking_data']
    flight_id = booking_data['flight_id']
    class_type = booking_data['class_type']
    passengers_count = booking_data['passengers_count']

    available_seats = get_available_seats(flight_id, class_type)
    total_price = get_price(num_seats=int(passengers_count),
                            flight_id=booking_data['flight_id'],
                            class_type=booking_data['class_type'])
    flights = find_flights_by(flight_id=flight_id)
    flight = flights[0] if flights else None

    return render_template("booking_step2_seats.html",
                           flight=flight,
                           available_seats=available_seats,
                           class_type=class_type,
                           passengers_count=passengers_count,
                           total_price=total_price,
                           booking_data=booking_data)


@application.route('/complete_booking', methods=['POST', 'GET'])
def complete_booking():
    """Complete the booking - save guest as guest, not customer"""
    if 'booking_data' not in session:
        flash('Booking session expired', 'error')
        return redirect(url_for('homepagenew'))

    try:
        session['booking_data'].update({'selected_seats': request.form.getlist('selected_seats')})
        booking_data = session['booking_data']
        email = booking_data['email']
        is_registered = booking_data['is_registered']

        if not is_registered:
            if not guest_exists(email):
                insert_customer_details(
                    First_name=booking_data['first_name'],
                    Last_name=booking_data['last_name'],
                    email=email,
                    passport_num=int(booking_data['passport_number']),
                    date_of_birth=datetime.strptime(booking_data['birth_date'], '%Y-%m-%d').date(),
                    is_signed_up=False
                )

            #  GuestsPhoneNumbers
            if booking_data.get('phone'):
                insert_phones(email, [ph for ph in booking_data['phone'] if is_phone_assigned(email, ph)], is_signed_up=False)

        flights = find_flights_by(flight_id=booking_data['flight_id'])
        plain_id = flights[0]['PlainID'] if flights else None

        order_id = insert_order(
            email=email,
            plain_id=plain_id,
            class_type=booking_data['class_type'],
            flight_id=booking_data['flight_id'],
            is_signed_up=is_registered  # GuestOrders אם False, CustomerOrders אם True
        )

        seat_data = []
        for seat in booking_data['selected_seats']:
            if '-' in seat:
                row, col = seat.split('-')
                seat_data.append((int(row), int(col)))

        if seat_data:
            # SelectedSeatsGuestOrders אם אורח, SelectedSeatsCustomerOrders אם רשום
            insert_order_seats(order_id, seat_data, is_signed_up=is_registered)
        total_price = get_price(num_seats=len(seat_data),
                                flight_id=booking_data['flight_id'],
                                class_type=booking_data['class_type'])
        #  session
        session.pop('booking_data', None)
        session.pop('search_params', None)

        flash(f'Booking successful! Order ID: {order_id}', 'success')
        return render_template("booking_confirmation.html",
                               order_id=order_id,
                               email=email,
                               total_price=total_price)

    except Exception as e:
        flash(f'Booking failed: {str(e)}', 'error')
        return redirect(url_for('booking_step2'))

@application.route('/login_new', methods=['GET', 'POST'])
def login_new():
    """Customer login"""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        if check_login(email, password):
            session.permanent = True
            session["email"] = email
            session["user_type"] = "customer"
            flash('Login successful!', 'success')
            return redirect(url_for('users_page'))
        flash("Incorrect login details", 'error')
        return render_template("login_new.html")

    return render_template("login_new.html")


@application.route('/signup_new', methods=['GET', 'POST'])
def signup_new():
    """Customer registration"""
    if request.method == 'POST':
        phone_count = request.form.get('phone_count', type=int)

        # Handle phone number input step
        if phone_count and not request.form.getlist("phones"):
            return render_template("signup_new.html", phone_count=phone_count)

        first_name = request.form.get('First_name')
        last_name = request.form.get('Last_name')
        email = request.form.get('email')
        password = request.form.get('password')
        phones = request.form.getlist("phones")
        passport_num = request.form.get('passport_num')
        date_of_birth = request.form.get('date_of_birth')
        signup_date = str(date.today())

        # Validation checks
        if assigned_customer_exists(email):
            flash('Email already registered', 'error')
            return render_template("login_new.html")

        if check_if_admin(email):
            flash("Admins are not allowed to order flights", 'error')
            return render_template("signup_new.html",
                                   message="Admins are not allowed to order flights")

        # Insert customer details
        try:
            insert_customer_details(
                First_name=first_name,
                Last_name=last_name,
                email=email,
                password=password,
                passport_num=int(passport_num) if passport_num else None,
                date_of_birth=datetime.strptime(date_of_birth, '%Y-%m-%d').date() if date_of_birth else None,
                signup_date=datetime.strptime(signup_date, '%Y-%m-%d').date(),
                is_signed_up=True
            )

            # Insert phone numbers
            if phones:
                insert_phones(email, phones, is_signed_up=True)

            flash('Registration successful! Please login.', 'success')
            return render_template("login_new.html")

        except Exception as e:
            flash(f"Registration failed: {str(e)}")
            return render_template("signup_new.html")

    return render_template("signup_new.html")


@application.route('/login_admin', methods=['GET', 'POST'])
def login_admin():
    """Manager/Admin login"""
    if request.method == 'POST':
        manager_id = request.form.get('ID')
        password = request.form.get('password')

        if check_admin_login(manager_id, password):
            session.permanent = True
            session["ID"] = manager_id
            session["user_type"] = "manager"
            flash('Login successful!', 'success')
            return redirect(url_for('managers_page'))
        flash('Incorrect login details', 'error')
        return render_template("login_admin.html")

    return render_template("login_admin.html")


@application.route('/users_page')
def users_page():
    """Customer dashboard/main page"""
    if 'email' not in session or session.get('user_type') != 'customer':
        flash('Please login to access this page', 'error')
        return redirect(url_for('login_new'))
    if 'temp_email' in session:
        session.pop('temp_email')
    # Get customer orders for display
    user_email = session.get("email")
    orders = get_customer_history(user_email)
    for i in range(len(orders)):
        orders[i]['cancellable'] = (orders[i]['TakeOffTime'] - datetime.now()) > timedelta(hours=36)
    airports = get_all_fields()

    return render_template("users_page.html", orders=orders, airports=airports)

@application.route('/managers_page')
def managers_page():
    """Manager dashboard"""
    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Please login as manager to access this page', 'error')
        return redirect(url_for('login_admin'))

    return render_template("managers_page.html")


@application.route('/managers_reports_page')
def managers_reports_page():
    """Manager statistics and reports page with charts"""
    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Please login as manager to access this page', 'error')
        return redirect(url_for('login_admin'))

    try:
        # Get all report data
        summary = get_summary_statistics()
        occupancy = get_average_occupancy_report()
        revenue_data = get_revenue_breakdown_report()
        employee_hours = get_employee_hours_report()
        cancellation_data = get_cancellation_rate_report()
        plane_activity = get_plane_activity_report()

        return render_template(
            "managers_reports_page.html",
            summary=summary,
            occupancy=occupancy,
            revenue_data=revenue_data,
            employee_hours=employee_hours,
            cancellation_data=cancellation_data,
            plane_activity=plane_activity
        )

    except Exception as e:
        flash(f'Error loading reports: {str(e)}', 'error')
        return redirect(url_for('managers_page'))


@application.route('/flights', methods=['GET', 'POST'])
def flights():
    """Flight search from users page"""
    if request.method == 'POST':
        origin = request.form.get('source')
        destination = request.form.get('destination')
        departure_date = request.form.get('takeoff_date')
        passengers = request.form.get('passengers')

        if origin and destination and origin == destination:
            flash("Source and Destination cannot be the same field.", "error")
            if session.get("on_search"):
                return redirect(url_for('search_flights'))
            return redirect(url_for('homepagenew'))

        # Store search parameters
        session['search_params'] = {
            'source': origin,
            'destination': destination,
            'date': departure_date,
            'passengers': passengers
        }
        take_off_time = datetime.strptime(departure_date, '%Y-%m-%d') if departure_date else None

        # Get flights
        try:
            flights = find_flights_by(
                source_field=origin,
                destination_field=destination,
                after_time=take_off_time - timedelta(minutes=1) if take_off_time else None,
                num_seats= int(passengers),
                status="Active"
            )
        except Exception as e: # if no route exists in Routes Table
            flights = []

        return render_template("flight_search_results.html",
                               flights=flights,
                               airports=get_all_fields(),
                               search_params=session.get('search_params'))

    return render_template("users_page.html" if session.get('user_type') == 'customer' else "homepagenew.html")


@application.route("/customer_history", methods=['POST', 'GET'])
def customer_history():
    """View customer flight history"""
    if 'email' not in session:
        flash('Please login to view history', 'error')
        return redirect(url_for('login_new'))
    if 'temp_email' in session:
        session.pop('temp_email')
    user_email = session.get("email")
    status = request.form.get("status")

    orders = get_customer_history(user_email, status)
    for i in range(len(orders)):
        orders[i]['cancellable'] = (orders[i]['TakeOffTime'] - datetime.now()) > timedelta(hours=36)

    return render_template("users_page.html", orders=orders, by_status=status)


@application.route('/cancel_order', methods=['GET', 'POST'])
def cancel_order():
    if request.method == 'POST': 
        try:
            order_id = request.form.get('order_id')
            user_type = session.get('user_type', 'guest')
            if session.get("temp_email"):
                email = session['temp_email']
            else:
                email = session['email']
            assert user_type in ['guest', 'customer'], "Admins not allowed to cancel orders"
            assert assigned_customer_exists(email) or guest_exists(email), f"No Customer {email} exists"
            delete_order(order_id, is_signed_up=user_type == 'customer')
            flash('Order cancelled successfully', 'success')
        except Exception as e:
            flash(f'Error cancelling order: {str(e)}', 'error')

    return redirect(url_for('homepagenew'))


@application.route('/cancel_confirmation', methods=['POST', 'GET'])
def cancel_confirmation():
    if 'temp_email' in session:
        user_email = session.get('temp_email')
    elif 'email' in session:
        user_email = session.get('email')
    else:
        flash('Please login to access this page', 'error')
        return redirect(url_for('login_new'))
    order_id = request.form.get('order_id')
    order = get_order(order_id, user_email)

    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('homepagenew'))

    return render_template("cancel_confirmation.html", order=order)


@application.route('/flight_board')
def flight_board():
    """Display flight board page"""
    # Get all current flights
    flights = find_flights_by()
    return render_template("flight_board.html", flights=flights)


@application.route('/manage_order', methods=['GET', 'POST'])
def manage_order():
    """Manage order - find and display booking details"""
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        email = request.form.get('email')

        if not order_id or not email:
            return render_template("manage_order.html",
                                   message="Please fill in both Order ID and Email")

        order = get_order(order_id, email)

        if order:
            session['temp_email'] = email
            session['temp_order_id'] = order_id
            return redirect(url_for('booking_details', order_id=order_id))

        return render_template("manage_order.html",
                               message="Order not found. Please check your Order ID and Email.")

    return render_template("manage_order.html")



@application.route('/booking_details/<order_id>')
def booking_details(order_id):
    if 'temp_email' in session:
        user_email = session.get('temp_email')
    elif 'email' in session:
        user_email = session.get('email')
    else:
        flash('Please login or use order lookup', 'error')
        return redirect(url_for('manage_order'))

    order = get_order(order_id, user_email)

    if not order:
        flash('Booking not found', 'error')
        return redirect(url_for('manage_order'))

    flight_time_str = order["TakeOffTime"]

    if isinstance(flight_time_str, datetime):
        flight_time = flight_time_str
    else:
        format_string = "%Y-%m-%d %H:%M:%S"
        flight_time = datetime.strptime(flight_time_str, format_string)

    current_time = datetime.now()
    time_diff = flight_time - current_time
    is_cancellable = (time_diff > timedelta(hours=36)) and (
            order["OrderStatus"] not in ["System_Cancelled", "Customer_Cancelled"])

    return render_template("booking_details.html",
                           order=order,
                           show_cancel_button=is_cancellable)
@application.route('/layout')
def layout():
    """Layout/template page"""
    return render_template("layout.html")


@application.route('/add_flight_step1', methods=['GET', 'POST'])
def add_flight_step1():
    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Manager access required', 'error')
        return redirect(url_for('login_admin'))
    airports = get_all_fields()
    if request.method == 'POST':
        source_field = request.form.get('source_field')
        destination_field = request.form.get('destination_field')
        takeoff_date = request.form.get('takeoff_date')
        takeoff_time = request.form.get('takeoff_time')
        takeoff_datetime = datetime.strptime(f"{takeoff_date} {takeoff_time}", '%Y-%m-%d %H:%M')
        found_error = False
        if datetime.strptime(takeoff_date, '%Y-%m-%d') <= datetime.today():
            flash('Can only Schedule Flight for Future', 'error')
            found_error = True
        flight_category = get_flight_category(source_field, destination_field)
        flight_duration = select("Routes", ["Routes.FlightDuration"],
                                 where=f"Routes.SourceField='{source_field}' AND "
                                       f"Routes.DestinationField='{destination_field}'")
        if len(flight_duration) == 0:
            flash(f"No route from {source_field} to {destination_field}", 'error')
            found_error = True
        else:
            flight_duration = flight_duration[0]["FlightDuration"]
            landing_datetime = takeoff_datetime + flight_duration

            if destination_field and source_field and destination_field == source_field:
                flash("Cannot plan a flight from field to itself", 'error')
                found_error = True
            elif not flight_category:
                flash('Route does not exist', 'error')
                found_error = True
            else:
                available_plains = find_available_plains(takeoff_datetime, landing_datetime, source_field, destination_field, flight_category=="Long")
                available_attendants = get_available_attendants(takeoff_datetime, landing_datetime, source_field, destination_field, flight_category=="Long")
                available_pilots = get_available_pilots(takeoff_datetime, landing_datetime, source_field, destination_field, flight_category=="Long")
                if len(available_plains) == 0:
                    flash("No plain available", "error")
                    found_error = True
                if flight_category == "Long" or all(pl["Size"]=="Large" for pl in available_plains):
                    if len(available_attendants) <= 5:
                        flash("Not enough attendants available", "error")
                        found_error = True
                    if len(available_pilots) <= 2:
                        flash("Not enough pilots available", "error")
                        found_error = True
                elif flight_category == "Short":
                    if len(available_attendants) <= 2:
                        flash("Not enough attendants available", "error")
                        found_error = True
                    if len(available_pilots) <= 1:
                        flash("Not enough pilots available", "error")
                        found_error = True

        if found_error:
            return render_template("add_flight_step1.html", airports=airports)

        session['flight_data'] = {
            'source_field': source_field,
            'destination_field': destination_field,
            'takeoff_date': takeoff_date,
            'takeoff_time': takeoff_time,
            'takeoff_datetime': f"{takeoff_date} {takeoff_time}",
            'flight_category': flight_category,
            'is_long_flight': flight_category == 'Long'
        }

        return redirect(url_for('add_flight_step2'))
    return render_template("add_flight_step1.html", airports=airports)


@application.route('/add_flight_step2', methods=['GET', 'POST'])
def add_flight_step2():
    if 'ID' not in session or session.get('user_type') != 'manager':
        return redirect(url_for('login_admin'))

    if 'flight_data' not in session:
        flash('Please start from step 1', 'error')
        return redirect(url_for('add_flight_step1'))

    if request.method == 'POST':
        selected_plane = request.form.get('plane_id')
        session['flight_data']['selected_plane'] = selected_plane
        session['flight_data']['plain_size'] = select("Plains", ["Plains.Size"],
                                                      where=f"Plains.PlainID={selected_plane}")[0]["Size"]
        return redirect(url_for('add_flight_step3'))

    takeoff_datetime = datetime.strptime(session['flight_data']['takeoff_datetime'], '%Y-%m-%d %H:%M')
    flight_duration = select("Routes", ["Routes.FlightDuration"],
                             where=f"Routes.SourceField='{session['flight_data']['source_field']}' AND "
                                   f"Routes.DestinationField='{session['flight_data']['destination_field']}'")[0]["FlightDuration"]
    landing_datetime = takeoff_datetime + flight_duration
    available_planes = find_available_plains(
        take_off_time=takeoff_datetime,
        landing_time=landing_datetime,
        source_field=session['flight_data']['source_field'],
        destination_field=session['flight_data']['destination_field'],
        is_long_flight=session['flight_data']['is_long_flight']
    )
    if not available_planes:
        flash('No available planes for this route and time', 'error')
        return redirect(url_for('add_flight_step1'))

    return render_template("add_flight_step2.html",
                           planes=available_planes,
                           flight_data=session['flight_data'])


@application.route('/add_flight_step3', methods=['GET', 'POST'])
def add_flight_step3():
    if 'ID' not in session or session.get('user_type') != 'manager':
        return redirect(url_for('login_admin'))

    if 'flight_data' not in session:
        return redirect(url_for('add_flight_step1'))

    if request.method == 'POST':
        pricing = {}
        for key, value in request.form.items():
            if key.startswith('price_') and value:
                class_name = key.replace('price_', '')
                pricing[class_name] = float(value)

        session['flight_data'].update({
            'selected_pilots': request.form.getlist('pilots'),
            'selected_attendants': request.form.getlist('attendants'),
            'pricing': pricing
        })
        found_error = False
        if session["flight_data"]["plain_size"] == "Large":
            if len(session["flight_data"]["selected_attendants"]) <= 5:
                flash("Need 6 attendants", "error")
                found_error = True
            if len(session["flight_data"]["selected_pilots"]) <= 2:
                flash("Need 3 pilots", "error")
                found_error = True
        else:
            if len(session["flight_data"]["selected_attendants"]) <= 2:
                flash("Need 3 attendants", "error")
                found_error = True
            if len(session["flight_data"]["selected_pilots"]) <= 1:
                flash(f"Need 2 pilots", "error")
                found_error = True
        if not found_error:
            return redirect(url_for('add_flight_step4'))

    takeoff_datetime = datetime.strptime(session['flight_data']['takeoff_datetime'], '%Y-%m-%d %H:%M')
    landing_datetime = takeoff_datetime + timedelta(hours=8)
    source_field = session['flight_data']['source_field']
    destination_field = session['flight_data']['destination_field']

    is_long_flight = session['flight_data']['is_long_flight']

    available_pilots = get_available_pilots(takeoff_datetime, landing_datetime, source_field, destination_field, is_long_flight)
    available_attendants = get_available_attendants(takeoff_datetime, landing_datetime, source_field, destination_field, is_long_flight)
    found_error = False
    if is_long_flight or session["flight_data"]["plain_size"] == "Large":
        if len(available_attendants) <= 5:
            flash("Not enough attendants available", "error")
            found_error = True
        if len(available_pilots) <= 2:
            flash("Not enough pilots available", "error")
            found_error = True
    else:
        if len(available_attendants) <= 2:
            flash("Not enough attendants available", "error")
            found_error = True
        if len(available_pilots) <= 1:
            flash("Not enough pilots available", "error")
            found_error = True
    if found_error:
        flash('Please get a smaller plain', 'error')
        return redirect(url_for('add_flight_step2'))
    selected_plane_id = session['flight_data'].get('selected_plane')
    classes = []
    if selected_plane_id:
        classes = [{'ClassName': 'Regular'}, {'ClassName': 'Business'}]

    plane_size = session["flight_data"]["plain_size"]
    required_pilots = 3 if plane_size == 'Large' else 2
    required_attendants = 6 if plane_size == 'Large' else 3

    is_small_plane = plane_size == 'Small'
    if is_small_plane:
        classes = [c for c in classes if c['ClassName'] != 'Business']

    return render_template("add_flight_step3.html",
                           pilots=available_pilots,
                           attendants=available_attendants,
                           classes=classes,
                           required_pilots=required_pilots,
                           required_attendants=required_attendants,
                           flight_data=session['flight_data'])


@application.route('/add_flight_step4', methods=['GET', 'POST'])
def add_flight_step4():
    if 'ID' not in session or session.get('user_type') != 'manager':
        return redirect(url_for('login_admin'))

    if 'flight_data' not in session:
        return redirect(url_for('add_flight_step1'))

    flight_data = session['flight_data']

    takeoff_datetime = datetime.strptime(flight_data['takeoff_datetime'], '%Y-%m-%d %H:%M')
    landing_datetime = takeoff_datetime + timedelta(hours=8)

    all_available_planes = find_available_plains(
        take_off_time=takeoff_datetime,
        landing_time=landing_datetime,
        source_field=flight_data['source_field'],
        destination_field=flight_data['destination_field'],
        is_long_flight=flight_data['is_long_flight']
    )

    selected_plane = None
    target_id = str(flight_data['selected_plane'])

    if all_available_planes:
        for plane in all_available_planes:
            if str(plane['PlainID']) == target_id:
                selected_plane = plane
                break

    available_pilots = get_available_pilots(
        takeoff_datetime,
        landing_datetime,
        flight_data['source_field'],
        flight_data['destination_field'],
        flight_data['is_long_flight']
    )

    available_attendants = get_available_attendants(
        takeoff_datetime,
        landing_datetime,
        flight_data['source_field'],
        flight_data['destination_field'],
        flight_data['is_long_flight']
    )

    selected_pilot_ids = flight_data.get('selected_pilots', [])
    selected_pilots = [p for p in available_pilots if str(p['PilotID']) in selected_pilot_ids]

    selected_attendant_ids = flight_data.get('selected_attendants', [])
    selected_attendants = [a for a in available_attendants if str(a['AttendantID']) in selected_attendant_ids]

    if request.method == 'POST':
        try:

            attendant_ids = flight_data.get('selected_attendants') or []
            pilot_ids = flight_data.get('selected_pilots') or []

            if not attendant_ids or not pilot_ids:
                missing = []
                if not pilot_ids:
                    missing.append("pilots")
                if not attendant_ids:
                    missing.append("attendants")

                flash(f"Cannot add flight without {' and '.join(missing)}.", "error")
                return redirect(url_for('add_flight_step4'))

            flight_id = insert_flight(
                plain_id=flight_data['selected_plane'],
                take_off_time=takeoff_datetime,
                source_field=flight_data['source_field'],
                destination_field=flight_data['destination_field']
            )

            pricing = flight_data.get('pricing')
            if pricing:
                plain_id = flight_data['selected_plane']
                insert_flight_prices(flight_id, plain_id, list(pricing.items()))

            insert_working_attendants(flight_id, attendant_ids)

            insert_working_pilots(flight_id, pilot_ids)

            session.pop('flight_data', None)
            flash('Flight added successfully!', 'success')
            return redirect(url_for('manager_flight_table'))

        except Exception as e:
            flash(f'Error adding flight: {str(e)}', 'error')

    return render_template("add_flight_step4.html",
                           flight_data=flight_data,
                           selected_plane=selected_plane,
                           selected_pilots=selected_pilots,
                           selected_attendants=selected_attendants,
                           pricing=flight_data.get('pricing', {}),
                           source_field=flight_data['source_field'],
                           destination_field=flight_data['destination_field'],
                           takeoff_date=flight_data['takeoff_date'],
                           takeoff_time=flight_data['takeoff_time'],
                           flight_category=flight_data['flight_category'])

@application.route('/manager_flight_table', methods=['GET', 'POST'])
def manager_flight_table():

    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Manager access required', 'error')
        return redirect(url_for('login_admin'))

    filters = {}
    if request.method == 'POST':
        filters['source_field'] = request.form.get('source_filter')
        filters['destination_field'] = request.form.get('destination_filter')
        filters['flight_id'] = request.form.get('flight_number')
        filters['status'] = request.form.get('status_filter')
        html_month_input = request.form.get('month_filter')
        if html_month_input:
            # 1. Parse the input string to get year and month integers
            year_month_obj = datetime.strptime(html_month_input, "%Y-%m")
            year = year_month_obj.year
            month = year_month_obj.month

            # 2. Determine the number of days in the specific month and year
            # calendar.monthrange returns a tuple: (weekday of first day, number of days in month)
            num_days = calendar.monthrange(year if month > 1 else year - 1, month-1 if month > 1 else 12)[1]

            # 3. Create the start and end datetime objects
            filters["before_time"] = datetime(year if month < 12 else year + 1, month+1 if month < 12 else 1, 1, 0, 0, 0)
            filters["after_time"] = datetime(year if month > 1 else year - 1, month-1 if month > 1 else 12, num_days, 23, 59, 59)
    else:
        html_month_input = None

    flights = find_flights_by(**filters)
    sources = get_all_fields()
    destinations = [
        r["DestinationField"]
        for r in select(
            "Routes",
            ["DestinationField"],
            group_by=["DestinationField"]
        )
    ]

    for flight in flights:
        flight_time = flight['TakeOffTime']
        if isinstance(flight_time, str):
            flight_time = datetime.strptime(flight_time, '%Y-%m-%d %H:%M:%S')

        current_time = datetime.now()
        time_diff = flight_time - current_time

        flight['can_cancel'] = (
                time_diff > timedelta(hours=72) and
                flight['FlightStatus'] != 'Deleted'
        )
    return render_template("manager_flight_table.html", flights=flights, sources=sources,
    destinations=destinations,
    source_filter=filters.get('source_field'),
    destination_filter=filters.get('destination_field'),
                           status_filter=filters.get('status'),
                           flight_number_filter=filters.get('flight_id'),
                           month_filter=html_month_input)


@application.route('/delete_flight/<flight_id>')
def delete_flight_route(flight_id):
    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Manager access required', 'error')
        return redirect(url_for('login_admin'))

    flights = find_flights_by(flight_id=flight_id)
    if not flights:
        flash('Flight not found', 'error')
        return redirect(url_for('manager_flight_table'))

    flight = flights[0]

    flight_time = flight['TakeOffTime']
    if isinstance(flight_time, str):
        flight_time = datetime.strptime(flight_time, '%Y-%m-%d %H:%M:%S')

    current_time = datetime.now()
    time_diff = flight_time - current_time

    if time_diff <= timedelta(hours=72):
        flash('Cannot cancel flight within 72 hours of departure', 'error')
        return redirect(url_for('manager_flight_table'))

    if flight.get('IsDeleted', 0) == 1:
        flash('Flight is already cancelled', 'error')
        return redirect(url_for('manager_flight_table'))

    return redirect(url_for('cancel_flight_confirmation', flight_id=flight_id))


@application.route('/cancel_flight_confirmation/<flight_id>')
def cancel_flight_confirmation(flight_id):
    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Manager access required', 'error')
        return redirect(url_for('login_admin'))

    flights = find_flights_by(flight_id=flight_id)
    if not flights:
        flash('Flight not found', 'error')
        return redirect(url_for('manager_flight_table'))

    flight = flights[0]
    return render_template("cancel_flight_confirmation.html", flight=flight)


@application.route('/confirm_cancel_flight/<flight_id>', methods=['POST'])
def confirm_cancel_flight(flight_id):
    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Manager access required', 'error')
        return redirect(url_for('login_admin'))

    try:
        delete_flight(flight_id)
        flash('Flight cancelled successfully', 'success')
    except Exception as e:
        flash(f'Error cancelling flight: {str(e)}', 'error')

    return redirect(url_for('manager_flight_table'))


@application.route('/add_attendant', methods=['GET', 'POST'])
def add_attendant():
    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Manager access required', 'error')
        return redirect(url_for('login_admin'))

    if request.method == 'POST':
        try:
            attendant_id = request.form.get('attendant_id')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone')
            city = request.form.get('city')
            street = request.form.get('street')
            home_number = request.form.get('home_number', type=int)
            job_start_day = request.form.get('job_start_day')
            qualified_long = 1 if request.form.get('qualified_long') == 'yes' else 0

            job_start_date = datetime.strptime(job_start_day, '%Y-%m-%d').date()

            insert_attendant(
                attendant_id=attendant_id,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                city=city,
                street=street,
                home_number=home_number,
                job_start_day=job_start_date,
                qualified4long_flights=qualified_long
            )

            flash('Flight attendant added successfully', 'success')
            return redirect(url_for('managers_page'))

        except Exception as e:
            flash(f'Error adding attendant: {str(e)}', 'error')

    return render_template("add_attendant.html")


@application.route('/add_pilot', methods=['GET', 'POST'])
def add_pilot():
    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Manager access required', 'error')
        return redirect(url_for('login_admin'))

    if request.method == 'POST':
        try:
            pilot_id = request.form.get('pilot_id')
            first_name = request.form.get('first_name')
            last_name = request.form.get('last_name')
            phone = request.form.get('phone')
            city = request.form.get('city')
            street = request.form.get('street')
            home_number = request.form.get('home_number', type=int)
            job_start_day = request.form.get('job_start_day')
            qualified_long = 1 if request.form.get('qualified_long') == 'yes' else 0

            job_start_date = datetime.strptime(job_start_day, '%Y-%m-%d').date()

            insert_pilot(
                pilot_id=pilot_id,
                first_name=first_name,
                last_name=last_name,
                phone=phone,
                city=city,
                street=street,
                home_number=home_number,
                job_start_day=job_start_date,
                qualified4long_flights=qualified_long
            )

            flash('Pilot added successfully', 'success')
            return redirect(url_for('managers_page'))

        except Exception as e:
            flash(f'Error adding pilot: {str(e)}', 'error')

    return render_template("add_pilot.html")


@application.route('/add_plane', methods=['GET', 'POST'])
def add_plane():
    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Manager access required', 'error')
        return redirect(url_for('login_admin'))

    if request.method == 'POST':
        try:
            plain_id = request.form.get('plane_id')
            manufacturer = request.form.get('manufacturer')
            classes = []
            for cls in ["regular", "business"]:
                rows = request.form.get(f"{cls}_class_rows")
                cols = request.form.get(f"{cls}_class_columns")
                if rows and cols and int(rows) > 0 and int(cols) > 0:
                    classes.append((cls.capitalize(), rows, cols))
            size = "Large" if len(classes) == 2 else "Small"
            purchase_date = request.form.get('purchase_date')

            purchase_date_obj = datetime.strptime(purchase_date, '%Y-%m-%d').date()

            insert_plain(
                plain_id=plain_id,
                manufacturer=manufacturer,
                size=size,
                purchase_date=purchase_date_obj
            )

            insert_classes(plain_id, classes)

            flash('Plane purchased successfully', 'success')
            return redirect(url_for('managers_page'))

        except Exception as e:
            flash(f'Error adding plane: {str(e)}', 'error')

    return render_template("add_plane.html")


@application.route('/logout')
def logout():
    """Logout user"""
    user_type = session.get('user_type', 'user')
    session.clear()
    flash(f'{user_type.title()} logged out successfully', 'info')
    return redirect(url_for('homepagenew'))


# Context processor to make session available in templates
@application.context_processor
def inject_user():
    return dict(
        user_email=session.get('email'),
        user_type=session.get('user_type'),
        manager_id=session.get('ID'),
        current_date=datetime.now().strftime('%Y-%m-%d'),
        current_time=datetime.now().strftime('%H:%M')
    )


# Template filters
@application.template_filter('datetime')
def datetime_filter(value, format='%Y-%m-%d %H:%M'):
    """Custom datetime filter for templates"""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except:
            return value
    return value.strftime(format) if value else ''


# Error handlers
@application.errorhandler(404)
def page_not_found(e):
    return render_template('homepagenew.html'), 404


@application.errorhandler(500)
def internal_server_error(e):
    flash('An internal error occurred. Please try again.', 'error')
    return render_template('homepagenew.html'), 500


if __name__ == '__main__':
    application.run(debug=True, host='0.0.0.0', port=5000)
