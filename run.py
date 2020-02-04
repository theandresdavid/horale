# coding=utf-8
import api
from flask import Flask, render_template, redirect, url_for, request, jsonify

app = Flask(__name__)
app.jinja_env.variable_start_string = '@('
app.jinja_env.variable_end_string = ')'
app.jinja_env.add_extension('pypugjs.ext.jinja.PyPugJSExtension')
app.config['JSON_AS_ASCII'] = False

@app.route('/')
def inicio():
    (periodos, __) = api.periodos_y_niveles()
    return redirect(url_for('main', periodo = max(int(x) for x in periodos.keys())))

@app.route('/<periodo>')
def main(periodo):
    (periodos, niveles) = api.periodos_y_niveles()
    if (periodo in periodos):
        return render_template('main.pug', periodos=periodos, niveles=niveles, periodo=periodo)
    else:
        return redirect(url_for('inicio'))

@app.route('/api/<periodo>/buscar/<busca>')
def buscar(periodo, busca):
    niveles = dict(request.args)
    return jsonify(api.buscar(periodo, busca, niveles))

@app.route('/api/<periodo>/horarios')
def horarios():
    args = dict(request.args)
    return jsonify(api.horarios(periodo, args))

@app.route('/api/<periodo>/actualizar/<codigo>', methods=['POST'])
def actualizar(periodo, codigo):
    niveles = dict(request.args)
    return api.actualizar(periodo, codigo, niveles)

if __name__ == '__main__':
    app.run(debug = True)
