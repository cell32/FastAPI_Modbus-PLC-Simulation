"""
Purpose: Simulates a real Modbus device (PLC) by acting as a Modbus TCP server.
Functionality:
Listens on localhost:5020 for Modbus TCP requests.
Holds register values that can be read by a client.
Emulates a machine with registers for temperature, oil level, cycle count, stops, etc.
Allows testing without needing a real PLC.
"""

from pymodbus.server import StartTcpServer
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.datastore import ModbusSlaveContext, ModbusServerContext
from pymodbus.device import ModbusDeviceIdentification
from threading import Thread
import random
import time

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

# Start Modbus TCP Server
print("Starting Modbus Server on 0.0.0.0:5020...")
StartTcpServer(context, address=("0.0.0.0", 5020))