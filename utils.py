from datetime import datetime, date, time
from typing import Union, Dict, List, Tuple
from str_queries import *

def check_if_admin(email: str):
    find = select("Admins",
                  ["Admins.Email"],
                  where=f"Admins.Email={email}")
    return len(find)>0

def get_future_flights(include_deleted: bool = False):
    query = get_select_query("Flights",
                             [
                                 "Flights.FlightID",
                                 "Flights.SourceField",
                                 "Flights.DestinationField",
                                 "Flights.TakeOffTime",
                                 "Flights.IsDeleted"
                             ],
                             join=("FlightPrices", ["FlightID"]))

    if include_deleted:
        return select(f"({query}) AS F",
                      [
                          "F.FlightID",
                          "F.SourceField",
                          "F.DestinationField",
                          "F.TakeOffTime"
                      ],
                      where="F.TakeOffTime > NOW()")
    else:
        return select(f"({query}) AS F",
                      [
                          "F.FlightID",
                          "F.SourceField",
                          "F.DestinationField",
                          "F.TakeOffTime"
                      ],
                      where="F.TakeOffTime > NOW() AND F.IsDeleted==0")

def get_past_flights(include_deleted: bool = False):
    query = get_select_query("Flights",
                             [
                                 "Flights.FlightID",
                                 "Flights.SourceField",
                                 "Flights.DestinationField",
                                 "Flights.TakeOffTime",
                                 "Flights.IsDeleted"
                             ],
                             join=("FlightPrices", ["FlightID"]))

    if include_deleted:
        return select(f"({query}) AS F",
                      [
                          "F.FlightID",
                          "F.SourceField",
                          "F.DestinationField",
                          "F.TakeOffTime"
                      ],
                      where="F.TakeOffTime <= NOW()")
    else:
        return select(f"({query}) AS F",
                      [
                          "F.FlightID",
                          "F.SourceField",
                          "F.DestinationField",
                          "F.TakeOffTime"
                      ],
                      where="F.TakeOffTime <= NOW() AND F.IsDeleted==0")



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


def get_all_fields(except_for: str = None):
    if except_for:
        return select("Routes",
                      ["SourceField"],
                      where=f"SourceField != {except_for}")
    return select("Routes", ["SourceField"])


def find_flights_by(flight_id:Union[str,int] = None,
                    source_field: str = None,
                    destination_field: str = None,
                    take_off_time: datetime = None,
                    before_time : datetime = None,
                    after_time: datetime = None,
                    is_deleted: bool = False,
                    num_seats: int = None):
    columns = ["Flights.FlightID",
               "Flights.SourceField",
               "Flights.DestinationField",
               "Flights.TakeOffTime"]
    conditions = []
    if flight_id:
        conditions.append(f"Flights.FlightID = {flight_id}")
    if is_deleted:
        conditions.append(f"Flights.IsDeleted = {is_deleted}")
    if source_field:
        conditions.append(f"Flights.SourceField LIKE '%{source_field}%'")
    if destination_field:
        conditions.append(f"Flights.DestinationField LIKE '%{destination_field}%'")
    if take_off_time:
        conditions.append(f"Flights.TakeOffTime=={take_off_time}")
    if before_time:
        conditions.append(f"Flights.TakeOffTime<{before_time}")
    if after_time:
        conditions.append(f"Flights.TakeOffTime>{after_time}")
    if num_seats:
        prices_subquery = table_class_prices_query(num_seats)
        status_subquery = flight_status_query()
        joint_subquery = get_select_query(f"({status_subquery}) AS FStatus",
                                          join=(f"({prices_subquery} AS FPrices", ["FlightID"]))
        allquery = get_select_query("Flights",
                                    columns,
                                    where=" AND ".join(conditions) if len(conditions)>0 else None,
                                    join=(f"({joint_subquery}) AS F",["FlightID"]),
                                    side_join="Outer")
        return select(f"({allquery}) AS FF")
    else:
        status_subquery = flight_status_query()
        return select("Flights",
                      columns,
                      where=" AND ".join(conditions) if len(conditions)>0 else None,
                      join=(f"({status_subquery}) AS FStatus",["FlightID"]))

def get_available_pilots(on_time: datetime, required_qualify: bool = False):
    if required_qualify:
        q_required = get_select_query("Pilots",
                                      ["PilotID"],
                                      where="Qualified4LongFlights==1")
        return select(f"({attendants_on_land_query(on_time)}) AS AvailablePilots",
                      ["PilotID"],
                      join=(f"({q_required}) AS RequiredPilots", ["PilotID"]))
    return select(f"({pilots_on_land_query(on_time)}) AS AvailablePilots",
                  ["PilotID"])

