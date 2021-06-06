# -*- coding: utf-8 -*-
"""
filename: UserPersonalAgent
Agent que implementa la interacció amb l'usuari
@author: bejar
"""
import random
from multiprocessing import Queue, Process
import sys
from AgentUtil.ACLMessages import get_agent_info, send_message, build_message, get_message_properties, register_agent
from AgentUtil.OntoNamespaces import ACL, ECSDI
import argparse
import socket
from multiprocessing import Process
from flask import Flask, render_template, request
from rdflib import Graph, Namespace, RDF, URIRef, Literal, XSD
from AgentUtil.Agent import Agent
from AgentUtil.FlaskServer import shutdown_server
from AgentUtil.Logging import config_logger
from datetime import datetime

__author__ = 'bejar'


class Alojamiento:

    def __init__(self):
        self.coste = None
        self.latitud = None
        self.longitud = None


class Actividad:

    def __init__(self):
        self.coste = None


class Transporte:

    def __init__(self):
        self.origen = None
        self.destino = None
        self.salida = None
        self.llegada = None
        self.coste = None


# Definimos los parametros de la linea de comandos
parser = argparse.ArgumentParser()
parser.add_argument('--open', help="Define si el servidor est abierto al exterior o no", action='store_true',
                    default=True)
parser.add_argument('--port', type=int, help="Puerto de comunicacion del agente")
parser.add_argument('--dhost', default=socket.gethostname(), help="Host del agente de directorio")
parser.add_argument('--dport', type=int, help="Puerto de comunicacion del agente de directorio")

# Logging
logger = config_logger(level=1)

# parsing de los parametros de la linea de comandos
args = parser.parse_args()

# Configuration stuff
if args.port is None:
    port = 9002
else:
    port = args.port

if args.open is None:
    hostname = '0.0.0.0'
else:
    hostname = socket.gethostname()

