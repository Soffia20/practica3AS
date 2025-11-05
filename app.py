# python.exe -m venv .venv
# cd .venv/Scripts
# activate.bat
# py -m ensurepip --upgrade
# pip install -r requirements.txt

from functools import wraps
from flask import Flask, render_template, request, jsonify, make_response, session

from flask_cors import CORS, cross_origin

import mysql.connector.pooling
import pusher
import pytz
import datetime

app            = Flask(__name__)
app.secret_key = "Test12345"
CORS(app)

con_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="my_pool",
    pool_size=5,
    host="185.232.14.52",
    database="u760464709_23005355_bd",
    user="u760464709_23005355_usr",
    password="F1O[QWJ$@2x"
)

def pusherClientes():
    import pusher
    
    pusher_client = pusher.Pusher(
    app_id="2046017",
    key="b51b00ad61c8006b2e6f",
    secret="d2ec35aa5498a18af7bf",
    cluster="us2",
    ssl=True
    )
    
    pusher_client.trigger("canalClientes", "eventoClientes", {"message": "Hola Mundo!"})
    return make_response(jsonify({}))

def login(fun):
    @wraps(fun)
    def decorador(*args, **kwargs):
        if not session.get("login"):
            return jsonify({
                "estado": "error",
                "respuesta": "No has iniciado sesión"
            }), 401
        return fun(*args, **kwargs)
    return decorador

@app.route("/")
def landingPage():
    return render_template("landing-page.html")

@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html")

@app.route("/login")
def appLogin():
    return render_template("login.html")
    # return "<h5>Hola, soy la view app</h5>"

@app.route("/fechaHora")
def fechaHora():
    tz    = pytz.timezone("America/Matamoros")
    ahora = datetime.datetime.now(tz)
    return ahora.strftime("%Y-%m-%d %H:%M:%S")

@app.route("/iniciarSesion", methods=["POST"])
# Usar cuando solo se quiera usar CORS en rutas específicas
# @cross_origin()
def iniciarSesion():
    usuario    = request.form["usuarios"]
    contrasena = request.form["contrasena"]

    con    = con_pool.get_connection()
    cursor = con.cursor(dictionary=True)
    sql    = """
    SELECT Id_Usuario, Nombre_Usuario, Tipo_Usuario
    FROM usuarios
    WHERE Nombre_Usuario = %s
    AND Contrasena = %s
    """
    val    = (usuario, contrasena)

    cursor.execute(sql, val)
    registros = cursor.fetchall()
    if cursor:
        cursor.close()
    if con and con.is_connected():
        con.close()

    session["login"]      = False
    session["login-usr"]  = None
    session["login-tipo"] = 0
    if registros:
        usuario = registros[0]
        session["login"]      = True
        session["login-usr"]  = usuario["Nombre_Usuario"]
        session["login-tipo"] = usuario["Tipo_Usuario"]

    return make_response(jsonify(registros))

@app.route("/cerrarSesion", methods=["POST"])
@login
def cerrarSesion():
    session["login"]      = False
    session["login-usr"]  = None
    session["login-tipo"] = 0
    return make_response(jsonify({}))

@app.route("/preferencias")
@login
def preferencias():
    return make_response(jsonify({
        "usr": session.get("login-usr"),
        "tipo": session.get("login-tipo", 2)
    }))


# @app.route("/rentas")
# def rentas():
#     return render_template("rentas.html")

# @app.route("/tbodyRentas")
# def tbodyRentas():
#     try:
#         con = con_pool.get_connection()
#         cursor = con.cursor(dictionary=True)

#         sql = """
#         SELECT rentas.idRenta, clientes.nombreCliente, trajes.nombreTraje, trajes.descripcion, rentas.fechaHoraInicio, rentas.fechaHoraFin
#         FROM rentas
#         INNER JOIN clientes ON rentas.idCliente = clientes.idCliente
#         INNER JOIN trajes ON rentas.idTraje = trajes.idTraje

#         ORDER BY idRenta DESC
#         LIMIT 10 OFFSET 0
#         """

#         cursor.execute(sql)
#         registros = cursor.fetchall()

#         # Aquí puedes devolver HTML renderizado o JSON
#         return render_template("tbodyRentas.html", rentas=registros)

#     except Exception as e:
#         print("Error en /tbodyRentas:", e)
#         return make_response(jsonify({"error": str(e)}), 500)

#     finally:
#         if cursor:
#             cursor.close()
#         if con and con.is_connected():
#             con.close()


# @app.route("/rentas/buscar", methods=["GET"])
# def buscarRentas():
#     con = con_pool.get_connection()

#     args     = request.args
#     busqueda = args["busqueda"]
#     busqueda = f"%{busqueda}%"
    
