# coding=utf-8
from pymongo import MongoClient
db =  MongoClient().db

from string import capwords
from lxml import html
import requests
from requests.exceptions import ConnectionError

def quitar_tildes(frase):
    if frase:
        letras = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ü':'u',
                  'Á':'A', 'É':'E', 'Í':'I', 'Ó':'O', 'Ú':'U', 'Ü':'U'}
        for k, v in letras.iteritems():
            frase = frase.replace(k.decode('utf-8'), v)
    return frase

def webscraping(url, data):
    while True:
        try:
            return html.fromstring(requests.post(url,data=data).content,
                                   parser=html.HTMLParser(encoding='utf-8'))
        except ConnectionError as e:
            print(e)

def actualizar(periodo, nivel, codigo):
    codigo = quitar_tildes(codigo[:3]).upper()
    pagina = webscraping('https://guayacan.uninorte.edu.co/4PL1CACI0N35/registro/resultado_codigo1.php', {
        'valida':'OK',
        'mat': codigo,
        'datos_periodo':periodo,
        'datos_nivel':nivel})
    
    db.clases.delete_many({'periodo': periodo, 'nivel': nivel, 'codigo': codigo})
    resultados = pagina.xpath('//div[contains(@class, "div")]')
    if resultados:
        clases = []
        for resultado in resultados:
            curso = resultado.xpath('p/text()')[1].strip()
            clase = next((c for c in clases if c['curso']==curso[4:]), None)
            if clase is None:
                print('Insert '+curso)
                nombre = resultado.xpath('p/b/text()')[0].replace('?', 'Ñ')
                departamento = resultado.xpath('p/text()')[0].replace('?', 'ñ')
                clase = {
                    'periodo': periodo,
                    'nivel': nivel,
                    'nombre': nombre,
                    'departamento': departamento,
                    'codigo': curso[:3],
                    'curso': curso[4:]
                }
                db.clases.insert_one(clase)
                clases.append(clase)
        return len(clases)
    else:
        return {}

def buscar(periodo, busca, nivel, codigo, dpto):
    filtro = {'periodo': periodo}
    if nivel: filtro['nivel'] = nivel
    if codigo: filtro['codigo'] = codigo
    if dpto: filtro['departamento'] = dpto
    
    clases = sorted(db.clases.find(filtro), key= lambda c: c['nombre'])
    busca = quitar_tildes(busca).lower()
    for palabra in busca.split():
        def orden(clase):
            blanco = [clase['nombre'].lower(),
                      clase['codigo'].lower() + clase['curso'],
                      clase['departamento'].lower()]
            for i, parte in enumerate(blanco):
                if palabra in parte:
                    ind, pal = min([(ind, pal) for ind, pal in enumerate(parte.split()) if palabra in pal])
                    return i, pal.find(palabra), ind
            return None
            
        if palabra != '-':
            clases = sorted((c for c in clases if orden(c)), key=orden)
    return { 'clases':clases }

def horarios(periodo, nivel, codigo, curso):
    pagina = webscraping('https://guayacan.uninorte.edu.co/4PL1CACI0N35/registro/resultado_curso1.php', {
        'valida':'OK',
        'curso':curso,
        'mat2':codigo,
        'datos_periodo':periodo,
        'datos_nivel':nivel
    })
    
    resultados = pagina.xpath('//div[contains(@class, "div")]')
    if resultados:
        print('Webscraping de horarios hecho.')
        grupos = []
        profesores = []
        dias = dict(M='Lunes', T='Martes', W='Miércoles', R='Jueves', F='Viernes', S='Sábado')
        for resultado in resultados:
            datos = resultado.xpath('p/text()')
            grupo = datos[2].strip()
            nrc = datos[3].strip()
            matriculados = int(datos[4].strip())
            disponibles = int(datos[5].strip())
            horarios = []
            for item in resultado.xpath('div/div/div/table/tr')[1:]:
                datos = item.xpath('td/text()')
                for dia in datos[2]:
                    horas = [int(militar[:2]) for militar in datos[3].split(' - ')]
                    horas = set(h for h in range(horas[0], horas[1]))
                    profesor = datos[5].split(' - ')
                    profesor = capwords((profesor[1] + ' ' + profesor[0]).replace('?', 'ñ'))
                    if profesor not in profesores: profesores.append(profesor)

                    horario = next((h for h in horarios
                                    if h['dia']==dias[dia] and horas.intersection(h['horas'])
                                   ), None)
                    if horario is None:
                        horarios.append({
                            'dia': dias[dia],
                            'horas': list(horas),
                            'lugar': [datos[4]],
                            'profesor': [profesor]
                        })
                    else:
                        if datos[4] not in horario['lugar']: horario['lugar'].append(datos[4])
                        if profesor not in horario['profesor']: horario['profesor'].append(profesor)
                        for h in horas.difference(horario['horas']): horario['horas'].append(h)
            grupos.append({
                'grupo': int(grupo),
                'nrc': nrc,
                'horarios': horarios,
                'matriculados': matriculados,
                'disponibles': disponibles
            })
        return {
            'grupos':grupos,
            'profesores':profesores
        }
    else:
        return {}
