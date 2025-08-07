from flask import Flask, render_template, request,url_for, jsonify, render_template_string, abort, redirect
import pyodbc
import jwt
from functools import wraps
import pandas as pd
import os
import sys
import requests
from dotenv import load_dotenv
load_dotenv()

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime


app = Flask(__name__)
SECRET_KEY = os.getenv("SECRET_KEY") 

PRIME_MX_API_URL = "https://api.primecomms.mx/portal-authenticator-service/auth/validate_external_token"
PRIME_MX_API_KEY = os.getenv("PRIME_MX_API_KEY")
ENVIRONMENT = os.getenv("ENVIRONMENT", "production")

def validate_token_with_prime_mx(token):
    """
    Valida el token con el API de Prime MX
    Retorna: (es_valido: bool, user_info: dict)
    """
    try:
        headers = {
            "Authorization": PRIME_MX_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "token": token
        }
        
        response = requests.post(PRIME_MX_API_URL, json=payload, headers=headers, timeout=10)
        
        if response.status_code == 200:
            user_info = response.json()
            return True, user_info
        elif response.status_code == 401:
            return False, {}
        else:
            print(f"Error inesperado del API Prime MX: {response.status_code}")
            return False, {}
            
    except requests.RequestException as e:
        print(f"Error al conectar con Prime MX API: {e}")
        return False, {}

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if ENVIRONMENT == "local":
            # Simulación de usuario local
            request.user_info = {
                "user_id": "local_user",
                "name": "Usuario Local",
                "email": "local@demo.com"
            }
            return f(*args, **kwargs)

        token = None
        auth_header = request.headers.get("Authorization")
        if auth_header and auth_header.startswith("Bearer "):
            token = auth_header.split(" ")[1]
        else:
            token = request.args.get("token")

        if not token:
            return render_template("login.html"), 401

        is_valid, user_info = validate_token_with_prime_mx(token)
        if not is_valid:
            return render_template("login.html", error="Sesión expirada o token inválido"), 401

        request.user_info = user_info
        return f(*args, **kwargs)
    return decorated

# Nueva ruta para manejar el flujo de autenticación desde Prime MX
@app.route("/token")
def handle_token_auth():
    """
    Endpoint que recibe el token desde Prime MX Portal
    Formato esperado: https://tu-app.com/token?token=USER_AUTH_TOKEN
    """
    token = request.args.get("token")
    
    if not token:
        return render_template("login.html", error="Token no proporcionado"), 400
    
    # Validar token con Prime MX
    is_valid, user_info = validate_token_with_prime_mx(token)
    
    if is_valid:
        # Token válido, redirigir a la página principal con el token
        return redirect(url_for('index', token=token))
    else:
        # Token inválido, mostrar login
        return render_template("login.html", error="Token inválido o expirado"), 401

# Ruta de login manual (fallback)
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Aquí podrías implementar autenticación local si es necesario
        # Por ahora, solo mostrar mensaje de que deben usar Prime MX Portal
        return render_template("login.html", 
                             error="Por favor, accede a través del Portal de Prime MX")
    
    return render_template("login.html")



driver = os.getenv("DB_DRIVER")
server = os.getenv("DB_SERVER")
username = os.getenv("DB_USERNAME")
password = os.getenv("DB_PASSWORD")
database = os.getenv("DB_NAME")

# Conexión usando pyodbc
conn_string = (
    f"DRIVER={{{driver}}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password};"
    "TrustServerCertificate=yes;"
)


conn = pyodbc.connect(conn_string)

try:
    conn = pyodbc.connect(conn_string)
    print("Conexión a base de datos exitosa.")
except Exception as e:
    print(f"Error al conectar a la base de datos: {e}", file=sys.stderr)
    sys.exit(1)

