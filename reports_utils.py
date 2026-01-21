"""
FLYTAU Reports Utilities
Management report functions for statistical analysis
"""

from sql_base import select, get_select_query
from datetime import datetime


# ============== REPORT 1: Average Flight Occupancy ==============

def get_average_occupancy_report():
    """
    Calculate average occupancy percentage for completed flights
    Returns: Dict with average_occupancy_percent
    """
    # Plane capacity subquery
    plane_capacity_query = get_select_query(
        "Class",
        ["PlainID", "SUM(NumberRows * NumberCols) AS TotalCapacity"],
        group_by=["PlainID"]
    )

    # Unified orders subquery
    customer_orders = get_select_query(
        "CustomerOrders",
        ["FlightID", "OrderStatus"]
    )
    guest_orders = get_select_query(
        "GuestOrders",
        ["FlightID", "OrderStatus"]
    )
    unified_orders = f"({customer_orders}) UNION ALL ({guest_orders})"

    # Passenger count subquery
    passenger_count_query = get_select_query(
        f"({unified_orders}) AS UnifiedOrders",
        ["FlightID", "COUNT(*) AS ActualPax"],
        where="OrderStatus = 'Complete'",
        group_by=["FlightID"]
    )

    # Main query - Join flights with capacity and passenger data
    flights_with_capacity = get_select_query(
        "Flights AS F",
        ["F.FlightID", "PlaneData.TotalCapacity", "IFNULL(PassengerData.ActualPax, 0) AS ActualPax"],
        where="F.IsDeleted = 0 AND F.TakeOffTime <= NOW()",
        join=(f"({plane_capacity_query}) AS PlaneData", ["PlainID"])
    )

    # Add passenger data with LEFT JOIN
    final_query = get_select_query(
        f"({flights_with_capacity}) AS FlightsData",
        ["ROUND(AVG((FlightsData.ActualPax / FlightsData.TotalCapacity) * 100), 2) AS Average_Occupancy_Percent"]
    )

    # Execute with passenger join manually (complex LEFT JOIN)
    full_query = f"""
        SELECT 
            ROUND(AVG((IFNULL(PassengerData.ActualPax, 0) / PlaneData.TotalCapacity) * 100), 2) 
            AS Average_Occupancy_Percent
        FROM Flights F 
        JOIN ({plane_capacity_query}) AS PlaneData ON F.PlainID = PlaneData.PlainID
        LEFT JOIN ({passenger_count_query}) AS PassengerData ON F.FlightID = PassengerData.FlightID
        WHERE F.IsDeleted = 0 AND F.TakeOffTime <= NOW()
    """

    result = select(f"({full_query}) AS OccupancyReport")
    return result[0] if result else {"Average_Occupancy_Percent": 0}


# ============== REPORT 2: Revenue by Manufacturer, Size, and Class ==============

def get_revenue_breakdown_report():
    """
    Get revenue breakdown by manufacturer, plane size, and class
    Returns: List of dicts with Manufacturer, Size, Economy_Revenue, Business_Revenue, Total_Revenue
    """
    # Unified orders from both customer and guest tables
    customer_orders_query = get_select_query(
        "CustomerOrders",
        ["PlainID", "FlightID", "ClassType", "OrderStatus"],
        where="OrderStatus NOT LIKE '%Cancelled%' OR OrderStatus = 'Customer_Cancelled'"
    )

    guest_orders_query = get_select_query(
        "GuestOrders",
        ["PlainID", "FlightID", "ClassType", "OrderStatus"],
        where="OrderStatus NOT LIKE '%Cancelled%' OR OrderStatus = 'Customer_Cancelled'"
    )

    all_orders_union = f"({customer_orders_query}) UNION ALL ({guest_orders_query})"

    # Build the revenue calculation query
    revenue_query = f"""
        SELECT P.Manufacturer, P.Size,
            SUM(CASE 
                WHEN AllOrders.ClassType = 'Economy' THEN 
                    CASE 
                        WHEN AllOrders.OrderStatus = 'Customer_Cancelled' THEN FP.Price * 0.05
                        ELSE FP.Price 
                    END
                ELSE 0 
            END) AS Economy_Safe_Revenue,

            SUM(CASE 
                WHEN AllOrders.ClassType = 'Business' THEN 
                    CASE 
                        WHEN AllOrders.OrderStatus = 'Customer_Cancelled' THEN FP.Price * 0.05
                        ELSE FP.Price 
                    END
                ELSE 0 
            END) AS Business_Safe_Revenue,

            SUM(CASE 
                WHEN AllOrders.OrderStatus = 'Customer_Cancelled' THEN FP.Price * 0.05
                ELSE FP.Price 
            END) AS Total_Safe_Revenue

        FROM ({all_orders_union}) AS AllOrders
        JOIN Flights F ON AllOrders.FlightID = F.FlightID
        JOIN Plains P ON AllOrders.PlainID = P.PlainID
        JOIN FlightPrices FP ON AllOrders.FlightID = FP.FlightID 
                             AND AllOrders.ClassType = FP.ClassType
                             AND AllOrders.PlainID = FP.PlainID
        WHERE 
            F.IsDeleted = 0 
            AND 
            F.TakeOffTime <= DATE_ADD(NOW(), INTERVAL 36 HOUR)
        GROUP BY 
            P.Manufacturer, 
            P.Size
        ORDER BY 
            Total_Safe_Revenue DESC
    """

    return select(f"({revenue_query}) AS RevenueReport")


