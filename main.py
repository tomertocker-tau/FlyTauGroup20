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


@app.route('/')
def homepagenew():
    """Homepage with search functionality"""
    airports = get_all_fields()
    return render_template("homepagenew.html", airports=airports)

@app.route('/search_flights', methods=['GET', 'POST'])
def search_flights():
    """Handle flight search and show available flights"""
    if request.method == 'POST':
        source_field = request.form.get('source')
        destination_field = request.form.get('destination')
        take_off_date = request.form.get('takeoff_date')
        passengers_amount = request.form.get('passengers', type=int)

        if source_field == destination_field:
            flash("Source and Destination cannot be the same field.", "error")
            # מחזירים אותו לדף הבית לנסות שוב
            return redirect(url_for('homepagenew'))

        if not all([source_field, destination_field, take_off_date, passengers_amount]):
            flash('Please fill all required fields', 'error')
            return redirect(url_for('homepagenew'))

        session['search_params'] = {
            'source': source_field,
            'destination': destination_field,
            'date': take_off_date,
            'passengers': passengers_amount
        }

        takeoff_datetime = datetime.strptime(take_off_date, '%Y-%m-%d')

        # חיפוש טיסות - רק כאלה שיש בהן מספיק מקומות פנויים
        flights = find_flights_by(
            source_field=source_field,
            destination_field=destination_field,
            after_time=takeoff_datetime - timedelta(minutes=1),
            before_time=takeoff_datetime + timedelta(days=1),
            num_seats=passengers_amount  # כבר מסנן רק טיסות עם מספיק מקומות
        )

        return render_template("flight_search_results.html",
                               flights=flights,
                               search_params=session.get('search_params'))

    return redirect(url_for('homepagenew'))
@app.route('/flight_search_results')
def flight_search_results():
    """Show flight search results page (when accessed directly)"""
    if 'search_params' not in session:
        flash('Please search for flights first', 'error')
        return redirect(url_for('homepagenew'))

    # אם מגיעים לכאן ישירות - להציג את התוצאות שבsession
    return render_template("flight_search_results.html",
                           flights=session.get('flights', []),
                           search_params=session.get('search_params'))


@app.route('/book_flight/<flight_id>/<class_type>')
def book_flight(flight_id, class_type):
    """Process flight selection and move to passenger details"""
    # אין בדיקות - הטיסה כבר נבדקה בשלב החיפוש
    search_params = session.get('search_params')
    if not search_params:
        flash('Please search for flights first', 'error')
        return redirect(url_for('homepagenew'))

    # שליפת פרטי הטיסה רק לתצוגה
    flights = find_flights_by(flight_id=flight_id)
    flight = flights[0] if flights else {}

    passengers_count = search_params.get('passengers', 1)

    session['booking_data'] = {
        'flight_id': flight_id,
        'class_type': class_type,
        'passengers_count': passengers_count,
        'flight': flight
    }

    # טעינת נתוני משתמש רשום אם קיים
    user_data = None
    if 'email' in session and session.get('user_type') == 'customer':
        user_email = session.get('email')
        customer_data = get_assigned_customer(user_email)
        if customer_data:
            user_data = customer_data[0]

    # מעבר ישיר לדף פרטי הנוסעים
    return render_template("booking_step1.html",
                           flight=flight,
                           class_type=class_type,
                           user_data=user_data,
                           passengers_count=passengers_count)



@app.route('/booking_step1_process', methods=['POST'])
def booking_step1_process():
    """Process passenger details form - with passport and birth date"""
    if 'booking_data' not in session:
        flash('Please start booking process again', 'error')
        return redirect(url_for('homepagenew'))

    # עדכון נתוני ההזמנה עם כל הפרטים הנדרשים
    session['booking_data'].update({
        'first_name': request.form.get('first_name'),
        'last_name': request.form.get('last_name'),
        'email': request.form.get('email'),
        'phone': request.form.get('phone').strip().split(','),
        'passport_number': request.form.get('passport_number'),
        'birth_date': request.form.get('birth_date')
    })

    # בדיקה אם המשתמש רשום
    email = request.form.get('email')
    is_registered = assigned_customer_exists(email) and len(get_assigned_customer(email)) > 0
    session['booking_data']['is_registered'] = is_registered

    return redirect(url_for('booking_step2'))


