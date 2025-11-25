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
    
def pusherEstudiantes():
    import pusher
    
    pusher_client = pusher.Pusher(
    app_id="2046017",
    key="b51b00ad61c8006b2e6f",
    secret="d2ec35aa5498a18af7bf",
    cluster="us2",
    ssl=True
    )
    
    pusher_client.trigger("canalestudiantes", "eventoestudiantes", {"message": "Actualización en Estudiantes"})
    


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
    return ahora.replace(tzinfo=None)
    # return ahora.strftime("%Y-%m-%d %H:%M:%S")

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
@app.route("/log", methods=["GET"])
def logEstudiantes():
    args         = request.args
    actividad    = args["actividad"]
    descripcion  = args["descripcion"]
    tz           = pytz.timezone("America/Matamoros")
    ahora        = datetime.datetime.now(tz)
    fechaHoraStr = ahora.strftime("%Y-%m-%d %H:%M:%S")

    with open("log-busquedas.txt", "a") as f:
        f.write(f"{actividad}\t{descripcion}\t{fechaHoraStr}\n")

    with open("log-busquedas.txt") as f:
        log = f.read()

    return log

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
           Matricula,
           Carrera,
           Correo,
           Telefono
    FROM Estudiantes
    ORDER BY Id_Estudiante DESC
    LIMIT 10 OFFSET 0
    """
    cursor.execute(sql)
    registros = cursor.fetchall()
    cursor.close()
    return make_response(jsonify(registros))


@app.route("/estudiantes/buscar", methods=["GET"])
def buscarEstudiantes():
    if not con.is_connected():
        con.reconnect()

    args = request.args
    busqueda = args["busqueda"]
    busqueda = f"%{busqueda}%"

    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT Id_Estudiante, Nombre, Matricula, Carrera, Correo, Telefono
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
        
    # return render_template("tbodyEstudiantes.html", estudiantes=registros)
    return make_response(jsonify(registros))


@app.route("/estudiantes", methods=["POST"])
def guardarEstudiantes():
    if not con.is_connected():
        con.reconnect()
        
    IdEstudiante = request.form.get("IdEstudiante")
    Nombre = request.form["nombre"]
    Matricula = request.form["matricula"]
    Carrera = request.form["carrera"]
    Correo = request.form["correo"]
    Telefono = request.form["telefono"]


    cursor = con.cursor()

    if IdEstudiante:
        sql = """
        UPDATE Estudiantes
        SET Nombre = %s,
            Matricula = %s,
            Carrera = %s,
            Correo = %s,
            Telefono = %s
        WHERE Id_Estudiante = %s
        """
        val = (Nombre, Matricula, Carrera, Correo, Telefono, IdEstudiante)
    else:
        sql = """
        INSERT INTO Estudiantes (Nombre, Matricula, Carrera, Correo, Telefono)
        VALUES (%s, %s, %s, %s, %s)
        """
        val = (Nombre, Matricula, Carrera, Correo, Telefono)

    cursor.execute(sql, val)
    con.commit()
    con.close()

    pusherEstudiantes() 

    return make_response(jsonify({}))


@app.route("/estudiantes/<int:id>")
def editarEstudiantes(id):
    if not con.is_connected():
        con.reconnect()
        
    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT Id_Estudiante, Nombre, Matricula, Carrera, Correo, Telefono
    FROM Estudiantes
    WHERE Id_Estudiante = %s
    """
    val = (id,)

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

        pusherEstudiantes()

        return make_response(jsonify({"status": "ok"}))

    except Exception as e:
        print("Error eliminando registro en Estudiantes:", e)
        return make_response(jsonify({"error": str(e)}), 500)
    
@app.route("/acceso")
@login
def acceso():
    return render_template("Acceso.html")

