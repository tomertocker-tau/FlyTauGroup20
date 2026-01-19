from datetime import datetime, date, time, timedelta
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
    dict_details = {"EngFirstName": f"'{First_name}'",
                    "EngLastName": f"'{Last_name}'",
                    "Email": f"'{email}'"}
    if is_signed_up:
        assert passport_num is not None and password and signup_date and date_of_birth
        dict_details.update({"UserPassword": f"'{password}'",
                             "PassportNumber": passport_num,
                             "BirthDate": f"'{date_of_birth}'",
                             "SignupDate": f"'{signup_date}'"})
        table_name = "Customers"
    else:
        table_name = "Guests"
    insert(table_name, dict_details)

def insert_phones(email: str, phones: List[str], is_signed_up: bool = False):
    table_name = "CustomersPhoneNumbers" if is_signed_up else "GuestsPhoneNumbers"
    for phone in phones:
        phone = phone.strip()
        if len(select(table_name,
                  [f"{table_name}.Email", f"{table_name}.Phone"],
                  where=f"{table_name}.Email='{email}' AND {table_name}.Phone='{phone}'")) > 0:
            continue
        else:
            insert(table_name, {"Email": f"'{email}'", "Phone": f"'{phone}'"})

def insert_order(email : str,
                 plain_id: Union[str, int],
                 class_type: str,
                 flight_id: Union[str, int],
                 is_signed_up: bool = False):
    table_name = "CustomerOrders" if is_signed_up else "GuestOrders"
    last_id = select("((SELECT OrderID FROM GuestOrders) UNION (SELECT OrderID FROM CustomerOrders)) AS O",
                     ["MAX(O.OrderID) AS MaxId"])[0]["MaxId"]
    order_id = last_id + 1
    insert(table_name,
           {
               "OrderID": order_id,
               "Email": f"'{email}'",
               "PlainID": plain_id,
               "ClassType": f"'{class_type}'",
               "FlightID": flight_id,
               "OrderStatus": "'Active'",
               "OrderDate": f"'{datetime.today()}'"
           })
    return order_id

def insert_order_seats(order_id: Union[int, str], order_seats: List[Tuple[int, int]], is_signed_up: bool = False):
    for seat in order_seats:
        insert("SelectedSeatsCustomerOrders" if is_signed_up else "SelectedSeatsGuestOrders", {"OrderId": order_id, "Line": seat[0], "SeatLetter": seat[1]})

def insert_plain(plain_id: Union[str, int],
                 manufacturer: str,
                 size: str,
                 purchase_date: date):
    insert("Plains",
           {
               "PlainID": plain_id,
               "Manufacturer": f"'{manufacturer}'",
               "Size": f"'{size}'",
               "PurchaseDate": f"'{purchase_date}'"
           })

def insert_classes(plain_id: Union[str, int], classes: List[Tuple[str, int, int]]):
    for cls in classes:
        insert("Class", {"PlainID": plain_id, "ClassType": f"'{cls[0]}'", "NumberRows": cls[1], "NumberCols": cls[2]})

def insert_flight(plain_id: Union[str, int],
                  take_off_time: datetime,
                  source_field: str,
                  destination_field: str):
    last_id = select("Flights", ["MAX(FlightID) AS MaxId"])[0]["MaxId"]
    flight_id = last_id + 1
    insert("Flights",
           {
               "FlightID": flight_id,
               "PlainID": plain_id,
               "SourceField": f"'{source_field}'",
               "DestinationField": f"'{destination_field}'",
               "TakeOffTime": f"'{take_off_time.__str__().split('.')[0]}'",
               "IsDeleted": "BINARY(0)"
           })
    return flight_id


def insert_flight_prices(flight_id : Union[str, int], plain_id: Union[str, int], prices: List[Tuple[str, Union[str, int, float]]]):
    for price in prices:
        insert("FlightPrices", {"FlightID": flight_id, "PlainID": plain_id, "ClassType": f"'{price[0]}'", "Price": price[1]})


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
               "FirstName": f"'{first_name}'",
               "LastName": f"'{last_name}'",
               "Phone": f"'{phone}'",
               "City": f"'{city}'",
               "Street": f"'{street}'",
               "HomeNumber": home_number,
               "JobStartDay": f"'{job_start_day}'",
               "Qualified4LongFlights": f"BINARY({qualified4long_flights})"
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
               "PilotID": pilot_id,
               "FirstName": f"'{first_name}'",
               "LastName": f"'{last_name}'",
               "Phone": f"'{phone}'",
               "City": f"'{city}'",
               "Street": f"'{street}'",
               "HomeNumber": home_number,
               "JobStartDay": f"'{job_start_day}'",
               "Qualified4LongFlights": f"BINARY({qualified4long_flights})"
           })

def insert_working_attendants(flight_id: Union[str, int], attendant_ids: List[Union[str, int]]):
    for attendant_id in attendant_ids:
        insert("WorkingFlightAttendants",{"FlightID": flight_id, "AttendantID": attendant_id})

def insert_working_pilots(flight_id: Union[str, int], pilot_ids: List[Union[str, int]]):
    for pilot_id in pilot_ids:
        insert("WorkingFlightPilots", {"FlightID": flight_id, "PilotID": pilot_id})


def get_all_fields(to_field: str = None):
    if to_field:
        ret = select("Routes",
                      ["SourceField"],
                      where=f"DestinationField='{to_field}'")
    else:
        ret = select("Routes", ["SourceField"], group_by=["SourceField"])
    return [r["SourceField"] for r in ret]


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

