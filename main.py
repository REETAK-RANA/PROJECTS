import time
import random
import json
from datetime import datetime
import matplotlib.pyplot as plt

# Simulated device energy usage data generator
def simulate_device_energy_usage():
    # Simulate power consumption in watts for devices
    devices = {
        "AC": random.uniform(500, 2000),
        "Heater": random.uniform(300, 1500),
        "Fridge": random.uniform(100, 400),
        "Lighting": random.uniform(50, 150),
        "WashingMachine": random.choice([0, random.uniform(400, 1200)])  # On or off randomly
    }
    return devices

# Log energy usage data with timestamp
def log_energy_usage(devices, filename="energy_log.json"):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = {"timestamp": timestamp, "devices": devices}
    with open(filename, "a") as f:
        f.write(json.dumps(log_entry) + "\n")

# Basic intelligent control based on threshold power limits
def control_devices(devices, power_threshold=3000):
    total_power = sum(devices.values())
    actions = {}
    if total_power > power_threshold:
        for device, power in devices.items():
            if device != "Fridge" and power > 0:
                actions[device] = "Turn OFF"
                devices[device] = 0  # Simulate device turned off
                total_power = sum(devices.values())
                if total_power <= power_threshold:
                    break
    else:
        for device in devices:
            if devices[device] == 0 and device != "Fridge":
                actions[device] = "Turn ON (simulated)"
                devices[device] = random.uniform(100, 1500)  # Simulate device turned on with random power
    return devices, actions

# Visualization of logged energy consumption trends
def visualize_energy_log(filename="energy_log.json"):
    timestamps = []
    total_powers = []
    with open(filename, "r") as f:
        for line in f:
            entry = json.loads(line)
            timestamps.append(datetime.strptime(entry["timestamp"], "%Y-%m-%d %H:%M:%S"))
            total_power = sum(entry["devices"].values())
            total_powers.append(total_power)
    plt.figure(figsize=(10, 5))
    plt.plot(timestamps, total_powers, label="Total Power Consumption (W)")
    plt.xlabel("Time")
    plt.ylabel("Power (Watts)")
    plt.title("Home Energy Consumption Over Time")
    plt.legend()
    plt.grid(True)
    plt.show()

# Main loop simulating continuous monitoring and control
def main():
    print("Starting Intelligent Home Energy Management System...")
    for _ in range(10):  # Run for 10 iterations as a demo
        devices = simulate_device_energy_usage()
        devices, actions = control_devices(devices)
        log_energy_usage(devices)
        print(f"Devices power: {devices}")
        print(f"Actions taken: {actions}")
        time.sleep(2)  # Simulate real-time delay

    visualize_energy_log()

if __name__ == "__main__":
    main()
