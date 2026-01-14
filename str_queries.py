from sql_base import get_select_query, select
from typing import Union, Dict, List, Tuple
from datetime import datetime

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
    flights_query = get_select_query("Flights",
                                     ["FlightID", "PlainID"],
                                     join=("Class", ["PlainID"]))
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
    classes = select("Class", ["ClassType"], group_by=["ClassType"])
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

def flights_table_with_landing_query(table_query: str, columns: List[str]):
    q_join = get_select_query(f"({table_query}) AS Ftag_A",
                              join=("Routes", ["SourceField", "DestinationField"]),
                              side_join="Outer")
    q_landing = get_select_query(f"({q_join}) AS Ftag_B",
                                 columns + ["Ftag_B.TakeOffTime + Ftag_B.FlightDuration AS LandingTime"])
    return q_landing

def flight_status_query():
    q_count_available_seats = count_available_seats_query()
    q_count_by_flight = get_select_query(f"({q_count_available_seats}) AS FC",
                                         ["FlightID","SUM(AvailableSeats) AS TotalAvailableSeats"],
                                         group_by=["FlightID"])
    q_joint = get_select_query("Flights",
                               ["FlightID", "TakeOffTime"],
                               join=(f"({q_count_by_flight}) AS FCT", ["FlightID"]),
                               side_join="Right")
    return get_select_query(f"({q_joint}) AS FS",
                            ["FlightID"],
                            cases={
                                "FS.IsDeleted==1": "Deleted",
                                "FS.IsDeleted==0 AND FS.TotalAvailableSeats=0": "Occupied",
                                "FS.IsDeleted==0 AND FS.TotalAvailableSeats>0 AND FS.TakeOffTime<=NOW()": "Complete",
                                "ELSE": "Active",
                                "AS": "FlightStatus"
                            })


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
    q_landing = flights_table_with_landing_query(q_locate,
                                                 ["AttendantID", "DestinationField", "TakeOffTime"])
    return get_select_query(f"({q_landing}) AS Ftag_C",
                            where=f"LandingTime<{landing_time} OR LandingTime IS NULL")

def pilots_on_land_query(landing_time: datetime):
    q_locate = locate_pilots_query()
    q_landing = flights_table_with_landing_query(q_locate,
                                                 ["PilotID", "DestinationField", "TakeOffTime"])
    return get_select_query(f"({q_landing}) AS Ftag_C",
                            where=f"LandingTime<{landing_time} OR LandingTime IS NULL")
