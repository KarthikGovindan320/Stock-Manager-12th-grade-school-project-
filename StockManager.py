import subprocess
import sys
import io
import pip
from subprocess import call

try:
    sys.stdout = io.StringIO()
    sys.stderr = io.StringIO()

    call("python -m pip install --upgrade pip".split())
    pip.main(['install', 'customtkinter', 'mysql-connector-python', 'opencv-python', 'numpy', 'pynput', 'openai', 'Pillow', 'smtplib', 'email', 'sydney'])
except:
    pass

import customtkinter as ctk
import re
import threading
import os
import time
import tkinter.messagebox as tkmb
from tkcalendar import Calendar, DateEntry
import mysql.connector
from mysql.connector import Error
import json
import pandas
import numpy as np
import asyncio
from sydney import SydneyClient
import datetime
import socket
import math
from colorama import init, Fore, Style
import openai
from PIL import Image
from io import BytesIO
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import email
from email.header import decode_header

local_ip = 0
auto_login_username = ""
auto_login_password = ""

init(autoreset=True)
print(Fore.RED, end="")

# Credits to the main library https://github.com/TomSchimansky/CustomTkinter/tree/master/customtkinter

try:
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    s.connect(("8.8.8.8", 80))

    local_ip = s.getsockname()[0]
except Exception as e:
    print("Warnings : Connection error, probably due to poor internet. Please check internet connection and try again.")
    print("Error: ", e)
finally:
    s.close()

def connect_to_database():
    try:
        db_config = {
            'host': "HOST_IP",
            'user': "USER_NAME",
            'password': "PASSWORD",
            'database': "DB_NAME"
        }
        connection = mysql.connector.connect(**db_config)
        return connection
    except Error as e:
        print(f"Error: {e}")
        return None

connection = connect_to_database()
cursor = connection.cursor(dictionary=True)
query = f"Select username, password From Users where RememberIP = '{local_ip}'"
cursor.execute(query)
result = cursor.fetchone()

if result:
    auto_login_username = result['username']
    auto_login_password = result['password']

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

app = ctk.CTk()
app.geometry("400x350")
app.title("Login")

def check_window_duplicates():
    while True:
        windows = []
        for window in app.winfo_children():
            if isinstance(window, ctk.CTkToplevel):
                windows.append(window)
        for i in range(len(windows)):
            for j in range(i+1, len(windows)):
                if re.match(rf"^{windows[i].title()}$", windows[j].title()): 
                    windows[j].destroy()
        time.sleep(0.5)

threading.Thread(target=check_window_duplicates).start()

def open_stockwatch_window(user_id):
    global stockwatch_window
    stockwatch_window = ctk.CTkToplevel(app)
    stockwatch_window.protocol("WM_DELETE_WINDOW", lambda: None)
    stockwatch_window.title("Asset Management")
    stockwatch_window.geometry("530x400")

    header_frame = ctk.CTkFrame(stockwatch_window)
    header_frame.pack(pady=20, padx=20, fill='x')

    header_content_frame = ctk.CTkFrame(header_frame)
    header_content_frame.pack(side="left", fill='x', expand=True)
    
    heading = ctk.CTkLabel(header_content_frame, text="Welcome to Asset Manager", font=("Arial", 20, "bold"))
    heading.pack(side="left", padx=(10, 10))
    
    logout_button = ctk.CTkButton(header_content_frame, text="Logout", command=logout)
    logout_button.pack(side="right")
    
    button_frame = ctk.CTkFrame(stockwatch_window)
    button_frame.pack(pady=20, padx=20, fill='both', expand=True)
    
    buttons = [
        ("View Stock Tables", lambda: view_stock_tables(user_id)),
        ("New Stock Table", lambda: new_stock_table(user_id)),
        ("New Items", lambda: new_items(user_id)),
        ("Issue Items", lambda: remove_items(user_id)),
        ("Receive Items", lambda: receive_items(user_id)),
        ("View Logs", lambda: view_logs(user_id))
    ]
    
    for i, (text, command) in enumerate(buttons):
        row = i // 3
        column = i % 3
        btn = ctk.CTkButton(button_frame, text=text, command=command)
        btn.grid(row=row, column=column, padx=10, pady=10, sticky="nsew")

    button_frame.columnconfigure(0, weight=1)
    button_frame.columnconfigure(1, weight=1)
    button_frame.rowconfigure(0, weight=1)
    button_frame.rowconfigure(1, weight=1)

    stockwatch_window.transient(app)

