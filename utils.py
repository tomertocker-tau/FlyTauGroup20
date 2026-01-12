from contextlib import contextmanager
import mysql.connector
from datetime import datetime, date, time
from typing import Union, Dict, List, Tuple

@contextmanager
def db_cur():
    mydb = None
    cursor = None
    try:
        mydb = mysql.connector.connect(
            host="localhost",
            user="root",
            password="root",
            database="flytau",
            autocommit=True
        )
        cursor = mydb.cursor()
        yield cursor
    except mysql.connector.Error as err:
        raise err
    finally:
        if cursor:
            cursor.close()
        if mydb:
            mydb.close()

def insert(table_name: str, data: Dict[str,str]):
    with db_cur() as cursor:
        cursor.execute(f"INSERT INTO {table_name}({', '.join(data.keys())}) "
                     f"VALUES({', '.join(data.keys())})")

def delete(table_name: str, where: str):
    with db_cur() as cursor:
        cursor.execute(f"DELETE FROM {table_name} WHERE {where}")

def select(table_name: str,
           columns: List[str] = None,
           where: str =None,
           group_by:List[str]=None,
           having: str = None,
           cases: Dict[str,str]=None,
           join: Tuple[str, List[str]]=None,
           side_join: str=None):
    with db_cur() as cursor:
        query = get_select_query(table_name, columns, where, group_by, having, cases, join, side_join)
        cursor.execute(query)
    return cursor.fetchall()

def get_select_query(table_name: str,
                     columns: List[str] = None,
                     where: str =None,
                     group_by:List[str]=None,
                     having: str=None,
                     cases: Dict[str,str]=None,
                     join : Tuple[str,List[str]] = None,
                     side_join: str = ""):
    if not columns:
        query = "SELECT *"
        if cases:
            query += " CASE"
            for k, v in cases.items():
                if k in ["ELSE","AS"]:
                    continue
                query += f" WHEN {k} THEN {v}"
            elsecase = cases.get("ELSE")
            if elsecase:
                query += f" ELSE {elsecase}"
            query += f"END AS {cases['AS']}"
        query += f" FROM {table_name}"

    else:
        query = f"SELECT {', '.join(columns)}"
        if cases:
            query += " CASE"
            for k, v in cases.items():
                if k in ["ELSE","AS"]:
                    continue
                query += f" WHEN {k} THEN {v}"
            elsecase = cases.get("ELSE")
            if elsecase:
                query += f" ELSE {elsecase}"
            query += f"END AS {cases['AS']}"
        query += f" FROM {table_name}"
    if join:
        real_table_name = " ".split(table_name)[-1]
        if side_join:
            pass
        else:
            side_join = ""

        query += f"{side_join} JOIN {join[0]} ON {join[0]}.{join[1]} = {real_table_name}.{join[1][0]}"
        for column in join[1][1:]:
            query += f" AND {real_table_name} {column} = {join[0]}.{column}"
    if where:
        query += f" WHERE {where}"
    if group_by:
        query += f" GROUP BY {','.join(group_by)}"
        if having:
            query += f" HAVING {having}"
    return query



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

def occupied_seats_by_flight_and_class_query():
    customer_query = get_select_query("CustomerOrders",
                                      ["OrderID", "FlightID", "ClassType", "PlainID"],
                                      join=("SelectedSeatsCustomerOrders", ["OrderID"]))
    guests_query = get_select_query("GuestOrders",
                                    ["OrderID", "FlightID", "ClassType", "PlainID"],
                                    join=("SelectedSeatsGuestOrders", ["OrderID"]))
    union_query = f"(({customer_query}) UNION ({guests_query})) AS S"
    return union_query


def count_occupied_seats_query():
    union_query = occupied_seats_by_flight_and_class_query()
    return get_select_query(union_query, ["S.FlightID", "S.ClassType", "S.PlainID", "COUNT(S.OrderID) AS OccupiedSeats"],
                  group_by=["FlightID", "ClassType", "PlainID"])

