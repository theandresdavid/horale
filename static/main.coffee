clases = []
horarios = [[]]
bloqueos = cupos: true, horas:[], grupos:[]
horarios_no_bloqueados = [{}]

$('.dropdown').dropdown()
$('.checkbox').checkbox('check')

mensaje_en_buscador = (texto) ->
  $('#buscar').append('<div class="ui message">
    <i class="close icon"></i><p>' + texto + '</p>
  </div>')
  $('#buscar .message .close').click ->
    $(this).closest('.message').transition('fade')
    return
  return

$('#actualizar').click ->
  codigo = prompt '¡Actualizamos nuestra base de datos cuando tú lo pides! Sólo envíanos el código de materia (IGL, MAT, etc.) y en minutos podrás añadir tu clase.', ''
  if codigo isnt null
    $('#actualizar').append('<div style="margin-left:.5em" class="ui tiny active inline loader"></div>')
    $('#buscar .message').remove()
    $.ajax
      type: 'POST',
      url: '/api/' + periodo + '/actualizar/' + codigo
    .done (data) ->
      if 'cantidad' of data
        mensaje_en_buscador 'Se encontraron ' + data.cantidad + ' clases con el código ' + data['codigo'] + '.'
      else
        mensaje_en_buscador 'No se encontraron clases con el código ' + data['codigo'] + '.'
      return
    .fail (data) ->
      mensaje_en_buscador 'Hubo un error de conexión.'
      return
    .always (data) ->
      $('#actualizar .loader').remove()
      return
    return

$('#buscar .ui.search').search(
  apiSettings:
    url: '/api/' + periodo + '/buscar/{query}'
    onResponse: (res) ->
      for clase in res.clases
        clase.title = clase.codigo + " " + clase.curso + " - " + clase.nombre
        clase.description = clase.tipo + " - " + clase.departamento
      res
  fields:
    results: 'clases'
  onSelect: (clase, res) ->
    $('#buscar .ui.search').addClass('loading disabled')
    $('#buscar .message').remove()
    $.ajax
      url: '/api/' + periodo + '/horarios'
      data: clase
    .done (data) ->
      if data.grupos?
        clase.grupos = data.grupos
        clase.profesores = data.profesores
        clase.id = clase.nivel + '-' + clase.codigo + '-' + clase.curso
        if $('#' + clase.id).length
          mensaje_en_buscador 'Ya añadiste la clase ' + clase.title + '.'
        else
          añadir clase
      else
        mensaje_en_buscador 'Los horarios de la clase ' + clase.title + ' no fueron encontrados.'
      return
    .fail (data) ->
      mensaje_en_buscador 'Hubo un error de conexión.'
      return
    .always (data) ->
      $('#buscar .ui.search').removeClass('loading disabled')
      $('#buscar .ui.search .input input').val('')
      return
    return
)

añadir = (clase) ->
  clases.push clase
  horarios = meter_a_horario clase
  horarios_no_bloqueados = no_bloqueados()
  $('#clases').prepend('<div id="' + clase.id + '" class="item">
    <div class="content">
      <a class="ui eliminar right floated label"><i class="fitted delete icon"></i></a>
      <div class="ui small header">' + clase.title + '</div>
      <div class="meta">' + clase.description + '</div>
      <div class="description"></div>
    </div></div>')
  $('#' + clase.id + ' .eliminar').click ->
    quitar clase
    return

  seleccionar_horario 1
  return

horas_de_grupo = (grupo) ->
  horas = []
  for sesion in grupo.sesiones
    for hora in sesion.horas
      horas.push {dia: sesion.dia, hora:hora.toString()}
  horas

grupo_en_horario = (horario, clase) ->
  clase_grupo = horario.find (c) -> c.clase_id is clase.id
  grupo = clase.grupos.find (g) -> g.grupo is clase_grupo.grupo
  grupo

meter_a_horario = (clase) ->
  nuevos_horarios = []
  while horarios.length
    horario_original = horarios.pop()
    for grupo in clase.grupos
      horario = JSON.parse(JSON.stringify(horario_original))
      conflicto_de_horas = false
      for hora in horas_de_grupo grupo
        for clase_buscada in clases when clase_buscada isnt clase
          for h in horas_de_grupo grupo_en_horario horario, clase_buscada
            if h.hora is hora.hora and h.dia is hora.dia
              conflicto_de_horas = true
              break
          break if conflicto_de_horas
        break if conflicto_de_horas
      continue if conflicto_de_horas
      horario.push {clase_id: clase.id, grupo: grupo.grupo}
      nuevos_horarios.push horario
  nuevos_horarios

seleccionar_horario = (num) ->
  $('.hora:not(.active)').html('')
  $('#num').html(num)
  horario = horarios_no_bloqueados[num-1]
  for clase in clases
    grupo = grupo_en_horario horario, clase
    $('#' + clase.id + ' .description').html('<p class="info"></p>')
    $('#' + clase.id + ' .info').append('<b>NRC</b> ' + grupo.nrc)
    if grupo.disponibles is 1
      $('#' + clase.id + ' .info').append(' - <b>1</b> cupo disponible')
    else
      $('#' + clase.id + ' .info').append(' - <b>' + grupo.disponibles + '</b> cupos disponibles')
    $('#' + clase.id + ' .info').append('<div class="profesor">' + grupo.profesor + '</div>')

    $('#' + clase.id + ' .description').append('<p class="horario"></p>')
    for sesion in grupo.sesiones
      [prim, ..., ult] = sesion.horas
      hora = prim + ':30 - ' + (ult+1) + ':30'
      $('#' + clase.id + ' .horario').append('<div><b>' + sesion.dia + ':</b> ' + hora + '</div>')
    for hora in horas_de_grupo grupo
      $('#' + hora.dia + '-' + hora.hora).html(clase.codigo + ' ' + clase.curso)
  return

no_bloqueados = () ->
  resultados = []
  for horario in horarios
    bloqueado = false
    for clase in clases
      grupo = grupo_en_horario horario, clase
      if bloqueos.grupos.some (g) -> g.clase_id is clase.id and g.grupo is grupo.grupo
        bloqueado = true
      else if bloqueos.cupos and grupo.disponibles < 1
        bloqueado = true
      else
        for hora in horas_de_grupo grupo
          for h in bloqueos.horas
            if h.hora is hora.hora and h.dia is hora.dia
              bloqueado = true
              break
          break if bloqueado
      break if bloqueado
    resultados.push horario unless bloqueado

  if horarios.length == 1
    if resultados.length == 1
      $('#info').html('Se halló <b>1</b> horario posible que cumple con los filtros.')
    else
      $('#info').html('Se halló <b>1</b> horario posible que no cumple con los filtros.')
  else
    if resultados.length == 1
      $('#info').html('Se hallaron <b>' + horarios.length + '</b> horarios posibles,
            de los cuales <b>1</b> cumple con los filtros.')
    else
      $('#info').html('Se hallaron <b>' + horarios.length + '</b> horarios posibles,
            de los cuales <b>' + resultados.length + '</b> cumplen con los filtros.')
  resultados

quitar = (clase) ->
  $('#' + clase.id).remove()
  clases = clases.filter (c) -> c.id isnt clase.id
  horarios = [[]]
  horarios = meter_a_horario clase for clase in clases
  horarios_no_bloqueados = no_bloqueados()
  seleccionar_horario 1
  return

$('#mas').click ->
  num = (parseInt $('#num').text()) + 1
  num = 1 if num is horarios_no_bloqueados.length + 1
  seleccionar_horario num
  return

$('#menos').click ->
  num = (parseInt $('#num').text()) - 1
  num = horarios_no_bloqueados.length if num is 0
  seleccionar_horario num
  return

bloqueando = false
desbloqueando = false
texto = ''
$('.hora')
  .mousedown ->
    $(this).toggleClass('active')
    if $(this).hasClass('active')
      bloqueando = true
      $('.hora.active').html('Bloqueada')
    else
      desbloqueando = true
      $(this).html('')
    false
  .mouseover ->
    if bloqueando
      $(this).addClass('active')
      $(this).html('Bloqueada')
    else if desbloqueando
      $(this).removeClass('active')
      $(this).html('')
    else
      if not $(this).hasClass('active')
        texto = $(this).text()
        $(this).html('Bloquear')
    return
  .mouseleave ->
    if $(this).text() is 'Bloquear'
      $(this).html(texto)
    return
$(document).mouseup ->
  if bloqueando or desbloqueando
    bloqueos.horas = []
    for celda in $('.hora.active')
      data = celda.id.split('-')
      bloqueos.horas.push {dia: data[0], hora: data[1] }
    horarios_no_bloqueados = no_bloqueados()
    seleccionar_horario 1

    $('.hora.active').html('Desbloquear')
    desbloqueando = false
    bloqueando = false
  return

$('#imprimir').click ->
  $('main').css(padding: '2em')
  window.print()
  $('main').css(padding: '0')
  return