def open_stock_tables_window(user_id):
    global stock_tables_window
    stock_tables_window = ctk.CTkToplevel(app)
    stock_tables_window.title("Stock Tables")
    stock_tables_window.geometry("800x500") 

    header_frame = ctk.CTkFrame(stock_tables_window)
    header_frame.pack(pady=20, padx=20, fill='both', expand=True)

    heading = ctk.CTkLabel(header_frame, text="Current Stock Tables", font=("Arial", 20, "bold"))
    heading.pack(pady=10)

    table_frame = ctk.CTkFrame(header_frame)
    table_frame.pack(side= "top", fill="y", expand=False)

    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT Tables, Location, Incharge, ItemsNO as `No of Items` FROM Tables WHERE Id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        if not result:
            stock_tables_window.destroy()
            tkmb.showinfo(title="No Data", message="No stock tables found.")
            return

        columns = result[0].keys()
        col_count = len(columns)

        for i, column in enumerate(columns):
            label = ctk.CTkLabel(table_frame, text=column, font=("Arial", 12, "bold"))
            label.grid(row=0, column=i, padx=70, pady=5, sticky="nsew")

        for row_index, row in enumerate(result):
            for col_index, column in enumerate(columns):
                if col_index == 0:
                    table_button = ctk.CTkButton(table_frame, text=row[column])
                    table_button.grid(row=row_index + 1, column=0, sticky="nsew", pady = 5)
                    table_button.configure(command=lambda table_name=row[column]: open_table_window(table_name, user_id))
                else :
                    label = ctk.CTkLabel(table_frame, text=row[column])
                    label.grid(row=row_index + 1, column=col_index, sticky="nsew")

        for i in range(col_count):
            table_frame.columnconfigure(i, weight=1)
        table_frame.rowconfigure(0, weight=1)
        for row_index in range(1, len(result) + 1):
            table_frame.rowconfigure(row_index, weight=1)

    except Error as e:
        tkmb.showerror(title="Database Error", message=f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

    stock_tables_window.transient(app)
    stock_tables_window.grab_set()

def open_table_window(table_name, user_id):
    stock_tables_window.destroy()
    global table_window
    table_window = ctk.CTkToplevel(app)
    table_window.title(f"Table: {table_name}")
    w, h = table_window.winfo_screenwidth(), table_window.winfo_screenheight()
    table_window.geometry("%dx%d+0+0" % (w, h))

    header_frame = ctk.CTkFrame(table_window)
    header_frame.pack(pady=20, padx=20, fill='both', expand=True)

    heading = ctk.CTkLabel(header_frame, text=f"Table: {table_name}", font=("Arial", 20, "bold"))
    heading.pack(pady=10)

    table_frame1 = ctk.CTkFrame(header_frame)
    table_frame1.pack(side="top", fill="x", expand=False)

    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT * FROM `{table_name}`"
        cursor.execute(query)
        result = cursor.fetchall()

        if not result:
            table_window.destroy()
            tkmb.showinfo(title="No Data", message="No data found in the table.")
            return

        columns = result[0].keys()
        col_count = len(columns)

        for i, column in enumerate(columns):
            label = ctk.CTkLabel(table_frame1, text=column, font=("Arial", 12, "bold"))
            label.grid(row=0, column=i, padx=70, pady=5, sticky="nsew")

        for row_index, row in enumerate(result):
            for col_index, column in enumerate(columns):
                label = ctk.CTkLabel(table_frame1, text=row[column])
                label.grid(row=row_index + 1, column=col_index, sticky="nsew")

        for i in range(col_count):
            table_frame1.columnconfigure(i, weight=1)
        table_frame1.rowconfigure(0, weight=1) 
        for row_index in range(1, len(result) + 1):
            table_frame1.rowconfigure(row_index, weight=1)

        ctk.CTkLabel(header_frame, text="").pack(pady=10)

        table_frame2 = ctk.CTkFrame(header_frame)
        table_frame2.pack(side="top", fill="x", expand=False)

        try:
            cursor = connection.cursor(dictionary=True)
            query = f"SELECT ItemCode, ItemName, Count, ValuePerPiece, IssuedBy, IssuedTo, DueDate FROM Issued where `Table` = '{table_name}'"
            cursor.execute(query)
            result = cursor.fetchall()

            if result:
                columns = result[0].keys()
                col_count = len(columns)

                for i, column in enumerate(columns):
                    label = ctk.CTkLabel(table_frame2, text=column, font=("Arial", 12, "bold"))
                    label.grid(row=0, column=i, padx=50, pady=5, sticky="nsew")

                for row_index, row in enumerate(result):
                    for col_index, column in enumerate(columns):
                        label = ctk.CTkLabel(table_frame2, text=row[column])
                        label.grid(row=row_index + 1, column=col_index, sticky="nsew")

                for i in range(col_count):
                    table_frame2.columnconfigure(i, weight=1)
                table_frame2.rowconfigure(0, weight=1) 
                for row_index in range(1, len(result) + 1):
                    table_frame2.rowconfigure(row_index, weight=1)

        except Error as e:
            tkmb.showerror(title="Database Error", message=f"Error: {e}")
        finally:
            cursor.close()

    except Error as e:
        tkmb.showerror(title="Database Error", message=f"Error: {e}")
    finally:
        connection.close()

    table_window.transient(app)
    table_window.grab_set()

def open_new_stock_table_window(user_id):
    new_stock_table_window = ctk.CTkToplevel(app)
    new_stock_table_window.title("New Stock Table")
    new_stock_table_window.geometry("350x450")

    frame = ctk.CTkFrame(new_stock_table_window)
    frame.pack(pady=20, padx=20, fill='both', expand=True)

    table_name_label = ctk.CTkLabel(frame, text="Table Name:")
    table_name_label.pack(padx=10,pady=5, anchor='w')
    table_name_entry = ctk.CTkEntry(frame)
    table_name_entry.pack(padx=10,pady=5, fill='x')

    location_label = ctk.CTkLabel(frame, text="Location:")
    location_label.pack(padx=10,pady=5, anchor='w')
    location_entry = ctk.CTkEntry(frame)
    location_entry.pack(padx=10,pady=5, fill='x')

    incharge_label = ctk.CTkLabel(frame, text="Incharge:")
    incharge_label.pack(padx=10,pady=5, anchor='w')
    incharge_entry = ctk.CTkEntry(frame)
    incharge_entry.pack(padx=10,pady=5, fill='x')

    created_by_label = ctk.CTkLabel(frame, text="Created By:")
    created_by_label.pack(padx=10,pady=5, anchor='w')
    created_by = ctk.CTkEntry(frame)
    created_by.pack(padx=10,pady=5, fill='x')

    def submit_form():
        table_name = table_name_entry.get()
        location = location_entry.get()
        incharge = incharge_entry.get()
        created_by_text = created_by.get()

        try:
            connection = connect_to_database()
            cursor = connection.cursor()
            query = "INSERT INTO Tables(Id, Tables, Location, Incharge) VALUES (%s, %s, %s, %s)"
            cursor.execute(query, (user_id, table_name, location, incharge))
            connection.commit()
            query = f"CREATE TABLE `{table_name}` (ItemCode INT AUTO_INCREMENT UNIQUE KEY, ItemName VARCHAR(255), ItemDesc VARCHAR(255), Count INT, Location VARCHAR(255), LatestStatus VARCHAR(255), ValuePerPiece INT)"
            cursor.execute(query)
            connection.commit()
            query = "INSERT INTO Logs(`Id`, `Element`, `Description`, `Table`, `Account`) VALUES (%s, %s, %s, %s, %s)"
            cursor.execute(query, (user_id, "0", f"Table {table_name} Created on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by {created_by_text}", table_name, username))
            connection.commit()
        except Error as e:
            tkmb.showerror(title="Database Error", message=f"Error: {e}")
        finally:
            cursor.close()
            connection.close()

        new_stock_table_window.destroy()

    ok_button = ctk.CTkButton(frame, text="OK", command=submit_form)
    ok_button.pack(pady=20)

    new_stock_table_window.transient(app)
    new_stock_table_window.grab_set()

def newItem(table_name, user_id):
    global new_items_window
    new_items_window.destroy()
   
    global new_item_window
    new_item_window = ctk.CTkToplevel(app)
    new_item_window.title("New Item")
    new_item_window.geometry("400x600")

    frame = ctk.CTkFrame(new_item_window)
    frame.pack(pady=20, padx=20, fill='both', expand=True)

    item_name_label = ctk.CTkLabel(frame, text="Item Name:")
    item_name_label.pack(padx=10, pady=5, anchor='w')
    item_name_entry = ctk.CTkEntry(frame)
    item_name_entry.pack(padx=10, pady=5, fill='x')

    item_desc_label = ctk.CTkLabel(frame, text="Item Description:")
    item_desc_label.pack(padx=10, pady=5, anchor='w')
    item_desc_entry = ctk.CTkEntry(frame)
    item_desc_entry.pack(padx=10, pady=5, fill='x')

    location_label = ctk.CTkLabel(frame, text="Location (Optional):")
    location_label.pack(padx=10, pady=5, anchor='w')
    location_entry = ctk.CTkEntry(frame)
    location_entry.pack(padx=10, pady=5, fill='x')

    count_label = ctk.CTkLabel(frame, text="Count:")
    count_label.pack(padx=10, pady=5, anchor='w')
    count_entry = ctk.CTkEntry(frame)
    count_entry.pack(padx=10, pady=5, fill='x')

    value_label = ctk.CTkLabel(frame, text="Value/piece (Optional):")
    value_label.pack(padx=10, pady=5, anchor='w')
    value_entry = ctk.CTkEntry(frame)
    value_entry.pack(padx=10, pady=5, fill='x')

    person_label = ctk.CTkLabel(frame, text="Item Given By:")
    person_label.pack(padx=10, pady=5, anchor='w')
    person_entry = ctk.CTkEntry(frame)
    person_entry.pack(padx=10, pady=5, fill='x')

    def submit_form():
        item_name = item_name_entry.get()
        item_desc = item_desc_entry.get()
        location = location_entry.get()
        count = count_entry.get()
        value = value_entry.get()
        person = person_entry.get()

        if not count or int(count) == 0:
            tkmb.showerror(title="Invalid Entry", message="Count cannot be null or zero.")
            return

        current_time = datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S")
        query = f"INSERT INTO `{table_name}` (ItemName, ItemDesc, Count, Location, LatestStatus, ValuePerPiece) VALUES (%s, %s, %s, %s, %s, %s)"
        try:
            connection = connect_to_database()
            cursor = connection.cursor()
            cursor.execute(query, (item_name, item_desc, count, location, f"Added to Inventory on {current_time} by {person}", value))
            connection.commit()

            try:
                connection = connect_to_database()
                cursor = connection.cursor()
                query = f"UPDATE `Tables` SET `ItemsNO`=`ItemsNO`+{count} WHERE TABLES = '{table_name}'"
                cursor.execute(query)
                connection.commit()

                try:
                    connection = connect_to_database()
                    cursor = connection.cursor()
                    query = f"SELECT ItemCode FROM `{table_name}` WHERE ItemName = %s"
                    cursor.execute(query, (item_name,))

                    item_code = cursor.fetchone()[0]
                    query = f"INSERT INTO `Logs` (`Id`, `Element`, `Description`, `Table`, `Account`) VALUES ({user_id},{item_code},'{f'Added to Inventory on {current_time} by {person}'}','{table_name}', '{username}')"
                    cursor.execute(query)
                    connection.commit()

                except Error as e:
                    tkmb.showerror(title="Database Error", message=f"Error on line {e.__traceback__.tb_lineno}: {e}")
                finally:
                    cursor.close()
                    connection.close()
            except Error as e:
                tkmb.showerror(title="Database Error", message=f"Error: {e}")
            finally:
                cursor.close()
                connection.close()
            
        except Error as e:
            tkmb.showerror(title="Database Error", message=f"Error: {e}")
        finally:
            cursor.close()
            connection.close()

        new_item_window.destroy()

    ok_button = ctk.CTkButton(frame, text="OK", command=lambda: (ok_button.configure(state='disabled'), submit_form(), ok_button.configure(state='normal')))
    ok_button.pack(pady=20)

    new_item_window.transient(app)
    new_item_window.grab_set()

def open_new_items_window(user_id):
    global new_items_window
    new_items_window = ctk.CTkToplevel(app)
    new_items_window.title("Select a Table")
    new_items_window.geometry("400x300")

    heading = ctk.CTkLabel(new_items_window, text="Select a Table", font=("Arial", 24, "bold"))
    heading.pack(pady=20)

    frame = ctk.CTkFrame(new_items_window)
    frame.pack(side="top",padx=50,expand=False)

    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT Tables FROM Tables WHERE Id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        if not result:
            new_items_window.destroy()
            tkmb.showinfo(title="No Data", message="No stock tables found.")
            return

        for row in result:
            table_name = row["Tables"]
            button = ctk.CTkButton(frame, text=table_name, command=lambda table_name=table_name: newItem(table_name, user_id))
            button.pack(pady=5)

    except Error as e:
        tkmb.showerror(title="Database Error", message=f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

    new_items_window.transient(app)  
    new_items_window.grab_set() 

def view_logs_window(user_id):
    global view_log_window
    view_log_window = ctk.CTkToplevel(app)
    view_log_window.title("View Logs")
    w, h = view_log_window.winfo_screenwidth(), view_log_window.winfo_screenheight()
    view_log_window.geometry("%dx%d+0+0" % (w, h))

    header_frame = ctk.CTkFrame(view_log_window)
    header_frame.pack(pady=20, padx=0, fill='both', expand=True)

    heading = ctk.CTkLabel(header_frame, text="Logs", font=("Arial", 20, "bold"))
    heading.pack(pady=10)

    table_frame = ctk.CTkFrame(header_frame)
    table_frame.pack(side= "top", fill="y", expand=False)

    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM Logs WHERE Id = %s order by Time desc" 
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        if not result:
            view_log_window.destroy()
            tkmb.showinfo(title="No Data", message="No stock tables found.")
            return

        columns = result[0].keys()
        col_count = len(columns)

        for i, column in enumerate(columns):
            label = ctk.CTkLabel(table_frame, text=column, font=("Arial", 12, "bold"))
            label.grid(row=0, column=i, padx=100, pady=5, sticky="nsew")

        for row_index, row in enumerate(result):
            for col_index, column in enumerate(columns):
                label = ctk.CTkLabel(table_frame, text=row[column])
                label.grid(row=row_index + 1, column=col_index, sticky="nsew")

        for i in range(col_count):
            table_frame.columnconfigure(i, weight=1)
        table_frame.rowconfigure(0, weight=1) 
        for row_index in range(1, len(result) + 1):
            table_frame.rowconfigure(row_index, weight=1)

        view_log_window.transient(app)
        view_log_window.grab_set()
    except Error as e:
        tkmb.showerror(title="Database Error", message=f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

def issue_item(table_name, user_id):
    issue_items_table_select_window.destroy()
    global issue_items_window
    issue_items_window = ctk.CTkToplevel(app)
    issue_items_window.title("Issue Items")
    w, h = issue_items_window.winfo_screenwidth(), issue_items_window.winfo_screenheight()
    issue_items_window.geometry("%dx%d+0+0" % (w, h))

    header_frame = ctk.CTkFrame(issue_items_window)
    header_frame.pack(pady=20, padx=20, fill='both', expand=True)

    heading = ctk.CTkLabel(header_frame, text="Issue Items", font=("Arial", 20, "bold"))
    heading.pack(pady=10)

    table_frame = ctk.CTkFrame(header_frame)
    table_frame.pack(fill='both', expand=True)

    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT * FROM `{table_name}`"
        cursor.execute(query)
        items = cursor.fetchall()

        if not items:
            issue_items_window.destroy()
            tkmb.showinfo(title="No Data", message="No items found in the selected table.")
            return

        headers = np.array(["ItemName", "ItemDesc", "ValuePerPiece", "Count", "Issued By", "Issued To", "Due Date", "Number Of Pieces", "Increment", "Decrement"]) 
        for col_num, header in enumerate(headers):
            label = ctk.CTkLabel(table_frame, text=header, font=("Arial", 12, "bold"))
            label.grid(row=0, column=col_num, padx=36, pady=5, sticky="nsew")

        counters = {}
        entries = {}
        itemName = {}
        due_date_entries = {}

        for row_num, item in enumerate(items, start=1):
            ctk.CTkLabel(table_frame, text=item["ItemName"]).grid(row=row_num, column=0, padx=10, pady=5)
            ctk.CTkLabel(table_frame, text=item["ItemDesc"]).grid(row=row_num, column=1, padx=10, pady=5)
            ctk.CTkLabel(table_frame, text=item["ValuePerPiece"]).grid(row=row_num, column=2, padx=10, pady=5)
            ctk.CTkLabel(table_frame, text=item["Count"]).grid(row=row_num, column=3, padx=10, pady=5)

            itemName[item["ItemCode"]] = item["ItemName"]

            counter = ctk.IntVar(value=0)
            counters[item["ItemCode"]] = counter

            issued_by = ctk.CTkEntry(table_frame, placeholder_text="Name of Issuer")
            issued_by.grid(row=row_num, column=4, padx=10, pady=5)

            issued_to = ctk.CTkEntry(table_frame, placeholder_text="Name of Receiver")
            issued_to.grid(row=row_num, column=5, padx=10, pady=5)

            due_date_entry = DateEntry(table_frame, width=15, date_pattern='dd/mm/yyyy', font=("Arial", 14), bg="#2B2D42", fg="#FFFFFF") 
            due_date_entry.set_date(datetime.date.today())
            due_date_entry.grid(row=row_num, column=6, padx=10, pady=5)
            due_date_entries[item["ItemCode"]] = due_date_entry

            counter_label = ctk.CTkLabel(table_frame, textvariable=counter)
            counter_label.grid(row=row_num, column=7, padx=10, pady=5)

            increment_button = ctk.CTkButton(table_frame, text="^^", command=lambda code=item["ItemCode"]: update_counter(code, 1))
            increment_button.grid(row=row_num, column=8, padx=5, pady=5)

            decrement_button = ctk.CTkButton(table_frame, text="vv", command=lambda code=item["ItemCode"]: update_counter(code, -1))
            decrement_button.grid(row=row_num, column=9, padx=5, pady=5)

            entries[item["ItemCode"]] = (issued_by, issued_to)

        def update_counter(item_code, delta):
            current_count = counters[item_code].get()
            item_count = next(item["Count"] for item in items if item["ItemCode"] == item_code)
            if 0 <= current_count + delta <= item_count:
                counters[item_code].set(current_count + delta)

        def submit_form():
            issued_items = [(item_code, itemName[item_code], counter.get(), entries[item_code][0].get(), entries[item_code][1].get(), due_date_entries[item_code].get()) for item_code, counter in counters.items() if counter.get() > 0 and datetime.datetime.strptime(due_date_entries[item_code].get(), '%d/%m/%Y').date() >= datetime.date.today()] 
            if not issued_items:
                tkmb.showinfo(title="Invalid Entry", message="Please check the entered values of Due date and Number of Pieces.")
                return
            print("Items Issued:")
            for item_code, item_name,count, issuer, receiver, date in issued_items:
                print(f"Item Code: {item_code}, Count: {count}, Issued By: {issuer}, Issued To: {receiver}, Due Date: {datetime.datetime.strptime(date, '%d/%m/%Y').strftime('%Y-%m-%d')}")
            try:
                connection = connect_to_database()
                cursor = connection.cursor(dictionary=True)
                for item_code, item_name, count, issuer, receiver, date in issued_items:
                    query1 = f"UPDATE `{table_name}` SET `Count`=`Count` - %s, LatestStatus = 'Issued %s on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by {issuer} to {receiver}' WHERE ItemCode = %s"
                    cursor.execute(query1, (count, count, item_code))
                    query2 = "INSERT INTO `Issued`(`Id`, `ItemCode`, `ItemName`, `Count`, `ValuePerPiece`, `Table`, `IssuedBy`, `IssuedTo`, `DueDate`) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)"
                    tkmb.showinfo(title="Final Query", message=query2 % (user_id, item_code, item_name, count, item["ValuePerPiece"], table_name, issuer, receiver, datetime.datetime.strptime(date, '%d/%m/%Y').strftime('%Y-%m-%d')))
                    cursor.execute(query2, (user_id, item_code, item_name, count, item["ValuePerPiece"], table_name, issuer, receiver, datetime.datetime.strptime(date, '%d/%m/%Y').strftime('%Y-%m-%d')))
                    query3 = "INSERT INTO `Logs`(`Id`, `Element`, `Description`, `Table`, `Account`) VALUES (%s, %s, %s, %s, %s)"
                    cursor.execute(query3, (user_id, item_code, f"Issued {count} on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by {issuer} to {receiver}", table_name, username))
                    connection.commit()
            except Error as e:
                tkmb.showerror(title="Database Error", message=f"Error: {e}")
            finally:
                cursor.close()
                connection.close()
                issue_items_window.destroy()

        ok_button = ctk.CTkButton(header_frame, text="OK", command=submit_form)
        ok_button.pack(pady=20)

    except Error as e:
        tkmb.showerror(title="Database Error", message=f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

    issue_items_window.transient(app)
    issue_items_window.grab_set()

def receive_items_window_final(table_name, user_id):
    receive_items_window.destroy()
    global receive_items_window_object
    receive_items_window_object = ctk.CTkToplevel(app)
    receive_items_window_object.title("Receive Items")
    w, h = receive_items_window_object.winfo_screenwidth(), receive_items_window_object.winfo_screenheight()
    receive_items_window_object.geometry("%dx%d+0+0" % (w, h))

    header_frame = ctk.CTkFrame(receive_items_window_object)
    header_frame.pack(pady=20, padx=20, fill='both', expand=True)

    heading = ctk.CTkLabel(header_frame, text="Receive Items", font=("Arial", 20, "bold"))
    heading.pack(pady=10)

    table_frame = ctk.CTkFrame(header_frame)
    table_frame.pack(fill='both', expand=True)

    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        query = f"SELECT * FROM `{table_name}`"
        cursor.execute(query)
        items = cursor.fetchall()

        if not items:
            receive_items_window_object.destroy()
            tkmb.showinfo(title="No Data", message="No items found in the selected table.")
            return

        headers = ["ItemName", "ItemDesc", "ValuePerPiece", "Returner", "Receiver", "No Of Pieces",  "Increment", "Decrement"]
        for col_num, header in enumerate(headers):
            label = ctk.CTkLabel(table_frame, text=header, font=("Arial", 12, "bold"))
            label.grid(row=0, column=col_num, padx=60, pady=5, sticky="nsew")

        counters = {}
        entries = {}
        
        for row_num, item in enumerate(items, start=1):
            ctk.CTkLabel(table_frame, text=item["ItemName"]).grid(row=row_num, column=0, padx=10, pady=5)
            ctk.CTkLabel(table_frame, text=item["ItemDesc"]).grid(row=row_num, column=1, padx=10, pady=5)
            ctk.CTkLabel(table_frame, text=item["ValuePerPiece"]).grid(row=row_num, column=2, padx=10, pady=5)

            counter = ctk.IntVar(value=0)
            counters[item["ItemCode"]] = counter

            given_by = ctk.CTkEntry(table_frame, placeholder_text="Name of Returner")
            given_by.grid(row=row_num, column=3, padx=10, pady=5)

            received_by = ctk.CTkEntry(table_frame, placeholder_text="Name of Receiver")
            received_by.grid(row=row_num, column=4, padx=10, pady=5)

            counter_label = ctk.CTkLabel(table_frame, textvariable=counter)
            counter_label.grid(row=row_num, column=5, padx=10, pady=5)

            increment_button = ctk.CTkButton(table_frame, text="^^", command=lambda code=item["ItemCode"]: update_counter(code, 1, counters))
            increment_button.grid(row=row_num, column=6, padx=5, pady=5)

            decrement_button = ctk.CTkButton(table_frame, text="vv", command=lambda code=item["ItemCode"]: update_counter(code, -1, counters))
            decrement_button.grid(row=row_num, column=7, padx=5, pady=5)

            entries[item["ItemCode"]] = (given_by, received_by)

        def update_counter(item_code, delta, counters):
            current_count = counters[item_code].get()
            if 0 <= current_count + delta:
                counters[item_code].set(current_count + delta)

        def submit_form():
            receive_items = [(item_code, counter.get(), entries[item_code][0].get(), entries[item_code][1].get()) for item_code, counter in counters.items() if counter.get() > 0]
            if not receive_items:
                tkmb.showinfo(title="Invalid Entry", message="Please check the entered values.")
                return

            for item_code, count, given_by, received_by in receive_items:
                connection = connect_to_database()
                cursor = connection.cursor(dictionary=True)

                query1 = f"UPDATE `{table_name}` SET `Count`=`Count` + %s, LatestStatus = 'Received %s on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by {received_by} and returned by {given_by}' WHERE ItemCode = %s"
                cursor.execute(query1, (count, count, item_code))

                query2 = f"UPDATE `Issued` SET `Count`=`Count` - %s WHERE ItemCode = %s AND IssuedTo = %s AND IssuedBy = %s"
                cursor.execute(query2, (count, item_code, given_by, received_by))

                query3 = "INSERT INTO `Logs`(`Id`, `Element`, `Description`, `Table`, `Account`) VALUES (%s, %s, %s, %s, %s)"
                cursor.execute(query3, (user_id, item_code, f"Received {count} on {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')} by {received_by} and returned by {given_by}", table_name, username))
                connection.commit()
            receive_items_window_object.destroy()

        ok_button = ctk.CTkButton(header_frame, text="OK", command=submit_form)
        ok_button.pack(pady=20)

    except Error as e:
        tkmb.showerror(title="Database Error", message=f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

    receive_items_window_object.transient(app)
    receive_items_window_object.grab_set()

def issue_items_table_select(user_id):
    global issue_items_table_select_window
    issue_items_table_select_window = ctk.CTkToplevel(app)
    issue_items_table_select_window.title("Select a Table")
    issue_items_table_select_window.geometry("400x300")

    heading = ctk.CTkLabel(issue_items_table_select_window, text="Select a Table", font=("Arial", 24, "bold"))
    heading.pack(pady=20)

    frame = ctk.CTkFrame(issue_items_table_select_window)
    frame.pack(side="top",padx=50,expand=False)

    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT Tables FROM Tables WHERE Id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        if not result:
            issue_items_table_select_window.destroy()
            tkmb.showinfo(title="No Data", message="No items found to issue.")
            return

        for row in result:
            table_name = row["Tables"]
            button = ctk.CTkButton(frame, text=table_name, command=lambda table_name=table_name: issue_item(table_name, user_id))
            button.pack(pady=5)

    except Error as e:
        tkmb.showerror(title="Database Error", message=f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

    issue_items_table_select_window.transient(app)
    issue_items_table_select_window.grab_set() 

def receive_items_table_select(user_id):
    global receive_items_window
    receive_items_window = ctk.CTkToplevel(app)
    receive_items_window.title("Select a Table")
    receive_items_window.geometry("400x300")

    heading = ctk.CTkLabel(receive_items_window, text="Select a Table", font=("Arial", 24, "bold"))
    heading.pack(pady=20)

    frame = ctk.CTkFrame(receive_items_window)
    frame.pack(side="top",padx=50,expand=False)

    try:
        connection = connect_to_database()
        cursor = connection.cursor(dictionary=True)
        query = "SELECT Tables FROM Tables WHERE Id = %s"
        cursor.execute(query, (user_id,))
        result = cursor.fetchall()

        if not result:
            receive_items_window.destroy()
            tkmb.showinfo(title="No Data", message="No registered items to receive.")
            return

        for row in result:
            table_name = row["Tables"]
            button = ctk.CTkButton(frame, text=table_name, command=lambda table_name=table_name: receive_items_window_final(table_name, user_id))
            button.pack(pady=5)

    except Error as e:
        tkmb.showerror(title="Database Error", message=f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

    receive_items_window.transient(app)
    receive_items_window.grab_set() 

# Redirecting to the respective windows. Multithreading comming soon.
def view_stock_tables(user_id):
    open_stock_tables_window(user_id)

def new_stock_table(user_id):
    open_new_stock_table_window(user_id)

def new_items(user_id):
    open_new_items_window(user_id)

def remove_items(user_id):
    issue_items_table_select(user_id)

def receive_items(user_id):
    receive_items_table_select(user_id)

def view_logs(user_id):
    view_logs_window(user_id)

def login():
    global username
    username = user_entry.get()
    password = user_pass.get()
    remember_me = remember_me_var.get()

    connection = connect_to_database()
    if connection is None:
        tkmb.showerror(title="Database Error", message="Unable to connect to the database")
        return

    try:
        cursor = connection.cursor(dictionary=True)
        query = "SELECT * FROM Users WHERE username = %s AND password = %s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
            
        if result:
            user_id = result["Id"]
            open_stockwatch_window(user_id)
            app.withdraw()

            if remember_me:
                update_query = "UPDATE Users SET RememberIP = %s WHERE username = %s AND password = %s"
                cursor.execute(update_query, (local_ip, username, password))
                connection.commit()
            else :
                update_query = "UPDATE Users SET RememberIP = '' WHERE username = %s AND password = %s"
                cursor.execute(update_query, (username, password))
                connection.commit()

        else:
            tkmb.showerror(title="Login Failed", message="Invalid Username or Password")
    except Error as e:
        tkmb.showerror(title="Database Error", message=f"Error: {e}")
    finally:
        cursor.close()
        connection.close()

def logout():
    stockwatch_window.destroy()
    app.deiconify()

label = ctk.CTkLabel(app, text="")
label.pack(pady=0)

frame = ctk.CTkFrame(master=app)
frame.pack(pady=20, padx=40, fill='both', expand=True)

label = ctk.CTkLabel(master=frame, text='Login', font=("Arial", 24, "bold"))
label.pack(pady=20, padx=10) 

if auto_login_username == "" :
    user_entry = ctk.CTkEntry(master=frame, placeholder_text="Username")
    user_entry.pack(pady=12, padx=10)
else :
    user_entry = ctk.CTkEntry(master=frame)
    user_entry.insert(0, auto_login_username)
    user_entry.pack(pady=12, padx=10)

if auto_login_password == "" :
    user_pass = ctk.CTkEntry(master=frame, placeholder_text="Password", show="*")
    user_pass.pack(pady=12, padx=10)
else :
    user_pass = ctk.CTkEntry(master=frame, show="*")
    user_pass.insert(0, auto_login_password)
    user_pass.pack(pady=12, padx=10)

button = ctk.CTkButton(master=frame, text='Login', command=login)
button.pack(pady=12, padx=10)

remember_me_var = ctk.IntVar(value=1 if auto_login_username != "" else 0)
remember_me_checkbox = ctk.CTkCheckBox(master=frame, text="Remember Me", variable=remember_me_var)
remember_me_checkbox.pack(pady=12, padx=10)

app.mainloop()


