import streamlit as st
import sqlite3
import pandas as pd


conn = sqlite3.connect('railway.db')
current_page = 'Login or Sign Up'
c = conn.cursor()


def create_db():

    c.execute("CREATE TABLE IF NOT EXISTS users (username TEXT,password TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS employees (empid TEXT,password TEXT,designation TEXT)")
    c.execute("CREATE TABLE IF NOT EXISTS trains (train_no TEXT,train_name TEXT,depature_date TEXT,start TEXT,end TEXT)")

create_db()

def add_train(train_no,train_name,depature_date,start,end):
    c.execute(f"INSERT INTO trains (train_no,train_name,depature_date,start,end) values ({train_no},{train_name},{depature_date},{start},{end})")
    conn.commit()
    create_seat_table(train_no)

def delete_train(train_no,depature_date):
    train_query = c.execute(f"""
                        select * from trains where train_no = {train_no}
                    """)
    train_data = train_query.fetchone()
    if train_data:
        c.execute(f"""
                    delete from trains
                    where train_no = {train_no} and 
                    departure_date = {depature_date}
                """)
        conn.commit()
        st.success("TRAIN IS SUCCESSFULLY DELETED !!")

conn = sqlite3.connect('railway.db')
c = conn.cursor()

def create_seat_table(train_no):
    c.execute(f"""CREATE TABLE IF NOT EXISTS seats_{train_no}
              (seat_number INTEGER PRIMARY KEY,
              seat_type TEXT,
              booked INTEGER,
              passenger_name TEXT,
              passenger_age INTEGER,
              passenger_gender TEXT)""")
    for i in range(1,51):
        val = categorize_seat(i)
        c.execute(f"INSERT INTO seat_{train_no} (seat_number,seat_type,booked,passenger_name,passenger_age,passenger_gender)"
                  f"values ({i},{val},{0},'','','')")
        conn.commit()

def categorize_seat(seat_number):
    if seat_number%10 in [0,4,5,9]:
        return "Window"
    elif seat_number%10 in [2,3,6,7]:
        return "Upper"
    else:
        return "Middle"
    
def allocate_next_available_seat(train_no,seat_type):
    seat_query = c.execute(f"select seat_number from seat_{train_no} where booked=0 and seat_type={seat_type} order by seat_number")
    res = seat_query.fetchall()

    if res:
        return res[0][0]
    
def book_ticket(train_no,name,age,gender,type):
    train_query = c.execute(f"select * from trains where train_no={train_no}")
    train_data = train_query.fetchone()
    if train_data:
        seat_number = allocate_next_available_seat(train_no,type)
        if seat_number:
            c.execute(f"""update seats_{train_no} 
                        set booked = 1,
                        seat_type={type},
                        passenger_name={name},
                        passenger_age={age},
                        passenger_gender={gender}
                        where seat_number = {seat_number}    
                    """)
            conn.commit()
            st.success("BOOKED SUCCESFULLY !!")
        else:
            st.error("No available seats for booking in this train.")
    else:
        st.error(f"No such Train with Number {train_no} is available")


def cancel_ticket(train_no,seat_no):
    train_query = c.execute(f"select * from trains where train_no = {train_no}")
    train_data = train_query.fetchone()

    if train_data:
        c.execute(f"""
                    update seats_{train_no} 
                    set booked = 0,
                    passenger_name='',
                    passenger_age='',
                    passenger_gender=''
                    where seat_number = {seat_no}
                """)
        conn.commit()
        st.success("CANCELED SUCCESSFULLY")
    else:
        st.error(f"No such Train with Number {train_no} is available")

def search_train(train_no):
    train_query = c.execute(f"SELECT * FROM trains where train_no={train_no}")
    train_data = train_query.fetchone()
    return train_data

def train_dest(start,end):
    train_query = c.execute(f"select * from trains where start={start} and end={end}")
    train_data = train_query.fetchall()
    return train_data

    
