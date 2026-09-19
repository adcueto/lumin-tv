' Arnes fuera del dispositivo para la ESCENA (MainScene.brs): comandos que
' cambian el flujo de reproduccion. Igual que planificacion.brs, ejecuta el
' codigo real del componente con el interprete brs y sustituye solo los nodos
' de SceneGraph por dobles (AA con los mismos campos) y el sistema de archivos.
' No se llama a init(): los nodos se inyectan en m. Lo que NO cubre: el nodo
' de video real, los observadores de campo y el reloj del equipo (F22-F24).
'
' Comprobado aqui (B5A-QA-02): "recargar" reinicia la reproduccion en el acto,
' con la lista que la escena ya tiene, sin esperar una respuesta del servidor;
' por eso da igual que la respuesta siguiente sea identica, distinta o no llegue.

sub main()
    m.comprobaciones = 0
    m.fallos = 0

    prueba_recargar_con_respuesta_identica()
    prueba_recargar_con_respuesta_distinta()
    prueba_recargar_sin_internet()
    prueba_recargar_sin_lista_alguna()
    prueba_recargar_no_reejecuta_comandos()

    print "RESUMEN: " + m.comprobaciones.ToStr() + " comprobaciones, " + m.fallos.ToStr() + " fallos"
end sub

' ---------------------------------------------------------------- dobles

function nodo() as object
    return {visible: false, control: "", state: "", text: "", uri: "", loadStatus: "", content: invalid,
            contentIsPlaylist: false, loop: false, mute: false, contentIndex: -1, duration: 0}
end function

sub preparar()
    m.fs = {archivos: {}, Exists: function(r as string) as boolean
        return m.archivos.DoesExist(r)
    end function, Delete: function(r as string) as boolean
        m.archivos.Delete(r)
        return true
    end function}
    m.video = nodo()
    m.foto = nodo()
    m.fotoB = nodo()
    m.fotoVisible = m.foto
    m.fotoBuffer = m.fotoB
    m.fotoPendiente = invalid
    m.estado = nodo()
    m.ayuda = nodo()
    m.codigoLbl = nodo()
    m.respaldo = nodo()
    m.detalle = nodo()
    m.indicador = nodo()
    m.capaEstado = nodo()
    m.timerFoto = nodo()
    m.timerBuffer = nodo()
    m.timerReintento = nodo()
    m.timerRespaldo = nodo()
    m.timerArranqueRespaldo = nodo()
    m.timerArranque = nodo()
    m.timerTurno = nodo()
    m.cacheTask = {vaciar: 0, reconectado: 0, deseados: invalid}
    m.task = {playlistJson: "", conectado: true, desdeCache: false, ultimaSincronizacion: "12:00",
              consultarAhora: 0, estado: invalid, serverUrl: "http://s"}
    ' m.top: cualquier findNode devuelve un doble; el cintillo y la orientacion
    ' no son objeto de este arnes y sus claves se dejan ya "aplicadas"
    m.top = {nodos: {}, findNode: function(id as string) as object
        if not m.nodos.DoesExist(id) then m.nodos[id] = nodo()
        return m.nodos[id]
    end function}
    m.barraClave = "|horario|false|false|130"
    m.fotoClave = "horario|false"
    m.textosClave = "horario|false"
    m.ancho = 1080
    m.alto = 1920
    m.sinRegistro = true

    m.enRespaldo = false
    m.esperaRespaldo = 10
    m.fallosSeguidos = 0
    m.fallosPorUrl = {}
    m.bloqueadasHasta = {}
    m.cacheInservibleVideo = 0
    m.desconectadoDesde = ""
    m.revisarComandoViejo = false
    m.recibioPlaylist = false
    m.urlsEnVideo = []
    m.rutasEnVideo = []
    m.ultimosDatos = invalid
    m.ultimaReconciliacion = 0
    m.cachePedidaEnVivo = false
    m.estadoTv = {r: "", c: 0, k: false, e: "", et: 0}
    m.playlistActual = ""
    m.segmentos = []
    m.indice = 0
    m.ultimoComando = -1
    m.fotoRapida = false
    m.pendienteActivo = false
    m.ultimoTurno = -1
end sub

function lista(nombres as object, n = 1 as integer) as object
    vs = []
    for each nom in nombres
        tipo = "video"
        if Right(nom, 4) = ".jpg" then tipo = "imagen"
        vs.Push({url: "http://s/v/" + nom, tipo: tipo, duracion: 10, title: nom})
    end for
    return {videos: vs, mensaje: "", cintillo: false, velocidad: 1, comando: {n: n, accion: "recargar"}, turno: {n: 0}}
end function

' Simula la llegada de una respuesta del servidor (lo que hace PlaylistTask).
' Si el JSON es identico al anterior, el campo string NO notifica: no se llama
' a onPlaylistJson. Es exactamente el comportamiento de SceneGraph que senalo
' Codex, reproducido aqui a proposito.
function llegaRespuesta(datos as object) as boolean
    j = FormatJson(datos)
    if j = m.task.playlistJson then return false
    m.task.playlistJson = j
    onPlaylistJson()
    return true
end function

