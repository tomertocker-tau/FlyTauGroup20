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


def find_flights_by(flight_id:Union[str,int] = None,
                    source_field: str = None,
                    destination_field: str = None,
                    take_off_time: datetime = None,
                    before_time : datetime = None,
                    after_time: datetime = None,
                    status: str = None,
                    num_seats: int = None):
    columns = ["Flights.FlightID",
               "Flights.SourceField",
               "Flights.DestinationField",
               "Flights.TakeOffTime",
               "Flights.PlainID"]
    conditions = []
    if flight_id:
        conditions.append(f"Flights.FlightID = {flight_id}")
    if status:
        conditions.append(f"F.Status = '{status}'")
    if source_field:
        conditions.append(f"Flights.SourceField LIKE '%{source_field}%'")
    if destination_field:
        conditions.append(f"Flights.DestinationField LIKE '%{destination_field}%'")
    if take_off_time:
        conditions.append(f"Flights.TakeOffTime='{take_off_time.__str__().split('.')[0]}'")
    if before_time:
        conditions.append(f"Flights.TakeOffTime<'{before_time.__str__().split('.')[0]}'")
    if after_time:
        conditions.append(f"Flights.TakeOffTime>'{after_time.__str__().split('.')[0]}'")
    if num_seats:
        pass
    else:
        num_seats = 0
    prices_subquery = table_class_prices_query(num_seats)
    status_subquery = flight_status_query()
    classes = [cls["ClassType"] for cls in select("Class",
                                                  ["ClassType"],
                                                  group_by=["ClassType"])]
    joint_subquery = get_select_query(f"({status_subquery}) AS FStatus",
                                      ["FStatus.FlightID", "FStatus.FlightStatus"]+[f"FPrices.{cls}_price" for cls in classes],
                                      join=(f"({prices_subquery}) AS FPrices", ["FlightID"]))
    allquery = get_select_query("Flights",
                                columns + ["F.FlightStatus"]+[f"F.{cls}_price" for cls in classes],
                                where=" AND ".join(conditions) if len(conditions)>0 else None,
                                join=(f"({joint_subquery}) AS F",["FlightID"]),
                                side_join="LEFT")
    return select(f"({allquery}) AS FF")


def get_available_pilots(on_time: datetime, required_qualify: bool = False):

    return [{"PilotID:" : 2001}, {"PilotID:" : 2002}, {"PilotID:" : 2006}]

def get_available_attendants(on_time: datetime, required_qualify: bool = False):

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
    pass

def find_available_plains(take_off_time: datetime,
                          landing_time: datetime,
                          source_field: str,
                          is_long_flight: bool):
    return[{"PlaneID":1 , "NumClasses":2},{"PlaneID":2 , "NumClasses":2},{"PlaneID":6 , "NumClasses":1}]
