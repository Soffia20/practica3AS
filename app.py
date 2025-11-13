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
import traceback

app            = Flask(__name__)
app.secret_key = "Test12345"
CORS(app)

con = mysql.connector.connect(
    host="185.232.14.52",
    database="u760464709_23005355_bd",
    user="u760464709_23005355_usr",
    password="F1O[QWJ$@2x"
)

# TRAJES
def pusherLaboratorio():
    import pusher
    
    pusher_client = pusher.Pusher(
    app_id="2046017",
    key="b51b00ad61c8006b2e6f",
    secret="d2ec35aa5498a18af7bf",
    cluster="us2",
    ssl=True
    )
    
    pusher_client.trigger("canallaboratorio", "eventolaboratorio", {"message": "Hola Mundo!"})


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

@app.errorhandler(Exception)
def handle_exception(e):
    print("❌ ERROR DETECTADO EN FLASK ❌")
    traceback.print_exc()
    return make_response(jsonify({"error": str(e)}), 500)

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
    if not con.is_connected():
        con.reconnect()
    usuario    = request.form["usuario"]
    contrasena = request.form["contrasena"]

    cursor = con.cursor(dictionary=True)
    sql    = """
    SELECT Id_Usuario, Nombre_Usuario, Correo_Electronico
    FROM usuarios
    WHERE Nombre_Usuario = %s
    AND Contrasena = %s
    """
    val    = (usuario, contrasena)

    cursor.execute(sql, val)
    registros = cursor.fetchall()
    if cursor:
        cursor.close()
    # if con and con.is_connected():
    #     con.close()

    session["login"]      = False
    session["login-usr"]  = None
    session["login-tipo"] = 0
    if registros:
        usuario = registros[0]
        session["login"]      = True
        session["login-usr"]  = usuario["Nombre_Usuario"]
        session["login-tipo"] = usuario["Correo_Electronico"]

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
        "usuario": session.get("login-usr"),
        "tipo": session.get("login-tipo", 2)
    }))

# lab
@app.route("/laboratorio")
@login
def laboratorio():
    return render_template("laboratorio.html")

@app.route("/tbodylaboratorio")
@login
def tbodylaboratorio():
    if not con.is_connected():
        con.reconnect()
    cursor = con.cursor(dictionary=True)
    sql    = """
    SELECT Id_Hora,
           Hora,
           Categoria
    FROM Hora_Lab
    ORDER BY Id_Hora DESC
    LIMIT 10 OFFSET 0
    """
    cursor.execute(sql)
    registros = cursor.fetchall()
    return render_template("tbodylaboratorio.html", horas=registros)


@app.route("/laboratorio/categorias", methods=["GET"])
@login
def laboratoriocategoria():
    if not con.is_connected():
        con.reconnect()

    args     = request.args
    categoria = args["categoria"]
    
    cursor = con.cursor(dictionary=True)
    sql    = """
    SELECT Hora
    FROM Hora_Lab

    WHERE categoria = %s
    ORDER BY Hora ASC

    LIMIT 10 OFFSET 0
    """
    val    = (categoria, )

    try:
        cursor.execute(sql, val)
        registros = cursor.fetchall()

    except mysql.connector.errors.ProgrammingError as error:
        print(f"Ocurrió un error de programación en MySQL: {error}")
        registros = []

    finally:
        con.close()

    return make_response(jsonify(registros))

@app.route("/laboratorios/buscar", methods=["GET"])
def buscarLaboratorios():
    if not con.is_connected():
        con.reconnect()

    args = request.args
    busqueda = args["busqueda"]
    busqueda = f"%{busqueda}%"

    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT Id_Hora, Hora, Categoria
    FROM Hora_Lab
    WHERE Hora LIKE %s
       OR Categoria LIKE %s
    ORDER BY Id_Hora DESC
    LIMIT 10 OFFSET 0
    """
    val = (busqueda, busqueda)

    try:
        cursor.execute(sql, val)
        registros = cursor.fetchall()

    except mysql.connector.errors.ProgrammingError as error:
        print(f"Ocurrió un error de programación en MySQL: {error}")
        registros = []

    finally:
        cursor.close()

    return make_response(jsonify(registros))


@app.route("/laboratorios", methods=["POST"])
def guardarLaboratorio():
    if not con.is_connected():
        con.reconnect()
        
    idHora = request.form.get("idHora")
    Hora = request.form["hora"]
    Categoria = request.form["categoria"]

    cursor = con.cursor()

    if idHora:
        sql = """
        UPDATE Hora_Lab
        SET Hora = %s,
            Categoria = %s
        WHERE Id_Hora = %s
        """
        val = (Hora, Categoria, idHora)
    else:
        sql = """
        INSERT INTO Hora_Lab (Hora, Categoria)
        VALUES (%s, %s)
        """
        val = (Hora, Categoria)

    cursor.execute(sql, val)
    con.commit()
    con.close()

    pusherLaboratorio() 

    return make_response(jsonify({}))


@app.route("/laboratorio/<int:id>")
def editarLaboratorio(id):
    if not con.is_connected():
        con.reconnect()
        
    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT Id_Hora, Hora, Categoria
    FROM Hora_Lab
    WHERE Id_Hora = %s
    """
    val = (id,)

    cursor.execute(sql, val)
    registros = cursor.fetchall()
    con.close()

    return make_response(jsonify(registros))


