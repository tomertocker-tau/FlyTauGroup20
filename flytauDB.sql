CREATE SCHEMA IF NOT EXISTS FLYTAU;
USE FLYTAU;
CREATE TABLE IF NOT EXISTS Managers (
	ManagerID INT NOT NULL UNIQUE,
    FirstName VARCHAR(45) NOT NULL,
    LastName VARCHAR(45) NOT NULL,
    Phone VARCHAR(45),
    City VARCHAR(45),
    Street VARCHAR(45),
    HomeNumber INT,
    JobStartDay DATE NOT NULL,
    Email VARCHAR(45) NOT NULL,
    UserPassword VARCHAR(45) NOT NULL,
    PRIMARY KEY(ManagerID)
);

CREATE TABLE IF NOT EXISTS Pilots (
	PilotID INT NOT NULL UNIQUE,
    FirstName VARCHAR(45) NOT NULL,
    LastName VARCHAR(45) NOT NULL,
    Phone VARCHAR(45),
    City VARCHAR(45),
    Street VARCHAR(45),
    HomeNumber INT,
    JobStartDay DATE NOT NULL,
    Qualified4LongFlights BINARY NOT NULL,
    PRIMARY KEY(PilotID)
);

CREATE TABLE IF NOT EXISTS FlightAttendants (
	AttendantID INT NOT NULL UNIQUE,
    FirstName VARCHAR(45) NOT NULL,
    LastName VARCHAR(45) NOT NULL,
    Phone VARCHAR(45),
    City VARCHAR(45),
    Street VARCHAR(45),
    HomeNumber INT,
    JobStartDay DATE NOT NULL,
    Qualified4LongFlights BINARY NOT NULL,
    PRIMARY KEY(AttendantID)
);

CREATE TABLE IF NOT EXISTS Guests(
	Email VARCHAR(45) NOT NULL UNIQUE,
    EngFirstName VARCHAR(45) NOT NULL,
    EngLastName VARCHAR(45) NOT NULL,
    PRIMARY KEY(Email)
);

CREATE TABLE IF NOT EXISTS Customers(
	Email VARCHAR(45) NOT NULL UNIQUE,
    EngFirstName VARCHAR(45) NOT NULL,
    EngLastName VARCHAR(45) NOT NULL,
    PassportNumber INT NOT NULL,
    Birthdate DATE,
    SignUpDate DATE NOT NULL,
    UserPassword VARCHAR(45) NOT NULL,
    PRIMARY KEY(Email)
);

CREATE TABLE IF NOT EXISTS GuestsPhoneNumbers(
	Email VARCHAR(45) NOT NULL,
    Phone VARCHAR(45) NOT NULL,
    FOREIGN KEY(Email) REFERENCES Guests(Email),
    PRIMARY KEY(Email, Phone)
);


CREATE TABLE IF NOT EXISTS CustomersPhoneNumbers(
	Email VARCHAR(45) NOT NULL,
    Phone VARCHAR(45) NOT NULL,
    FOREIGN KEY(Email) REFERENCES Customers(Email),
    PRIMARY KEY(Email, Phone)
);

CREATE TABLE IF NOT EXISTS Plains(
	PlainID INT NOT NULL UNIQUE,
    Manufacturer VARCHAR(45) NOT NULL,
    Size VARCHAR(45) NOT NULL,
    PurchaseDate DATE NOT NULL,
    PRIMARY KEY(PlainID)
);

CREATE TABLE IF NOT EXISTS Class(
	ClassType VARCHAR(45) NOT NULL,
    PlainID INT NOT NULL,
    NumberRows INT NOT NULL,
    NumberCols INT NOT NULL,
    FOREIGN KEY(PlainID) REFERENCES Plains(PlainID),
    PRIMARY KEY(ClassType, PlainID)
);


CREATE TABLE IF NOT EXISTS Routes(
	SourceField VARCHAR(45) NOT NULL,
    DestinationField VARCHAR(45) NOT NULL,
    FlightDuration TIME NOT NULL,
    PRIMARY KEY(SourceField, DestinationField)
);

CREATE TABLE IF NOT EXISTS Flights(
	FlightID INT NOT NULL UNIQUE,
    PlainID INT NOT NULL,
    TakeOffTime DATETIME NOT NULL,
    SourceField VARCHAR(45) NOT NULL,
    DestinationField VARCHAR(45) NOT NULL,
    IsDeleted BINARY NOT NULL DEFAULT 0,
    FOREIGN KEY(SourceField, DestinationField) REFERENCES Routes(SourceField, DestinationField),
    FOREIGN KEY(PlainID) REFERENCES Plains(PlainID),
    PRIMARY KEY(FlightID)
);

CREATE TABLE IF NOT EXISTS FlightPrices(
	ClassType VARCHAR(45) NOT NULL,
    FlightID INT NOT NULL,
    PlainID INT NOT NULL,
    Price DOUBLE NOT NULL,
    FOREIGN KEY(ClassType, PlainID) REFERENCES Class(ClassType, PlainID),
    FOREIGN KEY(FlightID) REFERENCES Flights(FlightID),
    PRIMARY KEY(ClassType, FlightID, PlainID)
);

CREATE TABLE IF NOT EXISTS CustomerOrders(
	OrderID INT NOT NULL UNIQUE,
    OrderStatus VARCHAR(45) NOT NULL,
    OrderDate DATE NOT NULL,
    Email VARCHAR(45) NOT NULL,
    PlainID INT NOT NULL,
    ClassType VARCHAR(45) NOT NULL,
    FlightID INT NOT NULL,
    FOREIGN KEY(ClassType, PlainID, FlightID) REFERENCES FlightPrices(ClassType, PlainID, FlightID),
    FOREIGN KEY(Email) REFERENCES Customers(Email),
    PRIMARY KEY(OrderID)
);