' El reproductor "termina" lo que tenia: simula el evento finished del video
sub videoTermina()
    m.video.state = "finished"
    onVideoState()
end sub

function reproduciendoAhora() as string
    return m.estadoTv.r
end function

sub comprobar(c as boolean, texto as string)
    m.comprobaciones = m.comprobaciones + 1
    if c
        print "  ok    " + texto
    else
        m.fallos = m.fallos + 1
        print "  FALLA " + texto
    end if
end sub

sub titulo(t as string)
    print ""
    print "== " + t
end sub

' ------------------------------------------------------------------ pruebas

sub prueba_recargar_con_respuesta_identica()
    titulo("B5A-QA-02 recargar con respuesta identica: la reproduccion arranca sin esperar")
    preparar()
    d = lista(["a.mp4", "b.mp4", "c.jpg"], 1)
    comprobar(llegaRespuesta(d), "primera lista aplicada")
    videoTermina()   ' avanza a la foto c.jpg
    comprobar(reproduciendoAhora() = "c.jpg", "estaba en el tercer elemento; fue " + reproduciendoAhora())
    m.bloqueadasHasta["http://s/v/b.mp4"] = 9999999999
    consultasAntes = m.task.consultarAhora

    ' llega el comando recargar (n=2) en un latido con la MISMA lista
    d2 = lista(["a.mp4", "b.mp4", "c.jpg"], 2)
    comprobar(llegaRespuesta(d2), "latido con comando n=2")
    comprobar(m.video.control = "play", "el video se puso a reproducir en el acto; control=" + m.video.control)
    comprobar(reproduciendoAhora() = "a.mp4", "desde el primer elemento; fue " + reproduciendoAhora())
    comprobar(m.bloqueadasHasta.Count() = 0, "bloqueos olvidados")
    comprobar(m.task.consultarAhora = consultasAntes + 1, "se pidio un refresco al servidor")
    comprobar(m.segmentos.Count() = 2, "segmentos reconstruidos (videos encadenados + foto)")

    ' el refresco vuelve IDENTICO: el campo no notifica y NO hace falta
    comprobar(not llegaRespuesta(d2), "respuesta identica: sin evento (como en SceneGraph)")
    comprobar(m.video.control = "play" and reproduciendoAhora() = "a.mp4", "y la reproduccion sigue donde arranco")
end sub

sub prueba_recargar_con_respuesta_distinta()
    titulo("recargar y despues una lista distinta: se reconstruye una sola vez mas")
    preparar()
    llegaRespuesta(lista(["a.mp4"], 1))
    llegaRespuesta(lista(["a.mp4"], 2))          ' recargar
    comprobar(reproduciendoAhora() = "a.mp4", "reinicio inmediato")
    comprobar(llegaRespuesta(lista(["x.jpg", "a.mp4"], 2)), "lista distinta si notifica")
    comprobar(reproduciendoAhora() = "x.jpg", "y se aplica por el camino normal; fue " + reproduciendoAhora())
end sub

sub prueba_recargar_sin_internet()
    titulo("recargar justo antes de perder la red: reproduce lo que tiene, sin lamina")
    preparar()
    llegaRespuesta(lista(["a.mp4", "b.jpg"], 1))
    llegaRespuesta(lista(["a.mp4", "b.jpg"], 2))  ' recargar
    m.task.conectado = false                       ' la consulta de refresco falla
    onConectado()
    comprobar(reproduciendoAhora() = "a.mp4", "sigue reproduciendo desde el primer elemento")
    comprobar(not m.enRespaldo, "no aparece la lamina: hay lista y contenido")
    comprobar(m.estadoTv.k = true, "el estado reporta 'sin red' para el proximo latido")
end sub

sub prueba_recargar_sin_lista_alguna()
    titulo("recargar sin haber recibido nunca una lista: lamina, no pantalla negra")
    preparar()
    recargar()
    comprobar(m.enRespaldo and m.respaldo.visible, "lamina visible")
    comprobar(m.task.consultarAhora = 1, "y se pide la lista")
    ' cuando por fin llega, se aplica
    llegaRespuesta(lista(["a.mp4"], 1))
    comprobar(reproduciendoAhora() = "a.mp4", "al llegar la primera lista se reproduce")
end sub

sub prueba_recargar_no_reejecuta_comandos()
    titulo("recargar no vuelve a ejecutar el comando que lo provoco")
    preparar()
    llegaRespuesta(lista(["a.mp4", "b.mp4"], 1))
    videoTermina()
    llegaRespuesta(lista(["a.mp4", "b.mp4"], 2))   ' recargar, n=2
    consultas = m.task.consultarAhora
    ' el refresco trae la misma lista y el mismo comando n=2: si notificara, no debe recargar otra vez
    m.task.playlistJson = ""                        ' forzar notificacion aunque sea identico
    llegaRespuesta(lista(["a.mp4", "b.mp4"], 2))
    comprobar(m.task.consultarAhora = consultas, "mismo n: no se recarga de nuevo; consultas=" + m.task.consultarAhora.ToStr())
    comprobar(m.ultimoComando = 2, "ultimo comando consumido = 2")
end sub
