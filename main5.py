from flask import Flask, jsonify, render_template_string, request
from threading import Thread
import time
import random

app = Flask(__name__)

appliances = {
    "fridge": {"current_usage": 0, "limit": 150, "status": "ON"},
    "ac": {"current_usage": 0, "limit": 1000, "status": "OFF"},
    "heater": {"current_usage": 0, "limit": 1200, "status": "OFF"},
    "light": {"current_usage": 0, "limit": 100, "status": "ON"},
}

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
        .dashboard {display:flex; flex-wrap:wrap; gap:24px; justify-content:center;}
        .panel {background:#223d6a; border-radius:12px; box-shadow:0 4px 16px #0003; padding:24px; margin:12px 0; min-width:320px;}
        .panel h2 {font-size:18px; margin-bottom:10px;}
        .appliances {margin-top:30px;}
        .appliance {background:#243e66; border-radius:8px; margin:8px 0; padding:12px;}
        .appliance span {font-weight:bold;}
        .btn {padding:6px 18px; font-size:14px; border:none; border-radius:5px; cursor:pointer;}
        .on {background:#4caf50; color:white;}
        .off {background:#f44336; color:white;}
        .charts {display:flex; flex-wrap:wrap; gap:24px; margin-top:20px;}
        canvas {background:#1a355a; margin-top:15px;}
    </style>
</head>
<body>
    <div class="container">
      <h1>🏠 Intelligent Home Energy Management System</h1>
      <div class="dashboard">
        <div class="panel">
          <h2>Usage Estimate</h2>
          <canvas id="usageChart" width="320" height="200"></canvas>
        </div>
        <div class="panel">
          <h2>Active Appliances</h2>
          <div id="applianceList"></div>
        </div>
        <div class="panel">
          <h2>Energy Intensity</h2>
          <canvas id="intensityChart" width="200" height="200"></canvas>
        </div>
        <div class="panel">
          <h2>Carbon Footprint</h2>
          <canvas id="emissionsChart" width="200" height="200"></canvas>
        </div>
      </div>
    </div>
    <script>
      function renderUsage() {
        fetch('/usage').then(res=>res.json()).then(data=>{
          new Chart(document.getElementById('usageChart'), {
            type:'line',
            data:{
              labels:data.dates,
              datasets:[
                {label:'Till Now',data:data.current,borderColor:'#2bdcff',backgroundColor:'#233b5b'},
                {label:'Predicted',data:data.predicted,borderColor:'#ffe100',backgroundColor:'#233b5b'}
              ]
            },
            options:{plugins:{title:{display:true,text:'Usage Estimate'}},scales:{y:{color:'#eee'}},legend: {labels:{color:'#eee'}}}
          });
        });
      }

      function renderAppliances() {
        fetch('/status').then(res=>res.json()).then(data=>{
          let inner = '';
          for (let [k,v] of Object.entries(data)) {
            inner += `<div class="appliance">
              <span>${k.charAt(0).toUpperCase()+k.slice(1)}</span>: 
              Usage <span>${v.current_usage}W</span> / Limit <span>${v.limit}W</span> - Status <span class="status">${v.status}</span> 
              <button class="${v.status=='ON'?'off':'on'} btn" onclick="toggleAppliance('${k}','${v.status=='ON'?'OFF':'ON'}')">Turn ${v.status=='ON'?'OFF':'ON'}</button>
            </div>`;
          }
          document.getElementById('applianceList').innerHTML = inner;
        });
      }

      function renderIntensity() {
        fetch('/intensity').then(res=>res.json()).then(data=>{
          new Chart(document.getElementById('intensityChart'), {
            type:'doughnut',
            data:{
              labels:['Energy Intensity','Remaining'],
              datasets:[{data:[data.intensity,100-data.intensity],backgroundColor:['#2bdcff','#eee']}]
            },
            options:{plugins:{title:{display:true,text:data.intensity+' kWh/Sqft'}},legend: {labels:{color:'#eee'}}}
          });
        });
      }

      function renderEmissions() {
        fetch('/emissions').then(res=>res.json()).then(data=>{
          new Chart(document.getElementById('emissionsChart'), {
            type:'bar',
            data:{
              labels:['Emission Till Date','Emission Predicted','Green Energy'],
              datasets:[{label:'kg CO2 / kWh',data:[data.CO2_now,data.CO2_predicted,data.green_energy],backgroundColor:['#ff6384','#36a2eb','#4caf50']}]
            },
            options:{plugins:{title:{display:true,text:'Goal: '+data.goal}},scales:{y:{color:'#eee'}},legend: {labels:{color:'#eee'}}}
          });
        });
      }

      function toggleAppliance(appliance, action) {
        fetch('/control', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ appliance, action })
        }).then(response=>response.json()).then(data=>{
          alert(data.message);
          renderAppliances();
        });
      }

      window.onload = function() {
        renderUsage();
        renderAppliances();
        renderIntensity();
        renderEmissions();
        setInterval(()=>{
          renderUsage();
          renderAppliances();
          renderIntensity();
          renderEmissions();
        }, 6000);
      }
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
    print(f"ALERT: {appliance.upper()} consumption {usage}W exceeded limit {appliances[appliance]['limit']}W!")

def monitor_energy():
    while True:
        for appliance, data in appliances.items():
            if data["current_usage"] > data["limit"]:
                send_sms_alert(appliance, data["current_usage"])
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
    dates = ["Jun 1", "Jun 8", "Jun 15", "Jun 22", "Jun 29"]
    current_usage = [30, 60, 90, 120, 164]
    predicted_usage = [60, 120, 220, 340, 439]
    return jsonify({"dates": dates, "current": current_usage, "predicted": predicted_usage})

@app.route('/intensity')
def intensity():
    intensity = random.randint(40, 55)
    return jsonify({"intensity": intensity})

@app.route('/emissions')
def emissions():
    CO2_now = round(random.uniform(30, 40), 1)
    CO2_predicted = round(random.uniform(170, 190), 1)
    green_energy = random.randint(25, 35)
    goal = 40
    return jsonify({
        "CO2_now": CO2_now,
        "CO2_predicted": CO2_predicted,
        "green_energy": green_energy,
        "goal": goal
    })

if __name__ == '__main__':
    Thread(target=simulate_energy_usage, daemon=True).start()
    Thread(target=monitor_energy, daemon=True).start()
    app.run(debug=True)