CREATE TABLE IF NOT EXISTS SelectedSeatsCustomerOrders(
	OrderID INT NOT NULL,
    Line INT NOT NULL,
    SeatLetter INT NOT NULL,
    FOREIGN KEY(OrderID) REFERENCES CustomerOrders(OrderID),
    PRIMARY KEY(OrderID,Line,SeatLetter)
 );

 CREATE TABLE IF NOT EXISTS GuestOrders(
 	OrderID INT NOT NULL UNIQUE,
    OrderStatus VARCHAR(45) NOT NULL,
    OrderDate DATE NOT NULL,
    Email VARCHAR(45) NOT NULL,
    PlainID INT NOT NULL,
    ClassType VARCHAR(45) NOT NULL,
    FlightID INT NOT NULL,
    FOREIGN KEY(ClassType, PlainID, FlightID) REFERENCES FlightPrices(ClassType, PlainID, FlightID),
    PRIMARY KEY(OrderID)
);


CREATE TABLE IF NOT EXISTS SelectedSeatsGuestOrders(
	OrderID INT NOT NULL,
    Line INT NOT NULL,
    SeatLetter INT NOT NULL,
    FOREIGN KEY(OrderID) REFERENCES GuestOrders(OrderID),
    PRIMARY KEY(OrderID,Line,SeatLetter)
 );

 CREATE TABLE IF NOT EXISTS WorkingFlightAttendants(
	AttendantID INT NOT NULL,
	FlightID INT NOT NULL,
    FOREIGN KEY(AttendantID) REFERENCES FlightAttendants(AttendantID),
    FOREIGN KEY(FlightID) REFERENCES Flights(FlightID),
    PRIMARY KEY(AttendantID,FlightID)
);

 CREATE TABLE IF NOT EXISTS WorkingFlightPilots(
	PilotID INT NOT NULL,
	FlightID INT NOT NULL,
    FOREIGN KEY(PilotID) REFERENCES Pilots(PilotID),
    FOREIGN KEY(FlightID) REFERENCES Flights(FlightID),
    PRIMARY KEY(PilotID,FlightID)
);


---------------------------------------------------
-- Managers
---------------------------------------------------
INSERT INTO Managers
(ManagerID, FirstName, LastName, Phone, City, Street, HomeNumber, JobStartDay, Email, UserPassword)
VALUES
(1001,'Dana','Cohen','050-1111111','Tel Aviv','Herzl',10,'2018-03-01','dana.cohen@flytau.com','mng1001'),
(1002,'Avi','Levi','050-1112222','Ramat Gan','Jabotinsky',5,'2019-06-15','avi.levi@flytau.com','mng1002'),
(1003,'Noa','Bar','052-3334444','Haifa','Hillel',12,'2020-01-01','noa.bar@flytau.com','mng1003'),
(1004,'Ron','Katz','052-5556666','Jerusalem','KingGeorge',7,'2017-09-10','ron.katz@flytau.com','mng1004'),
(1005,'Lior','Peretz','053-7778888','Beer Sheva','DerechHebron',22,'2021-04-20','lior.peretz@flytau.com','mng1005'),
(1006,'Tal','Shani','054-9990000','Netanya','Weizmann',3,'2016-11-05','tal.shani@flytau.com','mng1006'),
(1007,'Yael','Rosen','055-1234567','Holon','Sokolov',9,'2015-02-14','yael.rosen@flytau.com','mng1007'),
(1008,'Eitan','Mizrahi','052-7654321','Ashdod','Begin',18,'2022-08-01','eitan.mizrahi@flytau.com','mng1008'),
(1009,'Maya','Golan','050-2468101','Kfar Saba','Rothschild',4,'2020-10-10','maya.golan@flytau.com','mng1009'),
(1010,'Omer','Halevi','050-1357913','Rehovot','Herzl',6,'2019-12-31','omer.halevi@flytau.com','mng1010');

---------------------------------------------------
-- Pilots
---------------------------------------------------
INSERT INTO Pilots
(PilotID, FirstName, LastName, Phone, City, Street, HomeNumber, JobStartDay, Qualified4LongFlights)
VALUES
(2001,'Yossi','Ben Ami','050-2001001','Tel Aviv','Dizengoff',20,'2015-01-01',1),
(2002,'Gil','Ashkenazi','050-2001002','Herzliya','Hatzmaut',11,'2016-03-12',1),
(2003,'Nir','Koren','050-2001003','Haifa','Allenby',8,'2017-05-23',0),
(2004,'Ido','Sharabi','050-2001004','Jerusalem','Jaffa',15,'2018-07-30',1),
(2005,'Roni','Dahan','050-2001005','Rishon LeZion','Weizmann',19,'2019-09-09',0),
(2006,'Hadar','Sela','050-2001006','Ashkelon','Herzl',7,'2020-11-18',1),
(2007,'Bar','Shahar','050-2001007','Netanya','Smilansky',5,'2021-02-02',0),
(2008,'Roy','Carmi','050-2001008','Lod','HaShalom',3,'2014-06-06',1),
(2009,'Shir','Yaakov','050-2001009','Holon','Golda',9,'2013-10-10',1),
(2010,'Amit','Levi','050-2001010','Tel Aviv','Ibn Gabirol',12,'2016-04-14',1),
(2011,'Daniel','Mor','050-2001011','Petah Tikva','Rothschild',6,'2017-08-21',0),
(2012,'Eyal','Peretz','050-2001012','Beer Sheva','Ben Gurion',18,'2015-12-03',1),
(2013,'Noam','Friedman','050-2001013','Ramat Gan','Bialik',10,'2018-01-17',0),
(2014,'Itay','Cohen','050-2001014','Givatayim','Katznelson',4,'2019-06-25',1),
(2015,'Lior','Mizrahi','050-2001015','Kfar Saba','Weizmann',22,'2020-09-13',0),
(2016,'Sharon','Biton','050-2001016','Nahariya','Gaash',9,'2014-02-11',1),
(2017,'Omer','Raz','050-2001017','Modiin','HaPalmach',14,'2021-05-05',0),
(2018,'Tal','Aviv','050-2001018','Rehovot','Herzl',16,'2013-11-19',1);


