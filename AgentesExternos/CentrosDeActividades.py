from random import random

from flask import Flask, request, Response
from flask.json import jsonify
import json
import argparse
import requests
from requests import ConnectionError
import random

# Definimos los parametros de la linea de comandos
parser = argparse.ArgumentParser()
parser.add_argument('--host', default='localhost', help="Host del agente")
parser.add_argument('--port', type=int, help="Puerto de comunicacion del agente")
parser.add_argument('--acomm', help='Direccion del agente con el que comunicarse')
parser.add_argument('--aport', type=int, help='Puerto del agente con el que comunicarse')
parser.add_argument('--messages', nargs='+', default=[], help="mensajes a enviar")

app = Flask(__name__)

arrayActividadesEvento = ["FESTIVIDAD", "FIESTA NOCHE", "NIGHT CLUB"]
arrayActividadesRestaurante = ["RESTAURANTE PACO", "RESTAURANTE DE MARISCO 1", "RESTAURANTE 2" ,"RESTAURANTE 3"]
arrayActividadesTuristico = ["SAGRADA FAMILIA", "MACBA", "CASTILLO MONTJUIC", "PARC GÜELL", "MNAC", "FUNDACIÓ JOAN MIRÓ"]

@app.route("/")
def isAlive():
    texto = 'Hola soy los centros de actividades.  Para obtener las actividades para tu viaje ve a http://localhost:5000/actividades'
    return texto


@app.route("/actividades")
def actividades():
    """
    /place?location=loc&keyword=key&type=type
    :return:
    """
    country = request.args["pais"]
    currency = request.args["moneda"]
    date = request.args["fecha"]

    respuesta = arrayActividadesTuristico[random.randint(0, len(arrayActividadesTuristico)-1)]

    return respuesta

if __name__ == '__main__':

    # parsing de los parametros de la linea de comandos
    args = parser.parse_args()

    # Ponemos en marcha el servidor
    app.run(host=args.host, port=9101)

    print('The End')