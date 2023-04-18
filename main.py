import flask as fl
import pandas as pd
import requests
import sqlite3
import json
import hashlib

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
        return '''
            <h1>Práctica 2 SI</h1>
            <h2>Top X de IPs de origen más problemáticas:</h2>
            <form action="topIPs" method="POST">
                <label for="nombre">Ingresa tu número:</label>
                <input type="number" id="topIPs" name="topIPs"><br>
                <button type="submit">Ver</button><br>
            </form>
            <h2>Top X de dispositivos más vulnerables:</h2>
            <form action="topDevices" method="POST">
                <label>Ingresa tu número:</label>
                <input type="number" id="topDevices" name="topDevices"><br>
                <button type="submit">Ver</button><br>
            </form>
            <h2>Top X dispositivos peligrosos:</h2>
            <form action="dangerDev" method="POST">
                <label for="nombre">Ingresa tu número:</label>
                <input type="number" id="dangerDev" name="dangerDev"><br>
                <input type="checkbox" id="dangerCheck" name="dangerCheck"> mostrar información de dispositivios peligrosos<br>
                <input type="checkbox" id="noDangerCheck" name="noDangerCheck"> mostrar información de dispositivios no peligrosos<br>
                <button type="submit">Ver</button><br>
            </form>
            <h2>Últimas 10 vulnerabilidades:</h2>
            <button> <a href="/last10cve"> Ver</a></button><br>
            
            </form>
            <h2>Zona usuarios:</h2>
            <form action="login" method="POST">
                <label>Usuario:</label>
                <input type="text" id="userName" name="userName"><br>
                <label>Contraseña:</label>
                <input type="password" id="userPass" name="userPass"><br>
                <button type="submit">Ver</button><br>
            </form>
        '''

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
        html = f'<h1>Top {ips} de IPs de origen más problemáticas:</h1>'
        html += '<ul>'
        for row in rows:
            html += f'<li>{row[0]} ({row[1]} alertas)</li>'
        html += '</ul>'
        html += '<button> <a href="/"> Volver</a></button>'
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
        html = f'<h1>Top {devices} de dispositivos peligrosos:</h1>'
        html += '<ul>'
        for row in rows:
            html += f'<li>{row[0]} ({row[1]} servicios inseguros)</li>'
        html += '</ul>'
        html += '<button> <a href="/"> Volver</a></button>'
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

        cur.execute("SELECT id,ROUND(CAST(servicios_inseguros AS FLOAT) / servicios * 100, 2) as div FROM devices WHERE servicios > 0 and div > 33 GROUP BY id ORDER BY div DESC LIMIT {}".format(devices))
        rows = cur.fetchall()
        html = f'<h1>Top {devices} de dispositivos más peligrosos:</h1>'
        html += '<ul>'
        for row in rows:
            html += f'<li>{row[0]} ({row[1]}% servicios inseguros)</li>'
        html += '</ul>'

        if 'dangerCheck' in fl.request.form and fl.request.form['dangerCheck'].strip():
            cur.execute("SELECT id,ROUND(CAST(servicios_inseguros AS FLOAT) / servicios * 100, 2) as div FROM devices WHERE servicios > 0 and div > 33 GROUP BY id ORDER BY div DESC")
            rows = cur.fetchall()
            html += f'<h2>Información de dispositivos peligrosos:</h2>'
            html += '<ul>'
            for row in rows:
                html += f'<li>{row[0]} ({row[1]}% servicios inseguros)</li>'
            html += '</ul>'

        if 'noDangerCheck' in fl.request.form and fl.request.form['noDangerCheck'].strip():
            cur.execute("SELECT id,ROUND(CAST(servicios_inseguros AS FLOAT) / servicios * 100, 2) as div FROM devices WHERE div <= 33 OR div IS NULL GROUP BY id ORDER BY div DESC")
            rows = cur.fetchall()
            html += f'<h2>Información de dispositivos no peligrosos:</h2>'
            html += '<ul>'
            for row in rows:
                html += f'<li>{row[0]} ({row[1]}% servicios inseguros)</li>'
            html += '</ul>'

        html += '<button> <a href="/"> Volver</a></button>'
        con.commit()
        return html

    @app.route('/last10cve', methods=['POST','GET'])
    def last10cve():
        url = "https://cve.circl.lu/api/last"
        response = requests.get(url)
        data = response.json()[:10]
        html = f'<h1>Últimas 10 vulnerabilidades</h1>'
        html += '<ul>'
        for row in data:
            html += f'<li>Modified:{row["Modified"]},Published:{row["Published"]},Id:{row["id"]}</li>'
        html += '</ul>'
        html += '<button> <a href="/"> Volver</a></button>'
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
            html += '<ul>'
            for row in rows:
                html += f'''
                            <li>Usuario: {row[0]}</li><br>
                            <li>Ip: {row[1]}</li><br>
                            <li>Localización: {row[2]}</li><br>
                            <li>Responsable: {row[3]}</li><br>
                            <li>Número de puertos abiertos: {row[5]}</li><br>
                            <li>Puertos abiertos: {row[4]}</li><br>
                            <li>Número de servicios: {row[6]}</li><br>
                            <li>Número de servicios inseguros: {row[7]}</li><br>
                            <li>Número de vulnerabilidades: {row[8]}</li><br>
                        '''
            html += '</ul>'
            html += '<button> <a href="/"> Volver</a></button>'
            con.commit()
            return html
        else:
            html += f'<p>El usuario o contraseña son incorrectos</p>'

        return html


    if __name__ == '__main__':
        app.run(debug=True)


createBase()
flask()


