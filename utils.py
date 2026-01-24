from datetime import datetime, date, time, timedelta
from typing import Union, Dict, List, Tuple
from str_queries import *
from sql_base import insert, update

def check_if_admin(email: str):
    '''

    :param email: an email address
    :return: (True/False) if email is of an admin
    '''
    find = select("Managers",
                  ["Managers.Email"],
                  where=f"Managers.Email='{email}'")
    return len(find)>0


def insert_customer_details(First_name : str,
                            Last_name: str,
                            email: str,
                            password: str = None,
                            passport_num: int = None,
                            date_of_birth: date = None,
                            signup_date: date = None,
                            is_signed_up: bool = False):
    '''
    insert customer details into database (except for phones)
    :param First_name: English first name of customer
    :param Last_name: English last name of customer
    :param email: email address of customer
    :param password: password of customer (if is_signed_up == True)
    :param passport_num: passport number of customer (if is_signed_up == True)
    :param date_of_birth: birthdate of customer (if is_signed_up == True)
    :param signup_date: signup date of customer (if is_signed_up == True)
    :param is_signed_up: if customer is signed up True else if guest False
    :return:
    '''
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
    '''
    insert customer phones into database
    :param email: email address of customer
    :param phones: list of phone numbers of customer
    :param is_signed_up: if customer is signed up True else if guest False
    :return:
    '''
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
    '''
    insert customer order into database (except for seats)
    :param email: email address of customer
    :param plain_id: plain of the flight
    :param class_type: class where seats are placed
    :param flight_id: flight identifier
    :param is_signed_up: if customer is signed up True else if guest False
    :return: unique order id
    '''
    table_name = "CustomerOrders" if is_signed_up else "GuestOrders"
    last_id = select("((SELECT OrderID FROM GuestOrders) UNION (SELECT OrderID FROM CustomerOrders)) AS O",
                     ["MAX(O.OrderID) AS MaxId"])
    last_id = last_id[0]["MaxId"] if last_id and len(last_id) > 0 else 0
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
    '''
    insert customer order seats into database
    :param order_id: order identifier
    :param order_seats: list of 2-length tuples, where each tuple is (row number, column number)
    :param is_signed_up: if customer is signed up True else if guest False
    :return:
    '''
    for seat in order_seats:
        insert("SelectedSeatsCustomerOrders" if is_signed_up else "SelectedSeatsGuestOrders",
               {"OrderId": order_id, "Line": seat[0], "SeatLetter": seat[1]})

def insert_plain(plain_id: Union[str, int],
                 manufacturer: str,
                 size: str,
                 purchase_date: date):
    '''
    insert plain into database (except for classes)
    :param plain_id: identifier of the plain
    :param manufacturer: name of the manufacturer
    :param size: string size of the plain (Large/Small)
    :param purchase_date: date of purchase of plain
    :return:
    '''
    insert("Plains",
           {
               "PlainID": plain_id,
               "Manufacturer": f"'{manufacturer}'",
               "Size": f"'{size}'",
               "PurchaseDate": f"'{purchase_date}'"
           })

def insert_classes(plain_id: Union[str, int], classes: List[Tuple[str, int, int]]):
    '''
    insert plains' classes into database
    :param plain_id: plain identifier
    :param classes: list of 3-length tuples, where each tuple is (class_name,rows, columns)
    :return:
    '''
    for cls in classes:
        insert("Class", {"PlainID": plain_id, "ClassType": f"'{cls[0]}'", "NumberRows": cls[1], "NumberCols": cls[2]})

