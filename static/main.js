var clases = []
var horarios = [{horas:[]}]
var horarios_no_bloqueados = []

$('#add').search({
    apiSettings: {
        url: '/api/'+periodo+'/buscar?busca={query}',
        onResponse: function(res) {
            $.each(res.clases, function(index, clase) {
                clase.title = clase.codigo + " " + clase.curso + " - " + clase.nombre
                clase.description = niveles[clase.nivel] + " - " + clase.departamento
            });
            return res;
        }
    },
    minCharacters: 1,
    fields: {
        results: 'clases'
    },
    onSelect: function(clase, response) {
        $('#add').addClass('loading')
        $('#add').addClass('disabled')
        var div = document.createElement('span')
        div.innerHTML = '<div class="ui segment">\
                         <div class="ui placeholder">\
                         <div class="paragraph">\
                         <div class="line"></div>\
                         <div class="line"></div>\
                         </div></div></div>'
        $('#cursos').prepend(div)
        $.ajax('/api/'+periodo+'/horarios', {
            data: {
                periodo: periodo,
                nivel: clase.nivel,
                codigo: clase.codigo,
                curso: clase.curso
            }
        }).done(function(data) {
            clase.grupos = data.grupos
            clase.profesores = data.profesores
            if ($('#'+clase._id).length) {
                clases = clases.filter(c => c._id !== clase._id)
                $('#'+clase._id).parent().remove()
            }
            add(clase, div)
        }).fail(function(data) {
            div.parentElement.removeChild(div)
            $('body .tab.active').prepend('<div class="ui error message">\
                                <i class="close icon"></i>\
                                <p>Hubo un error al buscar los horarios de esta clase.</p>\
                                </div>')
            $('.message .close').click(function() {
                $(this).closest('.message').transition('fade')
            })
        }).always(function(data) {
            $('#add').removeClass('loading')
            $('#add').removeClass('disabled')
            $('#add .input input').val('')
        })
    }
})

function add(clase, div) {
    clases.push(clase)
    div.innerHTML = '<div class="title"><i class="dropdown icon"></i>\
                     '+clase.nombre+'</div>\
                     <div class="content" id='+clase._id+'>\
                         <div class="ui large image label">'+clase.codigo+'\
                         <div class="detail">'+clase.curso+'</div></div>\
                         <div class="ui large label">'+niveles[clase.nivel]+'</div>\
                         <a class="ui large red label quitar">Quitar</a>\
                         <div class="ui secondary pointing menu">\
                         <a class="item active" data-tab="grupos">Ver grupos</a>\
                         <a class="item" data-tab="profesores">Filtrar profesores</a></div>\
                         <div class="ui tab active accordion" data-tab="grupos"></div>\
                         <div class="ui tab" data-tab="profesores">\
                         <table class="ui celled unstackable table"><tbody></tbody></table></div>\
                     </div>'
    $('#'+clase._id+' .secondary.pointing.menu .item').tab()
    for (var i in clase.grupos) {
        var grupo = clase.grupos[i]
        grupo.bloqprof = false
        grupo.bloqhora = false
        var items = ''
        for (var j in grupo.horarios) {
            var horario = grupo.horarios[j]
            items += '<div class="ui segment">\
                        <div>'+horario.dia+' - '+horario.horas[0]+':30</div>\
                        <div><b>Ubicación:</b> '+horario.lugar+'</div>\
                        <div><b>Profesor:</b> '+horario.profesor+'</div>\
                     </div>'
        }
        $('#'+clase._id+' .accordion').append(
        '<div class="title" id="'+grupo.nrc+'">NRC '+grupo.nrc+'\
         <i class="dropdown icon"></i></div>\
         <div class="ui content">\
            <div><b>Matriculados:</b> '+grupo.matriculados+' - \
            <b>Cupos disponibles:</b> '+grupo.disponibles+'</div>\
            <div class="ui segments">'+items+'</div>\
         </div>')

        if (grupo.disponibles < 1)
            $('#'+clase._id+' #'+grupo.nrc).prepend('<div class="ui horizontal basic sincupo red label">Sin cupos</div>')
    }
    clase.profesores_bloqueados = []
    for (var i in clase.profesores) {
        $('#'+clase._id+' .tab table tbody').append('<tr>\
            <td class="collapsing selectable">\
            <a><i class="fitted eye slash outline icon"></i></a>\
            </td><td>'+clase.profesores[i]+'</td></tr>')
    }
    $('#'+clase._id+' td.selectable').click(function(e) {
        $(this).toggleClass('active')
        $('.bloqprof').remove()
        loop: for (var i in clase.grupos) {
            var grupo = clase.grupos[i]
            grupo.bloqprof = false
            for (var j in grupo.horarios) {
                for (var k in grupo.horarios[j].profesor) {
                    var profesor = grupo.horarios[j].profesor[k]
                    if ($('#'+clase._id+' td:contains("'+profesor+'")').prev().hasClass('active')) {
                        grupo.bloqprof = true
                        $('#'+clase._id+' #'+grupo.nrc).prepend('<div class="ui horizontal basic red bloqprof label">Profesor bloqueado</div>')
                        continue loop
                    }
                }
            }
        }
        horarios_no_bloqueados = no_bloqueados()
        $('#info').html('Se hallaron <b>'+horarios.length+'</b> horarios posibles,\
                     de los cuales <b>'+horarios_no_bloqueados.length+'</b> cumplen con los filtros.')
        seleccionar_horario(1)
    })
    meter_a_horario(clase)
    horarios_no_bloqueados = no_bloqueados()
    $('#info').html('Se hallaron <b>'+horarios.length+'</b> horarios posibles,\
                 de los cuales <b>'+horarios_no_bloqueados.length+'</b> cumplen con los filtros.')
    seleccionar_horario(1)

    $('#'+clase._id+' .quitar').click(function(e) {
        remove(clase)
    })
}