# ============== REPORT 3: Employee Work Hours ==============

def get_employee_hours_report():
    """
    Get cumulative flight hours for all employees (pilots and attendants)
    Separated by short/long flights
    Returns: List of dicts with Role, EmployeeID, Name, Short_Hours, Long_Hours, Total_Hours
    """
    # Pilots with their flights
    pilots_query = get_select_query(
        "Pilots AS P",
        ["'Pilot' AS RoleType", "P.PilotID AS EmployeeID", "P.FirstName", "P.LastName", "WFP.FlightID"],
        join=("WorkingFlightPilots AS WFP", ["PilotID"])
    )

    # Flight attendants with their flights
    attendants_query = get_select_query(
        "FlightAttendants AS FA",
        ["'Flight Attendant' AS RoleType", "FA.AttendantID AS EmployeeID", "FA.FirstName", "FA.LastName",
         "WFA.FlightID"],
        join=("WorkingFlightAttendants AS WFA", ["AttendantID"])
    )

    # Union of all crew
    all_crew_union = f"({pilots_query}) UNION ALL ({attendants_query})"

    # Full query with hours calculation
    hours_query = f"""
        SELECT 
            RoleType AS Role, 
            EmployeeID,
            FirstName,
            LastName,
            ROUND(SUM(CASE 
                WHEN TIME_TO_SEC(R.FlightDuration) / 3600.0 <= 6 THEN
                    TIME_TO_SEC(R.FlightDuration) / 3600.0
                ELSE 0 
            END), 2) AS Short_Flight_Hours,
            ROUND(SUM(CASE 
                WHEN TIME_TO_SEC(R.FlightDuration) / 3600.0 > 6 THEN
                    TIME_TO_SEC(R.FlightDuration) / 3600.0
                ELSE 0 
            END), 2) AS Long_Flight_Hours,
            ROUND(SUM(TIME_TO_SEC(R.FlightDuration) / 3600.0), 2) AS Total_Hours

        FROM ({all_crew_union}) AS AllCrew
        JOIN Flights F ON AllCrew.FlightID = F.FlightID
        JOIN Routes R ON F.SourceField = R.SourceField AND F.DestinationField = R.DestinationField
        WHERE 
            F.IsDeleted = 0
            AND 
            F.TakeOffTime <= NOW()
        GROUP BY 
            RoleType, 
            EmployeeID, 
            FirstName, 
            LastName
        ORDER BY 
            Total_Hours DESC
    """

    return select(f"({hours_query}) AS EmployeeHoursReport")


# ============== REPORT 4: Monthly Cancellation Rate ==============

def get_cancellation_rate_report():
    """
    Get monthly cancellation rate statistics
    Returns: List of dicts with Order_Month, Total_Orders, Cancelled_Orders, Cancellation_Rate_Percent
    """
    # Customer orders
    customer_orders_query = get_select_query(
        "CustomerOrders",
        ["OrderDate", "OrderStatus"]
    )

    # Guest orders
    guest_orders_query = get_select_query(
        "GuestOrders",
        ["OrderDate", "OrderStatus"]
    )

    # Union of all orders
    all_orders_union = f"({customer_orders_query}) UNION ALL ({guest_orders_query})"

    # Cancellation rate calculation
    cancellation_query = f"""
        SELECT 
            DATE_FORMAT(OrderDate, '%Y-%m') AS Order_Month, 
            COUNT(*) AS Total_Orders, 
            SUM(CASE 
                WHEN OrderStatus = 'Customer_Cancelled' THEN 1 
                ELSE 0 
            END) AS Cancelled_Orders,
            ROUND((SUM(CASE WHEN OrderStatus = 'Customer_Cancelled' THEN 1 ELSE 0 END) / 
                   COUNT(*)) * 100, 2) AS Cancellation_Rate_Percent
        FROM ({all_orders_union}) AS AllOrders
        GROUP BY 
            DATE_FORMAT(OrderDate, '%Y-%m') 
        ORDER BY 
            Order_Month ASC
    """

    return select(f"({cancellation_query}) AS CancellationReport")


# ============== REPORT 5: Monthly Plane Activity ==============