def get_available_pilots(take_off_time: datetime,
                          landing_time: datetime,
                          source_field: str,
                         destination_field: str,
                          is_long_flight: bool):
    q_ans = get_availables_query("Pilots", "PilotID", take_off_time, landing_time, source_field, destination_field, is_long_flight)
    return [s["PilotID"] for s in select(q_ans)]

def get_available_attendants(take_off_time: datetime,
                          landing_time: datetime,
                          source_field: str,
                             destination_field : str,
                          is_long_flight: bool):
    q_ans = get_availables_query("FlightAttendants", "AttendantID", take_off_time, landing_time, source_field, destination_field, is_long_flight)
    return [s["AttendantID"] for s in select(q_ans)]



def get_available_seats(flight_id : Union[str, int], class_type: str):
    q_flights = get_select_query("FlightPrices",
                                 ["FlightPrices.FlightID", "FlightPrices.PlainID", "FlightPrices.ClassType",
                                  "Class.NumberRows", "Class.NumberCols"],
                                 where=f"FlightPrices.FlightID={flight_id} AND FlightPrices.ClassType='{class_type}'",
                                 join=("Class", ["PlainID","ClassType"]))
    shape = select(f"({q_flights}) AS FSizes",
                        ["FSizes.NumberRows", "FSizes.NumberCols"])[0]
    rows, cols = shape["NumberRows"], shape["NumberCols"]
    q_occupied = occupied_seats_by_flight_and_class_query()
    occupied = select(q_occupied,
                      ["S.Line", "S.SeatLetter"],
                      where=f"S.FlightID={flight_id} AND S.ClassType='{class_type}'")
    seats_matrix = []
    for r in range(1, rows + 1):
        seats_matrix.append([])
        for c in range(1, cols + 1):
            isin_occupied = {"Line": r, "SeatLetter": c} in occupied
            seats_matrix[-1].append(isin_occupied)
    return seats_matrix

def get_price(num_seats: int, flight_id: int, class_type: str):
    price_per_seat = select("FlightPrices AS FP", ["FP.Price"],
                            where=f"FP.FlightID={flight_id} AND FP.ClassType='{class_type}'")[0]["Price"]
    return price_per_seat * num_seats

def get_customer_history(email: str, status: str = None):
    '''

    :param email:
    :param status:
    :return: OrderID, ClassType, NumSeats, SourceField, DestinationField, TakeOffTime, OrderPrice, Status
    '''
    find_and_set_complete()
    find_and_set_complete(True)
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

def get_assigned_customer(email: str):
    return select("Customers", where=f"Customers.Email='{email}'")


def delete_order(order_id: Union[str, int], is_signed_up: bool = False):
    if is_signed_up:
        update("CustomerOrders",
               {"OrderStatus":"'Customer_Cancelled'"},
               where=f"CustomerOrders.OrderID={order_id}")
    else:
        update("GuestOrders",
               {"OrderStatus":"'Customer_Cancelled'"},
               where=f"GuestOrders.OrderID={order_id}")

def find_and_set_complete(is_signed_up : bool = False):
    table_name = "CustomerOrders" if is_signed_up else "GuestOrders"
    clients = select(table_name, [f"{table_name}.OrderID"],
                     join=("Flights", ["FlightID"]),
                     where=f"Flights.TakeOffTime<='{datetime.now().__str__().split()[0]}' "
                           f"AND Flights.OrderStatus!='Customer_Cancelled' "
                           f"AND Flights.OrderStatus!='System_Cancelled' ")
    for client in clients:
        update(table_name, {"OrderStatus": "'Complete'"}, where=f"{table_name}.OrderID={client['OrderID']}")

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
    q_find = select("Customers",
                    where=f"Customers.Email='{email}' AND Customers.UserPassword='{password}'")
    return len(q_find) > 0

def check_admin_login(admin_id: Union[str, int], password: str):
    q_find = select("Managers",
                    where=f"Managers.ManagerID={admin_id} AND Managers.UserPassword='{password}'")
    return len(q_find) > 0

def assigned_customer_exists(email: str):
    q_find = select("Customers",
                    where=f"Customers.Email='{email}'")
    return len(q_find) > 0

def delete_flight(flight_id: Union[str, int]):
    update("Flights", {"IsDeleted": "BINARY(1)"},
           where=f"Flights.FlightID={flight_id}")
    update("CustomerOrders", {"OrderStatus":"'System_Cancelled'"},
           where=f"CustomerOrders.FlightID={flight_id}")
    update("GuestOrders", {"OrderStatus":"'System_Cancelled'"},
           where=f"GuestOrders.FlightID={flight_id}")

def get_flight_category(source_field: str, destination_field: str):
    ans = select("Routes", ["FlightDuration"],
                 where=f"SourceField='{source_field}' AND DestinationField='{destination_field}'"
                 )
    if len(ans) == 0:
        return
    if ans[0]["FlightDuration"] > timedelta(hours=6):
        return "Long"
    return "Short"

def find_available_plains(take_off_time: datetime,
                          landing_time: datetime,
                          source_field: str,
                          destination_field: str,
                          is_long_flight: bool):
    q_ans = get_availables_query("Plains", "PlainID",take_off_time, landing_time, source_field, destination_field, is_long_flight)
    return select(q_ans, ["Plains.PlainID", "Plains.Size"], join=("Plains", ["PlainID"]))