# Diccionario de comisiones
comisiones = {
    "equipo_nuevo": {
        "AT&T AZUL 1": {"COMISION":100,"RENTA":319, "INCENTIVO":0},
        "AT&T AZUL 2": {"COMISION":180,"RENTA":419, "INCENTIVO":0},
        "AT&T AZUL 3": {"COMISION":440,"RENTA":529, "INCENTIVO":0},
        "AT&T PLATA": {"COMISION":530,"RENTA":629, "INCENTIVO":500},
        "AT&T ORO": {"COMISION":590,"RENTA":699, "INCENTIVO":500},
        "AT&T BLACK": {"COMISION":670,"RENTA":799, "INCENTIVO":500},
        "AT&T PLATINO": {"COMISION":800,"RENTA":999, "INCENTIVO":500},
        "AT&T DIAMANTE": {"COMISION":800,"RENTA":1259, "INCENTIVO":500},
        "AT&T TITANIO": {"COMISION":670,"RENTA":1499, "INCENTIVO":500},
        "AT&T TITANIO TRADE IN": {"COMISION":335,"RENTA":1499, "INCENTIVO":250},
    },
    "equipo_propio": {
        "AT&T AZUL 1": {"COMISION":50,"RENTA":319, "INCENTIVO":0},
        "AT&T AZUL 2": {"COMISION":90,"RENTA":419, "INCENTIVO":0},
        "AT&T AZUL 3": {"COMISION":220,"RENTA":529, "INCENTIVO":0},
        "AT&T PLATA": {"COMISION":265,"RENTA":629, "INCENTIVO":500},
        "AT&T ORO": {"COMISION":295,"RENTA":699, "INCENTIVO":500},
        "AT&T BLACK": {"COMISION":335,"RENTA":799, "INCENTIVO":500},
        "AT&T PLATINO": {"COMISION":400,"RENTA":999, "INCENTIVO":500},
        "AT&T DIAMANTE": {"COMISION":400,"RENTA":1259, "INCENTIVO":500},
    }
}

# Comisiones Negocios
comisiones_negocios = {
    "equipo_nuevo": {
        "ARMALO NEGOCIOS 239": {"COMISION":50,"RENTA":239},
        "ARMALO NEGOCIOS 299": {"COMISION":87,"RENTA":299},
        "ARMALO NEGOCIOS 399": {"COMISION":200,"RENTA":399},
        "ARMALO NEGOCIOS 499": {"COMISION":419,"RENTA":499},
        "ARMALO NEGOCIOS 599": {"COMISION":503,"RENTA":599},
        "ARMALO NEGOCIOS 699": {"COMISION":587,"RENTA":699},
        "ARMALO NEGOCIOS 799": {"COMISION":671,"RENTA":799},
        "ARMALO NEGOCIOS 899": {"COMISION":755,"RENTA":899},
        "ARMALO NEGOCIOS 999": {"COMISION":839,"RENTA":999},
        "ARMALO NEGOCIOS 1299": {"COMISION":1091,"RENTA":1299},
        "ARMALO NEGOCIOS 1499": {"COMISION":1259,"RENTA":1499},
    },
    "equipo_propio": {
        "ARMALO NEGOCIOS 239": {"COMISION":25,"RENTA":239},
        "ARMALO NEGOCIOS 299": {"COMISION":44,"RENTA":299},
        "ARMALO NEGOCIOS 399": {"COMISION":100,"RENTA":399},
        "ARMALO NEGOCIOS 499": {"COMISION":210,"RENTA":499},
        "ARMALO NEGOCIOS 599": {"COMISION":252,"RENTA":599},
        "ARMALO NEGOCIOS 699": {"COMISION":294,"RENTA":699},
        "ARMALO NEGOCIOS 799": {"COMISION":336,"RENTA":799},
        "ARMALO NEGOCIOS 899": {"COMISION":378,"RENTA":899},
        "ARMALO NEGOCIOS 999": {"COMISION":420,"RENTA":999},
        "ARMALO NEGOCIOS 1299": {"COMISION":546,"RENTA":1299},
        "ARMALO NEGOCIOS 1499": {"COMISION":630,"RENTA":1499},
    }
}

