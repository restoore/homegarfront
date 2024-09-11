import os
import redis
from datetime import datetime, timedelta
import yaml


from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for)

app = Flask(__name__)

# Version de l'application
VERSION = "1.0.0"

config_file = 'config.yml'

# Load the configuration from a YAML file
with open(config_file, 'rb') as f:
    config = yaml.unsafe_load(f)

# Connexion Redis
r = redis.Redis(
    host=config['redis']['host'], 
    port=6380, 
    password=config['redis']['acces-key'], 
    ssl=True
)

def get_devices_from_redis():
    devices = []
    # Récupérer tous les keys de type "alert_*_name" qui représentent les devices
    device_keys = r.keys('alert_*_name')
    
    # Pour chaque device trouvé, extraire l'ID et le nom
    for key in device_keys:
        # Extraire l'ID du device à partir du key Redis (e.g., 'alert_49671_name' => ID = 49671)
        device_id = key.decode().split('_')[1]
        # Récupérer le nom du device depuis Redis
        device_name = r.get(key).decode() if r.get(key) else 'Unnamed Device'
        # Ajouter le device à la liste
        devices.append({'device_id': device_id, 'device_name': device_name})
    return devices

@app.route('/devices')
@app.route('/')
def list_devices():
    # Récupérer la liste des devices depuis Redis
    devices = get_devices_from_redis()
    return render_template('device_list.html', 
                           devices=devices,
                           version=VERSION)

@app.route('/device/<int:device_id>', methods=['GET', 'POST'])
def device_config(device_id):
    # Clés Redis spécifiques au device_id
    alert_name_key = f"alert_{device_id}_name"
    alert_curr_temp_key = f"alert_{device_id}_curr_temp"
    alert_time_key = f"alert_{device_id}_time"
    alert_max_temp_key = f"alert_{device_id}_max_temp"
    alert_enabled_key = f"alert_{device_id}_enabled"
    alert_time_next_key = f"alert_{device_id}_time_next"

    if request.method == 'POST':
        # Récupérer les données du formulaire
        device_name = request.form['deviceName']
        max_temperature = request.form['maxTemperature']
        alert_enabled =  1 if request.form.get('alertSwitch') == 'on' else 0
        time_next_delta = int(request.form['alertInterval'])  # Récupérer le nombre d'heures à ajouter à la date actuelle


        # Mettre à jour Redis
        r.set(alert_name_key, device_name)
        r.set(alert_max_temp_key, max_temperature)
        r.set(alert_enabled_key, alert_enabled)
        # Calculer la nouvelle date et l'enregistrer
        new_time_next = datetime.now() + timedelta(hours=time_next_delta)
        r.set(alert_time_next_key, new_time_next.isoformat())  # Stocker en format ISO
        return redirect(url_for('device_config', device_id=device_id))

    # Lecture des données depuis Redis
    device_name = r.get(alert_name_key).decode() if r.get(alert_name_key) else ""
    try:
        curr_temp = float(r.get(alert_curr_temp_key).decode()) if r.get(alert_curr_temp_key) else "N/A"
        curr_temp = round(curr_temp, 1)  # Arrondir à une décimale
    except ValueError:
        curr_temp = "N/A"  # Si la valeur n'est pas un nombre, gérer l'exception
    max_temp = r.get(alert_max_temp_key).decode() if r.get(alert_max_temp_key) else "0"
    enabled = True if r.get(alert_enabled_key).decode() == "1" else False
    
    # Lire la date du prochain relevé, ou prendre la date actuelle si elle n'existe pas
    time_next = r.get(alert_time_next_key).decode() if r.get(alert_time_next_key) else datetime.now().isoformat()
    # Calculer l'écart entre maintenant et le prochain relevé (en heures)
    time_next_dt = datetime.fromisoformat(time_next)
    time_diff = (time_next_dt - datetime.now()).total_seconds() / 3600
    time_diff = int(min(max(time_diff, 0), 48))  # Limiter entre 0 et 48 heures
    
    time = r.get(alert_time_key).decode() if r.get(alert_time_key) else "N/A"
    time_dt = datetime.fromisoformat(time)
    
    # Rendre la page avec les données remplies
    return render_template('device_form.html', 
                           device_id=device_id, 
                           device_name=device_name, 
                           curr_temp=curr_temp, 
                           max_temp=max_temp, 
                           enabled=enabled,
                           time=time_dt,
                           time_diff=time_diff, 
                           time_next=time_next_dt,
                           version=VERSION
                           )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
   app.run()