def insert_flight(plain_id: Union[str, int],
                  take_off_time: datetime,
                  source_field: str,
                  destination_field: str):
    '''
    insert flight into database (except for prices)
    :param plain_id: identifier of the plain
    :param take_off_time: take-off time of the flight
    :param source_field: where to take off the flight
    :param destination_field: where to land the flight
    :return: unique flight identifier
    '''
    last_id = select("Flights", ["MAX(FlightID) AS MaxId"])
    last_id = last_id[0]["MaxId"] if last_id and len(last_id) > 0 else 0
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
    '''
    insert flight prices into database
    :param flight_id: flight identifier
    :param plain_id: plain identifier
    :param prices: list of 2-length tuples, where each tuple is (class_name, price)
    :return:
    '''
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
    '''
    insert attendant into database
    :param attendant_id: attendant identifier
    :param first_name: first name of the attendant
    :param last_name: last name of the attendant
    :param phone: phone number of the attendant
    :param city: city (physical address) of the attendant
    :param street: street name (physical address) of the attendant
    :param home_number: home number (physical address) of the attendant
    :param job_start_day: date where the attendant starts
    :param qualified4long_flights: if attendant has qualified for long flights True else False
    :return:
    '''
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
    '''
    insert pilot into database
    :param pilot_id: pilot identifier
    :param first_name: first name of the pilot
    :param last_name: last name of the pilot
    :param phone: phone number of the pilot
    :param city: city (physical address) of the pilot
    :param street: street name (physical address) of the pilot
    :param home_number: home number (physical address) of the pilot
    :param job_start_day: date when the pilot starts working
    :param qualified4long_flights: if pilot has qualified for long flights True else False
    :return:
    '''
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
    '''
    insert attendants flight shift into database
    :param flight_id: flight identifier
    :param attendant_ids: list of attendants' identifiers
    :return:
    '''
    for attendant_id in attendant_ids:
        insert("WorkingFlightAttendants",{"FlightID": flight_id, "AttendantID": attendant_id})

def insert_working_pilots(flight_id: Union[str, int], pilot_ids: List[Union[str, int]]):
    '''
    insert pilots flight shift into database
    :param flight_id: flight identifier
    :param pilot_ids: list of pilots' identifiers
    :return:
    '''
    for pilot_id in pilot_ids:
        insert("WorkingFlightPilots", {"FlightID": flight_id, "PilotID": pilot_id})


def get_all_fields(to_field: str = None):
    '''

    :param to_field: to which destination field we search routes (default: any field)
    :return: list of all fields leading to to_field (if to_field is None, all fields in database are returned)
    '''
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
    '''

    :param flight_id: flight identifier filter
    :param source_field: source field filter
    :param destination_field: destination field filter
    :param take_off_time: take-off time filter
    :param before_time: take-off time before time filter
    :param after_time: take-off time after time filter
    :param status: flight status filter
    :param num_seats: number of seats available filter
    :return: list of dictionaries of flights by filters (if filters are specified)
                columns: FlightID, SourceField, DestinationField, TakeoffTime, FlightStatus, TotalSeats, BookedSeats,
                            [class1]_price, [class2]_price, ...
    '''
    columns = ["Flights.FlightID",
               "Flights.SourceField",
               "Flights.DestinationField",
               "Flights.TakeOffTime",
               "Flights.PlainID"]
    conditions = []
    if flight_id:
        conditions.append(f"Flights.FlightID = {flight_id}")
    if status:
        conditions.append(f"F.FlightStatus = '{status}'")
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
    capacity_subquery = get_select_query(f"({get_flights_capacity_query()}) AS Cap",
                                         ["Cap.FlightID", "SUM(Cap.Capacity) AS TotalSeats"],
                                         group_by=["Cap.FlightID"])
    occupied_subquery = get_select_query(f"({count_occupied_seats_query()}) AS Oc",
                                          ["Oc.FlightID", "SUM(Oc.OccupiedSeats) AS BookedSeats"],
                                          group_by=["Oc.FlightID"])
    classes = [cls["ClassType"] for cls in select("Class",
                                                  ["ClassType"],
                                                  group_by=["ClassType"])]
    joint_columns = ["FStatus.FlightID", "FStatus.FlightStatus"]+[f"FPrices.{cls}_price" for cls in classes]
    joint_subquery = get_select_query(f"({status_subquery}) AS FStatus",
                                      joint_columns,
                                      join=(f"({prices_subquery}) AS FPrices", ["FlightID"]))
    joint_columns = ["Joint.FlightID", "Joint.FlightStatus"]+[f"Joint.{cls}_price" for cls in classes] + ["Cap.TotalSeats"]
    joint_subquery = get_select_query(f"({joint_subquery}) AS Joint",
                                      joint_columns,
                                      join=(f"({capacity_subquery}) AS Cap", ["FlightID"]))
    joint_columns = ["Joint.FlightID", "Joint.FlightStatus"]+[f"Joint.{cls}_price" for cls in classes] + ["Joint.TotalSeats"] + ["Av.BookedSeats"]
    joint_subquery = get_select_query(f"({joint_subquery}) AS Joint",
                                      joint_columns,
                                      join=(f"({occupied_subquery}) AS Av", ["FlightID"]))
    joint_columns = columns + ["F.FlightStatus"]+[f"F.{cls}_price" for cls in classes] + ["F.TotalSeats"] + ["F.BookedSeats"]
    allquery = get_select_query("Flights",
                                joint_columns,
                                where=" AND ".join(conditions) if len(conditions)>0 else None,
                                join=(f"({joint_subquery}) AS F",["FlightID"]))
    return select(f"({allquery}) AS FF",
                  order_by=["FF.TakeOffTime"],
                  order_type="ASC")

