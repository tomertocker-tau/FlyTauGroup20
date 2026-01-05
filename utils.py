from contextlib import contextmanager
import mysql.connector
from datetime import datetime
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

def select(table_name: str, columns: List[str] = None, where: str =None, group_by:str=None, cases: Dict[str,str]=None):
    with db_cur() as cursor:
        query = get_select_query(table_name, columns, where, group_by, cases)
        cursor.execute(query)
    return cursor.fetchall()

def get_select_query(table_name: str,
                     columns: List[str] = None,
                     where: str =None,
                     group_by:str=None,
                     cases: Dict[str,str]=None,
                     join : Tuple[str,str] = None):
    if not columns:
        query = f"SELECT * FROM {table_name}"
    else:
        query = f"SELECT {', '.join(columns)} FROM {table_name}"
    if join:
        query += f" JOIN {join[0]} ON {join[0]}.{join[1]} = {join[0]}.{join[1]}"
    if where:
        query += f" WHERE {where}"
    if group_by:
        query += f" GROUP BY {group_by}"
    if cases:
        for k, v in cases.items():
            if k == "ELSE":
                continue
            query += f" WHEN {k} THEN {v}"
        elsecase = cases.get("ELSE")
        if elsecase:
            query += f" ELSE {elsecase}"


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
                             join=("FlightPrices", "FlightID"))

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
                             join=("FlightPrices", "FlightID"))

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