def get_available_attendants(on_time: datetime, required_qualify: bool = False):
    if required_qualify:
        q_required = get_select_query("FlightAttendants",
                                      ["AttendantID"],
                                      where="Qualified4LongFlights==1")
        return select(f"({attendants_on_land_query(on_time)}) AS AvailableAttendants",
                      ["AttendantID"],
                      join=(f"({q_required}) AS RequiredAttendants",["AttendantID"]))
    return select(f"({attendants_on_land_query(on_time)}) AS AvailableAttendants",
                  ["AttendantID"])


def get_available_seats(flight_id : Union[str, int], class_type: str):
    q_flights = get_select_query("FlightPrices",
                                 ["FlightID", "PlainID", "ClassType"],
                                 where=f"FlightPrices.FlightID={flight_id} AND FlightPrices.ClassType={class_type}",
                                 join=("Class", ["PlainID","ClassType"]))
    rows, cols = select(f"({q_flights}) AS FP",
                        ["Rows", "Cols"])[0]
    q_occupied = occupied_seats_by_flight_and_class_query()
    occupied = select(f"({q_occupied}) AS O",
                      ["Line", "SeatLetter"],
                      where=f"O.FlightID=={flight_id} AND O.ClassType=={class_type}")
    seats_matrix = []
    for r in range(1, rows + 1):
        seats_matrix.append([])
        for c in range(1, cols + 1):
            isin_occupied = (r,c) in occupied
            seats_matrix[-1].append(isin_occupied)
    return seats_matrix


def get_customer_history(email: str, status: str = None):
    '''

    :param email:
    :param status:
    :return: OrderID, ClassType, NumSeats, SourceField, DestinationField, TakeOffTime, OrderPrice, Status
    '''
    q_seats = occupied_seats_by_flight_and_class_query()
    q_orders_guests = get_select_query("GuestOrders",
                                       where=f"GuestOrders.Email={email}")
    q_orders_customers = get_select_query("CustomerOrders",
                                          where=f"CustomerOrders.Email={email}")
    q_orders_union = f"(({q_orders_guests}) UNION ({q_orders_customers})) AS UnionOrders"
    status_condition = f" AND UnionOrders.Status={status}" if status else ""
    q_with_client = get_select_query(q_seats,
                                     ["OrderID", "FlightID", "ClassType"],
                                     join=(q_orders_union, ["OrderID", "FlightID", "ClassType"]),
                                     where=f"UnionOrders.Email={email}"+status_condition)
    q_count_seats = get_select_query(f"({q_with_client}) AS WithClient",
                                     ["OrderID", "FlightID", "ClassType", "OrderStatus", "COUNT(OrderID) AS NumSeats"],
                                     group_by=["OrderID"],
                                     join=("FlightPrices",["FlightID","ClassType"]))
    q_orders = get_select_query(f"({q_count_seats}) AS CountSeats",
                                ["OrderID", "FlightID", "ClassType","NumSeats", "OrderStatus"],
                                cases={
                                    "CountSeats.OrderStatus='Deleted'": "NumSeats*Price",
                                    "ELSE": "NumSeats*Price*0.05",
                                    "AS": "OrderPrice"
                                },
                                join=("Flights", ["FlightID"]))
    return select(f"({q_orders}) AS O",
                  ["OrderID", "ClassType", "NumSeats", "SourceField","DestinationField","TakeOffTime", "OrderPrice", "OrderStatus"])




def delete_order(order_id: Union[str, int], is_signed_up: bool = False):
    if is_signed_up:
        update("CustomerOrders",
               {"OrderStatus":"Deleted"},
               where=f"CustomerOrders.OrderID={order_id}")
    else:
        update("GuestOrders",
               {"OrderStatus":"Deleted"},
               where=f"GuestOrders.OrderID={order_id}")

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

def check_login(email: str, password: str, is_admin: bool = False):
    if is_admin:
        q_find = select("Managers",
                        where=f"Managers.Email={email} AND Managers.Password={password}")
        return len(q_find) > 0
    q_find = select("Customers",
                    where=f"Customers.Email={email} AND Customers.Password={password}")
    return len(q_find) > 0

def customer_exists(email: str):
    q_find = select("Customers",
                    where=f"Customers.Email={email}")
    return len(q_find) > 0