---------------------------------------------------
-- FlightAttendants
---------------------------------------------------
INSERT INTO FlightAttendants
(AttendantID, FirstName, LastName, Phone, City, Street, HomeNumber, JobStartDay, Qualified4LongFlights)
VALUES
(3001,'Linoy','Mor','052-3001001','Tel Aviv','Nordau',2,'2020-01-01',1),
(3002,'Hila','Ben Ari','052-3001002','Ramat Gan','Krinitzi',14,'2019-03-10',0),
(3003,'Adi','Gur','052-3001003','Haifa','Hagiborim',6,'2018-05-22',1),
(3004,'Sivan','Tal','052-3001004','Ashdod','Herzl',16,'2017-07-01',0),
(3005,'Liad','Or','052-3001005','Holon','Sokolov',24,'2021-09-09',1),
(3006,'Yaara','Bitan','052-3001006','Herzliya','HaSela',3,'2022-02-15',0),
(3007,'Nofar','Regev','052-3001007','Beer Sheva','Rager',9,'2016-11-11',1),
(3008,'Shani','Malka','052-3001008','Kiryat Ono','Alon',5,'2015-04-04',1),
(3009,'Talya','Moreno','052-3001009','Rehovot','Even Gvirol',7,'2018-08-18',0),
(3010,'Nitzan','Erez','052-3001010','Modiin','Hashmonaim',10,'2019-12-12',1),
(3011,'Gal','Rom','052-3001011','Tel Aviv','Gordon',11,'2020-06-01',0),
(3012,'Odelia','Azoulay','052-3001012','Netanya','Ussishkin',18,'2017-01-20',1),
(3013,'Coral','Aviv','052-3001013','Haifa','HaPalmach',4,'2016-03-03',0),
(3014,'Bar','Sharvit','052-3001014','Ashkelon','Herzl',19,'2015-05-15',1),
(3015,'Inbar','Navon','052-3001015','Jerusalem','Haneviim',21,'2018-07-07',0),
(3016,'Tamar','Oz','052-3001016','Rishon LeZion','Herzl',25,'2019-09-19',1),
(3017,'Hadar','Yaron','052-3001017','Raanana','Ahuza',6,'2020-10-10',1),
(3018,'Noam','Fein','052-3001018','Petah Tikva','Bar Kochva',8,'2021-11-11',0),
(3019,'Lia','Romano','052-3001019','Holon','Sderot Yerushalayim',12,'2016-12-24',1),
(3020,'Dana','Mashali','052-3001020','Bat Yam','Ben Gurion',5,'2014-02-02',1),
(3021,'Maya','Levin','052-3001021','Tel Aviv','Ben Yehuda',13,'2021-01-05',1),
(3022,'Rotem','Katz','052-3001022','Givatayim','Borochov',7,'2020-04-18',0),
(3023,'Shaked','Alon','052-3001023','Haifa','Moriah',21,'2019-06-30',1),
(3024,'Yael','Sharon','052-3001024','Ramat Hasharon','Sokolov',9,'2018-10-10',0),
(3025,'Michal','Baron','052-3001025','Kfar Saba','Weizmann',16,'2022-03-03',1),
(3026,'Eden','Nachum','052-3001026','Ashdod','HaAtzmaut',4,'2021-07-07',0),
(3027,'Talia','Peretz','052-3001027','Beer Sheva','Ben Zvi',11,'2017-09-14',1),
(3028,'Rina','Halevi','052-3001028','Nahariya','Gaaton',19,'2016-02-22',1),
(3029,'Yuval','Gross','052-3001029','Hod Hasharon','HaRav Kook',6,'2019-11-11',0),
(3030,'Ofir','Maman','052-3001030','Yavne','HaPalmach',15,'2015-05-05',1);

---------------------------------------------------
-- Guests
---------------------------------------------------
INSERT INTO Guests (Email, EngFirstName, EngLastName)
VALUES
('guest1@example.com','Adam','Stone'),
('guest2@example.com','Emily','Clark'),
('guest3@example.com','David','Miller'),
('guest4@example.com','Sarah','King'),
('guest5@example.com','Michael','Green'),
('guest6@example.com','Julia','Parker'),
('guest7@example.com','Daniel','Roberts'),
('guest8@example.com','Olivia','Turner'),
('guest9@example.com','Liam','White'),
('guest10@example.com','Sophia','Adams');

---------------------------------------------------
-- Customers
---------------------------------------------------
INSERT INTO Customers
(Email, EngFirstName, EngLastName, PassportNumber, Birthdate, SignUpDate, UserPassword)
VALUES
('cust1@example.com','John','Doe',12345678,'1988-01-01','2022-01-10','cpass1'),
('cust2@example.com','Anna','Smith',23456789,'1990-02-02','2022-03-15','cpass2'),
('cust3@example.com','Mark','Brown',34567890,'1985-03-03','2021-11-05','cpass3'),
('cust4@example.com','Linda','Taylor',45678901,'1992-04-04','2023-02-20','cpass4'),
('cust5@example.com','Peter','Wilson',56789012,'1994-05-05','2021-09-09','cpass5'),
('cust6@example.com','Karen','Moore',67890123,'1987-06-06','2020-12-12','cpass6'),
('cust7@example.com','Jason','Hall',78901234,'1993-07-07','2022-07-07','cpass7'),
('cust8@example.com','Rachel','Lee',89012345,'1991-08-08','2023-04-01','cpass8'),
('cust9@example.com','Tom','Scott',90123456,'1989-09-09','2022-09-30','cpass9'),
('cust10@example.com','Bella','Evans',11223344,'1995-10-10','2023-01-01','cpass10');