def get_flights_capacity_query():
    flights_query = get_select_query("FlightPrices",
                                     ["FlightID", "PlainID", "ClassType"],
                                     join=("Class", ["PlainID", "ClassType"]))
    return get_select_query(f"({flights_query}) AS FP",
                            ["FlightID","PlainID", "ClassType", "NumberRows*NumberCols AS Capacity"])

def count_available_seats_query():
    occupied_query = count_occupied_seats_query()
    capacity_query = get_flights_capacity_query()
    joint_query = get_select_query(f"({occupied_query}) AS OS",
                                   join=(f"({capacity_query}) AS CS", ["FlightID","PlainID", "ClassType"]),
                                   side_join="Right")
    return get_select_query(f"({joint_query}) AS Joint",
                            ["FlightID","PlainID", "ClassType"],
                            cases={
                                "Joint.OccupiedSeats IS NULL": "Joint.Capacity",
                                "ELSE": "Joint.Capacity - Joint.OccupiedSeats",
                                "AS": "AvailableSeats"
                            })

def available_class_prices_query(atleast: int  = 1):

    count_seats = count_available_seats_query()
    if atleast < 1:
        atleast = 1
    prices_by_class = get_select_query(f"({count_seats}) AS CAS",
                                       ["FlightID","ClassType"],
                                       where=f"AvailableSeats > {atleast}",
                                       join=("FlightPrices", ["FlightID", "ClassType"]))
    return prices_by_class

def table_class_prices_query(atleast: int = 1):
    classes = select("Class", ["ClassType"], group_by=["ClassType"])[0]
    t_cols = ""
    price_seats = available_class_prices_query(atleast)
    for i, cls in enumerate(classes):

        tmp= get_select_query(f"({price_seats}) AS ACP{cls}",
                              ["FlightID", f"Price AS {cls}_price"],
                              where=f"ACP{cls}.AvailableSeats > 0 AND ACP{cls}.ClassType = {cls}")
        if i == 0:
            t_cols = tmp
        else:
            t_cols = get_select_query(f"({price_seats}) AS PBF{cls}",
                                      ["Flight_ID"]+[f"{classes[j]}_price" for j in range(i)],
                                      join=(f"PBF{cls}", ["Flight_ID"]),
                                      side_join="Outer")
    return t_cols


def get_all_fields(except_for: str = None):
    if except_for:
        return select("Routes",
                      ["SourceField"],
                      where=f"SourceField != {except_for}")
    return select("Routes", ["SourceField"])







def find_flights_by(source_field: str = None,
                    destination_field: str = None,
                    take_off_date: date = None,
                    before_date : date = None,
                    after_date: date = None,
                    num_seats: int = None):
    columns = ["Flights.FlightID",
               "Flights.SourceField",
               "Flights.DestinationField",
               "DATE(Flights.TakeOffTime)"]
    conditions = ["IsDeleted==0"]
    if source_field:
        conditions.append(f"Flights.SourceField=={source_field}")
    if destination_field:
        conditions.append(f"Flights.DestinationField=={destination_field}")
    if take_off_date:
        conditions.append(f"DATE(Flights.TakeOffTime)=={take_off_date}")
    if before_date:
        conditions.append(f"DATE(Flights.TakeOffTime)<{before_date}")
    if after_date:
        conditions.append(f"DATE(Flights.TakeOffTime)>{after_date}")
    if num_seats:
        subquery = table_class_prices_query(num_seats)
        allquery = get_select_query("Flights",
                                    columns,
                                    where=" AND ".join(conditions),
                                    join=(f"({subquery}) AS F",["FlightID"]))
        return select(f"({allquery}) AS FF",
                      where=" AND ".join(conditions),
                      join=("Flights", ["FlightID"]))
    else:
        return select("Flights",columns, where=" AND ".join(conditions))