@app.route("/laboratorios/eliminar", methods=["POST"])
def eliminarLaboratorio():
    try:
        if not con.is_connected():
            con.reconnect()
        cursor = con.cursor()

        idHora = request.form.get("id")

        sql = "DELETE FROM Hora_Lab WHERE Id_Hora = %s"
        val = (idHora,)

        cursor.execute(sql, val)
        con.commit()
        con.close()

        pusherLaboratorio()

        return make_response(jsonify({"status": "ok"}))

    except Exception as e:
        print("Error eliminando registro en Hora_Lab:", e)
        return make_response(jsonify({"error": str(e)}), 500)

@app.route("/estudiantes")
@login
def estudiantes():
    return render_template("Estudiantes.html")

@app.route("/tbodyEstudiantes")
@login
def tbodyEstudiantes():
    if not con.is_connected():
        con.reconnect()
    cursor = con.cursor(dictionary=True)
    sql    = """
    SELECT Id_Estudiante,
           Nombre,
           Matricula
    FROM Estudiantes
    ORDER BY Id_Estudiante DESC
    LIMIT 10 OFFSET 0
    """
    cursor.execute(sql)
    registros = cursor.fetchall()
    return render_template("tbodyEstudiantes.html", estudiantes=registros)


@app.route("/estudiantes/buscar", methods=["GET"])
def buscarEstudiantes():
    if not con.is_connected():
        con.reconnect()

    args = request.args
    busqueda = args["busqueda"]
    busqueda = f"%{busqueda}%"

    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT Id_Estudiante, Nombre, Matricula
    FROM Estudiantes
    WHERE Nombre LIKE %s
       OR Matricula LIKE %s
    ORDER BY Id_Estudiante DESC
    LIMIT 10 OFFSET 0
    """
    val = (busqueda, busqueda)

    try:
        cursor.execute(sql, val)
        registros = cursor.fetchall()

    except mysql.connector.errors.ProgrammingError as error:
        print(f"Ocurrió un error de programación en MySQL: {error}")
        registros = []

    finally:
        cursor.close()

    return make_response(jsonify(registros))


@app.route("/estudiantes", methods=["POST"])
def guardarEstudiantes():
    if not con.is_connected():
        con.reconnect()
        
    IdEstudiante = request.form.get("IdEstudiante")
    Matricula = request.form["Matricula"]
    Nombre = request.form["Nombre"]

    cursor = con.cursor()

    if IdEstudiante:
        sql = """
        UPDATE Estudiantes
        SET Nombre = %s,
            Matricula = %s
        WHERE Id_Estudiante = %s
        """
        val = (Nombre, Matricula, IdEstudiante)
    else:
        sql = """
        INSERT INTO Estudiantes (Nombre, Matricula)
        VALUES (%s, %s)
        """
        val = (Nombre, Matricula)

    cursor.execute(sql, val)
    con.commit()
    con.close()

    pusherLaboratorio() 

    return make_response(jsonify({}))


@app.route("/estudiantes/<int:id>")
def editarEstudiantes(IdEstudiante):
    if not con.is_connected():
        con.reconnect()
        
    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT Id_Estudiante, Nombre, Matricula
    FROM Estudiantes
    WHERE Id_Estudiante = %s
    """
    val = (IdEstudiante)

    cursor.execute(sql, val)
    registros = cursor.fetchall()
    con.close()

    return make_response(jsonify(registros))


@app.route("/estudiantes/eliminar", methods=["POST"])
def eliminarEstudiantes():
    try:
        if not con.is_connected():
            con.reconnect()
        cursor = con.cursor()

        IdEstudiante = request.form.get("IdEstudiante")

        sql = "DELETE FROM Estudiantes WHERE Id_Estudiante = %s"
        val = (IdEstudiante,)

        cursor.execute(sql, val)
        con.commit()
        con.close()

        pusherLaboratorio()

        return make_response(jsonify({"status": "ok"}))

    except Exception as e:
        print("Error eliminando registro en Estudiantes:", e)
        return make_response(jsonify({"error": str(e)}), 500)
