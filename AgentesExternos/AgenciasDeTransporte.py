__author__ = 'bejar'

import argparse
import random
import requests
from flask import Flask, request

# Definimos los parametros de la linea de comandos
parser = argparse.ArgumentParser()
parser.add_argument('--host', default='localhost', help="Host agente")
parser.add_argument('--port', type=int,  help="Puerto agente")
parser.add_argument('--acomm', help='Direccion del agente con el que comunicarse')
parser.add_argument('--aport', type=int, help='Puerto del agente con el que comunicarse')
parser.add_argument('--messages', nargs='+', default=[], help="mensajes a enviar")

app = Flask(__name__)

arraytransportes = ["avión", "tren", "barco"]
@app.route("/")
def index():
    texto = 'Hola soy la agencia de transportes.  Para obtener el medio de transporte ideal para tu viaje ve a http://localhost:5000/transportes'
    return texto

@app.route("/transportes")
def transportes():
    """
        calls to /browsequotes/v1.0/{country}/{currency}/{locale}/{originPlace}/{destinationPlace}/{outboundPartialDate}/{inboundPartialDate}
        :return:
        """
    country = request.args["pais"]
    currency = request.args["moneda"]
    originplace = request.args["origen"]
    destinationplace = request.args["destinación"]
    outbounddate = request.args["fechaSalida"]
    inbounddate = request.args["fechaVuelta"]
    respuesta = arraytransportes[random.randint(0, 3)]
    return respuesta

if __name__ == '__main__':

    # parsing de los parametros de la linea de comandos
    args = parser.parse_args()

    # Ponemos en marcha el servidor
    app.run(host=args.host, port=args.port)

    print('The End')