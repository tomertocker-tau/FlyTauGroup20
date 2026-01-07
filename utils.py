from contextlib import contextmanager
import mysql.connector
from datetime import datetime, date
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
           cases: Dict[str,str]=None,
           join: Tuple[str, List[str]]=None,
           side_join: str=None):
    with db_cur() as cursor:
        query = get_select_query(table_name, columns, where, group_by, cases, join, side_join)
        cursor.execute(query)
    return cursor.fetchall()

def get_select_query(table_name: str,
                     columns: List[str] = None,
                     where: str =None,
                     group_by:List[str]=None,
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
                            password: str,
                            passport_num: int,
                            date_of_birth: date,
                            signup_date: date,
                            is_signed_up: bool = True):
    dict_details = {"FirstName": First_name,
                    "LastName": Last_name,
                    "Email": email,
                    "Password": password,
                    "PassportID": passport_num,
                    "BirthDate": date_of_birth,
                    "SignupDate": signup_date}
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

def count_occupied_seats_query():
    customer_query = get_select_query("CustomerOrders",
                                      ["OrderID", "FlightID", "ClassType", "PlainID"],
                                      join=("SelectedSeatsCustomerOrders", ["OrderID"]))
    guests_query = get_select_query("GuestOrders",
                                    ["OrderID", "FlightID", "ClassType", "PlainID"],
                                    join=("SelectedSeatsGuestOrders", ["OrderID"]))
    union_query = f"(({customer_query}) UNION ({guests_query})) AS S"
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

'''def available_class_prices():
    classes = select("Class", ["ClassType"], group_by=["ClassType"])[0]
    '''



def find_flights_by(source_field: str = None,
                    destination_field: str = None,
                    take_off_date: date = None,
                    num_seats: int = None):
    if not any([source_field, destination_field, take_off_date, num_seats]):
        return get_future_flights()
    else:
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
        if num_seats:
            subquery = count_available_seats_query()
            allquery = get_select_query("Flights",
                                        columns,
                                        where=" AND ".join(conditions),
                                        join=(f"({subquery}) AS F",["FlightID"]))
            return select(f"({allquery}) AS FF",
                          where=" AND ".join(conditions),
                          join=("Flights", ["FlightID"]))
        else:
            return select("Flights",columns, where=" AND ".join(conditions))











