from flask import Flask, jsonify, render_template_string, request
from threading import Thread
import time
import random
import smtplib
import ssl
from collections import deque
from datetime import datetime


app = Flask(__name__)


appliances = {
    "fridge": {"current_usage": 0, "limit": 150, "status": "ON"},
    "ac": {"current_usage": 0, "limit": 1000, "status": "OFF"},
    "heater": {"current_usage": 0, "limit": 1200, "status": "OFF"},
    "light": {"current_usage": 0, "limit": 100, "status": "ON"},
}


# Buffer for recent usage readings
usage_history = deque(maxlen=50)


html_template = '''
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8"/>
    <title>Energy Dashboard</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body {font-family:sans-serif; background:#1a355a; color:#eee; margin:0;}
        .container {width:1200px; margin:40px auto;}
        h1 {text-align:left; margin-left:10px;}
        .dashboard {
            display:flex; 
            flex-wrap:wrap; 
            gap:24px; 
            justify-content:center;
        }
        .panel {
            background:#223d6a; 
            border-radius:12px; 
            box-shadow:0 4px 16px #0003; 
            padding:24px; 
            margin:12px 0;
        }
        .panel:nth-child(1) { flex: 2 1 640px; }
        .panel:nth-child(2) { flex: 1 1 320px; }
        .panel:nth-child(3) { flex: 1.5 1 480px; }
        .panel h2 {font-size:18px; margin-bottom:10px;}
        .appliances {margin-top:30px;}
        /* Enhanced Active Appliances Styles */
        .appliance {
            background: linear-gradient(135deg, #274872, #1a2c58);
            border-radius: 12px;
            margin: 12px 0;
            padding: 16px 20px;
            box-shadow: 0 6px 18px rgba(0,0,0,0.4);
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .appliance:hover {
            transform: translateY(-4px);
            box-shadow: 0 12px 24px rgba(0,0,0,0.6);
        }
        .appliance .info {
            display: flex;
            flex-direction: column;
        }
        .appliance span.name {
            font-weight: 700;
            font-size: 18px;
            display: flex;
            align-items: center;
            gap: 8px;
            margin-bottom: 6px;
        }
        .status-dot {
            width: 14px;
            height: 14px;
            border-radius: 50%;
            background: #4caf50; /* Green for ON */
            display: inline-block;
        }
        .status-dot.off {
            background: #f44336; /* Red for OFF */
        }
        .usage-bar-container {
            width: 180px;
            height: 12px;
            background: #2a4980;
            border-radius: 8px;
            overflow: hidden;
            margin-top: 4px;
        }
        .usage-bar {
            height: 100%;
            background: #42a5f5;
            border-radius: 8px 0 0 8px;
            transition: width 0.4s ease;
        }
        .appliance span.usage-info {
            margin-top: 8px;
            font-size: 14px;
            color: #c1d8ff;
            letter-spacing: 0.5px;
        }
        .btn {
            min-width: 72px;
            font-weight: 600;
            font-size: 14px;
            box-shadow: 0 2px 8px rgba(0,0,0,0.25);
            border: none;
            border-radius: 5px;
            cursor: pointer;
            padding: 6px 18px;
        }
        .on {
            background: #4caf50;
            color: white;
        }
        .off {
            background: #f44336;
            color: white;
        }
        .charts {display:flex; flex-wrap:wrap; gap:24px; margin-top:20px;}
        canvas {background:#1a355a; margin-top:15px;}
    </style>
</head>
<body>
    <div class="container">
      <h1>🏠 Intelligent Home Energy Management System</h1>
      <div class="dashboard">
        <div class="panel">
          <h2>ENERGY USAGE BY APPLIANCE</h2>
          <canvas id="usageChart" width="320" height="200"></canvas>
        </div>
        <div class="panel">
          <h2>APPLIANCES</h2>
          <div id="applianceList"></div>
        </div>
        <div class="panel">
          <h2>Energy Consumption</h2>
          <canvas id="intensityChart" width="200" height="200"></canvas>
        </div>
      </div>
    </div>
    <script>
      var usageChartInstance = null;
      function renderUsage() {
        fetch('/usage').then(res => res.json()).then(data => {
          const ctx = document.getElementById('usageChart').getContext('2d');
          if (usageChartInstance) usageChartInstance.destroy();
          usageChartInstance = new Chart(ctx, {
            type: 'line',
            data: {
              labels: data.times,
              datasets: [
                { label: 'Fridge', data: data.fridge, borderColor: '#2bdcff', fill: false },
                { label: 'AC', data: data.ac, borderColor: '#ffe100', fill: false },
                { label: 'Heater', data: data.heater, borderColor: '#ff6384', fill: false },
                { label: 'Light', data: data.light, borderColor: '#36a2eb', fill: false }
              ]
            },
            options: {
              plugins: { title: { display: true, text: 'Current Usage (W)' } },
              scales: { y: { color: '#eee' } },
              legend: { labels: { color: '#eee' } }
            }
          });
        });
      }
      function renderAppliances() {
        fetch('/status').then(res => res.json()).then(data => {
            let inner = '';
            for (let [k, v] of Object.entries(data)) {
                const usagePercent = v.limit > 0 ? Math.min(100, Math.round((v.current_usage / v.limit) * 100)) : 0;
                inner += `
                <div class="appliance">
                  <div class="info">
                    <span class="name">
                      <span class="status-dot ${v.status === 'ON' ? '' : 'off'}"></span>
                      ${k.charAt(0).toUpperCase() + k.slice(1)}
                    </span>
                    <div class="usage-bar-container">
                      <div class="usage-bar" style="width: ${usagePercent}%;"></div>
                    </div>
                    <span class="usage-info">Usage: ${v.current_usage}W / Limit: ${v.limit}W (${usagePercent}%)</span>
                  </div>
                  <button class="${v.status === 'ON' ? 'off' : 'on'} btn" onclick="toggleAppliance('${k}','${v.status === 'ON' ? 'OFF' : 'ON'}')">
                    Turn ${v.status === 'ON' ? 'OFF' : 'ON'}
                  </button>
                </div>`;
            }
            document.getElementById('applianceList').innerHTML = inner;
        });
      }
      function renderIntensity() {
        fetch('/intensity').then(res => res.json()).then(data => {
          const colors = ['#2bdcff', '#ffe100', '#ff6384', '#36a2eb']; // colors for appliances
          new Chart(document.getElementById('intensityChart'), {
            type: 'doughnut',
            data: {
              labels: data.labels,
              datasets: [{
                data: data.data,
                backgroundColor: colors.slice(0, data.labels.length)
              }]
            },
            options: {
              plugins: {
                title: {
                  display: true,
                  text: 'Energy Consumption by Appliance (W)'
                }
              },
              legend: {
                labels: { color: '#eee' }
              }
            }
          });
        });
      }
      function toggleAppliance(appliance, action) {
        fetch('/control', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ appliance, action })
        }).then(response => response.json()).then(data => {
          alert(data.message);
          renderAppliances();
        });
      }
      window.onload = function() {
        renderUsage();
        renderAppliances();
        renderIntensity();
        setInterval(() => {
          renderUsage();
          renderAppliances();
          renderIntensity();
        }, 6000);
      }
    </script>
</body>
</html>
'''