def view_seats(train_no):
    train_query = c.execute(f"select * from trains where train_no={train_no}")
    train_data = train_query.fetchone()
    if train_data:
        seat_query = c.execute(
            f"""
            SELECT 
                'number: ' || seat_number AS number,
                '\n type: ' || seat_type AS type,
                '\n name: ' || passenger_name AS name,
                '\n age: ' || passenger_age AS age,
                '\n gender: ' || passenger_gender AS gender,
                booked 
            FROM seats_{train_no} 
            ORDER BY seat_number
            """
        )
        res = seat_query.fetchall()
        if res:
            st.dataframe(data=res)
    else:
        st.error(f"No such Train with Number {train_no} is available")

def train_functions():
    st.title("Train Administrator")
    functions = st.sidebar.selectbox("select functionality",
                                     ["ADD TRAIN","VIEW TRAIN","SEARCH TRAIN","DELETE TRAIN","BOOK TICKET","CANCEL TICKET","VIEW SEATS"])
    
    if functions=="ADD TRAIN":
        st.header("Add Train")
        with st.form(key='new train details'):
            train_no = st.text_input("train number")
            train_name = st.text_input("train name")
            depature_date = st.text_input("depature date")
            start = st.text_input("starting point")
            end = st.text_input("Ending destination")
            submitted = st.form_submit_button("Add Train")
        if submitted and (train_no!='' and train_name!='' and depature_date!='' and start!='' and end!=''):
            add_train(train_no,train_name,depature_date,start,end)
            st.success("TRAIN ADDED SUCCESSFULLY !!")

    elif functions == "VIEW TRAIN":
        st.title("View All Trains")
        train_query= c.execute("select * from trains")
        train_data = train_query.fetchall()
        if train_data:
            st.header("Available trains:")
            st.dataframe(data=train_data)
        else:
            st.error("No trains available in the database.")

    elif functions == "SEARCH TRAIN":
        st.title("Train Details Search")

        st.write("Search by Train Number:")
        train_number = st.text_input("Enter Train Number:")

        st.write("Search by Starting and Ending Destination:")
        starting_destination = st.text_input("Starting Destination:")
        ending_destination = st.text_input("Ending Destination:")

        if st.button("Search by Train Number"):
            if train_number:
                train_data = search_train(train_number)
                if train_data:
                    st.header("Search Result:")
                    st.table(pd.DataFrame([train_data], columns=[
                        "Train Number", "Train Name", "Departure Date", "Starting Destination", "Ending Destination"]))
                else:
                    st.error(
                        f"No train found with the train number: {train_number}")
        if st.button("Search by Destinations"):
            if starting_destination and ending_destination:
                train_data = train_dest(
                    starting_destination, ending_destination)
                if train_data:
                    st.header("Search Results:")
                    df = pd.DataFrame(train_data, columns=[
                        "Train Number", "Train Name", "Departure Date", "Starting Destination", "Ending Destination"])
                    st.table(df)
                else:
                    st.error(
                        f"No trains found for the given source and destination.")
                    
    elif functions=="DELETE TRAIN":
        st.title("Delete Train")
        train_number = st.text_input("Enter Train Number")
        depature_date = st.text_input("Enter Date")
        if st.button("Delete Train"):
            c.execute(f"DROP TABLE IF EXISTS seats_{train_number}")
            delete_train(train_number,depature_date)

    elif functions=="BOOK TICKET":
        st.title("Book Train Ticket")
        train_number = st.text_input("Enter Train Number")
        seat_type = st.selectbox("Seat Type",["Upper","Middle","Window"],index=0)
        passenger_name = st.text_input("Passenger Name")
        passenger_age = st.text_input("Passenger Age",min_value=1)
        passenger_gender = st.selectbox("Gender",['Male','Female'],index=0)

        if st.button("Book Ticket"):
            if train_number and passenger_name and passenger_age and passenger_gender:
                book_ticket(train_number,passenger_name,passenger_age,passenger_gender,seat_type)

    elif functions=="CANCEL TICKET":
        st.title("Cancel Train Ticket")
        train_number = st.text_input("Enter Train Number")
        seat_number = st.text_input("Enter seat number ",min_value=1)
        if st.button("Cancel Tickets"):
            if train_number and seat_number:
                cancel_ticket(train_number,seat_number)

    elif functions=="VIEW SEATS":
        st.title("View Seats")
        train_number = st.text_input("Enter Train Number")
        if st.button("Submit"):
            if train_number:
                view_seats(train_number)
            
train_functions()
conn.close()

conn.close()