function remove(eliminada) {
    $('#'+eliminada._id).prev().remove()
    $('#'+eliminada._id).remove()
    clases = clases.filter(c => c._id !== eliminada._id)
    horarios = [{horas:[]}]
    for (var i in clases)
        meter_a_horario(clases[i])
    horarios_no_bloqueados = no_bloqueados()
    $('#info').html('Se hallaron <b>'+horarios.length+'</b> horarios posibles,\
                 de los cuales <b>'+horarios_no_bloqueados.length+'</b> cumplen con los filtros.')
    seleccionar_horario(1)
}

function meter_a_horario(clase) {
    var horarios_temp = []
    while(horarios.length) {
        var horario_original = horarios.pop()
        loop: for (var i in clase.grupos) {
            var horario = JSON.parse(JSON.stringify(horario_original))
            var grupo = clase.grupos[i]
            for (var j in grupo.horarios) {
                for (var k in grupo.horarios[j].horas) {
                    var hora = grupo.horarios[j]
                    if (horario.horas.some(h => h.dia === hora.dia && h.hora === hora.horas[k])) continue loop
                    horario.horas.push({
                        dia: hora.dia,
                        hora: hora.horas[k],
                        clase: clase._id,
                        codigo: clase.codigo + clase.curso
                    })
                }
            }
            horario[clase._id] = {
                nrc: grupo.nrc,
                codigo: clase.codigo + ' ' + clase.curso,
                nombre: clase.nombre
            }
            horarios_temp.push(horario)
        }
    }
    horarios = horarios_temp
}

function seleccionar_horario(num) {
    $('.actual').remove()
    $('.hora:not(.bloqueada)').html('')
    $('#nrcs .fijar:not(.active)').parent().remove()
    $('#num').html(num)

    var horario = horarios_no_bloqueados[num-1]
    for (var id in horario) {
        if (id === 'horas')
            for (var i in horario[id]) {
                h = horario[id][i]
                $('#'+h.dia+h.hora).html(h.codigo)
            }
        else if (! $('.fijado').parents('#'+id).length) {
            $('#'+id+' #'+horario[id].nrc).prepend('<div class="ui horizontal basic green label actual">En el horario actual</div>')
            $('#nrcs').append('<tr data-id='+id+'>\
                <td class="collapsing selectable fijar">\
                <a><i class="fitted thumbtack icon"></i></a></td>\
                <td><b>'+horario[id].codigo+':</b>\
                '+horario[id].nombre+' - NRC '+horario[id].nrc+'</td>\
                <td class="collapsing selectable quitar">\
                <a><i class="fitted close icon"></i></a></td>\
            </tr>')

            if ($('#'+id+' #'+horario[id].nrc+' .sincupo').length)
                $('#nrcs tr[data-id='+id+'] td:nth-child(2)').append(' (Sin cupo)')
        }
    }
    $('#nrcs .quitar').click(function(e) {
        var id = $(this).parent().attr('data-id')
        $(this).parent().find('.fijar').removeClass('active')
        var clase = clases.find(c => c._id === id)
        remove(clase)
    })
    $('.fijar:not(.active)').click(function(e) {
        var id = $(this).parent().attr('data-id')
        $(this).toggleClass('active')

        if ($('#'+id+' .actual').length)
            $('#'+id+' .actual')
                .addClass('fijado')
                .removeClass('actual')
                .html('Fijado en el horario')
        else
            $('#'+id+' .fijado')
                .addClass('actual')
                .removeClass('fijado')
                .html('En el horario actual')
        horarios_no_bloqueados = no_bloqueados()
        $('#info').html('Se hallaron <b>'+horarios.length+'</b> horarios posibles,\
                    de los cuales <b>'+horarios_no_bloqueados.length+'</b> cumplen con los filtros.')
        seleccionar_horario(1)
    })
}

