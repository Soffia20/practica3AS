from flask import Flask, render_template, request, jsonify, make_response, session
from flask_cors import CORS
from functools import wraps
import mysql.connector.pooling

app = Flask(__name__)
app.secret_key = "Test12345"  # Cambia esta clave por una más segura
CORS(app)

con_pool = mysql.connector.pooling.MySQLConnectionPool(
    pool_name="my_pool",
    pool_size=5,
    host="185.232.14.52", 
    database="u760464709_23005355_bd",
    user="u760464709_23005355_usr",
    password="F1O[QWJ$@2x"
)

def pusherLab():
    import pusher
    pusher_lab = pusher.Pusher(
    app_id = "2073359"
    key = "d60a574067b9a7511165"
    secret = "856804a6e7e433ae7a3e"
    cluster = "us2"
    ssl=True
    )
    
    pusher_client.trigger("canalLab", "eventoLab", {"message": "Hola Mundo!"})
    return make_response(jsonify({}))

def login_requerido(fun):
    @wraps(fun)
    def decorador(*args, **kwargs):
        if not session.get("login"):
            return jsonify({
                "estado": "error",
                "mensaje": "No has iniciado sesión"
            }), 401
        return fun(*args, **kwargs)
    return decorador

# --- RUTAS ---

@app.route("/")
def index():
    return render_template("login.html")

@app.route("/iniciarSesion", methods=["POST"])
def iniciarSesion():
    usuario = request.form["usuario"]
    contrasena = request.form["contrasena"]

    con = con_pool.get_connection()
    cursor = con.cursor(dictionary=True)
    sql = """
    SELECT Id_Usuario, Nombre_Usuario, Tipo_Usuario
    FROM usuarios
    WHERE Nombre_Usuario = %s
    AND Contrasena = %s
    """
    val = (usuario, contrasena)
    cursor.execute(sql, val)
    registros = cursor.fetchall()

    cursor.close()
    con.close()

    # Reset de sesión
    session["login"] = False
    session["login-usr"] = None
    session["login-tipo"] = 0

    if registros:
        usuario_db = registros[0]
        session["login"] = True
        session["login-usr"] = usuario_db["Nombre_Usuario"]
        session["login-tipo"] = usuario_db["Tipo_Usuario"]

    return make_response(jsonify(registros))

@app.route("/cerrarSesion", methods=["POST"])
@login_requerido
def cerrarSesion():
    session["login"] = False
    session["login-usr"] = None
    session["login-tipo"] = 0
    return make_response(jsonify({"estado": "ok"}))

@app.route("/preferencias")
@login_requerido
def preferencias():
    return make_response(jsonify({
        "usuario": session.get("login-usr"),
        "tipo": session.get("login-tipo")
    }))

if __name__ == "__main__":
    app.run(debug=True)