@app.route('/booking_step2')
def booking_step2():
    """Show seat selection page - only for selected class"""
    if 'booking_data' not in session:
        flash('Please start booking process again', 'error')
        return redirect(url_for('homepagenew'))

    booking_data = session['booking_data']
    flight_id = booking_data['flight_id']
    class_type = booking_data['class_type']  # המחלקה כבר נבחרה
    passengers_count = booking_data['passengers_count']

    # קבלת מקומות פנויים רק למחלקה הנבחרת
    available_seats = get_available_seats(flight_id, class_type)

    flights = find_flights_by(flight_id=flight_id)
    flight = flights[0] if flights else None

    return render_template("booking_step2_seats.html",
                           flight=flight,
                           available_seats=available_seats,
                           class_type=class_type,
                           passengers_count=passengers_count,
                           booking_data=booking_data)


@app.route('/complete_booking', methods=['POST', 'GET'])
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

        # אם זה אורח - נשאיר אותו אורח ולא ניצור customer
        if not is_registered:
            # הוספה לטבלת Guests (לא Customers)
            if not guest_exists(email):
                insert_customer_details(
                    First_name=booking_data['first_name'],
                    Last_name=booking_data['last_name'],
                    email=email,
                    passport_num=int(booking_data['passport_number']),
                    date_of_birth=datetime.strptime(booking_data['birth_date'], '%Y-%m-%d').date(),
                    is_signed_up=False  # זה יכניס ל-Guests
                )

            # הוספת טלפון לטבלת GuestsPhoneNumbers
            if booking_data.get('phone'):
                insert_phones(email, [ph for ph in booking_data['phone'] if is_phone_assigned(email, ph)], is_signed_up=False)

        # יצירת הזמנה - בטבלה הנכונה לפי סוג המשתמש
        flights = find_flights_by(flight_id=booking_data['flight_id'])
        plain_id = flights[0]['PlainID'] if flights else None

        order_id = insert_order(
            email=email,
            plain_id=plain_id,
            class_type=booking_data['class_type'],
            flight_id=booking_data['flight_id'],
            is_signed_up=is_registered  # GuestOrders אם False, CustomerOrders אם True
        )

        # הוספת מקומות ישיבה לטבלה הנכונה
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
        # ניקוי session
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

@app.route('/login_new', methods=['GET', 'POST'])
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

        return render_template("login_new.html",
                               message="Incorrect login details")

    return render_template("login_new.html")


@app.route('/signup_new', methods=['GET', 'POST'])
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
            return render_template("login_new.html",
                                   message="You are already registered")

        if check_if_admin(email):
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
            return render_template("signup_new.html",
                                   message=f"Registration failed: {str(e)}")

    return render_template("signup_new.html")


@app.route('/login_admin', methods=['GET', 'POST'])
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

        return render_template("login_admin.html",
                               message="Incorrect login details")

    return render_template("login_admin.html")


@app.route('/users_page')
def users_page():
    """Customer dashboard/main page"""
    if 'email' not in session or session.get('user_type') != 'customer':
        flash('Please login to access this page', 'error')
        return redirect(url_for('login_new'))

    # Get customer orders for display
    user_email = session.get("email")
    orders = get_customer_history(user_email)

    # --- הוספה חדשה: שליפת שדות תעופה עבור מנוע החיפוש ---
    airports = get_all_fields()

    return render_template("users_page.html", orders=orders, airports=airports)

@app.route('/managers_page')
def managers_page():
    """Manager dashboard"""
    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Please login as manager to access this page', 'error')
        return redirect(url_for('login_admin'))

    return render_template("managers_page.html")


@app.route('/managers_reports_page')
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


