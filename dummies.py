from datetime import datetime, date, time
from typing import Union, Dict, List, Tuple
from str_queries import *
from sql_base import insert, update

def check_if_admin(email: str):
    '''

    :param email: an email address
    :return: (True/False) if email is of an admin
    '''
    find = select("Admins",
                  ["Admins.Email"],
                  where=f"Admins.Email={email}")
    return len(find)>0


def insert_customer_details(First_name : str,
                            Last_name: str,
                            email: str,
                            password: str = None,
                            passport_num: int = None,
                            date_of_birth: date = None,
                            signup_date: date = None,
                            is_signed_up: bool = False):
    dict_details = {"EngFirstName": First_name,
                    "EngLastName": Last_name,
                    "Email": email}
    if is_signed_up:
        assert passport_num is not None and password and signup_date and date_of_birth
        dict_details.update({"Password": password,
                             "PassportID": passport_num,
                             "BirthDate": date_of_birth,
                             "SignupDate": signup_date})
        table_name = "Customers"
    else:
        table_name = "Guests"
    insert(table_name, dict_details)

def insert_phones(email: str, phones: List[str], is_signed_up: bool = True):
    table_name = "CustomersPhoneNumbers" if is_signed_up else "GuestsPhoneNumbers"
    for phone in phones:
        phone = phone.strip()
        if select(table_name,
                  [f"{table_name}.Email", f"{table_name}.Phone"],
                  where=f"{table_name}.Email={email} AND {table_name}.Phone={phone}"):
            continue
        else:
            insert(table_name, {"Email": email, "Phone": phone})

def insert_order(order_id: Union[str, int],
                 email : str,
                 plain_id: Union[str, int],
                 class_type: str,
                 flight_id: Union[str, int],
                 is_signed_up: bool = True):
    insert("CustomerOrders" if is_signed_up else "GuestOrders",
           {
               "OrderId": order_id,
               "Email": email,
               "PlainID": plain_id,
               "ClassType": class_type,
               "FlightID": flight_id,
               "OrderStatus": "Done",
               "OrderDate": datetime.today()
           })

def insert_order_seats(order_seats: List[Dict[str, Union[str, int]]], is_signed_up: bool = True):
    for order_seat in order_seats:
        insert("CustomerOrderSeats" if is_signed_up else "GuestOrderSeats", order_seat)

def insert_plain(plain_id: Union[str, int],
                 manufacturer: str,
                 size: str,
                 purchase_date: date):
    insert("Plains",
           {
               "PlainID": plain_id,
               "Manufacturer": manufacturer,
               "Size": size,
               "PurchaseDate": purchase_date
           })

def insert_classes(classes: List[Dict[str, Union[str, int]]]):
    for cls in classes:
        insert("Class", cls)

def insert_flight(flight_id: Union[str, int],
                  plain_id: Union[str, int],
                  take_off_time: datetime,
                  source_field: str,
                  destination_field: str):
    insert("Flights",
           {
               "FlightID": flight_id,
               "PlainID": plain_id,
               "SourceField": source_field,
               "DestinationField": destination_field,
               "TakeOffTime": take_off_time,
               "IsDeleted": "0"
           })

def insert_flight_prices(prices: List[Dict[str, Union[str, int]]]):
    for price in prices:
        insert("FlightPrices", price)

def insert_attendant(attendant_id: Union[str, int],
                     first_name: str,
                     last_name: str,
                     phone: str,
                     city: str,
                     street: str,
                     home_number: int,
                     job_start_day: date,
                     qualified4long_flights: int = 0):
    insert("FlightAttendants",
           {
               "AttendantId": attendant_id,
               "FirstName": first_name,
               "LastName": last_name,
               "Phone": phone,
               "City": city,
               "Street": street,
               "HomeNumber": home_number,
               "JobStartDay": job_start_day,
               "Qualified4LongFlights": qualified4long_flights
           })

def insert_pilot(pilot_id: Union[str, int],
                 first_name: str,
                 last_name: str,
                 phone: str,
                 city: str,
                 street: str,
                 home_number: int,
                 job_start_day: date,
                 qualified4long_flights: int = 0):
    insert("Pilots",
           {
               "PilotId": pilot_id,
               "FirstName": first_name,
               "LastName": last_name,
               "Phone": phone,
               "City": city,
               "Street": street,
               "HomeNumber": home_number,
               "JobStartDay": job_start_day,
               "Qualified4LongFlights": qualified4long_flights
           })