---------------------------------------------------
-- GuestsPhoneNumbers
---------------------------------------------------
INSERT INTO GuestsPhoneNumbers (Email, Phone)
VALUES
('guest1@example.com','050-4001001'),
('guest2@example.com','050-4001002'),
('guest3@example.com','050-4001003'),
('guest4@example.com','050-4001004'),
('guest5@example.com','050-4001005'),
('guest6@example.com','050-4001006'),
('guest7@example.com','050-4001007'),
('guest8@example.com','050-4001008'),
('guest9@example.com','050-4001009'),
('guest10@example.com','050-4001010');

---------------------------------------------------
-- CustomersPhoneNumbers
---------------------------------------------------
INSERT INTO CustomersPhoneNumbers (Email, Phone)
VALUES
('cust1@example.com','052-5001001'),
('cust2@example.com','052-5001002'),
('cust3@example.com','052-5001003'),
('cust4@example.com','052-5001004'),
('cust5@example.com','052-5001005'),
('cust6@example.com','052-5001006'),
('cust7@example.com','052-5001007'),
('cust8@example.com','052-5001008'),
('cust9@example.com','052-5001009'),
('cust10@example.com','052-5001010');

---------------------------------------------------
-- Plains
---------------------------------------------------
INSERT INTO Plains
(PlainID, Manufacturer, Size, PurchaseDate)
VALUES
(1,'Boeing','Large','2015-05-01'),
(2,'Airbus','Large','2016-07-15'),
(3,'Dassault','Large','2017-09-20'),
(4,'Boeing','Large','2018-11-11'),
(5,'Airbus','Large','2019-01-05'),
(6,'Boeing','Small','2020-03-03'),
(7,'Airbus','Small','2021-04-04'),
(8,'Dassault','Small','2022-06-06'),
(9,'Boeing','Small','2023-02-02'),
(10,'Airbus','Small','2023-07-07');

---------------------------------------------------
-- Class
---------------------------------------------------
INSERT INTO Class
(ClassType, PlainID, NumberRows, NumberCols)
VALUES
('Regular',1,32,6),
('Business',1,10,4),
('Regular',2,34,6),
('Business',2,12,4),
('Regular',3,30,6),
('Business',3,10,4),
('Regular',4,30,6),
('Business',4,8,4),
('Regular',5,28,6),
('Business',5,8,4),
('Regular',6,22,6),
('Regular',7,20,6),
('Regular',8,18,6),
('Regular',9,20,6),
('Regular',10,18,6);

---------------------------------------------------
-- Routes
-- מעודכן: נתיבים לכל כיוון כדי לאפשר חזרה
---------------------------------------------------
INSERT INTO Routes
(SourceField, DestinationField, FlightDuration)
VALUES

-- TLV
('TLV - Tel Aviv','LHR - London','05:05:00'),
('TLV - Tel Aviv','ATH - Athens','02:10:00'),
('TLV - Tel Aviv','CDG - Paris','02:00:00'),
('TLV - Tel Aviv','BCN - Barcelona','02:00:00'),
('TLV - Tel Aviv','FCO - Rome','02:00:00'),
('TLV - Tel Aviv','AMS - Amsterdam','02:00:00'),
('TLV - Tel Aviv','FRA - Frankfurt','02:00:00'),
('TLV - Tel Aviv','BKK - Bangkok','11:00:00'),
('TLV - Tel Aviv','JFK - New York','11:00:00'),

-- LHR
('LHR - London','TLV - Tel Aviv','04:55:00'),
('LHR - London','ATH - Athens','02:00:00'),
('LHR - London','CDG - Paris','02:00:00'),
('LHR - London','BCN - Barcelona','02:00:00'),
('LHR - London','FCO - Rome','02:00:00'),
('LHR - London','AMS - Amsterdam','02:00:00'),
('LHR - London','FRA - Frankfurt','02:00:00'),
('LHR - London','BKK - Bangkok','02:00:00'),
('LHR - London','JFK - New York','02:00:00'),

-- ATH
('ATH - Athens','TLV - Tel Aviv','02:15:00'),
('ATH - Athens','LHR - London','02:00:00'),
('ATH - Athens','CDG - Paris','02:00:00'),
('ATH - Athens','BCN - Barcelona','02:00:00'),
('ATH - Athens','FCO - Rome','02:10:00'),
('ATH - Athens','AMS - Amsterdam','02:00:00'),
('ATH - Athens','FRA - Frankfurt','02:00:00'),
('ATH - Athens','BKK - Bangkok','02:00:00'),
('ATH - Athens','JFK - New York','02:00:00'),

-- CDG
('CDG - Paris','TLV - Tel Aviv','02:00:00'),
('CDG - Paris','LHR - London','02:00:00'),
('CDG - Paris','ATH - Athens','02:00:00'),
('CDG - Paris','BCN - Barcelona','01:50:00'),
('CDG - Paris','FCO - Rome','02:00:00'),
('CDG - Paris','AMS - Amsterdam','02:00:00'),
('CDG - Paris','FRA - Frankfurt','01:10:00'),
('CDG - Paris','BKK - Bangkok','11:30:00'),
('CDG - Paris','JFK - New York','02:00:00'),

-- BCN
('BCN - Barcelona','TLV - Tel Aviv','02:00:00'),
('BCN - Barcelona','LHR - London','02:00:00'),
('BCN - Barcelona','ATH - Athens','02:00:00'),
('BCN - Barcelona','CDG - Paris','01:50:00'),
('BCN - Barcelona','FCO - Rome','01:45:00'),
('BCN - Barcelona','AMS - Amsterdam','02:00:00'),
('BCN - Barcelona','FRA - Frankfurt','02:00:00'),
('BCN - Barcelona','BKK - Bangkok','02:00:00'),
('BCN - Barcelona','JFK - New York','02:00:00'),