comisiones_simple={
    "simple_plus":{
        "SIMPLE PLUS/SIMPLE PLUS EMPRESARIAL 389":{"COMISION":163,"RENTA":389},
        "SIMPLE PLUS/SIMPLE PLUS EMPRESARIAL 399":{"COMISION":168,"RENTA":399},
        "SIMPLE PLUS/SIMPLE PLUS EMPRESARIAL 489":{"COMISION":205,"RENTA":489},
        "SIMPLE PLUS/SIMPLE PLUS EMPRESARIAL 589":{"COMISION":247,"RENTA":589},
        "SIMPLE PLUS/SIMPLE PLUS EMPRESARIAL 599":{"COMISION":252,"RENTA":599},
        "SIMPLE PLUS/SIMPLE PLUS EMPRESARIAL 649":{"COMISION":273,"RENTA":649},
        "SIMPLE PLUS/SIMPLE PLUS EMPRESARIAL 899":{"COMISION":377,"RENTA":899},
    },
    "simple":{
        "SIMPLE/SIMPLE EMPRESARIAL 389":{"COMISION":82,"RENTA":389},
        "SIMPLE/SIMPLE EMPRESARIAL 399":{"COMISION":84,"RENTA":399},
        "SIMPLE/SIMPLE EMPRESARIAL 489":{"COMISION":103,"RENTA":489},
        "SIMPLE/SIMPLE EMPRESARIAL 589":{"COMISION":124,"RENTA":589},
        "SIMPLE/SIMPLE EMPRESARIAL 599":{"COMISION":126,"RENTA":599},
        "SIMPLE/SIMPLE EMPRESARIAL 649":{"COMISION":136,"RENTA":649},
        "SIMPLE/SIMPLE EMPRESARIAL 899":{"COMISION":189,"RENTA":899},        
    }
}

comisiones_total ={
    "tv_incluida":{
        "VELOZ": {"COMISION":554,"RENTA":710},
        "TURBO": {"COMISION":646,"RENTA":820},
        "SONICO": {"COMISION":772,"RENTA":1000},
    },
    "tv_no_incluida":{
        "VELOZ": {"COMISION":436,"RENTA":570},
        "TURBO": {"COMISION":528,"RENTA":680},
        "SONICO": {"COMISION":638,"RENTA":830},
    }
}

comisiones_addons = {
    "CONTROL": 50,
    "NOCHES Y FINES DE SEMANA": 200,
    "FINES DE SEMANA": 100,
    "SUSCRIPCION MAX": 199,
    "PREMIUM DATOS ILIMITADOS": 300,
}




# Página principal (solo menú)
@app.route("/")
@token_required
def index():
    token = request.args.get("token") 
    return render_template("index.html", token = token)

@app.route("/posyrenos")
@token_required
def posyrenos():
    token = request.args.get("token") 
    return render_template("posyrenos.html", token= token)



# Ruta para la calculadora premium
@app.route("/premium", methods=["GET", "POST"])
@token_required
def premium():
    
    tipo_venta = request.form.get("tipo_venta", "equipo_nuevo")
    cantidades_ingresadas = {}

    # Si es POST, obtén las cantidades del formulario
    if request.method == "POST":
        for plan in comisiones[tipo_venta]:
            try:
                cantidades_ingresadas[plan] = int(request.form.get(plan, 0))
            except ValueError:
                cantidades_ingresadas[plan] = 0
    else:
        # En GET o sin valores previos
        for plan in comisiones[tipo_venta]:
            cantidades_ingresadas[plan] = 0

    total_comision = sum(
        cantidades_ingresadas[plan] * comisiones[tipo_venta][plan]["COMISION"]
        for plan in comisiones[tipo_venta]
    )

    return render_template(
        "premium.html",
        comisiones=comisiones,
        tipo_venta=tipo_venta,
        total_comision=total_comision,
        cantidades=cantidades_ingresadas,
        
    )
    

