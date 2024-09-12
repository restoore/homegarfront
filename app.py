import os
import redis
from datetime import datetime, timedelta
import pytz
import yaml


from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for,flash)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Nécessaire pour utiliser flash

# Version de l'application
VERSION = "1.1.0"

config_file = 'config.yml'

timezone = pytz.timezone('Europe/Paris')

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
    device_keys = r.keys('*_alert_name')
    
    # Pour chaque device trouvé, extraire l'ID et le nom
    for key in device_keys:
        # Extraire l'ID du device à partir du key Redis (e.g., 'alert_49671_name' => ID = 49671)
        device_id = key.decode().split('_')[0]
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
    # Créer un dictionnaire pour stocker les valeurs
    alert_data = {}
    keys = r.keys(f"{device_id}_alert_*")
    # Itérer sur toutes les clés et les assigner à l'objet
    for key in keys:
        # Extraire le nom de l'attribut à partir de la clé Redis (supprimer l'ID et le séparateur "_")
        attr_name = key.decode().replace(f"{device_id}_", "")
        value = r.get(key).decode() if r.get(key) is not None else None
        alert_data[attr_name] = value
        
    if request.method == 'POST':
        # Parcourir les données soumises dans le formulaire et les sauvegarder dans Redis
        for key, value in request.form.items():
            # Sauvegarder chaque valeur du formulaire dans Redis avec l'ID
            redis_key = f"{device_id}_{key}"
            r.set(redis_key, value)
        # Exception pour la check box alert_enabled
        if  request.form.get('alert_enabled') is None:
             r.set(f"{device_id}_alert_enabled", '0')
        # Si date frequence de mise à jour n'a pas changé, on ne recalcule pas la date
        if  alert_data["alert_frequency"] != request.form.get("alert_frequency"):
            # Calculer la nouvelle date et l'enregistrer
            alert_frequency = int(request.form['alert_frequency'])
            alert_next_check = datetime.now(timezone) + timedelta(hours=alert_frequency)
            r.set(f"{device_id}_alert_next_check", alert_next_check.strftime('%Y-%m-%d %H:%M:%S'))
        
        flash('Data have been successfully recorded 👌', 'success')  # 'success' est la catégorie de l'alerte
        return redirect(url_for('device_config', device_id=device_id))
    
    # On met en forme les données
    alert_last_check = timezone.localize(datetime.strptime(alert_data['alert_last_check'], '%Y-%m-%d %H:%M:%S'))
    alert_data['alert_last_check'] = alert_last_check.strftime("%d/%m %H:%M")
    alert_next_check = timezone.localize(datetime.strptime(alert_data['alert_next_check'], '%Y-%m-%d %H:%M:%S'))
    alert_data['alert_next_check'] = alert_next_check.strftime("%d/%m %H:%M")
    # Rendre la page avec les données remplies
    return render_template('device_form.html', 
                           data=alert_data,
                           device_id=device_id,
                           version=VERSION
                           )


@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
   app.run()