-- FCO
('FCO - Rome','TLV - Tel Aviv','02:00:00'),
('FCO - Rome','LHR - London','02:00:00'),
('FCO - Rome','ATH - Athens','02:00:00'),
('FCO - Rome','CDG - Paris','02:00:00'),
('FCO - Rome','BCN - Barcelona','01:45:00'),
('FCO - Rome','AMS - Amsterdam','02:00:00'),
('FCO - Rome','FRA - Frankfurt','02:00:00'),
('FCO - Rome','BKK - Bangkok','02:00:00'),
('FCO - Rome','JFK - New York','02:00:00'),

-- AMS
('AMS - Amsterdam','TLV - Tel Aviv','02:00:00'),
('AMS - Amsterdam','LHR - London','02:00:00'),
('AMS - Amsterdam','ATH - Athens','02:00:00'),
('AMS - Amsterdam','CDG - Paris','02:00:00'),
('AMS - Amsterdam','BCN - Barcelona','02:00:00'),
('AMS - Amsterdam','FCO - Rome','02:00:00'),
('AMS - Amsterdam','FRA - Frankfurt','01:20:00'),
('AMS - Amsterdam','BKK - Bangkok','02:00:00'),
('AMS - Amsterdam','JFK - New York','02:00:00'),

-- FRA
('FRA - Frankfurt','TLV - Tel Aviv','02:00:00'),
('FRA - Frankfurt','LHR - London','02:00:00'),
('FRA - Frankfurt','ATH - Athens','02:00:00'),
('FRA - Frankfurt','CDG - Paris','01:15:00'),
('FRA - Frankfurt','BCN - Barcelona','02:00:00'),
('FRA - Frankfurt','FCO - Rome','02:00:00'),
('FRA - Frankfurt','AMS - Amsterdam','01:25:00'),
('FRA - Frankfurt','BKK - Bangkok','10:20:00'),
('FRA - Frankfurt','JFK - New York','02:00:00'),

-- BKK
('BKK - Bangkok','TLV - Tel Aviv','10:45:00'),
('BKK - Bangkok','LHR - London','02:00:00'),
('BKK - Bangkok','ATH - Athens','02:00:00'),
('BKK - Bangkok','CDG - Paris','12:00:00'),
('BKK - Bangkok','BCN - Barcelona','02:00:00'),
('BKK - Bangkok','FCO - Rome','02:00:00'),
('BKK - Bangkok','AMS - Amsterdam','02:00:00'),
('BKK - Bangkok','FRA - Frankfurt','10:40:00'),
('BKK - Bangkok','JFK - New York','02:00:00'),

-- JFK
('JFK - New York','TLV - Tel Aviv','10:45:00'),
('JFK - New York','LHR - London','02:00:00'),
('JFK - New York','ATH - Athens','02:00:00'),
('JFK - New York','CDG - Paris','02:00:00'),
('JFK - New York','BCN - Barcelona','02:00:00'),
('JFK - New York','FCO - Rome','02:00:00'),
('JFK - New York','AMS - Amsterdam','02:00:00'),
('JFK - New York','FRA - Frankfurt','02:00:00'),
('JFK - New York','BKK - Bangkok','02:00:00');


---------------------------------------------------
-- Flights
-- מעודכן: שרשראות טיסה סגורות (חוזרות לנקודת ההתחלה)
---------------------------------------------------
INSERT INTO Flights
(FlightID, PlainID, TakeOffTime, SourceField, DestinationField, IsDeleted)
VALUES
-- Original Flights (1-12) Updated with new City Names
(1,1,'2025-02-10 08:00:00','TLV - Tel Aviv','LHR - London',0),
(2,2,'2025-02-10 12:00:00','TLV - Tel Aviv','ATH - Athens',0),
(3,3,'2026-02-11 06:30:00','CDG - Paris','BCN - Barcelona',0),
(4,4,'2026-02-11 14:15:00','CDG - Paris','BKK - Bangkok',0),
(5,5,'2027-02-12 09:45:00','TLV - Tel Aviv','JFK - New York',0),
(6,1,'2025-02-12 22:00:00','BKK - Bangkok','CDG - Paris',1), -- Note: Logic kept as requested (Deleted)
(7,2,'2025-02-13 07:20:00','JFK - New York','TLV - Tel Aviv',0),
(8,6,'2025-02-13 23:55:00','AMS - Amsterdam','FRA - Frankfurt',0), -- Chain 3 Start
(9,7,'2026-02-14 13:10:00','BCN - Barcelona','FCO - Rome',0),
(10,8,'2026-02-14 16:40:00','FRA - Frankfurt','CDG - Paris',1), -- Note: IsDeleted=1
(11,9,'2027-02-15 09:00:00','LHR - London','TLV - Tel Aviv',0), -- Chain 4 Start
(12,10,'2025-02-15 18:00:00','TLV - Tel Aviv','LHR - London',0),

-- Chain 1: Plane 1 (Large) | TLV (Home)
-- Route: TLV -> LHR -> TLV -> JFK -> TLV
(20, 1, '2025-02-12 10:00:00', 'LHR - London', 'TLV - Tel Aviv', 0),
(21, 1, '2025-02-15 06:00:00', 'TLV - Tel Aviv', 'JFK - New York', 0),
(22, 1, '2025-02-17 14:00:00', 'JFK - New York', 'TLV - Tel Aviv', 0),
(23, 1, '2027-03-01 08:00:00', 'TLV - Tel Aviv', 'LHR - London', 0),

-- Chain 2: Plane 4 (Large) | CDG (Home)
-- Route: CDG -> BKK -> CDG -> BCN -> CDG
(24, 4, '2026-02-14 10:00:00', 'BKK - Bangkok', 'CDG - Paris', 0),
(25, 4, '2026-02-18 09:00:00', 'CDG - Paris', 'BCN - Barcelona', 0),
(26, 4, '2026-02-19 12:00:00', 'BCN - Barcelona', 'CDG - Paris', 0), -- Return to Base

