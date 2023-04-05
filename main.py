import flask as fl
import pandas as pd
import sqlite3
import json

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
    cur.execute("CREATE TABLE IF NOT EXISTS responsable (nombre TEXT PRIMARY KEY, telefono TEXT, rol TEXT)")

    for d in devices:
        responsable = d['responsable']
        cur.execute("INSERT OR IGNORE INTO responsable (nombre,telefono,rol) VALUES (?, ?, ?)", (responsable['nombre'], responsable['telefono'], responsable['rol']))
        analisis = d['analisis']
        if analisis["puertos_abiertos"] == 'None':
            ports = 0
        else:
            ports = len(analisis["puertos_abiertos"])
        cur.execute("INSERT OR IGNORE INTO devices (id, ip, localizacion, responsable_id, puertos_abiertos, no_puertos_abiertos, servicios, servicios_inseguros, vulnerabilidades_detectadas) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)", (d['id'], d['ip'], d['localizacion'], responsable['nombre'], json.dumps(analisis['puertos_abiertos']), ports, analisis['servicios'], analisis['servicios_inseguros'], analisis['vulnerabilidades_detectadas']))

def flask():
    app = fl.Flask(__name__)

    @app.route('/')
    def index():
        return '''
            <h1>Práctica 2 SI</h1>
            <h2>Top X de IPs de origen más problemáticas:</h2>
            <form action="topIPs" method="POST">
                <label for="nombre">Ingresa tu número:</label>
                <input type="text" id="topIPs" name="topIPs">
                <button type="submit">Ver</button>
            </form>
            <h2>Top X de dispositivos más vulnerables:</h2>
            <form action="topDevices" method="POST">
                <label for="nombre">Ingresa tu número:</label>
                <input type="text" id="topDevices" name="topDevices">
                <button type="submit">Ver</button>
            </form>
        '''

    @app.route('/topIPs', methods=['POST'])
    def topIPs():
        con = sqlite3.connect("database.db")
        cur=con.cursor()
        ips = int(fl.request.form['topIPs'])
        cur.execute("SELECT origen, COUNT(*) as num_alertas FROM alerts WHERE prioridad = 1 GROUP BY origen ORDER BY num_alertas DESC LIMIT {}".format(ips))
        rows = cur.fetchall()
        html = f'<h1>Top {ips} de IPs de origen más problemáticas:</h1>'
        html += '<ul>'
        for row in rows:
            html += f'<li>{row[0]} ({row[1]} alertas)</li>'
        html += '</ul>'
        html += '<a href="/" class="button"> Volver</a>'
        con.commit()
        return html

    @app.route('/topDevices', methods=['POST'])
    def topDevices():
        con = sqlite3.connect("database.db")
        cur=con.cursor()
        devices = int(fl.request.form['topDevices'])
        cur.execute("SELECT id,SUM(servicios_inseguros + vulnerabilidades_detectadas) as inseguros FROM devices GROUP BY id ORDER BY inseguros DESC LIMIT {}".format(devices))
        rows = cur.fetchall()
        html = f'<h1>Top {devices} de dispositivos más vulnerables:</h1>'
        html += '<ul>'
        for row in rows:
            html += f'<li>{row[0]} ({row[1]} servicios inseguros)</li>'
        html += '</ul>'
        html += '<a href="/" class="button"> Volver</a>'
        con.commit()
        return html

    if __name__ == '__main__':
        app.run(debug=True)


#createBase(con)
flask()

