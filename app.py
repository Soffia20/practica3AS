# python.exe -m venv .venv
# cd .venv/Scripts
# activate.bat
# py -m ensurepip --upgrade
# pip install -r requirements.txt

from flask import Flask

from flask import render_template
from flask import request
from flask import jsonify, make_response

import mysql.connector

import datetime
import pytz

from flask_cors import CORS, cross_origin

con = mysql.connector.connect(
    host="185.232.14.52",
    database="u760464709_23005256_bd",
    user="u760464709_23005256_usr",
    password="~6ru!MMJZzX"
)

app = Flask(__name__)
CORS(app)

def pusherClientes():
    import pusher
    
    pusher_client = pusher.Pusher(
        app_id='2047513',
        key='bf79fc5f8fe969b1839e',
        secret='9b73ac4b30f41a28c732',
        cluster='us2',
        ssl=True
    )
    
    pusher_client.trigger("canalClientes", "eventoClientes", {"message": "Hola Mundo!"})
    return make_response(jsonify({}))

@app.route("/")
def index():
    if not con.is_connected():
        con.reconnect()

    con.close()

    return render_template("index.html")

@app.route("/app")
def app2():
    if not con.is_connected():
        con.reconnect()

    con.close()

    return render_template("login.html")
    # return "<h5>Hola, soy la view app</h5>"

@app.route("/iniciarSesion", methods=["POST"])
# Usar cuando solo se quiera usar CORS en rutas específicas
# @cross_origin()
def iniciarSesion():
    if not con.is_connected():
        con.reconnect()

    usuario    = request.form["txtUsuario"]
    contrasena = request.form["txtContrasena"]

    cursor = con.cursor(dictionary=True)
    sql    = """
    SELECT Id_Usuario
    FROM usuarios

    WHERE Nombre_Usuario = %s
    AND Contrasena = %s
    """
    val    = (usuario, contrasena)

    cursor.execute(sql, val)
    registros = cursor.fetchall()
    con.close()

    return make_response(jsonify(registros))


    if not con.is_connected():
        con.reconnect()

    id = request.form["id"]

    cursor = con.cursor(dictionary=True)
    sql    = """
    DELETE FROM productos
    WHERE Id_Producto = %s
    """
    val    = (id,)

    cursor.execute(sql, val)
    con.commit()
    con.close()

    return make_response(jsonify({}))

# CLIENTES

@app.route("/clientes")
def clientes():
    return render_template("clientes.html")

@app.route("/tbodyClientes")
def tbodyClientes():
    if not con.is_connected():
        con.reconnect()

    cursor = con.cursor(dictionary=True)
    sql    = """
    SELECT idCliente,
           nombreCliente,
           telefono,
           correoElectronico

    FROM clientes

    ORDER BY idCliente DESC

    LIMIT 10 OFFSET 0
    """

    cursor.execute(sql)
    registros = cursor.fetchall()

    # Si manejas fechas y horas
    """
    for registro in registros:
        fecha_hora = registro["Fecha_Hora"]

        registro["Fecha_Hora"] = fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
        registro["Fecha"]      = fecha_hora.strftime("%d/%m/%Y")
        registro["Hora"]       = fecha_hora.strftime("%H:%M:%S")
    """

    return render_template("tbodyClientes.html", clientes=registros)

@app.route("/clientes/buscar", methods=["GET"])
def buscarClientes():
    if not con.is_connected():
        con.reconnect()

    args     = request.args
    busqueda = args["busqueda"]
    busqueda = f"%{busqueda}%"
    
    cursor = con.cursor(dictionary=True)
    sql    = """
    SELECT idCliente,
           nombreCliente,
           telefono,
           correoElectronico

    FROM clientes

    WHERE nombreCliente LIKE %s
    OR    telefono          LIKE %s
    OR    correoElectronico     LIKE %s

    ORDER BY idCliente DESC

    LIMIT 10 OFFSET 0
    """
    val    = (busqueda, busqueda, busqueda)

    try:
        cursor.execute(sql, val)
        registros = cursor.fetchall()

        # Si manejas fechas y horas
        """
        for registro in registros:
            fecha_hora = registro["Fecha_Hora"]

            registro["Fecha_Hora"] = fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
            registro["Fecha"]      = fecha_hora.strftime("%d/%m/%Y")
            registro["Hora"]       = fecha_hora.strftime("%H:%M:%S")
        """

    except mysql.connector.errors.ProgrammingError as error:
        print(f"Ocurrió un error de programación en MySQL: {error}")
        registros = []

    finally:
        cursor.close()

    return make_response(jsonify(registros))

@app.route("/cliente", methods=["POST"])
# Usar cuando solo se quiera usar CORS en rutas específicas
# @cross_origin()
def guardarCliente():
    if not con.is_connected():
        con.reconnect()

    idCliente = request.form.get("idCliente")
    nombre      = request.form["nombreCliente"]
    telefono      = request.form["telefono"]
    correoElectronico = request.form["correoElectronico"]
    
    # fechahora   = datetime.datetime.now(pytz.timezone("America/Matamoros"))
    
    cursor = con.cursor()

    if idCliente:
        sql = """
        UPDATE clientes

        SET nombreCliente = %s,
            telefono          = %s,
            correoElectronico     = %s

        WHERE idCliente = %s
        """
        val = (nombre, telefono, correoElectronico, idCliente)
    else:
        sql = """
        INSERT INTO clientes (nombreCliente, telefono, correoElectronico)
                    VALUES    (%s,          %s,      %s)
        """
        val =                 (nombre, telefono, correoElectronico)
    
    cursor.execute(sql, val)
    con.commit()
    con.close()

    pusherClientes()
    
    return make_response(jsonify({}))

@app.route("/cliente/<int:id>")
def editarClientes(id):
    if not con.is_connected():
        con.reconnect()

    cursor = con.cursor(dictionary=True)
    sql    = """
    SELECT idCliente, nombreCliente, telefono, correoElectronico

    FROM clientes

    WHERE idCliente = %s
    """
    val    = (id,)

    cursor.execute(sql, val)
    registros = cursor.fetchall()
    con.close()

    return make_response(jsonify(registros))

@app.route("/clientes/eliminar", methods=["POST"])
def eliminarCliente():
    try:
        if not con.is_connected():
            con.reconnect()

        idCliente = request.form.get("id")

        cursor = con.cursor()
        sql = "DELETE FROM clientes WHERE idCliente = %s"
        val = (idCliente,)

        cursor.execute(sql, val)
        con.commit()
        con.close()

        pusherClientes()

        return make_response(jsonify({"status": "ok"}))

    except Exception as e:
        print("Error eliminando cliente:", e)
        return make_response(jsonify({"error": str(e)}), 500)