-- Chain 3: Plane 6 (Small) | AMS (Home) - European Loop
-- Route: AMS -> FRA -> CDG -> BCN -> FCO -> BCN -> CDG -> FRA -> AMS
(27, 6, '2025-02-14 08:00:00', 'FRA - Frankfurt', 'CDG - Paris', 0),
(28, 6, '2025-02-15 11:00:00', 'CDG - Paris', 'BCN - Barcelona', 0),
(29, 6, '2025-02-16 16:00:00', 'BCN - Barcelona', 'FCO - Rome', 0),
(33, 6, '2025-02-17 10:00:00', 'FCO - Rome', 'BCN - Barcelona', 0), -- Return Leg 1
(34, 6, '2025-02-18 08:00:00', 'BCN - Barcelona', 'CDG - Paris', 0), -- Return Leg 2
(35, 6, '2025-02-19 09:30:00', 'CDG - Paris', 'FRA - Frankfurt', 0), -- Return Leg 3
(36, 6, '2025-02-20 12:00:00', 'FRA - Frankfurt', 'AMS - Amsterdam', 0), -- Return Leg 4 (Home)

-- Chain 4: Plane 9 (Small) | LHR (Start) -> ... -> LHR (End) - Mediterranean Ring
-- Route: LHR -> TLV -> ATH -> FCO -> ATH -> TLV -> LHR
(30, 9, '2027-02-16 14:00:00', 'TLV - Tel Aviv', 'ATH - Athens', 0),
(31, 9, '2027-02-17 10:00:00', 'ATH - Athens', 'FCO - Rome', 0),
(32, 9, '2027-02-18 15:00:00', 'FCO - Rome', 'ATH - Athens', 0), -- Return Leg 1
(37, 9, '2027-02-19 09:00:00', 'ATH - Athens', 'TLV - Tel Aviv', 0), -- Return Leg 2
(38, 9, '2027-02-20 16:00:00', 'TLV - Tel Aviv', 'LHR - London', 0); -- Return Leg 3 (Home)

---------------------------------------------------
-- FlightPrices
---------------------------------------------------
INSERT INTO FlightPrices
(ClassType, FlightID, PlainID, Price)
VALUES
-- Original (1-12)
('Regular',1,1,350.00), ('Business',1,1,900.00),
('Regular',2,2,280.00), ('Business',2,2,750.00),
('Regular',3,3,150.00), ('Business',3,3,430.00),
('Regular',4,4,720.00), ('Business',4,4,1600.00),
('Regular',5,5,780.00), ('Business',5,5,1700.00),
('Regular',6,1,700.00), ('Business',6,1,1550.00),
('Regular',7,2,760.00), ('Business',7,2,1650.00),
('Regular',8,6,180.00),
('Regular',9,7,160.00),
('Regular',10,8,140.00),
('Regular',11,9,340.00),
('Regular',12,10,360.00),

-- New Flights
-- Plane 1
('Regular',20,1,360.00), ('Business',20,1,920.00),
('Regular',21,1,800.00), ('Business',21,1,1800.00),
('Regular',22,1,800.00), ('Business',22,1,1800.00),
('Regular',23,1,350.00), ('Business',23,1,900.00),
-- Plane 4
('Regular',24,4,700.00), ('Business',24,4,1550.00),
('Regular',25,4,160.00), ('Business',25,4,450.00),
('Regular',26,4,180.00), ('Business',26,4,480.00),
-- Plane 6 (The European Looper)
('Regular',27,6,150.00),
('Regular',28,6,160.00),
('Regular',29,6,170.00),
('Regular',33,6,175.00),
('Regular',34,6,160.00),
('Regular',35,6,155.00),
('Regular',36,6,180.00),
-- Plane 9 (The Med Ring)
('Regular',30,9,200.00),
('Regular',31,9,190.00),
('Regular',32,9,190.00),
('Regular',37,9,200.00),
('Regular',38,9,340.00);

---------------------------------------------------
-- CustomerOrders
---------------------------------------------------
INSERT INTO CustomerOrders
(OrderID, OrderStatus, OrderDate, Email, PlainID, ClassType, FlightID)
VALUES
-- טיסות עבר → Completed
(5001,'Completed','2025-01-20','cust1@example.com',1,'Regular',1),
(5002,'Completed','2025-01-20','cust2@example.com',1,'Business',1),
(5003,'Completed','2025-01-21','cust3@example.com',2,'Regular',2),
(5006,'Completed','2025-01-22','cust6@example.com',5,'Regular',5),
(5008,'Completed','2025-01-23','cust8@example.com',6,'Regular',8),

-- ביטולים – לא משתנים
(5004,'Customer_Cancelled','2025-01-21','cust4@example.com',2,'Business',2),
(5005,'System_Cancelled','2025-01-22','cust5@example.com',4,'Regular',4),
(5010,'Customer_Cancelled','2025-01-24','cust10@example.com',9,'Regular',11),

-- טיסות עתיד → Active
(5007,'Active','2025-01-23','cust7@example.com',2,'Business',7),
(5009,'Active','2025-01-24','cust9@example.com',7,'Regular',9);


---------------------------------------------------
-- SelectedSeatsCustomerOrders
---------------------------------------------------
INSERT INTO SelectedSeatsCustomerOrders
(OrderID, Line, SeatLetter)
VALUES
(5001,12,3), (5002,2,1), (5003,18,4), (5004,5,2), (5005,20,6),
(5006,14,3), (5007,9,2), (5008,3,1), (5009,11,5), (5010,7,4);

---------------------------------------------------
-- GuestOrders
---------------------------------------------------
INSERT INTO GuestOrders
(OrderID, OrderStatus, OrderDate, Email, PlainID, ClassType, FlightID)
VALUES
-- טיסות עבר → Completed
(6001,'Completed','2025-01-20','guest1@example.com',1,'Regular',1),
(6002,'Completed','2025-01-20','guest2@example.com',1,'Business',1),
(6003,'Completed','2025-01-21','guest3@example.com',3,'Regular',3),
(6006,'Completed','2025-01-22','guest6@example.com',1,'Regular',6),
(6008,'Completed','2025-01-23','guest8@example.com',8,'Regular',10),