def get_available_pilots(take_off_time: datetime,
                          landing_time: datetime,
                          source_field: str,
                         destination_field: str,
                          is_long_flight: bool):
    '''

    :param take_off_time: flight takeoff time
    :param landing_time: flight landing time
    :param source_field: where flight takes off
    :param destination_field: where flight lands
    :param is_long_flight: if flight is long True else flight is short False
    :return: Pilots table filtered by available suitable pilots for flight
    '''
    q_ans = get_availables_query("Pilots", "PilotID", take_off_time, landing_time, source_field, destination_field, is_long_flight)
    return select(q_ans, ["Pilots.*"], join=("Pilots", ["PilotID"]))

def get_available_attendants(take_off_time: datetime,
                          landing_time: datetime,
                          source_field: str,
                             destination_field : str,
                          is_long_flight: bool):
    '''

    :param take_off_time: flight takeoff time
    :param landing_time: flight landing time
    :param source_field: where flight takes off
    :param destination_field: where flight lands
    :param is_long_flight: if flight is long True else flight is short False
    :return: FlightAttendants table filtered by available suitable attendants for flight
    '''
    q_ans = get_availables_query("FlightAttendants", "AttendantID", take_off_time, landing_time, source_field, destination_field, is_long_flight)
    return select(q_ans, ["FlightAttendants.*"], join=("FlightAttendants", ["AttendantID"]))



def get_available_seats(flight_id : Union[str, int], class_type: str):
    '''

    :param flight_id: flight identifier
    :param class_type: class type
    :return: table (list of lists) representing class in a flight,
                where each cell is True if seat is available, false otherwise
    '''
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
            notin_occupied = {"Line": r, "SeatLetter": c} not in occupied
            seats_matrix[-1].append(notin_occupied)
    return seats_matrix

def get_price(num_seats: int, flight_id: int, class_type: str):
    '''

    :param num_seats: number of seats in the order
    :param flight_id: flight identifier in the order
    :param class_type: class type in the order
    :return: calculated total price of the order
    '''
    price_per_seat = select("FlightPrices AS FP", ["FP.Price"],
                            where=f"FP.FlightID={flight_id} AND FP.ClassType='{class_type}'")[0]["Price"]
    return price_per_seat * num_seats

def get_customer_history(email: str, status: str = None):
    '''

    :param email: email address of the customer
    :param status: status filter (default any status)
    :return: table of customer's history filtered by status (if status specified)
                columns: OrderID, ClassType, NumSeats, SourceField, DestinationField, TakeOffTime, OrderPrice, OrderStatus
    '''
    find_and_set_complete()
    find_and_set_complete(True)
    q_seats = occupied_seats_by_flight_and_class_query(include_cancelled=True)
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
                  join=("Flights", ["FlightID"]),
                  order_by=["O.OrderID"],
                  order_type="DESC")

def get_assigned_customer(email: str):
    '''

    :param email: email address of the customer
    :return: dictionary of assigned customer's details including phones (unified str, separated by commas)
    '''
    user = select("Customers", where=f"Customers.Email='{email}'")[0]
    user['Phones'] = ','.join(ph['Phone'] for ph in
                              select("CustomersPhoneNumbers AS CPN", ["CPN.Phone"],
                                                           where=f"CPN.Email='{email}'"))
    return user


def delete_order(order_id: Union[str, int], is_signed_up: bool = False):
    '''
    change order status to 'Customer_Cancelled'
    :param order_id: order identifier
    :param is_signed_up: if order done by signed up customer True else False
    :return:
    '''
    if is_signed_up:
        update("CustomerOrders",
               {"OrderStatus":"'Customer_Cancelled'"},
               where=f"CustomerOrders.OrderID={order_id}")
    else:
        update("GuestOrders",
               {"OrderStatus":"'Customer_Cancelled'"},
               where=f"GuestOrders.OrderID={order_id}")