function no_bloqueados() {
    var nrcs_fijados = $('.fijado').parent().map(function(){return this.id})
    var clases_fijadas = $('.fijado').closest('.content').map(function(){return this.id})
    var fijados = {}
    for (var i in nrcs_fijados)
        fijados[clases_fijadas[i]] = nrcs_fijados[i]

    var solo_con_cupo = ! $('#sincupo').is(':checked')
    var resultado = []
    loop: for (var i in horarios) {
        var horario = horarios[i]
        for (var id in horario) if (id !== 'horas') {
            var clase = clases.find(c => c._id === id)
            var grupo = clase.grupos.find(g => g.nrc === horario[id].nrc)
            if (solo_con_cupo && grupo.disponibles < 1) continue loop
            if (grupo.bloqhora) continue loop
            if (grupo.bloqprof) continue loop
            if (id in fijados) if (fijados[id] !== grupo.nrc) continue loop
        }
        resultado.push(horario)
    }
    return resultado
}

$('#mas').click(function(e) {
    var num = parseInt($('#num').text())
    if (num === horarios_no_bloqueados.length)
        num = 1
    else
        num++
    seleccionar_horario(num)
})

$('#menos').click(function(e) {
    var num = parseInt($('#num').text())
    if (num === 1)
        num = horarios_no_bloqueados.length
    else
        num--
    $('#num').html(num)
    seleccionar_horario(num)
})

$('#sincupo').change(function(e){
    horarios_no_bloqueados = no_bloqueados()
    $('#info').html('Se hallaron <b>'+horarios.length+'</b> horarios posibles,\
                 de los cuales <b>'+horarios_no_bloqueados.length+'</b> cumplen con los filtros.')
    seleccionar_horario(1)
})

var bloqueando = false, desbloqueando = false
$('.hora')
    .mousedown(function(e) {
        $(this).toggleClass('bloqueada')
        if ($(this).hasClass('bloqueada')) {
            bloqueando = true
            $('.hora.bloqueada').html('Bloqueada')
        } else {
            desbloqueando = true
            $(this).html('')
        }
        return false
    })
    .mouseover(function(e) {
        if (bloqueando) {
            $(this).addClass('bloqueada')
            $(this).html('Bloqueada')
        } else if (desbloqueando) {
            $(this).removeClass('bloqueada')
            $(this).html('')
        }
    })

$(document).mouseup(function () {
    if (bloqueando || desbloqueando) {
        $('.bloqhora').remove()
        for (var i in clases) {
            var clase = clases[i]
            loop: for (var j in clase.grupos) {
                var grupo = clase.grupos[j]
                grupo.bloqhora = false
                for (var k in grupo.horarios) {
                    var horario = grupo.horarios[k]
                    for (var h in horario.horas) {
                        if ($('#'+horario.dia+horario.horas[h]).hasClass('bloqueada')) {
                            grupo.bloqhora = true
                            $('#'+clase._id+' #'+grupo.nrc).prepend('<div class="ui horizontal basic red bloqhora label">Hora bloqueada</div>')
                            continue loop
                        }
                    }
                }
            }
        }
        horarios_no_bloqueados = no_bloqueados()
        $('#info').html('Se hallaron <b>'+horarios.length+'</b> horarios posibles,\
                     de los cuales <b>'+horarios_no_bloqueados.length+'</b> cumplen con los filtros.')
        seleccionar_horario(1)

        $('.hora.bloqueada').html('Desbloquear')
        if (desbloqueando) desbloqueando = false
        else bloqueando = false
    }

})

$('.pointing.menu .item').tab()
$('.ui.checkbox').checkbox()
$('.ui.accordion').accordion({
    animateChildren: false
})