-- ביטולים
(6004,'Customer_Cancelled','2025-01-21','guest4@example.com',5,'Regular',5),
(6005,'System_Cancelled','2025-01-22','guest5@example.com',4,'Business',4),
(6010,'Customer_Cancelled','2025-01-24','guest10@example.com',5,'Business',5),

-- טיסות עתיד → Active
(6007,'Active','2025-01-23','guest7@example.com',6,'Regular',8),
(6009,'Active','2025-01-24','guest9@example.com',10,'Regular',12);


---------------------------------------------------
-- SelectedSeatsGuestOrders
---------------------------------------------------
INSERT INTO SelectedSeatsGuestOrders
(OrderID, Line, SeatLetter)
VALUES
(6001,15,4), (6002,4,1), (6003,7,2), (6004,21,6), (6005,10,3),
(6006,8,2), (6007,19,5), (6008,6,1), (6009,13,4), (6010,9,2);

---------------------------------------------------
-- WorkingFlightAttendants
---------------------------------------------------
INSERT INTO WorkingFlightAttendants (AttendantID, FlightID) VALUES
-- Original Flights (1-12)
(3001,1),(3002,1),(3003,1),(3004,1),(3005,1),(3006,1),
(3007,2),(3008,2),(3009,2),(3010,2),(3011,2),(3012,2),
(3013,3),(3014,3),(3015,3),(3016,3),(3017,3),(3018,3),
(3019,4),(3020,4),(3001,4),(3002,4),(3003,4),(3004,4),
(3005,5),(3006,5),(3007,5),(3008,5),(3009,5),(3010,5),
(3011,6),(3012,6),(3013,6),(3014,6),(3015,6),(3016,6),
(3017,7),(3018,7),(3019,7),(3020,7),(3001,7),(3002,7),
(3003,8),(3004,8),(3005,8),
(3006,9),(3007,9),(3008,9),
(3009,10),(3010,10),(3011,10),
(3012,11),(3013,11),(3014,11),
(3015,12),(3016,12),(3017,12),

-- Chain 1 (Plane 1)
(3001,20), (3002,20), (3003,20), (3004,20), (3005,20), (3006,20),
(3001,21), (3002,21), (3003,21), (3004,21), (3005,21), (3006,21),
(3001,22), (3002,22), (3003,22), (3004,22), (3005,22), (3006,22),
(3001,23), (3002,23), (3003,23), (3004,23), (3005,23), (3006,23),

-- Chain 2 (Plane 4)
(3019,24), (3020,24), (3001,24), (3002,24), (3003,24), (3004,24),
(3019,25), (3020,25), (3001,25), (3002,25), (3003,25), (3004,25),
(3019,26), (3020,26), (3001,26), (3002,26), (3003,26), (3004,26),

-- Chain 3 (Plane 6) - The Full Loop
(3003,27), (3004,27), (3005,27),
(3003,28), (3004,28), (3005,28),
(3003,29), (3004,29), (3005,29),
(3003,33), (3004,33), (3005,33),
(3003,34), (3004,34), (3005,34),
(3003,35), (3004,35), (3005,35),
(3003,36), (3004,36), (3005,36),

-- Chain 4 (Plane 9) - The Full Loop
(3012,30), (3013,30), (3014,30),
(3012,31), (3013,31), (3014,31),
(3012,32), (3013,32), (3014,32),
(3012,37), (3013,37), (3014,37),
(3012,38), (3013,38), (3014,38);

---------------------------------------------------
-- WorkingFlightPilots
---------------------------------------------------
INSERT INTO WorkingFlightPilots (PilotID, FlightID) VALUES
-- Original Flights (1-12)
(2001,1),(2002,1),(2003,1),
(2004,2),(2005,2),(2006,2),
(2007,3),(2008,3),(2009,3),
(2010,4),(2001,4),(2002,4),
(2003,5),(2004,5),(2005,5),
(2006,6),(2007,6),(2008,6),
(2009,7),(2010,7),(2001,7),
(2002,8),(2003,8),
(2004,9),(2005,9),
(2006,10),(2007,10),
(2008,11),(2009,11),
(2010,12),(2002,12),

-- Chain 1 (Plane 1)
(2001,20), (2002,20), (2003,20),
(2001,21), (2002,21), (2003,21),
(2001,22), (2002,22), (2003,22),
(2001,23), (2002,23), (2003,23),

-- Chain 2 (Plane 4)
(2010,24), (2001,24), (2002,24),
(2010,25), (2001,25), (2002,25),
(2010,26), (2001,26), (2002,26),

-- Chain 3 (Plane 6)
(2002,27), (2003,27),
(2002,28), (2003,28),
(2002,29), (2003,29),
(2002,33), (2003,33),
(2002,34), (2003,34),
(2002,35), (2003,35),
(2002,36), (2003,36),

-- Chain 4 (Plane 9)
(2008,30), (2009,30),
(2008,31), (2009,31),
(2008,32), (2009,32),
(2008,37), (2009,37),
(2008,38), (2009,38);




---------------------------------------------------------------------
-- חלק 1: הוספת 5 טיסות עבר (התקיימו) במטוס Dassault (PlaneID=3)
-- נשתמש בנתיב CDG-BCN (פריז-ברצלונה) שהוא קצר ומתאים למטוס זה.
-- תאריכים: ינואר 2024 (עבר).
---------------------------------------------------------------------