def find_and_set_complete(is_signed_up : bool = False):
    '''
    find orders of flights of flight status 'Complete' and set those orders status to 'Complete'
    :param is_signed_up: if True search on signed up customers' orders else on guests' orders (default False)
    :return:
    '''
    table_name = "CustomerOrders" if is_signed_up else "GuestOrders"
    clients = select(table_name, [f"{table_name}.OrderID"],
                     join=("Flights", ["FlightID"]),
                     where=f"Flights.TakeOffTime<='{datetime.now().__str__().split()[0]}' "
                           f"AND  {table_name}.OrderStatus!='Customer_Cancelled' "
                           f"AND  {table_name}.OrderStatus!='System_Cancelled' ")
    for client in clients:
        update(table_name, {"OrderStatus": "'Complete'"}, where=f"{table_name}.OrderID={client['OrderID']}")


def get_order(order_id: Union[str, int], email: str):
    '''
    Get order by order_id and email

    :param order_id: Order ID
    :param email: Customer email
    :return: OrderID, ClassType, NumSeats, SourceField,
            DestinationField, TakeOffTime, OrderPrice, OrderStatus
    '''
    if isinstance(order_id, str):
        order_id_int = int(order_id)

    for order in get_customer_history(email):
        if order["OrderID"] == order_id_int:
            return order

    return {}

def check_login(email: str, password: str):
    '''

    :param email: customer email address
    :param password: customer password
    :return: if those details match True else False
    '''
    q_find = select("Customers",
                    where=f"Customers.Email='{email}' AND Customers.UserPassword='{password}'")
    return len(q_find) > 0

def check_admin_login(admin_id: Union[str, int], password: str):
    '''

    :param admin_id: admin email address
    :param password: admin password
    :return: if those details match True else False
    '''
    q_find = select("Managers",
                    where=f"Managers.ManagerID={admin_id} AND Managers.UserPassword='{password}'")
    return len(q_find) > 0

def assigned_customer_exists(email: str):
    '''

    :param email: assigned customer email address
    :return: if exists such assigned customer with this email True, else False
    '''
    q_find = select("Customers",
                    where=f"Customers.Email='{email}'")
    return len(q_find) > 0

def guest_exists(email: str):
    '''

    :param email: guest email address
    :return: if such guest with this email exists, else False
    '''
    q_find = select("Guests",
                    where=f"Guests.Email='{email}'")
    return len(q_find) > 0

def is_phone_assigned(email: str, phone: str, is_signed_up : bool = False):
    '''

    :param email: customer email address
    :param phone: customer phone number
    :param is_signed_up: if True search on signed up customers' phones else on guests' phones (default False)
    :return: if combination of email and phone exists in the database True, else False
    '''
    table_name = "CustomersPhoneNumbers" if is_signed_up else "GuestsPhoneNumbers"
    q_find = select(table_name, where=f"{table_name}.Email='{email}' AND {table_name}.Phone='{phone}'")
    return len(q_find) > 0

def delete_flight(flight_id: Union[str, int]):
    '''
    set flight status to 'System Cancelled'
    :param flight_id: flight identifier
    :return:
    '''
    update("Flights", {"IsDeleted": "BINARY(1)"},
           where=f"Flights.FlightID={flight_id}")
    update("CustomerOrders", {"OrderStatus":"'System_Cancelled'"},
           where=f"CustomerOrders.FlightID={flight_id}")
    update("GuestOrders", {"OrderStatus":"'System_Cancelled'"},
           where=f"GuestOrders.FlightID={flight_id}")

def get_flight_category(source_field: str, destination_field: str):
    '''

    :param source_field: take-off place
    :param destination_field: landing place
    :return: according to Routes table, if Flight's duration is 6 hours or more returns "Long"
                else "Short"
    '''
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
    '''

    :param take_off_time: flight takeoff time
    :param landing_time: flight landing time
    :param source_field: where flight takes off
    :param destination_field: where flight lands
    :param is_long_flight: if flight is long True else flight is short False
    :return: Plains table filtered by available suitable plains for flight
    '''
    q_ans = get_availables_query("Plains", "PlainID",take_off_time, landing_time, source_field, destination_field, is_long_flight)
    return select(q_ans, ["Plains.PlainID", "Plains.Size"], join=("Plains", ["PlainID"]))