def get_plane_activity_report():
    """
    Get monthly activity summary for each plane
    Returns: List of dicts with Manufacturer, PlainID, Activity_Month,
             Executed_Flights, Cancelled_Flights, Utilization_Percent, Dominant_Route
    """
    # This query uses CTE (WITH clause) which needs raw SQL
    activity_query = """
        WITH RouteRankings AS (
            SELECT 
                PlainID,
                DATE_FORMAT(TakeOffTime, '%Y-%m') AS MonthID,
                CONCAT(SourceField, ' - ', DestinationField) AS RoutePair,
                ROW_NUMBER() OVER (
                    PARTITION BY PlainID, DATE_FORMAT(TakeOffTime, '%Y-%m') 
                    ORDER BY COUNT(*) DESC
                ) AS rn
            FROM Flights
            WHERE IsDeleted = 0
            GROUP BY PlainID, MonthID, RoutePair
        )
        SELECT 
            P.Manufacturer,
            F.PlainID,
            DATE_FORMAT(F.TakeOffTime, '%Y-%m') AS Activity_Month,

            SUM(CASE WHEN F.IsDeleted = 0 THEN 1 ELSE 0 END) AS Executed_Flights,

            SUM(CASE WHEN F.IsDeleted = 1 THEN 1 ELSE 0 END) AS Cancelled_Flights,

            ROUND(
                (COUNT(DISTINCT CASE WHEN F.IsDeleted = 0 THEN DATE(F.TakeOffTime) END) /
                 30.0) * 100, 2
            ) AS Utilization_Percent,

            MAX(RR.RoutePair) AS Dominant_Route

        FROM Flights F
        JOIN Plains P ON F.PlainID = P.PlainID
        LEFT JOIN RouteRankings RR ON F.PlainID = RR.PlainID 
                                   AND DATE_FORMAT(F.TakeOffTime, '%Y-%m') = RR.MonthID
                                   AND RR.rn = 1
        GROUP BY 
            P.Manufacturer, 
            F.PlainID, 
            Activity_Month
        ORDER BY 
            F.PlainID, Activity_Month
    """

    return select(f"({activity_query}) AS PlaneActivityReport")


# ============== SUMMARY REPORT FOR DASHBOARD ==============

def get_summary_statistics():
    """
    Get quick summary statistics for dashboard overview
    Returns: Dict with key metrics
    """
    # Total flights
    total_flights_query = get_select_query(
        "Flights",
        ["COUNT(*) AS total"],
        where="IsDeleted = 0"
    )
    total_flights = select(f"({total_flights_query}) AS TF")[0]['total']

    # Active customer orders
    active_customer_query = get_select_query(
        "CustomerOrders",
        ["OrderID"],
        where="OrderStatus = 'Active'"
    )

    # Active guest orders
    active_guest_query = get_select_query(
        "GuestOrders",
        ["OrderID"],
        where="OrderStatus = 'Active'"
    )

    # Union and count
    active_union = f"({active_customer_query}) UNION ALL ({active_guest_query})"
    active_count_query = f"SELECT COUNT(*) AS total FROM ({active_union}) AS ActiveOrders"
    active_orders = select(f"({active_count_query}) AS AO")[0]['total']

    # Total revenue - unified orders for revenue calculation
    customer_rev_query = get_select_query(
        "CustomerOrders",
        ["PlainID", "FlightID", "ClassType", "OrderStatus"],
        where="OrderStatus NOT LIKE '%System%'"
    )

    guest_rev_query = get_select_query(
        "GuestOrders",
        ["PlainID", "FlightID", "ClassType", "OrderStatus"],
        where="OrderStatus NOT LIKE '%System%'"
    )

    all_orders_rev = f"({customer_rev_query}) UNION ALL ({guest_rev_query})"

    revenue_query = f"""
        SELECT 
            SUM(CASE 
                WHEN AllOrders.OrderStatus = 'Customer_Cancelled' THEN FP.Price * 0.05
                ELSE FP.Price 
            END) AS Total_Revenue
        FROM ({all_orders_rev}) AS AllOrders
        JOIN FlightPrices FP ON AllOrders.FlightID = FP.FlightID 
                             AND AllOrders.ClassType = FP.ClassType
                             AND AllOrders.PlainID = FP.PlainID
    """

    revenue_result = select(f"({revenue_query}) AS Rev")
    total_revenue = revenue_result[0]['Total_Revenue'] if revenue_result and revenue_result[0]['Total_Revenue'] else 0

    # Fleet size
    fleet_query = get_select_query(
        "Plains",
        ["COUNT(*) AS total"]
    )
    fleet_size = select(f"({fleet_query}) AS Fleet")[0]['total']

    return {
        'total_flights': total_flights,
        'active_orders': active_orders,
        'total_revenue': float(total_revenue),
        'fleet_size': fleet_size
    }