-- 1. הוספת הטיסות לטבלת Flights
INSERT INTO Flights (FlightID, PlainID, TakeOffTime, SourceField, DestinationField, IsDeleted)
VALUES
(101, 3, '2024-01-01 08:00:00', 'CDG - Paris', 'BCN - Barcelona', 0),
(102, 3, '2024-01-02 08:00:00', 'CDG - Paris', 'BCN - Barcelona', 0),
(103, 3, '2024-01-03 08:00:00', 'CDG - Paris', 'BCN - Barcelona', 0),
(104, 3, '2024-01-04 08:00:00', 'CDG - Paris', 'BCN - Barcelona', 0),
(105, 3, '2024-01-05 08:00:00', 'CDG - Paris', 'BCN - Barcelona', 0);

-- 2. עדכון מחירי הטיסות (FlightPrices)
-- מטוס 3 הוא Dassault Large, יש לו גם אקונומי וגם ביזנס
INSERT INTO FlightPrices (ClassType, FlightID, PlainID, Price)
VALUES
('Regular', 101, 3, 140.00), ('Business', 101, 3, 400.00),
('Regular', 102, 3, 140.00), ('Business', 102, 3, 400.00),
('Regular', 103, 3, 145.00), ('Business', 103, 3, 410.00),
('Regular', 104, 3, 150.00), ('Business', 104, 3, 420.00),
('Regular', 105, 3, 130.00), ('Business', 105, 3, 380.00);

-- 3. שיבוץ צוותים (טייסים ודיילים)
-- מטוס גדול דורש 3 טייסים ו-6 דיילים.
-- נשתמש בצוותים שעובדים על קו פריז (לפי הנתונים הקודמים: טייסים 2007-2009, דיילים 3013-3018)

-- טייסים (WorkingFlightPilots)
INSERT INTO WorkingFlightPilots (PilotID, FlightID) VALUES
(2007,101), (2008,101), (2009,101),
(2007,102), (2008,102), (2009,102),
(2007,103), (2008,103), (2009,103),
(2007,104), (2008,104), (2009,104),
(2007,105), (2008,105), (2009,105);

-- דיילים (WorkingFlightAttendants)
INSERT INTO WorkingFlightAttendants (AttendantID, FlightID) VALUES
(3013,101), (3014,101), (3015,101), (3016,101), (3017,101), (3018,101),
(3013,102), (3014,102), (3015,102), (3016,102), (3017,102), (3018,102),
(3013,103), (3014,103), (3015,103), (3016,103), (3017,103), (3018,103),
(3013,104), (3014,104), (3015,104), (3016,104), (3017,104), (3018,104),
(3013,105), (3014,105), (3015,105), (3016,105), (3017,105), (3018,105);

-- 4. הוספת הזמנות שהושלמו (לא בוטלו) לטיסות אלו
-- נערבב בין לקוחות רשומים לאורחים
INSERT INTO CustomerOrders (OrderID, OrderStatus, OrderDate, Email, PlainID, ClassType, FlightID) VALUES
(8001, 'Completed', '2023-12-01', 'cust1@example.com', 3, 'Regular', 101),
(8002, 'Completed', '2023-12-05', 'cust2@example.com', 3, 'Business', 102),
(8003, 'Completed', '2023-12-10', 'cust3@example.com', 3, 'Regular', 103);

INSERT INTO GuestOrders (OrderID, OrderStatus, OrderDate, Email, PlainID, ClassType, FlightID) VALUES
(8004, 'Completed', '2023-12-15', 'guest1@example.com', 3, 'Regular', 104),
(8005, 'Completed', '2023-12-20', 'guest2@example.com', 3, 'Business', 105);


---------------------------------------------------------------------
-- חלק 2: יצירת נתונים לגרף הביטולים (5 חודשים שונים)
-- ניצור 5 טיסות בחודשים שונים (מרץ-יולי 2025)
-- וניצור עבורן הזמנות בסטטוס 'Customer_Cancelled'
---------------------------------------------------------------------

-- 1. יצירת הטיסות (נשתמש במטוס קטן - PlaneID=6, קו AMS-FRA)
INSERT INTO Flights (FlightID, PlainID, TakeOffTime, SourceField, DestinationField, IsDeleted)
VALUES
(201, 6, '2025-03-10 10:00:00', 'AMS - Amsterdam', 'FRA - Frankfurt', 0), -- חודש 3
(202, 6, '2025-04-10 10:00:00', 'AMS - Amsterdam', 'FRA - Frankfurt', 0), -- חודש 4
(203, 6, '2025-05-10 10:00:00', 'AMS - Amsterdam', 'FRA - Frankfurt', 0), -- חודש 5
(204, 6, '2025-06-10 10:00:00', 'AMS - Amsterdam', 'FRA - Frankfurt', 0), -- חודש 6
(205, 6, '2025-07-10 10:00:00', 'AMS - Amsterdam', 'FRA - Frankfurt', 0); -- חודש 7

-- 2. עדכון מחירים לטיסות החדשות
INSERT INTO FlightPrices (ClassType, FlightID, PlainID, Price)
VALUES
('Regular', 201, 6, 160.00),
('Regular', 202, 6, 170.00),
('Regular', 203, 6, 180.00),
('Regular', 204, 6, 190.00),
('Regular', 205, 6, 200.00);

-- 3. יצירת ההזמנות המבוטלות (Cancelled)
-- שים לב: תאריך ההזמנה הוא לפני הטיסה, הסטטוס הוא ביטול
INSERT INTO CustomerOrders (OrderID, OrderStatus, OrderDate, Email, PlainID, ClassType, FlightID) VALUES
(9001, 'Customer_Cancelled', '2025-03-01', 'cust1@example.com', 6, 'Regular', 201),
(9002, 'Customer_Cancelled', '2025-04-01', 'cust1@example.com', 6, 'Regular', 202),
(9003, 'Customer_Cancelled', '2025-05-01', 'cust1@example.com', 6, 'Regular', 203),
(9004, 'Customer_Cancelled', '2025-06-01', 'cust1@example.com', 6, 'Regular', 204),
(9005, 'Customer_Cancelled', '2025-07-01', 'cust1@example.com', 6, 'Regular', 205);