@app.route("/api/acceso/commands/entrada", methods=["POST"])
@login
def registrar_entrada():
    if not con.is_connected():
        con.reconnect()

    data = request.get_json()
    id_est = data.get("Id_Estudiante")
    id_lab = data.get("Id_Laboratorio")

    if not id_est or not id_lab:
        return make_response(jsonify({
            "ok": False,
            "error": "Id_Estudiante e Id_Laboratorio son obligatorios"
        }), 400)

    try:
        cursor = con.cursor(dictionary=True)

        # Validar que el estudiante exista
        cursor.execute("""
            SELECT Id_Estudiante
            FROM Estudiantes
            WHERE Id_Estudiante = %s
        """, (id_est,))
        existe = cursor.fetchone()
        if not existe:
            cursor.close()
            return make_response(jsonify({
                "ok": False,
                "error": "El estudiante no existe"
            }), 400)

        fecha_entrada = fechaHora()

        cursor.execute("""
            INSERT INTO Accesos (Id_Estudiante, Id_Laboratorio, FechaHora_Entrada, Tipo)
            VALUES (%s, %s, %s, 'ENTRADA')
        """, (id_est, id_lab, fecha_entrada))

        con.commit()
        cursor.close()

        return make_response(jsonify({
            "ok": True,
            "msg": "Entrada registrada correctamente",
            "fechaHoraEntrada": fecha_entrada.strftime("%Y-%m-%d %H:%M:%S")
        }))

    except Exception as e:
        print("Error en /api/acceso/commands/entrada:", e)
        con.rollback()
        return make_response(jsonify({
            "ok": False,
            "error": str(e)
        }), 500)

@app.route("/api/acceso/commands/salida", methods=["POST"])
@login
def registrar_salida():
    if not con.is_connected():
        con.reconnect()

    data = request.get_json()
    id_est = data.get("Id_Estudiante")
    id_lab = data.get("Id_Laboratorio")

    if not id_est or not id_lab:
        return make_response(jsonify({
            "ok": False,
            "error": "Id_Estudiante e Id_Laboratorio son obligatorios"
        }), 400)

    try:
        cursor = con.cursor(dictionary=True)

        # Buscar el último acceso sin salida
        cursor.execute("""
            SELECT Id_Acceso
            FROM Accesos
            WHERE Id_Estudiante = %s
              AND Id_Laboratorio = %s
              AND FechaHora_Salida IS NULL
            ORDER BY FechaHora_Entrada DESC
            LIMIT 1
        """, (id_est, id_lab))

        acceso = cursor.fetchone()
        if not acceso:
            cursor.close()
            return make_response(jsonify({
                "ok": False,
                "error": "No hay una ENTRADA abierta para este estudiante en este laboratorio"
            }), 400)

        id_acceso = acceso["Id_Acceso"]
        fecha_salida = fechaHora()

        cursor.execute("""
            UPDATE Accesos
            SET FechaHora_Salida = %s,
                Tipo = 'SALIDA'
            WHERE Id_Acceso = %s
        """, (fecha_salida, id_acceso))

        con.commit()
        cursor.close()

        return make_response(jsonify({
            "ok": True,
            "msg": "Salida registrada correctamente",
            "Id_Acceso": id_acceso,
            "fechaHoraSalida": fecha_salida.strftime("%Y-%m-%d %H:%M:%S")
        }))

    except Exception as e:
        print("Error en /api/acceso/commands/salida:", e)
        con.rollback()
        return make_response(jsonify({
            "ok": False,
            "error": str(e)
        }), 500)

@app.route("/api/acceso/commands/eliminar", methods=["POST"])
@login
def eliminar_acceso():
    if not con.is_connected():
        con.reconnect()

    id_acceso = request.form.get("idAcceso")

    if not id_acceso:
        return make_response(jsonify({
            "ok": False,
            "error": "Se requiere idAcceso"
        }), 400)

    try:
        cursor = con.cursor()

        sql = "DELETE FROM Accesos WHERE Id_Acceso = %s"
        val = (id_acceso,)

        cursor.execute(sql, val)
        con.commit()
        borrados = cursor.rowcount
        cursor.close()

        if borrados == 0:
            return make_response(jsonify({
                "ok": False,
                "error": "Acceso no encontrado"
            }), 404)

        return make_response(jsonify({
            "ok": True,
            "msg": "Acceso eliminado"
        }))

    except Exception as e:
        print("Error en /api/acceso/commands/eliminar:", e)
        con.rollback()
        return make_response(jsonify({
            "ok": False,
            "error": str(e)
        }), 500)

@app.route("/api/acceso/queries/todos", methods=["GET"])
@login
def listar_acceso():
    if not con.is_connected():
        con.reconnect()

    try:
        cursor = con.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                Id_Acceso,
                Id_Estudiante,
                Id_Laboratorio,
                FechaHora_Entrada,
                FechaHora_Salida,
                Tipo
            FROM Accesos
            ORDER BY FechaHora_Entrada DESC
            LIMIT 50
        """)
        registros = cursor.fetchall()
        cursor.close()

        return make_response(jsonify(registros))

    except Exception as e:
        print("Error en /api/acceso/queries/todos:", e)
        return make_response(jsonify({
            "ok": False,
            "error": str(e)
        }), 500)


