"""
.. module:: Solver

Solver
*************

:Description: Solver

    Solver generico que pasa los problemas a solvers especializados

:Authors: bejar
    

:Version: 

:Created on: 06/02/2018 8:20 

"""

from Util import gethostname
import argparse
from FlaskServer import shutdown_server
import requests
from flask import Flask, request, render_template
from requests import ConnectionError
from uuid import uuid4
import logging

__author__ = 'bejar'


def obscure(dir):
    """
    Hide real hostnames
    """
    odir = {}
    for d in dir:
        _, _, port = dir[d][1].split(':')
        odir[d] = (dir[d][0], f'{uuid4()}:{port}', dir[d][2], dir[d][3])

    return odir


app = Flask(__name__)
log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

problems = {}
logger = None


@app.route("/message")
def message():
    """
    Entrypoint para todas las comunicaciones

    :return:
    """
    global problems

    mess = request.args['message']

    if '|' not in mess:
        return 'ERROR: INVALID MESSAGE'
    else:
        # Sintaxis de los mensajes "TIPO|PARAMETROS"
        mess = mess.split('|')
        if len(mess) != 2:
            return 'ERROR: INVALID MESSAGE'
        else:
            messtype, messparam = mess

        if messtype not in ['SOLVE', 'SOLVED']:
            return 'ERROR: INVALID REQUEST'
        else:
            # parametros mensaje SOLVE = "PROBTYPE,CLIENTADDRESS,PROBID,PROB"
            if messtype == 'SOLVE':
                param = messparam.split(',')
                if len(param) == 4:
                    probtype, clientaddress, probid, prob = param
                    problems[probid] = [probtype, clientaddress, prob, 'PENDING']
                    # Buscamos el resolvedor del tipo adecuado y le mandamos el problema
                    if probtype in ['ARITH', 'MFREQ']:
                        minionadd = requests.get(diraddress + '/message',
                                                 params={'message': f'SEARCH|{probtype}'}).text
                        if 'OK' in minionadd:
                            # Le quitamos el OK de la respuesta
                            minionadd = minionadd[4:]
                            mess = 'SOLVE|%s,%s,%s' % (solveradd, probid, prob)
                            requests.get(minionadd + '/message', params={'message': mess})

                            # Registramos la actividad en el logger si existe
                            if logger is not None:
                                try:
                                    requests.get(logger + '/message', params={'message': f'{solverid},{probtype}'},
                                                 timeout=5)
                                except Exception:
                                    pass
                        else:
                            problems[probid][3] = 'FAILED SOLVER'
                            return 'ERROR: NO SOLVERS AVAILABLE'
                    else:
                        return 'ERROR: UNKNOWN PROBLEM TYPE'
                else:
                    return 'ERROR: WRONG PARAMETERS'
            # respuesta del solver con una solucion
            elif messtype == 'SOLVED':
                solution = messparam.split(',')
                if len(solution) == 2:
                    probid, sol = solution
                    if probid in problems:
                        problems[probid][3] = 'SOLVED'
                        resp = requests.get(problems[probid][1] + '/message',
                                            params={'message': f'SOLVED|{probid},{sol}'}).text
                    return 'OK'
                return 'OK'
    return ''


@app.route('/info')
def info():
    """
    Entrada que da informacion sobre el agente a traves de una pagina web
    """
    global problems

    return render_template('solverproblems.html', probs=obscure(problems))


@app.route("/stop")
def stop():
    """
    Entrada que para el agente
    """
    shutdown_server()
    return "Parando Servidor"


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--open', help="Define si el servidor esta abierto al exterior o no", action='store_true',
                        default=False)
    parser.add_argument('--port', type=int, help="Puerto de comunicacion del agente")
    parser.add_argument('--dir', default=None, help="Direccion del servicio de directorio")

    # parsing de los parametros de la linea de comandos
    args = parser.parse_args()

    # Configuration stuff
    if args.port is None:
        port = 9010
    else:
        port = args.port

    if args.open:
        hostname = '0.0.0.0'
    else:
        hostname = gethostname()

    if args.dir is None:
        raise NameError('A Directory Service addess is needed')
    else:
        diraddress = args.dir

    # Registramos el solver en el servicio de directorio
    solveradd = f'http://{gethostname()}:{port}'
    solverid = gethostname().split('.')[0] + '-' + str(port)
    mess = f'REGISTER|{solverid},SOLVER,{solveradd}'

    done = False
    while not done:
        try:
            resp = requests.get(diraddress + '/message', params={'message': mess}).text
            done = True
        except ConnectionError:
            pass

    if 'OK' in resp:
        print(f'SOLVER {solverid} successfully registered')
        # Buscamos el logger si existe en el registro
        loggeradd = requests.get(diraddress + '/message', params={'message': 'SEARCH|LOGGER'}).text
        if 'OK' in loggeradd:
            logger = loggeradd[4:]

        # Ponemos en marcha el servidor Flask
        app.run(host=hostname, port=port, debug=False, use_reloader=False)

        mess = f'UNREGISTER|{solverid}'
        requests.get(diraddress + '/message', params={'message': mess})
    else:
        print('Unable to register')
