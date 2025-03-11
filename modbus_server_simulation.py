"""
Purpose: Simulates a real Modbus device (PLC) by acting as a Modbus TCP server.
Functionality:
Listens on localhost:5020 for Modbus TCP requests.
Holds register values that can be read by a client.
Emulates a machine with registers for temperature, oil level, cycle count, stops, etc.
Allows testing without needing a real PLC.
"""

# from pymodbus.server import StartTcpServer
# from pymodbus.datastore import ModbusSequentialDataBlock
# from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
# from pymodbus.device import ModbusDeviceIdentification
# from threading import Thread
# import random
# import time
# from http.server import BaseHTTPRequestHandler, HTTPServer

# # Dummy HTTP server to satisfy Render's port scanner
# class DummyHttpHandler(BaseHTTPRequestHandler):
#     def do_GET(self):
#         self.send_response(200)
#         self.end_headers()
#         self.wfile.write(b"OK")

# def run_http_server():
#     http_server = HTTPServer(("0.0.0.0", 8080), DummyHttpHandler)
#     print("Dummy HTTP server running on 0.0.0.0:8080")
#     http_server.serve_forever()


# # Define a function to update values dynamically
# def update_registers(context):
#     while True:
#         temperature = random.randint(20, 100)  # Simulated temperature in °C
#         oil_level = random.randint(0, 100)    # Oil level percentage
#         cycle_count = random.randint(100, 10000)
#         stops = random.randint(0, 50)

#         # Update registers
#         context[0].setValues(3, 100, [temperature])  # Register 100: Temperature
#         context[0].setValues(3, 101, [oil_level])    
#         context[0].setValues(3, 102, [cycle_count]) 
#         context[0].setValues(3, 103, [stops])

#         time.sleep(1)  # Update every 1 seconds

# # Define the Modbus data store
# store = ModbusSlaveContext(
#     di=ModbusSequentialDataBlock(0, [0] * 100),
#     co=ModbusSequentialDataBlock(0, [0] * 100),
#     hr=ModbusSequentialDataBlock(0, [0] * 100),  # Holding Registers
#     ir=ModbusSequentialDataBlock(0, [0] * 100)
# )

# context = ModbusServerContext(slaves=store, single=True)

# # Start the register update thread
# Thread(target=update_registers, args=(context,), daemon=True).start()

# # Start Modbus TCP Server
# print("Starting Modbus Server on 0.0.0.0:5020...")
# StartTcpServer(context, address=("0.0.0.0", 5020))






from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from threading import Thread
import random
import time
from fastapi import FastAPI
import uvicorn

# Create a FastAPI app
app = FastAPI()

# Simple HTTP endpoint to satisfy Render's port scanner
@app.get("/")
def read_root():
    return {"message": "Modbus server is running"}

# Define a function to update values dynamically
def update_registers(context):
    while True:
        temperature = random.randint(20, 100)  # Simulated temperature in °C
        oil_level = random.randint(0, 100)    # Oil level percentage
        cycle_count = random.randint(100, 10000)
        stops = random.randint(0, 50)

        # Update registers
        context[0].setValues(3, 100, [temperature])  # Register 100: Temperature
        context[0].setValues(3, 101, [oil_level])    
        context[0].setValues(3, 102, [cycle_count]) 
        context[0].setValues(3, 103, [stops])

        time.sleep(1)  # Update every 1 seconds

# Define the Modbus data store
store = ModbusSlaveContext(
    di=ModbusSequentialDataBlock(0, [0] * 100),
    co=ModbusSequentialDataBlock(0, [0] * 100),
    hr=ModbusSequentialDataBlock(0, [0] * 100),  # Holding Registers
    ir=ModbusSequentialDataBlock(0, [0] * 100)
)

context = ModbusServerContext(slaves=store, single=True)

# Start the register update thread
Thread(target=update_registers, args=(context,), daemon=True).start()

# Start Modbus TCP Server in a separate thread
def run_modbus_server():
    print("Starting Modbus Server on 0.0.0.0:5020...")
    StartTcpServer(context, address=("0.0.0.0", 5020))

Thread(target=run_modbus_server, daemon=True).start()

# Start FastAPI HTTP server
if __name__ == "__main__":
    print("Starting FastAPI HTTP server on 0.0.0.0:8080...")
    uvicorn.run(app, host="0.0.0.0", port=8080)