from flask import Flask, request, jsonify, render_template_string
from threading import Thread
import time
import random

app = Flask(__name__)

# Simulated appliances and their energy usage limits (Watts)
appliances = {
    "fridge": {"current_usage": 0, "limit": 150, "status": "ON"},
    "ac": {"current_usage": 0, "limit": 1000, "status": "OFF"},
    "heater": {"current_usage": 0, "limit": 1200, "status": "OFF"},
    "light": {"current_usage": 0, "limit": 100, "status": "ON"},
}

# HTML template embedded as a string
html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8" />
    <title>Intelligent Home Energy Management</title>
    <style>
        body { font-family: Arial, sans-serif; background:#f4f7f8; padding: 40px; }
        h1 { text-align: center; }
        .appliance { background: white; border-radius: 8px; margin: 20px auto; padding: 20px; max-width: 400px; box-shadow: 0 4px 6px rgba(0,0,0,0.1); }
        .appliance h2 { margin: 0 0 10px; }
        .status { font-weight: bold; }
        button { padding: 10px 20px; font-size: 16px; border: none; border-radius: 5px; cursor: pointer; }
        .on { background: #4caf50; color: white; }
        .off { background: #f44336; color: white; }
    </style>
</head>
<body>
    <h1>Home Energy Management System</h1>
    {% for name, data in appliances.items() %}
    <div class="appliance" id="{{name}}">
        <h2>{{name | capitalize}}</h2>
        <p>Current Usage: <span class="usage">{{data.current_usage}}</span> Watts</p>
        <p>Limit: <span class="limit">{{data.limit}}</span> Watts</p>
        <p>Status: <span class="status">{{data.status}}</span></p>
        {% if data.status == 'ON' %}
        <button class="off" onclick="toggleAppliance('{{name}}', 'OFF')">Turn OFF</button>
        {% else %}
        <button class="on" onclick="toggleAppliance('{{name}}', 'ON')">Turn ON</button>
        {% endif %}
    </div>
    {% endfor %}
<script>
    function toggleAppliance(appliance, action) {
        fetch('/control', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ appliance, action })
        }).then(response => response.json()).then(data => {
            alert(data.message);
            refreshStatus();
        });
    }

    function refreshStatus() {
        fetch('/status').then(res => res.json()).then(data => {
            for (const [appliance, values] of Object.entries(data)) {
                const container = document.getElementById(appliance);
                container.querySelector('.usage').textContent = values.current_usage;
                container.querySelector('.status').textContent = values.status;
                const button = container.querySelector('button');
                if (button) {
                    if (values.status == 'ON') {
                        button.textContent = 'Turn OFF';
                        button.className = 'off';
                        button.onclick = () => toggleAppliance(appliance, 'OFF');
                    } else {
                        button.textContent = 'Turn ON';
                        button.className = 'on';
                        button.onclick = () => toggleAppliance(appliance, 'ON');
                    }
                }
            }
        });
    }

    setInterval(refreshStatus, 5000); // refresh every 5 seconds
</script>
</body>
</html>
'''

def simulate_energy_usage():
    while True:
        for appliance in appliances:
            if appliances[appliance]["status"] == "ON":
                base = appliances[appliance]["limit"]
                appliances[appliance]["current_usage"] = random.randint(int(base*0.5), int(base*1.5))
            else:
                appliances[appliance]["current_usage"] = 0
        time.sleep(5)

def send_sms_alert(appliance, usage):
    # Simulate SMS alert by printing
    print(f"ALERT: {appliance.upper()} consumption {usage}W exceeded limit {appliances[appliance]['limit']}W!")

def monitor_energy():
    while True:
        for appliance, data in appliances.items():
            if data["current_usage"] > data["limit"]:
                send_sms_alert(appliance, data["current_usage"])
        time.sleep(5)

@app.route('/')
def home():
    return render_template_string(html_template, appliances=appliances)

@app.route('/control', methods=['POST'])
def control():
    data = request.json
    appliance = data.get("appliance")
    action = data.get("action")
    if appliance in appliances and action in ["ON", "OFF"]:
        appliances[appliance]["status"] = action
        if action == "OFF":
            appliances[appliance]["current_usage"] = 0
        return jsonify({"message": f"{appliance.capitalize()} turned {action}"}), 200
    return jsonify({"message": "Invalid appliance or action"}), 400

@app.route('/status')
def status():
    return jsonify(appliances)

if __name__ == '__main__':
    Thread(target=simulate_energy_usage, daemon=True).start()
    Thread(target=monitor_energy, daemon=True).start()
    app.run(debug=True)