def simulate_energy_usage():
    while True:
        record = {}
        for appliance in appliances:
            if appliances[appliance]["status"] == "ON":
                base = appliances[appliance]["limit"]
                appliances[appliance]["current_usage"] = random.randint(int(base * 0.5), int(base * 1.5))
            else:
                appliances[appliance]["current_usage"] = 0
            record[appliance] = appliances[appliance]["current_usage"]
        record["time"] = datetime.now().strftime("%H:%M:%S")
        usage_history.append(record)
        time.sleep(5)


smtp_server = "smtp.gmail.com"
port = 587   
sender_email = "reetakrana65@gmail.com"
receiver_email = "reetakrana36@gmail.com"
password = "pcup wvsc lagd vbkk"   


def send_email_alert(appliance, usage):
    message = f"""\
Subject: Energy Alert for {appliance.upper()}


ALERT: {appliance.upper()} consumption {usage}W exceeded limit {appliances[appliance]['limit']}W!
"""
    context = ssl.create_default_context()
    try:
        with smtplib.SMTP(smtp_server, port) as server:
            server.starttls(context=context)
            server.login(sender_email, password)
            server.sendmail(sender_email, receiver_email, message)
        print(f"Email alert sent for {appliance}!")
    except Exception as e:
        print(f"Failed to send email alert: {e}")


def monitor_energy():
    while True:
        for appliance, data in appliances.items():
            if data["current_usage"] > data["limit"]:
                send_email_alert(appliance, data["current_usage"])
        time.sleep(5)


@app.route('/')
def home():
    return render_template_string(html_template)


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


@app.route('/usage')
def usage():
    times = [rec['time'] for rec in usage_history]
    fridge = [rec.get('fridge', 0) for rec in usage_history]
    ac = [rec.get('ac', 0) for rec in usage_history]
    heater = [rec.get('heater', 0) for rec in usage_history]
    light = [rec.get('light', 0) for rec in usage_history]
    return jsonify({
        "times": times,
        "fridge": fridge,
        "ac": ac,
        "heater": heater,
        "light": light
    })


@app.route('/intensity')
def intensity():
    labels = [appliance.capitalize() for appliance in appliances.keys()]
    data = [appliance["current_usage"] for appliance in appliances.values()]
    return jsonify({"labels": labels, "data": data})


if __name__ == '__main__':
    Thread(target=simulate_energy_usage, daemon=True).start()
    Thread(target=monitor_energy, daemon=True).start()
    app.run(debug=True)