def locate_attendants_query():
    q_attendants = get_select_query("Flights",
                                    ["FlightID", "SourceField", "DestinationField", "TakeOffTime"],
                                    join=("WorkingFlightAttendants", ["FlightID"]))
    q_when_attendants = get_select_query(f"({q_attendants}) AS FA",
                                         ["AttendantID", "MAX(TakeOffTime) AS TakeOffTime"],
                                         group_by=["AttendantID"])
    q_where_attendants = get_select_query(f"({q_attendants}) AS FB",
                                          ["AttendantID", "SourceField", "DestinationField", "TakeOffTime"],
                                          join=(f"({q_when_attendants}) AS FC", ["FlightID"]))
    q_all_attendants = get_select_query(f"({q_where_attendants}) AS F",
                                        ["AttendantID", "SourceField", "DestinationField", "TakeOffTime"],
                                        join=("FlightAttendants", ["AttendantID"]),
                                        side_join="Right")
    return get_select_query(f"({q_all_attendants}) AS Ftag",
                            ["AttendantID", "SourceField", "DestinationField", "TakeOffTime"])

def locate_pilots_query():
    q_pilots = get_select_query("Flights",
                                    ["FlightID", "SourceField", "DestinationField", "TakeOffTime"],
                                    join=("WorkingPilots", ["FlightID"]))
    q_when_pilots = get_select_query(f"({q_pilots}) AS FA",
                                         ["PilotID", "MAX(TakeOffTime) AS TakeOffTime"],
                                         group_by=["PilotID"])
    q_where_pilots = get_select_query(f"({q_pilots}) AS FB",
                                          ["PilotID", "SourceField", "DestinationField", "TakeOffTime"],
                                          join=(f"({q_when_pilots}) AS FC", ["FlightID"]))
    q_all_pilots = get_select_query(f"({q_where_pilots}) AS F",
                                        ["PilotID", "SourceField", "DestinationField", "TakeOffTime"],
                                        join=("Pilots", ["PilotID"]),
                                        side_join="Right")
    return get_select_query(f"({q_all_pilots}) AS Ftag",
                            ["PilotID", "SourceField", "DestinationField", "TakeOffTime"])

def attendants_on_land_query(landing_time: datetime):
    q_locate = locate_attendants_query()
    q_join = get_select_query(f"({q_locate}) AS Ftag_A",
                              join=("Routes", ["SourceField", "DestinationField"]),
                              side_join="Outer")
    q_landing = get_select_query(f"({q_join}) AS Ftag_B",
                                 ["AttendantID", "DestinationField", "TakeOffTime", "TakeOffTime + FlightDuration AS LandingTime"])
    return get_select_query(f"({q_landing}) AS Ftag_C",
                            where=f"LandingTime<{landing_time} OR LandingTime IS NULL")

def pilots_on_land_query(landing_time: datetime):
    q_locate = locate_pilots_query()
    q_join = get_select_query(f"({q_locate}) AS Ftag_A",
                              join=("Routes", ["SourceField", "DestinationField"]),
                              side_join="Outer")
    q_landing = get_select_query(f"({q_join}) AS Ftag_B",
                                 ["PilotID", "DestinationField", "TakeOffTime",
                                  "TakeOffTime + FlightDuration AS LandingTime"])
    return get_select_query(f"({q_landing}) AS Ftag_C",
                            where=f"LandingTime<{landing_time} OR LandingTime IS NULL")

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
    status_condition = f" AND CustomerOrders.Status={status}" if status else ""
    q_with_client = get_select_query(q_seats,
                                     ["OrderID", "FlightID", "ClassType"],
                                     join=("CustomerOrders", ["OrderID", "FlightID", "ClassType"]),
                                     where=f"CustomerOrders.Email={email}"+status_condition)
    q_count_seats = get_select_query(f"({q_with_client}) AS WithClient",
                                     ["OrderID", "FlightID", "ClassType", "OrderStatus", "COUNT(OrderID) AS NumSeats"],
                                     group_by=["OrderID"],
                                     join=("FlightPrices",["FlightID","ClassType"]))
    q_orders = get_select_query(f"({q_count_seats}) AS CountSeats",
                                ["OrderID", "FlightID", "ClassType","NumSeats", "NumSeats*Price AS OrderPrice", "OrderStatus"],
                                join=("Flights", ["FlightID"]))
    return select(f"({q_orders}) AS O",
                  ["OrderID", "ClassType", "NumSeats", "SourceField","DestinationField","TakeOffTime", "OrderPrice", "OrderStatus"])