# Ruta para la calculadora premium
@app.route("/armalo", methods=["GET", "POST"])
@token_required
def armalo():
    tipo_venta = request.form.get("tipo_venta", "equipo_nuevo")
    cantidades_ingresadas = {}

    # Si es POST, obtén las cantidades del formulario
    if request.method == "POST":
        for plan in comisiones_negocios[tipo_venta]:
            try:
                cantidades_ingresadas[plan] = int(request.form.get(plan, 0))
            except ValueError:
                cantidades_ingresadas[plan] = 0
    else:
        # En GET o sin valores previos
        for plan in comisiones_negocios[tipo_venta]:
            cantidades_ingresadas[plan] = 0

    total_comision = sum(
        cantidades_ingresadas[plan] * comisiones_negocios[tipo_venta][plan]["COMISION"]
        for plan in comisiones_negocios[tipo_venta]
    )

    return render_template(
        "armalo.html",
        comisiones=comisiones_negocios,
        tipo_venta=tipo_venta,
        total_comision=total_comision,
        cantidades=cantidades_ingresadas
    )
# Ruta para la calculadora premium
@app.route("/simples", methods=["GET", "POST"])
@token_required
def simple():
    tipo_venta = request.form.get("tipo_venta", "simple_plus")
    cantidades_ingresadas = {}

    # Si es POST, obtén las cantidades del formulario
    if request.method == "POST":
        for plan in comisiones_simple[tipo_venta]:
            try:
                cantidades_ingresadas[plan] = int(request.form.get(plan, 0))
            except ValueError:
                cantidades_ingresadas[plan] = 0
    else:
        # En GET o sin valores previos
        for plan in comisiones_simple[tipo_venta]:
            cantidades_ingresadas[plan] = 0

    total_comision = sum(
        cantidades_ingresadas[plan] * comisiones_simple[tipo_venta][plan]["COMISION"]
        for plan in comisiones_simple[tipo_venta]
    )

    return render_template(
        "simples.html",
        comisiones=comisiones_simple,
        tipo_venta=tipo_venta,
        total_comision=total_comision,
        cantidades=cantidades_ingresadas
    )


# Ruta para la calculadora premium
@app.route("/totalplay", methods=["GET", "POST"])
@token_required
def total():
    tipo_venta = request.form.get("tipo_venta", "tv_incluida")
    cantidades_ingresadas = {}

    # Si es POST, obtén las cantidades del formulario
    if request.method == "POST":
        for plan in comisiones_total[tipo_venta]:
            try:
                cantidades_ingresadas[plan] = int(request.form.get(plan, 0))
            except ValueError:
                cantidades_ingresadas[plan] = 0
    else:
        # En GET o sin valores previos
        for plan in comisiones_total[tipo_venta]:
            cantidades_ingresadas[plan] = 0

    total_comision = sum(
        cantidades_ingresadas[plan] * comisiones_total[tipo_venta][plan]["COMISION"]
        for plan in comisiones_total[tipo_venta]
    )

    return render_template(
        "totalplay.html",
        comisiones=comisiones_total,
        tipo_venta=tipo_venta,
        total_comision=total_comision,
        cantidades=cantidades_ingresadas
    )
def generar_cache_accesorios():
    print(f"[{datetime.now()}] Actualizando accesorios cache...")
    query = "SELECT SKU, ACCESSORY AS DESCRIPCION, COST AS PRECIO, MARCA FROM CAT_ACC WHERE STATUS = 1"
    df = pd.read_sql(query, conn)
    os.makedirs("cache", exist_ok=True)
    df.to_parquet("cache/accesorios.parquet", index=False)
    print("Cache accesorios actualizado correctamente.")

generar_cache_accesorios()

# Ruta que lee desde archivo Parquet (cache)
@app.route('/accesorios')
@token_required
def accesorios():
    path = "cache/accesorios.parquet"
    if not os.path.exists(path):
        generar_cache_accesorios()

    df = pd.read_parquet(path)
    accesorios = df.to_dict(orient="records")
    return render_template("accesorios.html", accesorios=accesorios)

def refrescar_accesorios():
    generar_cache_accesorios()
    return "Archivo accesorios.parquet actualizado correctamente"

# ---------------------------
# ACTUALIZACIÓN AUTOMÁTICA DIARIA
# ---------------------------

scheduler = BackgroundScheduler()
scheduler.add_job(func=generar_cache_accesorios, trigger="interval", days=1)
scheduler.start()

@app.route("/seguros", methods=["GET", "POST"])
@token_required
def seguros():
    token = request.args.get("token")
    return render_template("seguros.html", token = token)