if args.dport is None:
    dport = 9000
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
AgenteProcesador = Agent('AgenteProcesador',
                         agn.AgenteProcesador,
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

# Flask app
app = Flask(__name__)


def get_count():
    global mss_cnt
    mss_cnt += 1
    return mss_cnt


def register_message():
    """
    Envia un mensaje de registro al servicio de registro
    usando una performativa Request y una accion Register del
    servicio de directorio
    :param gmess:
    :return:
    """

    logger.info('Nos registramos')

    gr = register_agent(AgenteProcesador, DirectoryAgent, AgenteProcesador.uri, get_count())
    return gr


def buscar_alojamiento(ciudadNombre='Barcelona'):
    # Creamos el contenido
    content = ECSDI['peticion_de_alojamiento' + str(get_count())]

    # Creamos los objetos necesarios para las tripletas del grafo

    ciudad = ECSDI['ciudad' + str(get_count())]
    localizacion = ECSDI['localizacion' + str(get_count())]

    # Creamos el grafo con las tripletas

    grafo = Graph()

    grafo.add((ciudad, RDF.type, ECSDI.ciudad))
    grafo.add((localizacion, RDF.type, ECSDI.localizacion))
    grafo.add((ciudad, ECSDI.nombre, Literal(ciudadNombre)))
    grafo.add((localizacion, ECSDI.pertenece_a, URIRef(ciudad)))
    grafo.add((content, RDF.type, ECSDI.peticion_de_alojamiento))
    grafo.add((content, ECSDI.tiene_como_restriccion_de_localizacion, URIRef(localizacion)))

    # Preguntamos por el agente que necesitamos
    agente_alojamiento = get_agent_info(agn.AgenteObtenedorDeOfertasDeAlojamiento, DirectoryAgent, AgenteProcesador,
                                        get_count())

    # Enviamos el mensaje
    gr = send_message(
        build_message(grafo, perf=ACL.request, sender=AgenteProcesador.uri, receiver=agente_alojamiento.uri,
                      msgcnt=get_count(),
                      content=content), agente_alojamiento.address)

    # Retornamos el grafo respuesta del mensaje

    return gr


def buscar_desplazamiento(ciudadNombre='Barcelona'):
    # Creamos el contenido
    content = ECSDI['peticion_de_desplazamiento' + str(get_count())]

    # Creamos los objetos necesarios para las tripletas del grafo

    ciudadOrigen = ECSDI['ciudadOrigen' + str(get_count())]
    ciudadDestino = ECSDI['ciudadDestino' + str(get_count())]

    # Creamos el grafo con las tripletas

    grafo = Graph()

    grafo.add((ciudadOrigen, RDF.type, ECSDI.ciudadOrigen))
    grafo.add((ciudadDestino, RDF.type, ECSDI.ciudadOrigen))
    grafo.add((content, RDF.type, ECSDI.peticion_de_desplazamiento))

    # Preguntamos por el agente que necesitamos
    agente_desplazamiento = get_agent_info(agn.AgenteObtenedorDeOfertasDeDesplazamiento, DirectoryAgent,
                                           AgenteProcesador, get_count())

    # Enviamos el mensaje
    gr = send_message(
        build_message(grafo, perf=ACL.request, sender=AgenteProcesador.uri, receiver=agente_desplazamiento.uri,
                      msgcnt=get_count(),
                      content=content), agente_desplazamiento.address)

    # Retornamos el grafo respuesta del mensaje

    return gr


def buscar_actividades(type):  # type = ludica/festiva/cultural
    # Creamos el contenido
    content = ECSDI['peticion_de_actividades' + str(get_count())]

    # Creamos los objetos necesarios para las tripletas del grafo

    tipo = ECSDI['tipoActividad' + str(get_count())]

    # Creamos el grafo con las tripletas

    grafo = Graph()

    grafo.add((tipo, RDF.type, ECSDI.ciudadOrigen))
    grafo.add((content, RDF.type, ECSDI.peticion_de_actividades))

    # Preguntamos por el agente que necesitamos
    agente_actividades= get_agent_info(agn.AgenteObtenedorDeOfertasDeActividades, DirectoryAgent,
                                           AgenteProcesador, get_count())

    # Enviamos el mensaje
    gr = send_message(
        build_message(grafo, perf=ACL.request, sender=AgenteProcesador.uri, receiver=agente_actividades.uri,
                      msgcnt=get_count(),
                      content=content), agente_actividades.address)

    # Retornamos el grafo respuesta del mensaje

    return gr



def filtrar(ciudadOrigen,
           ciudadDestino,
           dataInicio,
           dataFin,
           ponderacionLudica,
           ponderacionCulturales,
           ponderacionFestivas,
           precioAlojamientoMinimo,
           precioAlojamientoMaximo,
           precioTransporteMinimo,
           precioTransporteMaximo,
           gr_actividades,
           gr_alojamiento):
    # gr_vuelos):

    grafo = Graph()
    content = ECSDI['respuesta_de_plan' + str(get_count())]
    grafo.add((content, RDF.type, ECSDI.respuesta_de_plan))
    plan = ECSDI['plan_de_viaje' + str(get_count())]
    grafo.add((plan, ECSDI.tiene_como_plan_de_viaje, URIRef(plan)))


    for s, p, o in gr_alojamiento:
        if o == ECSDI.alojamiento:
            coste = gr_alojamiento.value(subject=s, predicate=ECSDI.coste)
            if coste >= precioAlojamientoMinimo and coste <= precioAlojamientoMaximo:
                alojamiento = s

                compania = gr_alojamiento.value(subject=s, predicate=ECSDI.es_ofrecido_por)
                nombre_compania = gr_alojamiento.value(subject=compania, predicate=ECSDI.nombre)

                periodo = gr_alojamiento.value(subject=s, predicate=ECSDI.tiene_como_horario)
                dia_de_la_semana = gr_alojamiento.value(subject=periodo, predicate=ECSDI.dia_de_la_semana)
                inicio = gr_alojamiento.value(subject=periodo, predicate=ECSDI.inicio)
                fin = gr_alojamiento.value(subject=periodo, predicate=ECSDI.fin)

                localizacion = gr_alojamiento.value(subject=s, predicate=ECSDI.se_encuentra_en)
                ciudad = gr_alojamiento.value(subject=localizacion, predicate=ECSDI.pertenece_a)
                latitud = gr_alojamiento.value(subject=localizacion, predicate=ECSDI.latitud)
                longitud = gr_alojamiento.value(subject=localizacion, predicate=ECSDI.longitud)
                direccion = gr_alojamiento.value(subject=localizacion, predicate=ECSDI.direccion)
                nombre_ciudad = gr_alojamiento.value(subject=ciudad, predicate=ECSDI.nombre)

                # Compania
                grafo.add((compania, RDF.type, ECSDI.compania))
                grafo.add((compania, ECSDI.nombre, Literal(nombre_compania)))

                # Periodo
                grafo.add((periodo, RDF.type, ECSDI.periodo))
                grafo.add((periodo, ECSDI.dia_de_la_semana, Literal(dia_de_la_semana)))
                grafo.add((periodo, ECSDI.inicio, Literal(inicio)))
                grafo.add((periodo, ECSDI.fin, Literal(fin)))

                # Ciudad
                grafo.add((ciudad, RDF.type, ECSDI.ciudad))
                grafo.add((ciudad, ECSDI.nombre, Literal(nombre_ciudad)))

                # Localizacion
                grafo.add((localizacion, RDF.type, ECSDI.localizacion))
                grafo.add((localizacion, ECSDI.direccion, Literal(direccion)))
                grafo.add((localizacion, ECSDI.pertenece_a, URIRef(ciudad)))

                # Crear las tripletas

                grafo.add((alojamiento, RDF.type, ECSDI.alojamiento))
                grafo.add((alojamiento, ECSDI.se_encuentra_en, URIRef(localizacion)))
                grafo.add((alojamiento, ECSDI.coste, Literal(coste)))
                grafo.add((alojamiento, ECSDI.es_ofrecido_por, URIRef(compania)))
                grafo.add((alojamiento, ECSDI.tiene_como_horario, URIRef(periodo)))
                grafo.add((plan, ECSDI.tiene_como_alojamiento_del_plan, URIRef(alojamiento)))

                break


    vuelos_de_ida = []
    vuelos_de_vuelta = []
    # for s, p, o in gr_vuelos:
    #    if o == ECSDI.vuelo:
    #        NotImplementedYet = None

    actividades_festivas = []
    actividades_culturales = []
    actividades_ludicas = []
    for s, p, o in gr_actividades:
        if o == ECSDI.actividad:
            tipo = gr_actividades.value(subject=s, predicate=ECSDI.tipo_de_actividad)
            if tipo == "Fiesta":
                actividades_festivas.__add__(s)
            elif tipo == "Ludica":
                actividades_ludicas.__add__(s)
            elif tipo == "Cultural":
                actividades_culturales.__add__(s)
    # # No conseguimos sacar el numero de dias entre 2 hardcodeamos dias para tirar adelante
    # iniDate = datetime.strptime(dataInicio, "%d/%m/%Y").strftime("%Y-%m-%d")
    # finDate = datetime.strptime(dataFin, "%d/%m/%Y").strftime("%Y-%m-%d")
    # dias_de_plan = abs(finDate - iniDate).days

    dias_de_plan = 3

    data = dataInicio
    for i in range(dias_de_plan):
        plan_de_un_dia = ECSDI['plan_de_un_dia' + str(get_count())]
        grafo.add((plan_de_un_dia, RDF.type, ECSDI.plan_de_un_dia))
        grafo.add((plan, ECSDI.tiene_para_cada_dia, URIRef(plan_de_un_dia)))

        for activity in gr_actividades:
            localizacion = gr_actividades.value(subject=activity, predicate=ECSDI.se_encuentra_en)
            latitud = gr_actividades.value(subject=localizacion, predicate=ECSDI.latitud)
            longitud = gr_actividades.value(subject=localizacion, predicate=ECSDI.longitud)
            periodo = gr_actividades.value(subject=activity, predicate=ECSDI.tiene_como_horario)
            inicio = gr_actividades.value(subject=periodo, predicate=ECSDI.inicio)
            fin = gr_actividades.value(subject=periodo, predicate=ECSDI.fin)
            compania = gr_actividades.value(subject=activity, predicate=ECSDI.es_ofrecido_por)
            nombre_compania = gr_actividades.value(subject=compania, predicate=ECSDI.nombre)

            # Localizacion
            grafo.add((localizacion, RDF.type, ECSDI.localizacion))
            grafo.add((localizacion, ECSDI.longitud, Literal(longitud)))
            grafo.add((localizacion, ECSDI.latitud, Literal(latitud)))

            # Periodo
            grafo.add((periodo, RDF.type, ECSDI.periodo))
            grafo.add((periodo, ECSDI.inicio, Literal(inicio)))
            grafo.add((periodo, ECSDI.fin, Literal(fin)))

            # Compania
            grafo.add((compania, RDF.type, ECSDI.compania))
            grafo.add((compania, ECSDI.nombre, Literal(nombre_compania)))

            # Actividad
            grafo.add((activity, RDF.type, ECSDI.activiad))
            grafo.add((activity, ECSDI.coste, Literal(coste)))
            grafo.add((activity, ECSDI.se_encuentra_en, URIRef(localizacion)))
            grafo.add((activity, ECSDI.tiene_como_horario, URIRef(periodo)))
            grafo.add((activity, ECSDI.es_ofrecido_por, URIRef(compania)))

    return grafo


@app.route("/Stop")
def stop():
    """
    Entrypoint to the agent
    :return: string
    """

    tidyUp()
    shutdown_server()
    return "Stopping server"


def tidyUp():
    """
    Previous actions for the agent.
    """

    global queue
    queue.put(0)

    pass


def agent_behaviour(queue):
    """
    Agent Behaviour in a concurrent thread.
    :param queue: the queue
    :return: something
    """

    gr = register_message()
    gr_alo = buscar_alojamiento("Barcelona")
    gr_act = buscar_actividades("ludica")
    gr_des = buscar_desplazamiento()

    filtrar()


if __name__ == '__main__':
    # ------------------------------------------------------------------------------------------------------
    # Run behaviors
    ab1 = Process(target=agent_behaviour, args=(queue,))
    ab1.start()

    # Run server
    app.run(host=hostname, port=port, debug=True)

    # Wait behaviors
    ab1.join()
    print('The End')
