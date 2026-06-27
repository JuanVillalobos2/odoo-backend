import os
import time
import json
from flask import Flask, Response
from flask_cors import CORS
import odoorpc

app = Flask(__name__)
# CORS permite que tu página de Netlify lea los datos de Render sin bloqueos
# Reemplaza la línea vieja de CORS(app) por estas dos líneas:
CORS(app, resources={r"/api/*": {"origins": "*"}})
app.config['CORS_HEADERS'] = 'Content-Type'

# =====================================================================
# CONFIGURACIÓN SEGURA MEDIANTE VARIABLES DE ENTORNO (os.environ)
# =====================================================================
# Si Render no encuentra la variable, usará el valor por defecto que pongas a la derecha
ODOO_HOST = os.environ.get('ODOO_HOST', 'la-guardiana-de-characato-prueba-1.odoo.com') 
ODOO_PORT = int(os.environ.get('ODOO_PORT', 443))
ODOO_DB = os.environ.get('ODOO_DB', 'la-guardiana-de-characato-prueba-1')
ODOO_USER = os.environ.get('ODOO_USER', 'logistica2grupolamtrona@outloook.com')
ODOO_PASSWORD = os.environ.get('d89bc19cd1886af22be6949bbeca39919678c28a')
# =====================================================================

def consultar_odoo():
    """Se conecta a Odoo usando las variables seguras y extrae el inventario."""
    # Validación básica por si olvidaste configurar la contraseña en Render
    if not ODOO_PASSWORD:
        print("Error: La variable ODOO_PASSWORD no está configurada en el servidor.")
        return None

    try:
        # Inicializa la conexión con Odoo (JSON-RPC con SSL)
        odoo = odoorpc.ODOO(ODOO_HOST, protocol='jsonrpc+ssl', port=ODOO_PORT)
        
        # Inicia sesión con los datos ocultos
        odoo.login(ODOO_DB, ODOO_USER, ODOO_PASSWORD)
        
        # Apunta al modelo de variantes de producto en Odoo
        Product = odoo.env['product.product']
        
        # Busca solo los productos que estén marcados como Activos
        posiciones = Product.search([('active', '=', True)])
        
        # Lee los campos: Código (default_code), Nombre (name) y Stock a la mano (qty_available)
        productos_odoo = Product.read(posiciones, ['default_code', 'name', 'qty_available'])
        
        # Estructura la información para que la reciba tu HTML
        lista_productos = []
        for p in productos_odoo:
            lista_productos.append({
                "codigo": p.get('default_code') or 'S/C',
                "nombre": p.get('name'),
                "cantidad": int(p.get('qty_available') or 0),
                "ubicacion": "Almacén Odoo"
            })
        return lista_productos
    except Exception as e:
        print(f"Error en la conexión o consulta a Odoo: {e}")
        return None

@app.route('/api/live-inventario', methods=['GET', 'OPTIONS'])
def live_inventario():
    """Retorna el inventario en formato JSON estándar con soporte CORS completo"""
    # Si el navegador hace una pregunta de seguridad previa (OPTIONS)
    from flask import jsonify
    
    datos_actuales = consultar_odoo()
    
    if datos_actuales is None:
        response = jsonify({"error": "No se pudo conectar a Odoo"})
        response.status_code = 500
    else:
        response = jsonify(datos_actuales)
        
    # Forzamos las cabeceras CORS estándar que los navegadores aman
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Methods'] = 'GET, OPTIONS'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type'
    return response

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)