@app.route("/addons", methods=["GET", "POST"])
@token_required
def addons():
    
    cantidades_ingresadas = {}

    # Si es POST, obtén las cantidades del formulario
    if request.method == "POST":
        for plan in comisiones_addons:
            try:
                cantidades_ingresadas[plan] = int(request.form.get(plan, 0))
            except ValueError:
                cantidades_ingresadas[plan] = 0
    else:
        # En GET o sin valores previos
        for plan in comisiones_addons:
            cantidades_ingresadas[plan] = 0

    total_comision = sum(
        cantidades_ingresadas[plan] * comisiones_addons[plan] * 0.8
        for plan in comisiones_addons
    )

    return render_template(
        "addons.html",
        comisiones=comisiones_addons,
        total_comision=total_comision,
        cantidades=cantidades_ingresadas
    )

# AJAX: actualiza tabla de comisiones según el tipo
@app.route("/tabla_comisiones", methods=["POST"])
def tabla_comisiones():
    tipo_venta = request.form.get("tipo_venta", "equipo_nuevo")
    cantidades_ingresadas = {
        plan: 0 for plan in comisiones[tipo_venta]
    }
    tabla_html = render_template_string(
        render_template("tabla_comisiones.html", comisiones=comisiones, tipo_venta=tipo_venta, cantidades=cantidades_ingresadas)
    )
    return jsonify({"html": tabla_html})

@app.route("/tabla_comisiones_negocios", methods=["POST"])
def tabla_comisiones_negocios():
    tipo_venta = request.form.get("tipo_venta", "equipo_nuevo")
    cantidades_ingresadas = {
        plan: 0 for plan in comisiones_negocios[tipo_venta]
    }
    tabla_html = render_template_string(
        render_template("tabla_comisiones_negocios.html",
                        comisiones=comisiones_negocios,
                        tipo_venta=tipo_venta,
                        cantidades=cantidades_ingresadas)
    )
    return jsonify({"html": tabla_html})

@app.route("/tabla_comisiones_simple", methods=["POST"])
def tabla_comisiones_simple():
    tipo_venta = request.form.get("tipo_venta", "simple_plus")
    cantidades_ingresadas = {
        plan: 0 for plan in comisiones_simple[tipo_venta]
    }
    tabla_html = render_template_string(
        render_template("tabla_comisiones_simple.html", 
                        comisiones=comisiones_simple, 
                        tipo_venta=tipo_venta,
                        cantidades=cantidades_ingresadas)
    )
    return jsonify({"html": tabla_html})

@app.route("/tabla_comisiones_total", methods=["POST"])
def tabla_comisiones_total():
    tipo_venta = request.form.get("tipo_venta", "simple_plus")
    cantidades_ingresadas = {
        plan: 0 for plan in comisiones_total[tipo_venta]
    }
    tabla_html = render_template_string(
        render_template("tabla_comisiones_total.html", comisiones=comisiones_total, tipo_venta=tipo_venta,cantidades=cantidades_ingresadas)
    )
    return jsonify({"html": tabla_html})

@app.route("/tabla_comisiones_addons", methods=["POST"])
def tabla_comisiones_addons():
   
    cantidades_ingresadas = {
        plan: 0 for plan in comisiones_addons
    }
    tabla_html = render_template_string(
        render_template("tabla_comisiones_addons.html", comisiones=comisiones_addons,cantidades=cantidades_ingresadas)
    )
    return jsonify({"html": tabla_html})

@app.route('/calcular_comision', methods=['POST'])

def calcular_comision():
    data = request.json
    total_comision = 0

    for item in data:
        precio = float(item['precio'])
        cantidad = int(item['cantidad'])
        marca = item['marca'].lower()

        if 'alphacomm' in marca:
            comision = precio * cantidad * 0.10
        else:
            comision = precio * cantidad * 0.02

        total_comision += comision

    return jsonify({"total_comision": round(total_comision, 2)})


import atexit
atexit.register(lambda: scheduler.shutdown())


# if __name__ == "__main__":
#     # app.run()
#     generar_cache_accesorios()
#     app.run(debug=True, port=5000)
