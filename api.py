from pymongo import MongoClient
from lxml import html
import requests
from requests.exceptions import ConnectionError

db =  MongoClient('mongodb+srv://admin:thewaywesaygoodbye@cluster-rwz5k.gcp.mongodb.net/test?retryWrites=true&w=majority').db
niveles = {'PR':'Pregrado','EX':'Extracurricular','PG':'Posgrado','EC':'Educación Continua'}

def webscrape(url, data=None):
  try:
    return html.fromstring(requests.post(url,data=data).content,
                            parser=html.HTMLParser(encoding='utf-8'))
  except ConnectionError as e:
    print(e)
    return None

def periodos():
  pagina = webscrape('https://guayacan.uninorte.edu.co/4PL1CACI0N35/registro/consulta_horarios.php')
  if not pagina: return {}

  periodos = { periodo.get('value'): periodo.text
               for periodo in pagina.xpath('//select[@name="periodo"]/option')[1:]
               if periodo.get('value') != '0000' }
  return periodos

def actualizar(periodo, codigo):
  codigo = codigo[:3].upper()
  clases = []
  for nivel in niveles:
    pagina = webscrape('https://guayacan.uninorte.edu.co/4PL1CACI0N35/registro/resultado_codigo1.php', {
      'valida':'OK',
      'mat':codigo,
      'datos_periodo':periodo,
      'datos_nivel':nivel
    })
    if not pagina: return {}

    resultados = pagina.xpath('//div[contains(@class, "div")]')
    for resultado in resultados:
      curso = resultado.xpath('p/text()')[1].strip()
      clase = next((c for c in clases if c['curso']==curso[4:] and c['nivel']==nivel), None)
      if clase is None:
        nombre = resultado.xpath('p/b/text()')[0].replace('?', 'Ñ')
        departamento = resultado.xpath('p/text()')[0].replace('?', 'ñ')
        clase = {
          'periodo': periodo,
          'nivel': nivel,
          'tipo': niveles[nivel],
          'nombre': nombre,
          'departamento': departamento,
          'codigo': curso[:3],
          'curso': curso[4:]
        }
        clases.append(clase)
  if clases:
    db.clases.delete_many({'periodo': periodo, 'codigo': codigo})
    db.clases.insert(clases)
    return {'codigo': codigo, 'cantidad': len(clases)}
  else:
    return {'codigo': codigo}

def buscar(periodo, busca):
  busca = busca.lower()
  clases = sorted(db.clases.find({ 'periodo': periodo }), key= lambda c: c['nombre'])

  sin_tilde = {'á':'a', 'é':'e', 'í':'i', 'ó':'o', 'ú':'u', 'ü':'u',
               'Á':'A', 'É':'E', 'Í':'I', 'Ó':'O', 'Ú':'U', 'Ü':'U'}
  for k, v in sin_tilde.items():
    busca = busca.replace(k, v)

  for palabra in busca.split():
    def orden(clase):
      blanco = [clase['nombre'].lower(),
                clase['codigo'].lower() + clase['curso'],
                clase['tipo'].lower(),
                clase['departamento'].lower()]
      for i, param in enumerate(blanco):
        if palabra in param:
          ind, pal = min([ (ind, pal)
                           for ind, pal in enumerate(param.split())
                           if palabra in pal ])
          return i, pal.find(palabra), ind
      return None

    if palabra != '-':
      clases = sorted((c for c in clases if orden(c)), key=orden)

  for clase in clases: del clase['_id']
  return { 'clases': clases }

def horarios(periodo, args):
  pagina = webscrape('https://guayacan.uninorte.edu.co/4PL1CACI0N35/registro/resultado_curso1.php', {
      'valida':'OK',
      'curso':args['curso'],
      'mat2':args['codigo'],
      'datos_periodo':periodo,
      'datos_nivel':args['nivel']
  })
  if not pagina: return {}

  resultados = pagina.xpath('//div[contains(@class, "div")]')
  if resultados:
    grupos = []
    profesores = []
    dias = dict(M='Lunes', T='Martes', W='Miércoles', R='Jueves', F='Viernes', S='Sábado', U='Domingo')
    for resultado in resultados:
      data = resultado.xpath('p/text()')
      verifica = data[0].strip()
      if (verifica == 'No existe asignatura con ese código.'):
          return {}
      grupo = {
          'grupo': int(data[2].strip()),
          'nrc': data[3].strip(),
          'matriculados': int(data[4].strip()),
          'disponibles': int(data[5].strip()),
          'profesor': []
      }
      sesiones = []
      for item in resultado.xpath('div/div/div/table/tr')[1:]:
        data = item.xpath('td/text()')
        if (len(data) == 6):
          for dia in data[2]:
            horas = [int(militar[:2]) for militar in data[3].split(' - ')]
            horas = set(h for h in range(horas[0], horas[1]))

            profesor = data[5].split(' - ')
            profesor = profesor[1].split(' ') + profesor[0].split(' ')
            profesor = ' '.join(p.capitalize() for p in profesor).replace('?', 'ñ')
            if profesor not in profesores: profesores.append(profesor)
            if profesor not in grupo['profesor']: grupo['profesor'].append(profesor)

            sesion = next((s for s in sesiones
                            if s['dia']==dias[dia] and horas.intersection(s['horas'])
                          ), None)
            if sesion:
              if data[4] not in sesion['lugar']:
                sesion['lugar'].append(data[4])
              for h in horas.difference(sesion['horas']):
                sesion['horas'].append(h)
            else:
              sesiones.append({
                'dia': dias[dia],
                'horas': list(horas),
                'lugar': [data[4]]
              })
        else:
          profesor = data[-1].split(' - ')
          profesor = profesor[1].split(' ') + profesor[0].split(' ')
          profesor = ' '.join(p.capitalize() for p in profesor).replace('?', 'ñ')
          if profesor not in profesores: profesores.append(profesor)
          if profesor not in grupo['profesor']: grupo['profesor'].append(profesor)

          sesiones.append({
            'dia': None,
            'horas': [],
            'lugar': [data[-2]]
          })
      grupo['sesiones'] = sesiones
      grupos.append(grupo)
    return {
      'grupos':grupos,
      'profesores':profesores
    }
  else:
    return {}