def get_all_fields(except_for: str = None):
    return ["TLV Tel Aviv", "AMS - Amsterdam","FRA - Frankfurt","ATH - Athens"]


from datetime import datetime, timedelta
from typing import Union, List, Dict, Any


def find_flights_by(flight_id: Union[str, int] = None,
                    source_field: str = None,
                    destination_field: str = None,
                    take_off_time: datetime = None,
                    before_time: datetime = None,
                    after_time: datetime = None,
                    status: str = None,
                    num_seats: int = None):
    # יצירת מועד עכשיו לחישובים דינמיים
    now = datetime.now()

    # בניית המאגר הפיקטיבי עם שמות מפתחות זהים ב-100% ל-SQL המקורי
    # שימי לב: במקום Flights.SourceField המפתח הוא פשוט SourceField (ככה זה חוזר מ-Select בדרך כלל)
    dummy_db = [
        {
            "FlightID": 101,
            "SourceField": "Tel Aviv",
            "DestinationField": "New York",
            "TakeOffTime": (now + timedelta(days=1)).strftime('%Y-%m-%d %H:%M:%S'),  # מחזיר מחרוזת כמו SQL
            "PlainID": "Boeing-787",
            "FlightStatus": "active",
            "Economy_price": 850,
            "Business_price": 2000,
            "First_price": 5000,
            # שדות עזר שה-HTML שלך צריך (גם אם לא היו ב-Select המקורי, הם קריטיים לתצוגה)
            "IsDeleted": 0,
            "BookedSeats": 150,
            "TotalSeats": 300
        },
        {
            "FlightID": 102,
            "SourceField": "London",
            "DestinationField": "Paris",
            "TakeOffTime": (now + timedelta(days=3)).strftime('%Y-%m-%d %H:%M:%S'),
            "PlainID": "Airbus-A320",
            "FlightStatus": "active",
            "Economy_price": 120,
            "Business_price": 400,
            "First_price": 800,
            "IsDeleted": 0,
            "BookedSeats": 50,
            "TotalSeats": 180
        },
        {
            "FlightID": 103,
            "SourceField": "Rome",
            "DestinationField": "Tel Aviv",
            "TakeOffTime": (now - timedelta(hours=5)).strftime('%Y-%m-%d %H:%M:%S'),
            "PlainID": "Boeing-737",
            "FlightStatus": "complete",
            "Economy_price": 200,
            "Business_price": 600,
            "First_price": 1200,
            "IsDeleted": 0,
            "BookedSeats": 180,
            "TotalSeats": 180
        },
        {
            "FlightID": 105,
            "SourceField": "Rome",
            "DestinationField": "Tel Aviv",
            "TakeOffTime": (now + timedelta(days=5)).strftime('%Y-%m-%d %H:%M:%S'),
            "PlainID": "Boeing-737",
            "FlightStatus": "avtive",
            "Economy_price": 200,
            "Business_price": 600,
            "First_price": 1200,
            "IsDeleted": 0,
            "BookedSeats": 180,
            "TotalSeats": 180
        },
        {
            "FlightID": 104,
            "SourceField": "Tel Aviv",
            "DestinationField": "Berlin",
            "TakeOffTime": (now + timedelta(days=10)).strftime('%Y-%m-%d %H:%M:%S'),
            "PlainID": "Boeing-737",
            "FlightStatus": "cancelled",
            "Economy_price": 300,
            "Business_price": 800,
            "First_price": 1500,
            "IsDeleted": 1,
            "BookedSeats": 0,
            "TotalSeats": 180
        }
    ]

    # רשימת התוצאות שתחזור
    results = []

    # לוגיקת הסינון (חיקוי של ה-WHERE ב-SQL)
    for flight in dummy_db:
        # המרה ל-datetime לצורך השוואות
        f_time = datetime.strptime(flight["TakeOffTime"], '%Y-%m-%d %H:%M:%S')

        # 1. סינון לפי ID
        if flight_id is not None and str(flight["FlightID"]) != str(flight_id):
            continue

        # 2. סינון לפי סטטוס
        if status and flight["FlightStatus"] != status:
            continue

        # 3. סינון לפי שדה מוצא (Source) - מכיל את הטקסט (LIKE)
        if source_field and source_field.lower() not in flight["SourceField"].lower():
            continue

        # 4. סינון לפי שדה יעד (Destination) - מכיל את הטקסט (LIKE)
        if destination_field and destination_field.lower() not in flight["DestinationField"].lower():
            continue

        # 5. סינון לפי זמן מדויק
        if take_off_time:
            # נשווה תאריכים בלבד כדי למנוע פספוסים בגלל שעות
            if f_time.date() != take_off_time.date():
                continue

        # 6. סינון לפני זמן (Before)
        if before_time and f_time >= before_time:
            continue

        # 7. סינון אחרי זמן (After)
        if after_time and f_time <= after_time:
            continue

        # 8. סינון לפי מקום פנוי (Seats)
        if num_seats:
            available_seats = flight["TotalSeats"] - flight["BookedSeats"]
            if available_seats < num_seats:
                continue

        # אם עבר את כל הסינונים - הוסף לרשימה
        results.append(flight)

    return results

