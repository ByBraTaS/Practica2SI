import flask as fl
import pandas as pd
import requests
import sqlite3
import json
import hashlib
from flask import render_template

def createBase():
    con = sqlite3.connect("database.db")

    #alerts to database
    alerts = pd.read_csv("data/alerts.csv")
    alerts.to_sql("alerts", con, if_exists="replace", index=False)

    #devices to database
    dev = open("data/devices.json")
    devices = json.load(dev)

    #tables
    cur = con.cursor()
    cur.execute("CREATE TABLE IF NOT EXISTS devices (id TEXT PRIMARY KEY, ip TEXT, localizacion TEXT, responsable_id TEXT, puertos_abiertos TEXT, no_puertos_abiertos INTEGER, servicios INTEGER, servicios_inseguros INTEGER, vulnerabilidades_detectadas INTEGER)")
    cur.execute("CREATE TABLE IF NOT EXISTS responsable (nombre TEXT, telefono TEXT, rol TEXT)")
    cur.execute("CREATE TABLE IF NOT EXISTS users (name TEXT PRIMARY KEY, password TEXT)")

    for d in devices:
        responsable = d['responsable']
        cur.execute("INSERT OR IGNORE INTO responsable (nombre,telefono,rol) VALUES (?, ?, ?)", (responsable['nombre'], responsable['telefono'], responsable['rol']))
        analisis = d['analisis']
        if analisis["puertos_abiertos"] == 'None':
            ports = 0
        else:
            ports = len(analisis["puertos_abiertos"])
        cur.execute("INSERT OR IGNORE INTO devices (id, ip, localizacion, responsable_id, puertos_abiertos, no_puertos_abiertos, servicios, servicios_inseguros, vulnerabilidades_detectadas) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (d['id'], d['ip'], d['localizacion'], responsable['nombre'], json.dumps(analisis['puertos_abiertos']), ports, analisis['servicios'], analisis['servicios_inseguros'], analisis['vulnerabilidades_detectadas']))
        password = d['id'].encode('utf-8')
        hash_object = hashlib.sha256()
        hash_object.update(password)
        hashed_pass = hash_object.hexdigest()
        cur.execute("INSERT OR IGNORE INTO users (name, password) VALUES (?, ?)", (d['id'], hashed_pass))



    con.commit()

def flask():
    app = fl.Flask(__name__)

    @app.route('/')
    def index():
        return render_template('Index.html')

    @app.route('/topIPs', methods=['POST'])
    def topIPs():
        con = sqlite3.connect("database.db")
        cur=con.cursor()
        if fl.request.form['topIPs'].strip():
            ips = int(fl.request.form['topIPs'])
            if ips < 0:
                ips = 0
        else:
            ips = 0
        cur.execute("SELECT origen, COUNT(*) as num_alertas FROM alerts WHERE prioridad = 1 GROUP BY origen ORDER BY num_alertas DESC LIMIT {}".format(ips))
        rows = cur.fetchall()
        html = f'<h1 style="color:#006699; text-align:center; font-size:30px; font-weight:bold;">Top {ips} de IPs de origen más problemáticas:</h1>'
        html += '<ul style="list-style: none; margin: 0; padding: 0; border: 1px solid #ccc; border-radius: 5px;">'

        for row in rows:
            html += f'<li style="padding: 10px 0; border-bottom: 1px solid #ccc;">{row[0]} ({row[1]} servicios inseguros)</li>'

        html += '</ul>'
        html += '<button style="background-color: #006699; color: #fff; border: none; border-radius: 3px; padding: 10px 20px; font-size: 16px; cursor: pointer;"> <a href="/" style="color: #fff; text-decoration: none;">Volver</a></button>'

        con.commit()
        return html

    @app.route('/topDevices', methods=['POST'])
    def topDevices():
        con = sqlite3.connect("database.db")
        cur=con.cursor()
        if fl.request.form['topDevices'].strip():
            devices = int(fl.request.form['topDevices'])
            if devices < 0:
                devices = 0
        else:
            devices = 0
        cur.execute("SELECT id,SUM(servicios_inseguros + vulnerabilidades_detectadas) as inseguros FROM devices GROUP BY id ORDER BY inseguros DESC LIMIT {}".format(devices))
        rows = cur.fetchall()
        html = f'<h1 style="color:#006699; text-align:center; font-size:30px; font-weight:bold;">Top {devices} de dispositivos peligrosos:</h1>'
        html += '<ul style="list-style: none; margin: 0; padding: 0; border: 1px solid #ccc; border-radius: 5px;">'
        for row in rows:
            html += f'<li style="padding: 10px 0; border-bottom: 1px solid #ccc;">{row[0]} ({row[1]} servicios inseguros)</li>'
        html += '</ul>'
        html += '<button style="background-color: #006699; color: #ffffff; border: none; border-radius: 3px; padding: 10px 20px; font-size: 16px; cursor: pointer;"> <a href="/"> Volver</a></button>'
        con.commit()
        return html

    @app.route('/dangerDev', methods=['POST'])
    def dangerDev():
        con = sqlite3.connect("database.db")
        cur=con.cursor()
        if fl.request.form['dangerDev'].strip():
            devices = int(fl.request.form['dangerDev'])
            if devices < 0:
                devices = 0
        else:
            devices = 0

        cur.execute("SELECT id, ip, responsable_id, ROUND(CAST(servicios_inseguros AS FLOAT) / servicios * 100, 2) as div FROM devices WHERE servicios > 0 and div > 33 GROUP BY id ORDER BY div DESC LIMIT {}".format(devices))
        rows = cur.fetchall()
        html = f'<h1 style="color:#006699; text-align:center; font-size:30px; font-weight:bold;">Top {devices} de dispositivos más peligrosos:</h1>'
        html += '<ul style="list-style: none; margin: 0; padding: 0; border: 1px solid #ccc; border-radius: 5px;">'
        for row in rows:
            html += f'<li style="padding: 10px 0; border-bottom: 1px solid #ccc;">ID:  {row[0]}/ IP: {row[1]} / RESPONSABLE: {row[2]} / SERVICIOS INSEGUROS: {row[3]}%</li>'
        html += '</ul>'

        if 'dangerCheck' in fl.request.form and fl.request.form['dangerCheck'].strip():
            cur.execute("SELECT id, ip, responsable_id, ROUND(CAST(servicios_inseguros AS FLOAT) / servicios * 100, 2) as div FROM devices WHERE servicios > 0 and div > 33 GROUP BY id ORDER BY div DESC")
            rows = cur.fetchall()
            html += f'<h2 style="color:#006699; text-align:center; font-size:30px; font-weight:bold;">Información de dispositivos peligrosos:</h2>'
            html += '<ul style="list-style: none; margin: 0; padding: 0; border: 1px solid #ccc; border-radius: 5px;">'
            for row in rows:
                html += f'<li style="padding: 10px 0; border-bottom: 1px solid #ccc;">ID:  {row[0]}/ IP: {row[1]}/ RESPONSABLE: {row[2]} / SERVICIOS INSEGUROS: {row[3]}%</li>'
            html += '</ul>'

        if 'noDangerCheck' in fl.request.form and fl.request.form['noDangerCheck'].strip():
            cur.execute("SELECT id, ip, responsable_id, ROUND(CAST(servicios_inseguros AS FLOAT) / servicios * 100, 2) as div FROM devices WHERE div <= 33 OR div IS NULL GROUP BY id ORDER BY div DESC")
            rows = cur.fetchall()
            html += f'<h2 style="color:#006699; text-align:center; font-size:30px; font-weight:bold;">Información de dispositivos no peligrosos:</h2>'
            html += '<ul style="list-style: none; margin: 0; padding: 0; border: 1px solid #ccc; border-radius: 5px;">'
            for row in rows:
                html += f'<li style="padding: 10px 0; border-bottom: 1px solid #ccc;">ID:  {row[0]} / IP: {row[1]} / RESPONSABLE: {row[2]} / SERVICIOS INSEGUROS: {row[3]}%</li>'
            html += '</ul>'

        html += '<button style="background-color: #006699; color: #ffffff; border: none; border-radius: 3px; padding: 10px 20px; font-size: 16px; cursor: pointer;"> <a href="/"> Volver</a></button>'
        con.commit()
        return html

    @app.route('/last10cve', methods=['POST','GET'])
    def last10cve():
        url = "https://cve.circl.lu/api/last"
        response = requests.get(url)
        data = response.json()[:10]
        html = '<h1 style="color:#006699; text-align:center; font-size:30px; font-weight:bold;">Últimas 10 vulnerabilidades</h1>'
        html += '<table border="2" cellpadding="10">'
        html += '<tr><th>Modified</th><th>Published</th><th>Id</th><th>Summary</th></tr>'
        for row in data:
            html += f'<tr><td>{row["Modified"]}</td><td>{row["Published"]}</td><td>{row["id"]}</td><td>{row["summary"]}</td></tr>'
        html += '</table>'
        html += '<button style="background-color: #006699; color: #ffffff; border: none; border-radius: 3px; padding: 10px 20px; font-size: 16px; cursor: pointer;"> <a href="/"> Volver</a></button>'
        return html

    @app.route('/login', methods=['POST'])
    def login():
        con = sqlite3.connect("database.db")
        cur = con.cursor()
        html = f'<h1>Información de usuario:</h1>'
        if fl.request.form['userName'].strip() and fl.request.form['userPass']:
            user = fl.request.form['userName']
            password = fl.request.form['userPass']
        else:
            html += f'<p>El usuario o contraseña son incorrectos</p>'
            user = "None"

        cur.execute("SELECT password FROM users WHERE name = ?", (user,))
        row = cur.fetchone()
        check = row[0]

        hash_object = hashlib.sha256()
        hash_object.update(password.encode('utf-8'))
        hashed_input_password = hash_object.hexdigest()

        if check == hashed_input_password:
            cur.execute("SELECT * FROM devices WHERE id='{}'".format(user))
            rows = cur.fetchall()
            html += '<ul style="list-style: none; padding: 0; margin: 0;">'
            for row in rows:
                html += f'''
                            <li style="padding: 10px 0; border-bottom: 1px solid #ccc;">Usuario: {row[0]}</li><br>
                            <li style="padding: 10px 0; border-bottom: 1px solid #ccc;">Ip: {row[1]}</li><br>
                            <li style="padding: 10px 0; border-bottom: 1px solid #ccc;">Localización: {row[2]}</li><br>
                            <li style="padding: 10px 0; border-bottom: 1px solid #ccc;">Responsable: {row[3]}</li><br>
                            <li style="padding: 10px 0; border-bottom: 1px solid #ccc;">Número de puertos abiertos: {row[5]}</li><br>
                            <li style="padding: 10px 0; border-bottom: 1px solid #ccc;">Puertos abiertos: {row[4]}</li><br>
                            <li style="padding: 10px 0; border-bottom: 1px solid #ccc;">Número de servicios: {row[6]}</li><br>
                            <li style="padding: 10px 0; border-bottom: 1px solid #ccc;">Número de servicios inseguros: {row[7]}</li><br>
                            <li style="padding: 10px 0; border-bottom: 1px solid #ccc;">Número de vulnerabilidades: {row[8]}</li><br>
                        '''
            html += '</ul>'
            html += '<button style="background-color: #006699; color: #fff; border: none; border-radius: 3px; padding: 10px 20px; font-size: 16px; cursor: pointer;"> <a href="/" style="color: #fff; text-decoration: none;"> <a href="/"> Volver</a></button>'
            con.commit()
            return html
        else:
            html += f'<p>El usuario o contraseña son incorrectos</p>'

        return html


    if __name__ == '__main__':
        app.run(debug=True)


createBase()
flask()