@app.route('/flights', methods=['GET', 'POST'])
def flights():
    """Flight search from users page"""
    if request.method == 'POST':
        origin = request.form.get('source')
        destination = request.form.get('destination')
        departure_date = request.form.get('takeoff_date')
        passengers = request.form.get('passengers')

        if origin == destination:
            flash("Source and Destination cannot be the same field.", "error")
            # מחזירים אותו לדף הבית לנסות שוב
            return redirect(url_for('users_page' if session.get('user_type') == 'customer' else ''))

        # Store search parameters
        session['search_params'] = {
            'source': origin,
            'destination': destination,
            'date': departure_date,
            'passengers': passengers
        }
        take_off_time = datetime.strptime(departure_date, '%Y-%m-%d') if departure_date else None

        # Get flights
        flights = find_flights_by(
            source_field=origin,
            destination_field=destination,
            after_time=take_off_time - timedelta(minutes=1),
            num_seats= int(passengers),
            status="Active"
        )

        return render_template("flight_search_results.html",
                               flights=flights,
                               search_params=session.get('search_params'))

    return render_template("users_page.html" if session.get('user_type') == 'customer' else "homepagenew.html")


@app.route("/customer_history", methods=['POST', 'GET'])
def customer_history():
    """View customer flight history"""
    if 'email' not in session:
        flash('Please login to view history', 'error')
        return redirect(url_for('login_new'))

    user_email = session.get("email")
    status = request.form.get("status")

    orders = get_customer_history(user_email, status)
    for i in range(len(orders)):
        orders[i]['cancellable'] = orders[i]['TakeOffTime'] - datetime.now() > timedelta(hours=36)

    return render_template("users_page.html", orders=orders, by_status=status)


@app.route('/cancel_order/<order_id>')
def cancel_order(order_id):
    delete_order(order_id, is_signed_up=session['user_type'] == 'customer')
    flash('Order Cancelled Successfully', 'success')
    return redirect(url_for('cancel_confirmation', order_id=order_id))


@app.route('/cancel_confirmation/<order_id>')
def cancel_confirmation(order_id):
    if 'email' not in session:
        flash('Please login to access this page', 'error')
        return redirect(url_for('login_new'))

    user_email = session.get('email')
    order = get_order(order_id, user_email)

    if not order:
        flash('Order not found', 'error')
        return redirect(url_for('users_page'))

    return render_template("cancel_confirmation.html", order=order)


@app.route('/confirm_cancel/<order_id>', methods=['POST'])
def confirm_cancel(order_id):
    """(chnging the order status to cancelled!)"""
    if 'email' not in session:
        flash('Please login to access this page', 'error')
        return redirect(url_for('login_new'))

    try:
        delete_order(order_id, is_signed_up=True)
        flash('Order cancelled successfully', 'success')
    except Exception as e:
        flash(f'Error cancelling order: {str(e)}', 'error')

    return redirect(url_for('users_page' if session.get('user_type') == 'customer' else ''))


@app.route('/flight_board')
def flight_board():
    """Display flight board page"""
    # Get all current flights
    flights = find_flights_by()
    return render_template("flight_board.html", flights=flights)


@app.route('/manage_order', methods=['GET', 'POST'])
def manage_order():
    if request.method == 'POST':
        order_id = request.form.get('order_id')
        email = request.form.get('email')

        order = get_order(order_id, email)

        if not order:
            flash('Order not found', 'error')
            return render_template("manage_order.html")

        return redirect(url_for('booking_details', order_id=order_id))

    return render_template("manage_order.html")


@app.route('/booking_details/<order_id>')
def booking_details(order_id):
    if 'email' in session:
        user_email = session.get('email')
    else:
        flash('Please login or use order lookup', 'error')
        return redirect(url_for('manage_order'))

    order = get_order(order_id, user_email)

    if not order:
        flash('Booking not found', 'error')
        return redirect(url_for('users_page'))

    flight_time_str = order["TakeOffTime"]
    format_string = "%Y-%m-%d %H:%M:%S"
    flight_time = datetime.strptime(flight_time_str, format_string)
    current_time = datetime.now()
    time_diff = flight_time - current_time
    is_cancellable = (time_diff > timedelta(hours=36)) and (
                order["OrderStatus"] not in ["Cancelled", "Customer_Cancelled"])

    return render_template("booking_details.html",
                           order=order,
                           show_cancel_button=is_cancellable)