#     cursor = con.cursor(dictionary=True)
#     sql    = """
#     SELECT idRenta,
#            idCliente,
#            idTraje,
#            descripcion,
#            fechaHoraInicio,
#            fechaHoraFin

#     FROM rentas

#     WHERE idRenta LIKE %s
#     OR    idCliente         LIKE %s
#     OR    idTraje           LIKE %s
#     OR    fechaHoraInicio   LIKE %s
#     OR    fechaHoraFin      LIKE %s

#     ORDER BY idRenta DESC

#     LIMIT 10 OFFSET 0
#     """
#     val    = (busqueda, busqueda, busqueda, busqueda)

#     try:
#         cursor.execute(sql, val)
#         registros = cursor.fetchall()

#         # Si manejas fechas y horas
        
#         for registro in registros:
#             inicio = registro["FechaHoraInicio"]
#             fin = registro["FechaHoraFin"]

#             # registro["fechahoraInicio"] = inicio.strftime("%Y-%m-%d %H:%M:%S")
#             registro["fechaInicio"] = inicio.strftime("%d/%m/%Y")
#             registro["horaInicio"]  = inicio.strftime("%H:%M:%S")

#             # registro["fechahoraFin"] = fin.strftime("%Y-%m-%d %H:%M:%S")
#             registro["fechaFin"]    = fin.strftime("%d/%m/%Y")
#             registro["horaFin"]     = fin.strftime("%H:%M:%S")
        
#     except mysql.connector.errors.ProgrammingError as error:
#         print(f"Ocurrió un error de programación en MySQL: {error}")
#         registros = []

#     finally:
#         cursor.close()

#     return make_response(jsonify(registros))

# @app.route("/rentas", methods=["POST"])
# # Usar cuando solo se quiera usar CORS en rutas específicas
# # @cross_origin()
# def guardarRentas():
#     con = con_pool.get_connection()

#     idRenta         = request.form.get("idRenta")
#     cliente         = request.form["idCliente"]
#     traje           = request.form["idTraje"]
#     descripcion     = request.form["descripcion"]
#     fechahorainicio = datetime.datetime.now(pytz.timezone("America/Matamoros"))
#     fechahorafin    = datetime.datetime.now(pytz.timezone("America/Matamoros"))
    
#     cursor = con.cursor()

#     if idRenta:
#         sql = """
#         UPDATE rentas

#         SET idCliente        = %s,
#             idTraje          = %s,
#             descripcion      = %s,
#             fechaHoraInicio  = %s,
#             fechHoraFin      = %s

#         WHERE idRenta = %s
#         """
#         val = (cliente, traje, descripcion, fechahorainicio, fechahorafin)
#     else:
#         sql = """
#         INSERT INTO rentas (idCliente, idTraje, descripcion, FechaHoraInicio, fechaHoraFin)
#                     VALUES (   %s,       %s,        %s,            %s,             %s)
#         """
#         val =              (cliente, traje, descripcion, fechahorainicio, fechahorafin)
    
#     cursor.execute(sql, val)
#     con.commit()
#     con.close()

#     pusherRentas()
    
#     return make_response(jsonify({}))

# @app.route("/rentas/<int:id>")
# def editarRentas(id):
#     con = con_pool.get_connection()
    
#     cursor = con.cursor(dictionary=True)
#     sql    = """
#     SELECT idRenta, idCliente, idTraje, descripcion, fechaHoraInicio, fechaHoraFin

#     FROM rentas

#     WHERE idRenta = %s
#     """
#     val    = (id,)

#     cursor.execute(sql, val)
#     registros = cursor.fetchall()
#     con.close()

#     return make_response(jsonify(registros))

# @app.route("/rentas/eliminar", methods=["POST"])
# def eliminarRentas():
#     try:
#         con = con_pool.get_connection()
#         cursor = con.cursor()

#         idRenta = request.form.get("id")

#         cursor = con.cursor()
#         sql = "DELETE FROM rentas WHERE idRenta = %s"
#         val = (idRenta,)

#         cursor.execute(sql, val)
#         con.commit()
#         con.close()

#         pusherRentas()

#         return make_response(jsonify({"status": "ok"}))

#     except Exception as e:
#         print("Error eliminando renta:", e)
#         return make_response(jsonify({"error": str(e)}), 500)

@app.route("/clientes")
def clientes():
    return render_template("clientes.html")

@app.route("/tbodyClientes")
def tbodyClientes():
    try:
        con = con_pool.get_connection()
        cursor = con.cursor(dictionary=True)

        sql = """
        SELECT idCliente, nombreCliente, telefono, correoElectronico
        FROM clientes
        ORDER BY idCliente DESC
        LIMIT 10 OFFSET 0
        """

        cursor.execute(sql)
        registros = cursor.fetchall()

        # Aquí puedes devolver HTML renderizado o JSON
        return render_template("tbodyClientes.html", clientes=registros)

    except Exception as e:
        print("Error en /tbodyClientes:", e)
        return make_response(jsonify({"error": str(e)}), 500)

    finally:
        if cursor:
            cursor.close()
        if con and con.is_connected():
            con.close()


