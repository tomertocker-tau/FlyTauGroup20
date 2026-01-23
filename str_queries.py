from sql_base import get_select_query, select
from typing import Union, Dict, List, Tuple
from datetime import datetime

def occupied_seats_by_flight_and_class_query():
    customer_query = get_select_query("CustomerOrders",
                                      [
                                          "SelectedSeatsCustomerOrders.Line",
                                          "SelectedSeatsCustomerOrders.SeatLetter",
                                          "CustomerOrders.*"
                                      ],
                                      join=("SelectedSeatsCustomerOrders", ["OrderID"]),
                                      where="CustomerOrders.OrderStatus NOT IN ('System_Cancelled', 'Customer_Cancelled')")
    guests_query = get_select_query("GuestOrders",
                                    [
                                        "SelectedSeatsGuestOrders.Line",
                                        "SelectedSeatsGuestOrders.SeatLetter",
                                        "GuestOrders.*"
                                    ],
                                    join=("SelectedSeatsGuestOrders", ["OrderID"]),
                                    where="GuestOrders.OrderStatus NOT IN ('System_Cancelled', 'Customer_Cancelled')")
    union_query = f"(({customer_query}) UNION ({guests_query})) AS S"
    return union_query


def count_occupied_seats_query():
    union_query = occupied_seats_by_flight_and_class_query()
    occupied_query = get_select_query(union_query, ["S.FlightID", "S.ClassType", "S.PlainID", "COUNT(S.OrderID) AS OccupiedSeats"],
                  group_by=["S.FlightID", "S.ClassType", "S.PlainID"])
    cond_query = get_select_query(f"({occupied_query}) AS OS", ["1"],
                                  where="OS.FlightID=FP.FlightID AND OS.PlainID=FP.PlainID AND OS.ClassType=FP.ClassType")
    empty_flights_query = get_select_query(f"FlightPrices AS FP",
                                           ["FP.FlightID", "FP.ClassType", "FP.PlainID", "0 AS OccupiedSeats"],
                                           where=f"NOT EXISTS ({cond_query})")
    return f"({occupied_query}) UNION ({empty_flights_query})"

def get_flights_capacity_query():
    flights_query = get_select_query("Flights",
                                     ["Flights.FlightID", "Flights.PlainID", "Class.ClassType", "Class.NumberRows*Class.NumberCols AS Capacity"],
                                     join=("Class", ["PlainID"]))
    return flights_query

def count_available_seats_query():
    occupied_query = count_occupied_seats_query()
    capacity_query = get_flights_capacity_query()
    joint_query = get_select_query(f"({occupied_query}) AS OS",
                                   ["OS.FlightID", "OS.ClassType", "OS.PlainID", "OS.OccupiedSeats", "CS.Capacity"],
                                   join=(f"({capacity_query}) AS CS", ["FlightID","PlainID", "ClassType"]))
    return get_select_query(f"({joint_query}) AS Joint",
                            ["Joint.FlightID","Joint.PlainID", "Joint.ClassType",
                             "Joint.Capacity - Joint.OccupiedSeats AS AvailableSeats"])

def available_class_prices_query(atleast: int  = 0):

    count_seats = count_available_seats_query()
    if atleast < 0:
        atleast = 0
    prices_by_class = get_select_query(f"({count_seats}) AS CAS",
                                       ["CAS.FlightID","CAS.ClassType", "FlightPrices.Price"],
                                       where=f"AvailableSeats >= {atleast}",
                                       join=("FlightPrices", ["FlightID", "ClassType"]))
    return prices_by_class

def table_class_prices_query(atleast: int = 0):
    classes = select("Class", ["Class.ClassType"], group_by=["Class.ClassType"])
    classes = [cls["ClassType"] for cls in classes]
    price_seats = available_class_prices_query(atleast)
    t_cols = get_select_query(f"({price_seats}) AS T", ["FlightID"],
                              group_by=["FlightID"])
    for i, cls in enumerate(classes):

        tmp= get_select_query(f"({price_seats}) AS ACP{cls}",
                              [f"ACP{cls}.FlightID", f"ACP{cls}.Price AS {cls}_price"],
                              where=f"ACP{cls}.ClassType = '{cls}'")
        t_cols = get_select_query(f"({t_cols}) AS PBF{cls}",
                                  [f"PBF{cls}.FlightID"]+[f"PBF{cls}.{classes[j]}_price" for j in range(i)]+[f"TMP{i}.{cls}_price"],
                                  join=(f"({tmp}) AS TMP{i}", ["FlightID"]),
                                  side_join="LEFT")
    return t_cols

def get_flights_with_landing_query():
    q_join = get_select_query("Flights",
                              ["Flights.*", "DATE_ADD(Flights.TakeOffTime, INTERVAL Routes.FlightDuration MINUTE) AS LandingTime"],
                              join=("Routes", ["SourceField", "DestinationField"]))
    return q_join

