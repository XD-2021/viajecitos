
import argparse
import random
from multiprocessing import Queue

import requests
import socket
from flask import Flask, request

# Definimos los parametros de la linea de comandos
from rdflib import Graph, namespace, Namespace, RDF

from AgentUtil.ACL import ACL
from AgentUtil.ACLMessages import get_message_properties, build_message
from AgentUtil.Agent import Agent
from AgentUtil.Logging import config_logger
from Agentes.AgenteObtenedorDeOfertasDeAlojamiento import AgenteObtenedorAlojamiento

parser = argparse.ArgumentParser()
parser.add_argument('--host', default='localhost', help="Host agente")
parser.add_argument('--port', type=int,  help="Puerto agente")
parser.add_argument('--acomm', help='Direccion del agente con el que comunicarse')
parser.add_argument('--aport', type=int, help='Puerto del agente con el que comunicarse')
parser.add_argument('--messages', nargs='+', default=[], help="mensajes a enviar")

# Logging
logger = config_logger(level=1)

# parsing de los parametros de la linea de comandos
args = parser.parse_args()

# Configuration stuff
if args.port is None:
    port = 9010
else:
    port = args.port

if args.open is None:
    hostname = '0.0.0.0'
else:
    hostname = socket.gethostname()

if args.dport is None:
    dport = 9081
else:
    dport = args.dport

if args.dhost is None:
    dhostname = socket.gethostname()
else:
    dhostname = args.dhost
    # Agent Namespace
    agn = Namespace("http://www.agentes.org#")

    # Message Count
    mss_cnt = 0

    # Data Agent
    # Datos del Agente
    AgenteObtenedorAlojamiento = Agent('AgenteObtenedorDeOfertasDeAlojamiento',
                        agn.AgenteObtenedorAlojamiento,
                        'http://%s:%d/comm' % (hostname, port),
                        'http://%s:%d/Stop' % (hostname, port))

    # Directory agent address
    DirectoryAgent = Agent('DirectoryAgent',
                           agn.Directory,
                           'http://%s:%d/Register' % (dhostname, dport),
                           'http://%s:%d/Stop' % (dhostname, dport))

    # Global triplestore graph
    dsGraph = Graph()

    # Queue
    queue = Queue()

app = Flask(__name__)

arrayalojamientos = ["HOTEL PACO", "HOTEL VELA", "HOTEL ARTS", "HOTEL IBIS", "HOTEL REINA SOFIA", "HOTEL HILTON"]
mss_cnt = 0
# Directory agent address
DirectoryAgent = Agent('DirectoryAgent',
                        agn.Directory,
                        'http://%s:%d/Register' % (dhostname, dport),
                        'http://%s:%d/Stop' % (dhostname, dport))
# Global triplestore graph
dsGraph = Graph()

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
    global dsGraph

    message = request.args['content']
    gm = Graph()
    gm.parse(data=message)

    msgdic = get_message_properties(gm)

    gr = Graph

    if msgdic is None:
        # Si no es, respondemos que no hemos entendido el mensaje
        gr = build_message(Graph(), ACL['not-understood'], sender=AgenteObtenedorAlojamiento.uri, msgcnt=get_count())
    else:
        # Obtenemos la performativa
        if msgdic['performative'] != ACL.request:
            # Si no es un request, respondemos que no hemos entendido el mensaje
            gr = build_message(Graph(),
                               ACL['not-understood'],
                               sender=DirectoryAgent.uri,
                               msgcnt=get_count())
        else:
            content = msgdic['content']
            # Averiguamos el tipo de la accion
            accion = gm.value(subject=content, predicate=RDF.type)

            if accion == "peticion_de_alojamiento":
                outbounddate = request.args["fechaSalida"]
                inbounddate = request.args["fechaVuelta"]
                respuesta = arrayalojamientos[random.randint(0, len(arrayalojamientos)-1)]
                return respuesta
            return 0    #lol

def get_count():
    global mss_cnt
    mss_cnt += 1
    return mss_cnt

if __name__ == '__main__':

    # parsing de los parametros de la linea de comandos
    args = parser.parse_args()

    # Ponemos en marcha el servidor
    app.run(host=args.host, port=5001)

    print('The End')
