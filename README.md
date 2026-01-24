# FlyTauGroup20


## Project Overview
This project implements an airline management system for the company **FLYTAU**.  
The system is designed to serve three types of users: **guests**, **registered customers**, and **administrators (company employees)**.

The system supports searching, booking, and managing flights, while also providing administrative tools for managing the airline’s operational resources.

### User Roles and Capabilities

#### Guests
- Search for available flights
- Book flights
- View our next coming flights.
- View and manage existing bookings

#### Registered Customers
- All guest capabilities
- View personal purchase and booking history

#### Administrators
Administrators are airline employees who access a dedicated management interface. They can:
- View managerial and operational reports
- Access visualizations that represent company performance and data
- Purchase additional aircraft for the company fleet
- Add pilots and flight attendants to the company workforce
- View and cancel existing flights
- Add new future flights to the system

The system is supported by a structured database and predefined operational assumptions to ensure data consistency and realistic airline behavior.

---

## Assumptions

The following assumptions were defined and applied during the design and implementation of the system:

### Booking and Flight Assumptions
1. **Single Class per Booking**  
   Each booking can include only one flight class (either Regular or Business).

2. **Aircraft Class Structure**  
   Each aircraft contains at most one Regular class and one Business class (if Business class exists).

3. **Uniform Ticket Pricing**  
   All tickets for the same flight and the same class have an identical price.

4. **Seat Availability Management** 
    Seat availability is managed per flight and per class.

5. **Booking Ownership** 
     Each booking belongs to exactly one user.

6. **Booking Time Restriction** 
     Flights cannot be booked after their scheduled departure time.

   
### Flight Route Model – Continuous Flight Lines
7. **Flight Routes Operational Model**
    The system is based on an operational model of *flight chains*, referred to as the **Continuous Flight Lines method**.

   This method ensures:
   - Logical continuity between flights
   - Reliable and consistent flight data
   - Realistic resource and fleet management

The airline operates four main continuous flight lines. 
New flights can be added **only according to the following predefined routes**: 

**Flight Routes:** 
- Amsterdam (AMS) → Frankfurt (FRA) 
- Frankfurt (FRA) → Amsterdam (AMS) 
- Athens (ATH) → Rome (FCO) 
- Rome (FCO) → Athens (ATH) 
- Athens (ATH) → Tel Aviv (TLV) 
- Tel Aviv (TLV) → Athens (ATH) 
- Barcelona (BCN) → Paris (CDG) 
- Paris (CDG) → Barcelona (BCN) 
- Barcelona (BCN) → Rome (FCO) 
- Rome (FCO) → Barcelona (BCN) 
- Paris (CDG) → Frankfurt (FRA) 
- Frankfurt (FRA) → Paris (CDG) 
- Bangkok (BKK) → Paris (CDG) 
- Paris (CDG) → Bangkok (BKK) 
- Bangkok (BKK) → Frankfurt (FRA) 
- Frankfurt (FRA) → Bangkok (BKK) 
- New York (JFK) → Tel Aviv (TLV) 
- Tel Aviv (TLV) → New York (JFK) 
- London (LHR) → Tel Aviv (TLV) 
- Tel Aviv (TLV) → London (LHR)

*Our flight routes model supports the approach that for every outward route there is also a return route..*

### User Registration and Roles Assumptions
8. **Multiple Phone Numbers per User**  
   During user registration, a new user may enter up to **10 phone numbers**.

9. **Administrator Permissions** 
    Administrators cannot perform customer actions such as booking flights.

10. **Employee Role Uniqueness** 
    Each employee has a single role only (Pilot, Flight Attendant, or Administrator).

---

## Notes
- The assumptions above were intentionally chosen to simplify system logic while maintaining realistic airline operations.