@app.route('/layout')
def layout():
    """Layout/template page"""
    return render_template("layout.html")


@app.route('/add_flight_step1', methods=['GET', 'POST'])
def add_flight_step1():
    if 'ID' not in session or session.get('user_type') != 'manager':
        flash('Manager access required', 'error')
        return redirect(url_for('login_admin'))

    if request.method == 'POST':
        source_field = request.form.get('source_field')
        destination_field = request.form.get('destination_field')
        takeoff_date = request.form.get('takeoff_date')
        takeoff_time = request.form.get('takeoff_time')

        flight_category = get_flight_category(source_field, destination_field)
        if not flight_category:
            flash('Route not found', 'error')
            return render_template("add_flight_step1.html")

        session['flight_data'] = {
            'source_field': source_field,
            'destination_field': destination_field,
            'takeoff_date': takeoff_date,  # שמירה נפרדת
            'takeoff_time': takeoff_time,  # שמירה נפרדת
            'takeoff_datetime': f"{takeoff_date} {takeoff_time}",
            'flight_category': flight_category,
            'is_long_flight': flight_category == 'Long'
        }

        return redirect(url_for('add_flight_step2'))

    airports = get_all_fields()
    return render_template("add_flight_step1.html", airports=airports)


@app.route('/add_flight_step2', methods=['GET', 'POST'])
def add_flight_step2():
    if 'ID' not in session or session.get('user_type') != 'manager':
        return redirect(url_for('login_admin'))

    if 'flight_data' not in session:
        flash('Please start from step 1', 'error')
        return redirect(url_for('add_flight_step1'))

    if request.method == 'POST':
        # תיקון: קריאה לשדה הנכון מהHTML
        selected_plane = request.form.get('plane_id')  # במקום 'PlainID'
        session['flight_data']['selected_plane'] = selected_plane
        return redirect(url_for('add_flight_step3'))

    takeoff_datetime = datetime.strptime(session['flight_data']['takeoff_datetime'], '%Y-%m-%d %H:%M')
    landing_datetime = takeoff_datetime + timedelta(hours=8)

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


@app.route('/add_flight_step3', methods=['GET', 'POST'])
def add_flight_step3():
    if 'ID' not in session or session.get('user_type') != 'manager':
        return redirect(url_for('login_admin'))

    if 'flight_data' not in session:
        return redirect(url_for('add_flight_step1'))

    if request.method == 'POST':
        # תיקון: קבלת מחירים בצורה דינמית
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

        # תיקון: מעבר לשלב 4 הנכון
        return redirect(url_for('add_flight_step4'))

    takeoff_datetime = datetime.strptime(session['flight_data']['takeoff_datetime'], '%Y-%m-%d %H:%M')
    landing_datetime = takeoff_datetime + timedelta(hours=8)
    source_field = session['flight_data']['source_field']
    destination_field = session['flight_data']['destination_field']

    # תיקון: שימוש בנתון שכבר יש לנו
    is_long_flight = session['flight_data']['is_long_flight']

    available_pilots = get_available_pilots(takeoff_datetime, landing_datetime, source_field, destination_field, is_long_flight)
    available_attendants = get_available_attendants(takeoff_datetime, landing_datetime, source_field, destination_field, is_long_flight)

    # קבלת מחלקות המטוס
    selected_plane_id = session['flight_data'].get('selected_plane')
    classes = []
    if selected_plane_id:
        # הנחה שיש לך פונקציה לקבלת מחלקות המטוס
        classes = [{'ClassName': 'Economy'}, {'ClassName': 'Business'}]  # או פונקציה מתאימה

    # תיקון: הוספת required_pilots ו-required_attendants
    plane_size = 'Large' if is_long_flight else 'Small'  # או לוגיקה מתאימה
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


