import os
import time
import json
from flask import Flask, Response
from flask_cors import CORS
import odoorpc

app = Flask(__name__)
# CORS permite que tu página de Netlify lea los datos de Render sin bloqueos
CORS(app)

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

@app.route('/api/live-inventario')
def live_inventario():
    """Mantiene un canal abierto con el navegador (SSE) para actualizar en tiempo real."""
    def evento_stream():
        ultimo_estado = []
        while True:
            datos_actuales = consultar_odoo()
            
            # Si la consulta funcionó y el stock cambió desde la última revisión...
            if datos_actuales is not None and datos_actuales != ultimo_estado:
                ultimo_estado = datos_actuales
                # Envía los datos frescos en formato JSON estructurado para SSE
                yield f"data: {json.dumps(datos_actuales)}\n\n"
            
            # Espera 5 segundos antes de volver a verificar si cambió algo en Odoo
            time.sleep(5)
            
    return Response(evento_stream(), mimetype='text/event-stream')

if __name__ == '__main__':
    # Configuración óptima para producción en Render con soporte multi-hilo
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)