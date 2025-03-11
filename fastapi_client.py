"""
Purpose: Provides an API layer for accessing Modbus data via HTTP.
Functionality:
Uses FastAPI to create an endpoint (/read_data) that reads registers from the Modbus server.
Acts as a bridge between HTTP requests and Modbus TCP communication.
Connects to the Modbus server (modbus_server_simulation.py), reads registers, and returns data in JSON format.
It renders on http://127.0.0.1:8000/
"""

import os
import csv
import socket
from fastapi import FastAPI, Request, BackgroundTasks, HTTPException
from fastapi.templating import Jinja2Templates
from pymodbus.client import ModbusTcpClient
from fastapi.responses import HTMLResponse
import atexit
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Initialize FastAPI app
app = FastAPI()

# Initialize Jinja2 template renderer
templates = Jinja2Templates(directory="templates")

# Modbus server details
MODBUS_SERVER_IP =  os.getenv("MODBUS_SERVER_IP", "127.0.0.1")
MODBUS_SERVER_PORT = int(os.getenv("MODBUS_SERVER_PORT", 5020))

def is_modbus_server_running(host=MODBUS_SERVER_IP, port=MODBUS_SERVER_PORT):
    """Check if the Modbus server is running."""
    try:
        client = ModbusTcpClient(host=host, port=port)
        client.connect()
        is_connected = client.is_socket_open()
        client.close()
        return is_connected
    except (socket.error, ConnectionRefusedError) as e:
        logging.error(f"Modbus server connection error: {e}")
        return False

def read_modbus_data():
    """Reads Modbus data without saving it to CSV."""
    try:
        client = ModbusTcpClient(MODBUS_SERVER_IP, port=MODBUS_SERVER_PORT)
        client.connect()
        
        if not client.is_socket_open():
            logging.error("Failed to connect to Modbus server.")
            return None

        response = client.read_holding_registers(address=100, count=4)  # Read 4 registers
        client.close()

        if response.isError():
            logging.error(f"Modbus read error: {response}")
            return None

        return {
            "temperature": response.registers[0],
            "oil_level": response.registers[1],
            "cycle_count": response.registers[2],
            "stops": response.registers[3]       
        }
    except Exception as e:
        logging.error(f"Error reading Modbus data: {e}")
        return None

@app.get("/fetch_data")
async def fetch_data():
    """Fetches Modbus data for the UI without saving it."""
    if not is_modbus_server_running():
        raise HTTPException(status_code=500, detail="Modbus server is down or unreachable.")
    
    data = read_modbus_data()
    if data is None:
        raise HTTPException(status_code=500, detail="Failed to read Modbus registers")
    
    return data

@app.get("/read_data")
async def read_data():
    """Fetches Modbus data and saves it to CSV."""
    data = read_modbus_data()
    if data is None:
        return {"error": "Failed to read Modbus registers"}
    
    save_data_to_csv(data)  # Save only if successful
    return data

def save_data_to_csv(data):
    """Saves Modbus data to CSV if it's different from the last entry, with a timestamp."""
    file_path = r"C:\Users\SkyNet_1\Downloads\modbus_data.csv"
    file_exists = os.path.exists(file_path)

    # Read last saved row and avoid duplicate entries
    last_row = read_last_csv_row(file_path)
    if last_row == data:
        return  

    # Add timestamp to data
    data_with_timestamp = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **data  # Merge the existing data
    }

    try:
        with open(file_path, mode="a", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["timestamp", "temperature", "oil_level", "cycle_count", "stops"])
            if not file_exists:
                writer.writeheader()
            writer.writerow(data_with_timestamp)
    except Exception as e:
        logging.error(f"Error saving data to CSV: {e}")

def read_last_csv_row(file_path):
    """Reads the last row from CSV to prevent duplicate writes."""
    if os.path.exists(file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
            if len(lines) > 1:
                values = lines[-1].strip().split(",")
                return {
                    "temperature": int(values[1]),
                    "oil_level": int(values[2]),
                    "cycle_count": int(values[3]),
                    "stops": int(values[4])              
                }
    return None  # If file is empty or doesn't exist

# Scheduler to save data every 30 seconds
scheduler = BackgroundScheduler()
scheduler.add_job(func=lambda: save_data_to_csv(read_modbus_data()), trigger="interval", seconds=30)
scheduler.add_job(func=lambda: save_data_to_csv(read_modbus_data()), trigger="interval", seconds=30)
scheduler.start()

# Shutdown scheduler when app exits
atexit.register(lambda: scheduler.shutdown())

@app.get("/", response_class=HTMLResponse)
async def read_data_ui(request: Request):
    """Serves the UI with live Modbus data."""
    # Default values for data
    data = {
        "temperature": "--",
        "oil_level": "--",
        "cycle_count": "--",
        "stops": "--"
    } 

    # Default values for identity
    identity = {
        "VendorName": "SkyNet_PLCs",
        "ProductCode": "sk-xyz",
        "ProductName": "PLC_simulator",
        "ModelName": "sk_393939",
        "VendorUrl": "https:/google.com",
        "MajorMinorRevision": "v1.0"
    } 

    return templates.TemplateResponse("index.html", {"request": request, "data": data, "identity": identity})