@app.route('/add_flight_step4', methods=['GET', 'POST'])
def add_flight_step4():
    if 'ID' not in session or session.get('user_type') != 'manager':
        return redirect(url_for('login_admin'))

    if 'flight_data' not in session:
        return redirect(url_for('add_flight_step1'))

    flight_data = session['flight_data']

    # שחזור המידע המלא
    takeoff_datetime = datetime.strptime(flight_data['takeoff_datetime'], '%Y-%m-%d %H:%M')
    landing_datetime = takeoff_datetime + timedelta(hours=8)

    # מציאת המטוס הנבחר
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

    # מציאת הצוות הנבחר
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
    selected_attendants = [a for a in available_attendants if str(a['FlightAttendantID']) in selected_attendant_ids]

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

            # יצירת הטיסה
            flight_id = insert_flight(
                plain_id=flight_data['selected_plane'],
                take_off_time=takeoff_datetime,
                source_field=flight_data['source_field'],
                destination_field=flight_data['destination_field']
            )

            # הוספת מחירים
            pricing = flight_data.get('pricing')
            if pricing:
                plain_id = flight_data['selected_plane']
                insert_flight_prices(flight_id, plain_id, list(pricing.items()))

            # הוספת דיילים שעובדים בטיסה
            insert_working_attendants(flight_id, attendant_ids)

            # הוספת טייסים שעובדים בטיסה
            insert_working_pilots(flight_id, pilot_ids)

            session.pop('flight_data', None)
            flash('Flight added successfully!', 'success')
            return redirect(url_for('manager_flight_table'))

        except Exception as e:
            flash(f'Error adding flight: {str(e)}', 'error')

    # העברת המשתנים לHTML
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

@app.route('/manager_flight_table', methods=['GET', 'POST'])
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
                flight.get('IsDeleted', 0) == 0
        )
    return render_template("manager_flight_table.html", flights=flights, sources=sources,
    destinations=destinations,
    source_filter=filters.get('source_field'),
    destination_filter=filters.get('destination_field'),
                           status_filter=filters.get('status'),
                           flight_number_filter=filters.get('flight_id'),
                           month_filter=html_month_input)


@app.route('/delete_flight/<flight_id>')
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


@app.route('/cancel_flight_confirmation/<flight_id>')
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


@app.route('/confirm_cancel_flight/<flight_id>', methods=['POST'])
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


@app.route('/add_attendant', methods=['GET', 'POST'])
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


@app.route('/add_pilot', methods=['GET', 'POST'])
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


@app.route('/add_plane', methods=['GET', 'POST'])
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


@app.route('/logout')
def logout():
    """Logout user"""
    user_type = session.get('user_type', 'user')
    session.clear()
    flash(f'{user_type.title()} logged out successfully', 'info')
    return redirect(url_for('homepagenew'))


# Context processor to make session available in templates
@app.context_processor
def inject_user():
    return dict(
        user_email=session.get('email'),
        user_type=session.get('user_type'),
        manager_id=session.get('ID'),
        current_date=datetime.now().strftime('%Y-%m-%d'),
        current_time=datetime.now().strftime('%H:%M')
    )


# Template filters
@app.template_filter('datetime')
def datetime_filter(value, format='%Y-%m-%d %H:%M'):
    """Custom datetime filter for templates"""
    if isinstance(value, str):
        try:
            value = datetime.strptime(value, '%Y-%m-%d %H:%M:%S')
        except:
            return value
    return value.strftime(format) if value else ''


# Error handlers
@app.errorhandler(404)
def page_not_found(e):
    return render_template('homepagenew.html'), 404


@app.errorhandler(500)
def internal_server_error(e):
    flash('An internal error occurred. Please try again.', 'error')
    return render_template('homepagenew.html'), 500


if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