def flight_status_query():
    q_count_available_seats = count_available_seats_query()
    q_count_by_flight = get_select_query(f"({q_count_available_seats}) AS FC",
                                         ["FC.FlightID","SUM(FC.AvailableSeats) AS TotalAvailableSeats"],
                                         group_by=["FC.FlightID"])
    q_joint = get_select_query("Flights",
                               ["Flights.FlightID", "Flights.TakeOffTime", "FCT.TotalAvailableSeats", "Flights.IsDeleted"],
                               join=(f"({q_count_by_flight}) AS FCT", ["FlightID"]),
                               side_join="RIGHT")
    return get_select_query(f"({q_joint}) AS FS",
                            ["FS.FlightID"],
                            cases={
                                "FS.IsDeleted=1": "'Deleted'",
                                "FS.IsDeleted=0 AND FS.TotalAvailableSeats=0": "'Full Capacity'",
                                "FS.IsDeleted=0 AND FS.TotalAvailableSeats>0 AND FS.TakeOffTime<=NOW()": "'Complete'",
                                "ELSE": "'Active'",
                                "AS": "FlightStatus"
                            })



def get_availables_query(origin_table: str,
                         pivot_column: str,
                         take_off_time: datetime,
                         landing_time: datetime,
                         source_field: str,
                         destination_field: str,
                         is_long_flight: bool):
     if (pivot_column == "PlainID" and origin_table == "Plains"):
         cond_qualify = f"{origin_table}.Size='Large'" if is_long_flight else None
         q_table = get_select_query(f"({get_flights_with_landing_query()}) AS FT",
                                    [f"FT.{pivot_column}",
                                                   "FT.FlightID",
                                                   "FT.SourceField",
                                                   "FT.DestinationField",
                                                   "FT.TakeOffTime",
                                                   "FT.LandingTime"],
                                    join=(origin_table, [pivot_column]),
                                    where=cond_qualify)
         shifts_table = "Flights"

     elif ((pivot_column=="AttendantID" and origin_table=="FlightAttendants") or
           (pivot_column == "PilotID" and origin_table=="Pilots")):
         cond_qualify = f"{origin_table}.Qualified4LongFlights" if is_long_flight else None
         w_table = get_select_query(origin_table, [f"{origin_table}.{pivot_column}","W.FlightID"],
                                    where=cond_qualify,
                                    join=(f"WorkingFlight{pivot_column.replace('ID','s')} AS W", [pivot_column]))
         q_table = get_select_query(f"({w_table}) AS Work", [f"Work.{pivot_column}",
                                                          "FT.FlightID",
                                                          "FT.SourceField",
                                                          "FT.DestinationField",
                                                          "FT.TakeOffTime",
                                                             "FT.LandingTime"],
                                    join=(f"({get_flights_with_landing_query()}) AS FT", ["FlightID"]))
         shifts_table = f"WorkingFlight{pivot_column.replace('ID','s')}"
     else:
         raise Exception("Invalid Values in origin_table and pivot_column")
     q_shift_cond = get_select_query(shifts_table, [pivot_column],
                                     where=f"{shifts_table}.{pivot_column}={origin_table}.{pivot_column}")
     q_no_flights = get_select_query(origin_table, [pivot_column],
                                     where=f"NOT EXISTS ({q_shift_cond})"+
                                           f" AND {cond_qualify}" if cond_qualify else "")
     str_landing_time = landing_time.__str__().split('.')[0]
     str_take_off_time = take_off_time.__str__().split('.')[0]
     q_max_time = get_select_query(f"({q_table}) AS MaxTime",
                                       ["MAX(MaxTime.LandingTime)"],
                                   where=f"MaxTime.{pivot_column} = AfterQ.{pivot_column}")
     q_min_time = get_select_query(f"({q_table}) AS MinTime",
                                   ["MIN(MinTime.TakeOffTime)"],
                                   where=f"MinTime.{pivot_column} = BeforeQ.{pivot_column}")
     q_before = get_select_query(f"({q_table}) AS BeforeQ",
                                 [f"BeforeQ.{pivot_column}"],
                                 where=f"(BeforeQ.TakeOffTime IS NULL OR BeforeQ.TakeOffTime > '{str_landing_time}') "
                                       f"AND (BeforeQ.SourceField IS NULL OR BeforeQ.SourceField = '{destination_field}') "
                                       f"AND BeforeQ.TakeOffTime = ({q_min_time})")
     q_after = get_select_query(f"({q_table}) AS AfterQ",
                                [f"AfterQ.{pivot_column}"],
                                where=f"(AfterQ.LandingTime IS NULL OR AfterQ.LandingTime < '{str_take_off_time}')"
                                      f"AND (AfterQ.DestinationField IS NULL OR AfterQ.DestinationField = '{source_field}') "
                                      f"AND AfterQ.LandingTime = ({q_max_time})")
     q_ans = f"(({q_before}) UNION ({q_after}) UNION ({q_no_flights})) AS Q"
     return q_ans

