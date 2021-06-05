
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

arrayalojamientos = ["HOTEL PACO", "HOTEL VELA", "HOTEL ARTS", "HOTEL IBIS", "HOTEL REINA SOFIA", "HOTEL HILTON"]
@app.route("/")
def index():
    texto = 'Hola soy la agencia de hoteles.  Para obtener los hoteles ideales para tu viaje ve a http://localhost:5001/hoteles'
    return texto

@app.route("/hoteles")
def hoteles():
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
    respuesta = arrayalojamientos[random.randint(0, len(arrayalojamientos)-1)]
    return respuesta

if __name__ == '__main__':

    # parsing de los parametros de la linea de comandos
    args = parser.parse_args()

    # Ponemos en marcha el servidor
    app.run(host=args.host, port=5001)

    print('The End')
