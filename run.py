# coding=utf-8
import api

# Scraping rápido del formulario de horarios
from lxml import html
import requests
from requests.exceptions import ConnectionError
while True:
    try:
        pagina = html.fromstring(
            requests.get('https://guayacan.uninorte.edu.co/4PL1CACI0N35/registro/consulta_horarios.php').content,
            parser=html.HTMLParser(encoding='utf-8')
        )
        niveles = {nivel.get('value'): nivel.text for nivel in pagina.xpath('//select[@name="nivel"]/option')[1:]}
        periodos = {periodo.get('value'): periodo.text for periodo in pagina.xpath('//select[@name="periodo"]/option')[1:]}
        break
    except ConnectionError as e:
        print(e)

# Creación de la aplicación en Flask
from flask import Flask, render_template, redirect, url_for, request, jsonify
app = Flask(__name__)

from flask.json import JSONEncoder
from bson import ObjectId
class encoder(JSONEncoder):
    def default(self, o):
        if isinstance(o, ObjectId):
            return str(o)
        return JSONEncoder.default(self, o)
app.json_encoder = encoder
app.config['JSON_AS_ASCII'] = False

app.jinja_env.variable_start_string = '@('
app.jinja_env.variable_end_string = ')'
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')

@app.route('/')
def inicio():
    return redirect(url_for('main', periodo = max(int(x) for x in periodos.keys())))

@app.route('/<periodo>')
def main(periodo):
    return render_template('main.pug', periodos=periodos, periodo=periodo, niveles=niveles)

@app.route('/api/<periodo>/buscar')
def buscar(periodo):
    busca = request.args.get('busca')
    codigo = request.args.get('codigo')
    dpto = request.args.get('departamento')
    nivel = request.args.get('nivel')
    return jsonify(api.buscar(periodo, busca, nivel, codigo, dpto))

@app.route('/api/<periodo>/horarios')
def horarios(periodo):
    nivel = request.args.get('nivel')
    codigo = request.args.get('codigo')
    curso = request.args.get('curso')
    return jsonify(api.horarios(periodo, nivel, codigo, curso))

@app.route('/api/<periodo>/actualizar', methods=['POST'])
def actualizar(periodo):
    nivel = request.form['nivel']
    codigo = request.form['codigo']
    return api.actualizar(periodo, nivel, codigo)

##@app.route('/<periodo>/vieja')
##def vieja(periodo):
##    return render_template('vieja.pug', periodo=periodo, niveles=niveles)
    
if __name__ == '__main__':
    app.run(debug = True)