def get_available_pilots(take_off_time: datetime,
                          landing_time: datetime,
                          source_field: str,
                          is_long_flight: bool):

    return [{"PilotID:": 2001}, {"PilotID:": 2002}, {"PilotID:": 2006}]

def get_available_attendants(take_off_time: datetime,
                          landing_time: datetime,
                          source_field: str,
                          is_long_flight: bool):
    return [{"FlightAttendantID:": 3001}, {"FlightAttendantID:": 3002}, {"FlightAttendantID:": 3006}, {"FlightAttendantID:": 30010},{"FlightAttendantID:": 30012}]



def get_available_seats(flight_id : Union[str, int], class_type: str):

    return [[True,False,True],[False,False,True],[True,True,True]]


def get_customer_history(email: str, status: str = None):
    '''

    :param email:
    :param status:
    :return: OrderID, ClassType, NumSeats, SourceField, DestinationField, TakeOffTime, OrderPrice, Status
    '''
    q_seats = occupied_seats_by_flight_and_class_query()
    status_condition = f" AND S.OrderStatus='{status}'" if status else ""
    q_with_client = get_select_query(q_seats,
                                     where=f"S.Email='{email}'"+status_condition)
    q_count_seats = get_select_query(f"({q_with_client}) AS WithClient",
                                     ["WithClient.OrderID", "WithClient.FlightID", "WithClient.ClassType",
                                      "WithClient.OrderStatus", "WithClient.OrderDate", "COUNT(WithClient.OrderID) AS NumSeats", "FlightPrices.Price"],
                                     group_by=["WithClient.OrderID", "WithClient.FlightID", "WithClient.ClassType", "WithClient.OrderStatus", "WithClient.OrderDate", "FlightPrices.Price"],
                                     join=("FlightPrices",["FlightID","ClassType"]))
    q_orders = get_select_query(f"({q_count_seats}) AS CountSeats",
                                ["CountSeats.OrderID", "CountSeats.FlightID", "CountSeats.ClassType","CountSeats.NumSeats", "CountSeats.OrderStatus", "CountSeats.OrderDate"],
                                cases={
                                    "CountSeats.OrderStatus='Customer_Cancelled'": "CountSeats.NumSeats*CountSeats.Price*0.05",
                                    "CountSeats.OrderStatus='System_Cancelled'": "0",
                                    "ELSE": "CountSeats.NumSeats*CountSeats.Price",
                                    "AS": "OrderPrice"
                                })
    return select(f"({q_orders}) AS O",
                  ["O.*", "Flights.SourceField","Flights.DestinationField","Flights.TakeOffTime"],
                  join=("Flights", ["FlightID"]))



def delete_order(order_id: Union[str, int], is_signed_up: bool = False):
    pass


def get_order(order_id:Union[str, int], email: str):
    '''

    :param order_id:
    :param email:
    :return: OrderID, ClassType, NumSeats SourceField,
            DestinationField, TakeOffTime, OrderPrice, OrderStatus
    '''
    for order in get_customer_history(email):
        if order["OrderID"] == order_id:
            return order
    return {}

def check_login(email: str, password: str):
    return True

def check_admin_login(admin_id: Union[str, int], password: str):
    return True

def customer_exists(email: str):
    return True

def delete_flight(flight_id: Union[str, int]):
    pass


def get_flight_category(source_field: str, destination_field: str):

    return "Short"

def find_available_plains(take_off_time: datetime,
                          landing_time: datetime,
                          source_field: str,
                          is_long_flight: bool):
    return[{"PlaneID":1 , "Size":"Large"},{"PlaneID":2 , "Size":"Small"},{"PlaneID":3 , "Size":"Large"}]