@app.route("/clientes/buscar", methods=["GET"])
def buscarClientes():
    con = con_pool.get_connection()

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
    con = con_pool.get_connection()

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
    con = con_pool.get_connection()
    
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
        con = con_pool.get_connection()
        cursor = con.cursor()

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

# # TRAJES
# @app.route("/trajes")
# def trajes():
#     return render_template("trajes.html")

# @app.route("/tbodyTrajes")
# def tbodyTrajes():
#     con = con_pool.get_connection()
#     cursor = con.cursor(dictionary=True)
#     sql    = """
#     SELECT IdTraje,
#            nombreTraje,
#            descripcion

#     FROM trajes

#     ORDER BY IdTraje DESC

#     LIMIT 10 OFFSET 0
#     """

#     cursor.execute(sql)
#     registros = cursor.fetchall()

#     # Si manejas fechas y horas
#     """
#     for registro in registros:
#         fecha_hora = registro["Fecha_Hora"]

#         registro["Fecha_Hora"] = fecha_hora.strftime("%Y-%m-%d %H:%M:%S")
#         registro["Fecha"]      = fecha_hora.strftime("%d/%m/%Y")
#         registro["Hora"]       = fecha_hora.strftime("%H:%M:%S")
#     """

#     return render_template("tbodyTrajes.html", trajes=registros)

# @app.route("/trajes/guardar", methods=["POST", "GET"])
# def guardarTraje():
#     con = con_pool.get_connection()

#     if request.method == "POST":
#         data = request.get_json(silent=True) or request.form
#         id_traje = data.get("IdTraje")
#         nombre = data.get("txtNombre")
#         descripcion = data.get("txtDescripcion")
#     else: 
#         nombre = request.args.get("nombre")
#         descripcion = request.args.get("descripcion")
#     if not nombre or not descripcion:
#         return jsonify({"error": "Faltan parámetros"}), 400
        
#     cursor = con.cursor()
    
#     if id_traje:
#         sql = """
#         UPDATE  trajes
#             SET nombreTraje = %s,
#             descripcion = %s
#         WHERE IdTraje = %s
#         """
#         cursor.execute(sql, (nombre, descripcion, id_traje))
        
#         pusherProductos()
#     else: 
#         sql = """
#         INSERT INTO trajes (nombreTraje, descripcion)
#         VALUES (%s, %s)
#         """
#         cursor.execute(sql, (nombre, descripcion))

#         pusherProductos()

#     con.commit()
#     con.close()
#     return make_response(jsonify({"mensaje": "Traje guardado correctamente"}))

# @app.route("/trajes/eliminar", methods=["POST", "GET"])
# def eliminartraje():
#     con = con_pool.get_connection()

#     if request.method == "POST":
#         IdTraje = request.form.get("id")
#     else:
#         IdTraje = request.args.get("id")

#     cursor = con.cursor()
#     sql = "DELETE FROM trajes WHERE IdTraje = %s"
#     val = (IdTraje,)

#     cursor.execute(sql, val)
#     con.commit()
#     con.close()

#     pusherProductos()

#     return make_response(jsonify({"status": "ok"}))

# @app.route("/trajes/<int:id>")
# def editarTrajes(id):
#     con = con_pool.get_connection()

#     cursor = con.cursor(dictionary=True)
#     sql    = """
#     SELECT IdTraje, nombreTraje, descripcion

#     FROM trajes

#     WHERE IdTraje = %s
#     """
#     val    = (id,)

#     cursor.execute(sql, val)
#     registros = cursor.fetchall()
#     con.close()

#     return make_response(jsonify(registros))

# @app.route("/trajes/buscar", methods=["GET"])
# def buscarTrajes():
#     con = con_pool.get_connection()

#     args     = request.args
#     busqueda = args["busqueda"]
#     busqueda = f"%{busqueda}%"
    
#     cursor = con.cursor(dictionary=True)
#     sql    = """
#     SELECT IdTraje,
#            nombreTraje,
#            descripcion

#     FROM trajes

#     WHERE nombreTraje LIKE %s
#     OR    descripcion          LIKE %s

#     ORDER BY IdTraje DESC

#     LIMIT 10 OFFSET 0
#     """
#     val    = (busqueda, busqueda)

#     try:
#         cursor.execute(sql, val)
#         registros = cursor.fetchall()

#     except mysql.connector.errors.ProgrammingError as error:
#         print(f"Ocurrió un error de programación en MySQL: {error}")
#         registros = []

#     finally:
#         con.close()

#     return make_response(jsonify(registros))

