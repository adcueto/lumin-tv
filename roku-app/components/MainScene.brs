' MainScene — LUMIN TV
'
' B1 (continuidad y recuperacion) anade, sin tocar el contrato con el servidor:
'   - vigilante del estado "buffering": ya no se queda cargando sin fin;
'   - contador de fallos con histeresis: tras una vuelta completa sin nada
'     reproducible se muestra la lamina de respaldo y se reintenta cada vez
'     mas despacio (10, 20, 40, 60 s), nunca en bucle apretado;
'   - archivos danados: se apartan 10 minutos sin detener el resto de la lista;
'   - cache en cachefs: lo que ya se reprodujo sirve si se cae la red;
'   - turnos vencidos: no se anuncian al recuperar la conexion;
'   - comandos "reproducir" emitidos durante una desconexion no se ejecutan
'     tarde; los comandos de estado (pausa, silencio) si se aplican;
'   - la clienta nunca ve mensajes tecnicos: solo la lamina y un punto ambar.

sub init()
    m.video = m.top.findNode("video")
    if m.video.hasField("disableScreenSaver") then m.video.disableScreenSaver = true
    m.foto = m.top.findNode("foto")
    m.fotoB = m.top.findNode("fotoB")
    m.fotoVisible = m.foto
    m.fotoBuffer = m.fotoB
    m.fotoPendiente = invalid
    m.foto.observeField("loadStatus", "onFotoCargada")
    m.fotoB.observeField("loadStatus", "onFotoCargada")
    m.estado = m.top.findNode("estado")
    m.ayuda = m.top.findNode("ayuda")
    m.codigoLbl = m.top.findNode("codigo")
    m.pendienteActivo = false

    ' --- B1: capa de continuidad ---
    m.capaEstado = m.top.findNode("capaEstado")
    m.respaldo = m.top.findNode("respaldo")
    m.detalle = m.top.findNode("detalle")
    m.indicador = m.top.findNode("indicador")
    m.fs = CreateObject("roFileSystem")
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

    m.turnoGrp = m.top.findNode("turno")
    m.tPanel = m.top.findNode("tPanel")
    m.tAnimIn = m.top.findNode("tAnimIn")
    m.tAnimOut = m.top.findNode("tAnimOut")
    m.tInterpIn = m.top.findNode("tInterpIn")
    m.tInterpOut = m.top.findNode("tInterpOut")
    m.tAnimOut.observeField("state", "onTurnoOculto")
    m.ultimoTurno = -1
    m.turnoBlockH = 0
    m.timerTurno = createObject("roSGNode", "Timer")
    m.timerTurno.repeat = false
    m.timerTurno.observeField("fire", "onTurnoFin")

    m.playlistActual = ""
    m.barraClave = ""
    m.fotoClave = ""
    m.segmentos = []
    m.indice = 0
    m.ultimoComando = -1
    m.fotoRapida = false
    m.top.backgroundColor = "0x000000FF"
    m.top.backgroundUri = ""

    ' Adaptar al tamaño real de la interfaz (algunas TVs usan 1280x720)
    res = m.top.currentDesignResolution
    if res <> invalid and res.width <> invalid and res.width > 0
        ancho = res.width
        alto = res.height
    else
        ancho = 1920
        alto = 1080
    end if
    fondo = m.top.findNode("fondo")
    fondo.width = ancho
    fondo.height = alto
    m.video.width = ancho
    m.video.height = alto
    m.ancho = ancho
    m.alto = alto
    m.textosClave = ""
    m.estado.wrap = true
    ' De fábrica los textos se orientan para TV vertical (giro horario)
    orientarTextos(true, "horario")
    ' B1: orientar la capa de continuidad con lo ultimo que se supo de la TV,
    ' para que la lamina salga bien aunque arranque sin red.
    configurarFoto(orientacionGuardada())

    ' Tarea que maneja registro (URL guardada) y consulta el servidor
    m.task = createObject("roSGNode", "PlaylistTask")
    m.task.observeField("playlistJson", "onPlaylistJson")
    m.task.observeField("serverUrl", "onServerUrlLoaded")
    m.task.observeField("errorMsg", "onTaskError")
    m.task.observeField("conectado", "onConectado")
    m.task.control = "RUN"

    ' B1: tarea de cache, aparte para que una descarga nunca retrase el latido
    m.cacheTask = createObject("roSGNode", "CacheTask")
    m.cacheTask.observeField("listo", "onCacheListo")
    m.cacheTask.observeField("fallo", "onCacheFallo")
    m.cacheTask.control = "RUN"

    m.video.observeField("state", "onVideoState")

    ' Temporizador para la duración de cada foto
    m.timerFoto = createObject("roSGNode", "Timer")
    m.timerFoto.repeat = false
    m.timerFoto.observeField("fire", "onFotoTimer")

    ' Temporizador para reintentar/saltar tras un error
    m.timerReintento = createObject("roSGNode", "Timer")
    m.timerReintento.duration = 5
    m.timerReintento.repeat = false
    m.timerReintento.observeField("fire", "onReintento")

    ' B1: vigilante de buffering. Si en 25 s el video no arranca ni avanza,
    ' se considera colgado y se pasa al siguiente.
    m.timerBuffer = createObject("roSGNode", "Timer")
    m.timerBuffer.duration = 25
    m.timerBuffer.repeat = false
    m.timerBuffer.observeField("fire", "onBufferColgado")

    ' B1: reintentos desde la lamina de respaldo, con espera creciente
    m.timerRespaldo = createObject("roSGNode", "Timer")
    m.timerRespaldo.repeat = false
    m.timerRespaldo.observeField("fire", "onReintentoRespaldo")

    ' B1: si en 15 s no llego ninguna lista, mostrar la lamina en vez de
    ' "Cargando configuración..." indefinido
    m.timerArranqueRespaldo = createObject("roSGNode", "Timer")
    m.timerArranqueRespaldo.duration = 15
    m.timerArranqueRespaldo.repeat = false
    m.timerArranqueRespaldo.observeField("fire", "onArranqueSinLista")
    m.timerArranqueRespaldo.control = "start"

    m.estado.text = "Cargando configuración..."
    m.top.setFocus(true)

    ' Red de seguridad: si en 4 s no cargó nada, pedir la URL de todos modos
    m.timerArranque = createObject("roSGNode", "Timer")
    m.timerArranque.duration = 4
    m.timerArranque.repeat = false
    m.timerArranque.observeField("fire", "onTimeoutArranque")
    m.timerArranque.control = "start"
end sub

sub onTimeoutArranque()
    if (m.task.serverUrl = invalid or m.task.serverUrl = "") and m.top.dialog = invalid
        mostrarDialogoUrl("")
    end if
end sub

sub onArranqueSinLista()
    if m.recibioPlaylist or m.pendienteActivo then return
    if m.task.serverUrl = invalid or m.task.serverUrl = "" then return
    ' Nunca se ha recibido una lista: puede ser red o una URL mal escrita.
    ' La pista para cambiarla va pequena, en la lamina, no en grande.
    mostrarRespaldo("sin respuesta del servidor  ·  presiona * para cambiar la URL")
end sub

' ---------- Configuración de URL ----------

sub onServerUrlLoaded()
    if m.timerArranque <> invalid then m.timerArranque.control = "stop"
    url = m.task.serverUrl
    if url = invalid or url = ""
        mostrarDialogoUrl("")
    else
        m.estado.text = "Conectando a " + url + " ..."
        m.ayuda.text = "Presiona * (opciones) para cambiar el servidor"
    end if
end sub

sub mostrarDialogoUrl(textoInicial as string)
    kb = createObject("roSGNode", "StandardKeyboardDialog")
    kb.title = "URL del servidor Lumin"
    kb.message = ["Ejemplo: https://tv.luminbelleza.com o http://192.168.1.50:8080"]
    kb.buttons = ["Guardar", "Cancelar"]
    if textoInicial <> ""
        kb.text = textoInicial
    else
        kb.text = "http"
    end if
    kb.observeField("buttonSelected", "onDialogoBoton")
    m.dialogoUrl = kb
    m.top.dialog = kb
end sub

sub onDialogoBoton()
    kb = m.dialogoUrl
    if kb.buttonSelected = 0
        url = kb.text.Trim()
        if url.Len() > 0 and Right(url, 1) = "/"
            url = Left(url, url.Len() - 1)
        end if
        if url <> "" and url <> "http"
            m.task.saveUrl = url
            m.estado.text = "Conectando a " + url + " ..."
            m.ayuda.text = "Presiona * (opciones) para cambiar el servidor"
        end if
    end if
    kb.close = true
end sub

' ---------- Playlist ----------

sub onPlaylistJson()
    jsonStr = m.task.playlistJson
    if jsonStr = invalid or jsonStr = "" then return

    datos = ParseJson(jsonStr)
    if datos = invalid then return

    desdeCache = (m.task.desdeCache = true)

    if datos.pendiente <> invalid and datos.pendiente = true
        if desdeCache then return
        modoPendiente(datos)
        return
    end if
    if m.pendienteActivo
        ' recien aprobada: limpiar la pantalla del codigo
        m.pendienteActivo = false
        m.codigoLbl.text = ""
        m.estado.text = ""
        m.playlistActual = ""
    end if

    if datos.videos = invalid then return
    m.recibioPlaylist = true
    m.timerArranqueRespaldo.control = "stop"

    actualizarBarra(datos)
    configurarFoto(datos)
    guardarOrientacion(datos)

    videosStr = FormatJson(datos.videos)
    cambioLista = (videosStr <> m.playlistActual)
    if cambioLista
        m.playlistActual = videosStr
        reconstruirSegmentos(datos)
    else if m.enRespaldo and m.segmentos.Count() > 0 and not desdeCache
        ' misma lista, pero volvio el servidor: intentar salir de la lamina ya
        salirDeRespaldoEIntentar()
    end if

    ' Reconciliar la cache con la lista deseada (B1-QA-02). No en cada latido:
    ' cuando cambia la lista, en la primera respuesta en vivo tras arrancar
    ' desde cache, y como maximo una vez por minuto. CacheTask solo descarga
    ' lo que falte, asi que reconciliar es barato.
    if not desdeCache
        m.ultimosDatos = datos
        ahora = ahoraSegundos()
        if cambioLista or not m.cachePedidaEnVivo or (ahora - m.ultimaReconciliacion) >= 60
            pedirCache(datos)
        end if
    end if

    ' Una lista servida desde la copia local no trae eventos nuevos:
    ' sus comandos y turnos ya se atendieron (o vencieron) en su momento.
    if desdeCache then return
    manejarComando(datos)
    manejarTurno(datos)
end sub

sub reconstruirSegmentos(datos as object)

    m.segmentos = []
    segVideo = invalid
    for each v in datos.videos
        tipo = "video"
        if v.tipo <> invalid then tipo = v.tipo
        if tipo = "imagen"
            if segVideo <> invalid
                m.segmentos.Push(segVideo)
                segVideo = invalid
            end if
            dur = 10
            if v.duracion <> invalid then dur = v.duracion
            m.segmentos.Push({tipo: "imagen", url: v.url, duracion: dur})
        else
            ' videos consecutivos se encadenan para que Roku precargue el siguiente
            if segVideo = invalid
                segVideo = {tipo: "videos", urls: [], mini: ""}
                if v.mini <> invalid then segVideo.mini = v.mini
            end if
            segVideo.urls.Push(v.url)
        end if
    end for
    if segVideo <> invalid then m.segmentos.Push(segVideo)

    m.timerFoto.control = "stop"
    m.fallosSeguidos = 0
    if m.segmentos.Count() = 0
        m.video.control = "stop"
        m.video.visible = false
        ocultarFotos()
        ' Sin contenido no es un fallo de red: lamina con aviso para quien atiende
        mostrarRespaldo("sin contenido asignado")
        return
    end if

    m.ayuda.text = ""
    if hayFotoEnPantalla() or m.video.state = "playing" or m.video.state = "paused"
        ' ya hay algo en pantalla: no ensuciar con mensajes
        m.estado.text = ""
    else if not m.enRespaldo
        ' arranque: mantener un mensaje hasta que aparezca el primer contenido
        m.estado.text = "Cargando contenido…"
    end if
    m.indice = 0
    reproducirSiguiente()
end sub

sub reproducirSiguiente()
    m.fotoRapida = false
    if m.segmentos.Count() = 0 then return
    if m.indice >= m.segmentos.Count() then m.indice = 0
    seg = m.segmentos[m.indice]
    m.indice = m.indice + 1

    if seg.tipo = "imagen"
        if estaBloqueada(seg.url)
            saltarBloqueada()
            return
        end if
        mostrarFoto(resolverUrl(seg.url), seg.duracion, false, false, seg.url)
    else
        m.timerFoto.control = "stop"
        ' la foto actual se queda visible hasta que el video empiece;
        ' si no hay foto, usar la miniatura del video como cortina
        if not hayFotoEnPantalla() and seg.mini <> invalid and seg.mini <> ""
            mostrarFoto(resolverUrl(seg.mini), 0, false, true, seg.mini)
        end if
        raiz = createObject("roSGNode", "ContentNode")
        m.urlsEnVideo = []
        m.rutasEnVideo = []
        for each u in seg.urls
            if not estaBloqueada(u)
                hijo = raiz.createChild("ContentNode")
                ruta = resolverUrlVideo(u)
                hijo.url = ruta
                hijo.streamFormat = "mp4"
                m.urlsEnVideo.Push(u)
                m.rutasEnVideo.Push(ruta)
            end if
        end for
        if m.urlsEnVideo.Count() = 0
            ' todo el bloque esta apartado por danado: saltarlo sin colgarse
            saltarBloqueada()
            return
        end if
        m.video.visible = true
        m.video.control = "stop"
        m.video.contentIsPlaylist = true
        m.video.content = raiz
        ' si todo el contenido son videos, repetir sin cortes
        m.video.loop = (m.segmentos.Count() = 1)
        m.video.control = "play"
        m.timerBuffer.control = "start"
    end if
end sub

sub saltarBloqueada()
    ' Cuenta como fallo para que, si TODO esta apartado, se llegue a la lamina
    ' en vez de dar vueltas sin fin.
    m.fallosSeguidos = m.fallosSeguidos + 1
    if m.fallosSeguidos >= m.segmentos.Count()
        mostrarRespaldo()
        programarReintento()
    else
        reproducirSiguiente()
    end if
end sub

function hayFotoEnPantalla() as boolean
    return m.fotoVisible.visible
end function

sub mostrarFoto(url as string, dur as integer, fija as boolean, cortina = false as boolean, urlOriginal = "" as string)
    m.fotoPendiente = {dur: dur, fija: fija, cortina: cortina, origen: urlOriginal, uri: url}
    if m.fotoBuffer.uri = url and m.fotoBuffer.loadStatus = "ready"
        intercambiarFotos()
    else
        m.fotoBuffer.uri = url
    end if
end sub

sub onFotoCargada()
    if m.fotoPendiente = invalid then return
    estado = m.fotoBuffer.loadStatus
    if estado = "ready"
        intercambiarFotos()
    else if estado = "failed"
        p = m.fotoPendiente
        m.fotoPendiente = invalid
        if p.cortina = true
            ' una miniatura que no carga no es un fallo de contenido
            return
        end if
        if p.uri <> invalid and Left(p.uri, 8) = "cachefs:"
            ' la copia local esta mal: borrarla y reintentar por red la proxima
            m.fs.Delete(p.uri)
        else if p.origen <> invalid and p.origen <> ""
            registrarFalloUrl(p.origen)
        end if
        registrarFallo()
    end if
end sub

sub intercambiarFotos()
    p = m.fotoPendiente
    if p = invalid then return
    m.fotoPendiente = invalid

    if p.cortina = true
        ' cortina para el arranque de un video: si ya está reproduciendo, no taparlo
        if m.video.state = "playing" then return
    else
        m.video.control = "stop"
        m.video.visible = false
        m.timerBuffer.control = "stop"
    end if
    m.fotoBuffer.visible = true
    m.fotoVisible.visible = false
    temp = m.fotoVisible
    m.fotoVisible = m.fotoBuffer
    m.fotoBuffer = temp

    m.estado.text = ""
    m.ayuda.text = ""
    if p.cortina = true
        ' se quita sola cuando el video empieza (onVideoState "playing")
        m.timerFoto.control = "stop"
    else
        ' una foto en pantalla es contenido reproducido: salir de la lamina
        contenidoEnPantalla()
        if p.fija
            m.fotoRapida = true
            m.timerFoto.control = "stop"
        else
            m.fotoRapida = false
            m.timerFoto.duration = p.dur
            m.timerFoto.control = "start"
        end if
    end if
end sub

sub ocultarFotos()
    m.foto.visible = false
    m.fotoB.visible = false
    m.fotoPendiente = invalid
    m.fotoRapida = false
end sub

sub onFotoTimer()
    reproducirSiguiente()
end sub

' ---------- B1: cache local ----------

sub pedirCache(datos as object)
    m.cachePedidaEnVivo = true
    m.ultimaReconciliacion = ahoraSegundos()
    lista = []
    for each v in datos.videos
        if v.url <> invalid and v.url <> ""
            lista.Push({url: v.url})
        end if
        if v.mini <> invalid and v.mini <> ""
            lista.Push({url: v.mini})
        end if
    end for
    m.cacheTask.deseados = {lista: lista}
end sub

sub onCacheListo()
    ' Nada que hacer en caliente: resolverUrl consulta el disco al reproducir.
end sub

sub onCacheFallo()
    ' Informativo. Una descarga fallida no afecta la reproduccion por red.
end sub

' Fotos y miniaturas: cachefs esta recomendado por Roku para imagenes.
function resolverUrl(url as string) as string
    ruta = rutaDeCache(url)
    if m.fs.Exists(ruta) then return ruta
    return url
end function

' Videos: usar la copia local salvo que este modelo demuestre no soportarlo.
function resolverUrlVideo(url as string) as string
    if m.cacheInservibleVideo >= 2 then return url
    return resolverUrl(url)
end function

' ---------- B1: fallos, histeresis y lamina de respaldo ----------

function estaBloqueada(url as string) as boolean
    hasta = m.bloqueadasHasta[url]
    if hasta = invalid then return false
    if ahoraSegundos() >= hasta
        m.bloqueadasHasta.Delete(url)
        m.fallosPorUrl.Delete(url)
        return false
    end if
    return true
end function

sub registrarFalloUrl(url as string)
    ' Sin red, todo falla: eso no dice nada del archivo. No se le cuenta.
    if m.task.conectado = false then return
    n = m.fallosPorUrl[url]
    if n = invalid then n = 0
    n = n + 1
    m.fallosPorUrl[url] = n
    ' Tres fallos seguidos del mismo archivo: apartarlo 10 minutos. Asi un
    ' archivo danado no detiene el resto de la lista, y si era la red la que
    ' fallaba, vuelve a intentarse solo.
    if n >= 3 then m.bloqueadasHasta[url] = ahoraSegundos() + 600
end sub

sub registrarFallo()
    m.fallosSeguidos = m.fallosSeguidos + 1
    total = m.segmentos.Count()
    if total < 1 then total = 1
    if m.fallosSeguidos >= total and not m.enRespaldo
        ' una vuelta completa sin nada reproducible
        mostrarRespaldo()
    end if
    programarReintento()
end sub

sub programarReintento()
    if m.enRespaldo
        m.timerRespaldo.duration = m.esperaRespaldo
        m.timerRespaldo.control = "start"
        if m.esperaRespaldo < 60
            m.esperaRespaldo = m.esperaRespaldo * 2
            if m.esperaRespaldo > 60 then m.esperaRespaldo = 60
        end if
    else
        m.timerReintento.control = "start"
    end if
end sub

sub onReintentoRespaldo()
    if not m.enRespaldo then return
    if m.segmentos.Count() = 0 then return
    reproducirSiguiente()
end sub

sub salirDeRespaldoEIntentar()
    m.esperaRespaldo = 10
    m.fallosSeguidos = 0
    m.timerRespaldo.control = "stop"
    reproducirSiguiente()
end sub

' Algo (video o foto) esta de verdad en pantalla
sub contenidoEnPantalla()
    m.fallosSeguidos = 0
    m.esperaRespaldo = 10
    if m.enRespaldo then ocultarRespaldo()
end sub

sub mostrarRespaldo(motivo = "" as string)
    m.timerFoto.control = "stop"
    m.timerBuffer.control = "stop"
    m.video.control = "stop"
    m.video.visible = false
    ocultarFotos()
    m.estado.text = ""
    m.ayuda.text = ""
    m.enRespaldo = true
    m.respaldo.visible = true
    actualizarDetalle(motivo)
end sub

sub ocultarRespaldo()
    m.enRespaldo = false
    m.esperaRespaldo = 10
    m.timerRespaldo.control = "stop"
    m.respaldo.visible = false
    m.detalle.visible = false
end sub

' Texto pequeno para quien atiende, SOLO sobre la lamina, nunca sobre el contenido
sub actualizarDetalle(motivo = "" as string)
    if not m.enRespaldo then return
    texto = ""
    if m.task.conectado = false
        texto = "sin conexión"
        if m.desconectadoDesde <> "" then texto = texto + " desde " + m.desconectadoDesde
    else if motivo <> ""
        texto = motivo
    else
        texto = "contenido no disponible"
    end if
    if m.task.ultimaSincronizacion <> invalid and m.task.ultimaSincronizacion <> ""
        texto = texto + "  ·  última sincronización " + m.task.ultimaSincronizacion
    end if
    m.detalle.text = texto
    m.detalle.visible = true
end sub

' ---------- B1: estado de red ----------

sub onConectado()
    if m.task.conectado = false
        m.desconectadoDesde = horaLocal()
        m.indicador.visible = true
        ' cualquier comando que llegue tras reconectar se revisara antes de ejecutarlo
        m.revisarComandoViejo = true
        actualizarDetalle()
    else
        m.indicador.visible = false
        ' lo que fallo sin red no era culpa del archivo: limpiar apartados
        m.bloqueadasHasta = {}
        m.fallosPorUrl = {}
        ' y rellenar la cache con lo que no alcanzo a bajar durante la caida:
        ' primero se avisa a la tarea para que libere lo "agotado" por red,
        ' luego se reconcilia la lista
        m.cacheTask.reconectado = m.cacheTask.reconectado + 1
        if m.ultimosDatos <> invalid then pedirCache(m.ultimosDatos)
        if m.enRespaldo and m.segmentos.Count() > 0
            salirDeRespaldoEIntentar()
        else
            actualizarDetalle()
        end if
    end if
end sub

' ---------- Comandos en vivo desde el panel ----------

sub manejarComando(datos as object)
    c = datos.comando
    if c = invalid or c.n = invalid then return
    if m.ultimoComando = invalid or m.ultimoComando = -1
        ' primer ciclo tras abrir la app: ignorar comandos viejos
        m.ultimoComando = c.n
        return
    end if
    if m.revisarComandoViejo
        ' Primera respuesta tras una desconexion (B1-QA-03): la revision se
        ' consume AQUI, haya o no comando nuevo. Solo si el comando cambio
        ' durante la caida y es un "reproducir ahora", se descarta: llegaria
        ' tarde y sorprenderia a la clienta. Pausa/silencio describen un
        ' estado deseado y si se aplican. Un comando emitido DESPUES de
        ' reconectar ya no pasa por aqui y se ejecuta normal.
        m.revisarComandoViejo = false
        if c.n <> m.ultimoComando and c.accion = "reproducir"
            m.ultimoComando = c.n
            return
        end if
    end if
    if c.n = m.ultimoComando then return
    m.ultimoComando = c.n

    if c.accion = "pausa"
        if m.video.visible and (m.video.state = "playing" or m.video.state = "buffering")
            m.video.control = "pause"
        end if
        m.timerFoto.control = "stop"
        m.timerBuffer.control = "stop"
    else if c.accion = "continuar"
        if m.fotoRapida = true
            m.fotoRapida = false
            reproducirSiguiente()
        else if m.video.visible and m.video.state = "paused"
            m.video.control = "resume"
        else if hayFotoEnPantalla()
            m.timerFoto.control = "start"
        else
            reproducirSiguiente()
        end if
    else if c.accion = "silencio"
        m.video.mute = true
    else if c.accion = "sonido"
        m.video.mute = false
    else if c.accion = "reproducir" and c.url <> invalid and c.url <> ""
        if c.tipo = "imagen"
            dur = 10
            if c.duracion <> invalid then dur = c.duracion
            mostrarFoto(resolverUrl(c.url), dur, dur <= 0, false, c.url)
        else
            m.timerFoto.control = "stop"
            raiz = createObject("roSGNode", "ContentNode")
            hijo = raiz.createChild("ContentNode")
            hijo.url = resolverUrlVideo(c.url)
            hijo.streamFormat = "mp4"
            m.urlsEnVideo = [c.url]
            m.rutasEnVideo = [hijo.url]
            m.video.visible = true
            m.video.control = "stop"
            m.video.contentIsPlaylist = true
            m.video.content = raiz
            m.video.loop = false
            m.video.control = "play"
            m.timerBuffer.control = "start"
        end if
        ' al terminar, onVideoState/onFotoTimer continúan el bucle normal
    end if
end sub

' ---------- Reproduccion de video ----------

sub onVideoState()
    estado = m.video.state
    if estado = "buffering"
        ' arranca el vigilante; si ya estaba corriendo, sigue
        if m.timerBuffer.control <> "start" then m.timerBuffer.control = "start"
    else if estado = "playing"
        m.timerBuffer.control = "stop"
        ocultarFotos()
        m.estado.text = ""
        m.ayuda.text = ""
        contenidoEnPantalla()
    else if estado = "finished"
        m.timerBuffer.control = "stop"
        reproducirSiguiente()
    else if estado = "error"
        m.timerBuffer.control = "stop"
        atenderFalloDeVideo("error")
    else if estado = "paused"
        m.timerBuffer.control = "stop"
    end if
    ' "stopped" no apaga el vigilante a proposito: ese estado lo provocamos
    ' nosotros justo antes de "play" y su evento llega en cola despues de que
    ' el vigilante ya arranco. Si lo apagara, un video que nunca emite
    ' "buffering" podria quedarse colgado sin nadie que lo vigile.
end sub

sub onBufferColgado()
    if m.video.state = "buffering"
        ' 25 s sin arrancar ni avanzar: esto es "se queda cargando"
        m.video.control = "stop"
        atenderFalloDeVideo("buffering")
    end if
end sub

sub atenderFalloDeVideo(causa as string)
    ' Que archivo fallo: el que estaba sonando dentro del bloque encadenado
    i = m.video.contentIndex
    if i = invalid or i < 0 or i >= m.urlsEnVideo.Count() then i = 0
    if m.urlsEnVideo.Count() > 0
        url = m.urlsEnVideo[i]
        ruta = m.rutasEnVideo[i]
        if Left(ruta, 8) = "cachefs:"
            ' La copia local no se pudo reproducir. Puede ser el archivo o que
            ' este modelo no reproduzca desde cachefs: borrarla y, si se
            ' repite, dejar de usar cache para video en esta sesion.
            m.fs.Delete(ruta)
            m.cacheInservibleVideo = m.cacheInservibleVideo + 1
            ' no cuenta contra la URL: se volvera a intentar por red
        else
            registrarFalloUrl(url)
        end if
    end if
    ' Sin texto tecnico para la clienta: se salta en silencio
    registrarFallo()
end sub

sub onReintento()
    m.estado.text = ""
    reproducirSiguiente()
end sub

sub onTaskError()
    ' Solo mientras la pantalla no ha recibido nunca una lista (configuracion
    ' inicial). En operacion, la falta de red se muestra con la lamina.
    if m.recibioPlaylist then return
    if m.video.state <> "playing" and m.video.state <> "buffering" and not hayFotoEnPantalla()
        if not m.enRespaldo then m.estado.text = m.task.errorMsg
    end if
end sub

' ---------- Turnos: panel deslizante inferior ----------

sub manejarTurno(datos as object)
    t = datos.turno
    if t = invalid or t.n = invalid then return
    if m.ultimoTurno = -1
        ' primer ciclo tras abrir: no anunciar turnos viejos
        m.ultimoTurno = t.n
        return
    end if
    if t.n = m.ultimoTurno then return
    m.ultimoTurno = t.n
    if t.numero = invalid or t.numero = "" then return
    if turnoVencido(t) then return
    mostrarTurnoPanel(datos, t)
end sub

' Un turno cuya ventana de anuncio ya paso no se muestra: llamaria a alguien
' que ya no esta esperando. Tolerancia de 30 s por desfase de relojes.
function turnoVencido(t as object) as boolean
    if t.ts = invalid then return false
    dur = 60
    if t.duracion <> invalid then dur = t.duracion
    edad = ahoraSegundos() - t.ts
    return edad > (dur + 30)
end function

sub mostrarTurnoPanel(datos as object, t as object)
    espera = ""
    if t.espera <> invalid then espera = t.espera
    configurarTurnoPanel(datos, espera <> "")

    m.top.findNode("tNumero").text = t.numero
    est = ""
    if t.estacion <> invalid and t.estacion <> "" then est = "ESTACIÓN " + t.estacion
    m.top.findNode("tEstacion").text = est

    nums = ""
    ests = ""
    cuantos = 0
    if t.proximos <> invalid
        for each p in t.proximos
            if p.numero <> invalid and p.numero <> ""
                nums = nums + p.numero + chr(10)
                e = ""
                if p.estacion <> invalid and p.estacion <> "" then e = "EST. " + p.estacion
                ests = ests + e + chr(10)
                cuantos = cuantos + 1
            end if
        end for
    end if
    m.top.findNode("tAntNums").text = nums
    m.top.findNode("tAntEsts").text = ests
    hayProx = (cuantos > 0)
    m.top.findNode("tAntTit").visible = hayProx
    m.top.findNode("tAntNums").visible = hayProx
    m.top.findNode("tAntEsts").visible = hayProx
    m.top.findNode("tDivisor").visible = hayProx

    if espera <> ""
        m.top.findNode("tEspera").text = "Espera aprox.  " + espera + " min"
    end if
    m.top.findNode("tFooter").visible = (espera <> "")
    m.top.findNode("tEspera").visible = (espera <> "")

    if not m.turnoGrp.visible
        ' entra deslizando desde abajo
        m.tPanel.translation = [0, m.turnoBlockH]
        m.tInterpIn.keyValue = [[0, m.turnoBlockH], [0, 0]]
        m.turnoGrp.visible = true
        m.tAnimIn.control = "start"
    else
        m.tPanel.translation = [0, 0]
    end if

    dur = 60
    if t.duracion <> invalid then dur = t.duracion
    ' si el turno lleva tiempo emitido, solo se muestra lo que le queda
    if t.ts <> invalid
        restante = dur - (ahoraSegundos() - t.ts)
        if restante < 5 then restante = 5
        if restante < dur then dur = restante
    end if
    m.timerTurno.duration = dur
    m.timerTurno.control = "start"
end sub

sub onTurnoFin()
    ' sale deslizando hacia abajo
    m.tInterpOut.keyValue = [[0, 0], [0, m.turnoBlockH]]
    m.tAnimOut.control = "start"
end sub

sub onTurnoOculto()
    if m.tAnimOut.state = "stopped"
        m.turnoGrp.visible = false
    end if
end sub

sub configurarTurnoPanel(datos as object, tieneEspera as boolean)
    vertical = (datos.vertical = true)
    giro = "horario"
    if datos.giro <> invalid then giro = datos.giro

    g = m.turnoGrp
    if vertical
        lw = m.alto
        lh = m.ancho
        if giro = "horario"
            g.rotation = 1.5708
            g.translation = [0, m.alto]
        else
            g.rotation = -1.5708
            g.translation = [m.ancho, 0]
        end if
    else
        lw = m.ancho
        lh = m.alto
        g.rotation = 0
        g.translation = [0, 0]
    end if

    ph = int(0.20 * lh)
    fh = 0
    if tieneEspera then fh = int(0.047 * lh)
    m.turnoBlockH = ph + fh
    py0 = lh - ph - fh

    fondo = m.top.findNode("tFondoPanel")
    fondo.width = lw
    fondo.height = ph
    fondo.translation = [0, py0]

    linea = m.top.findNode("tLinea")
    linea.width = lw
    linea.height = 4
    linea.translation = [0, py0]

    cxIzq = int(0.26 * lw)
    tit = m.top.findNode("tTitulo")
    tit.width = int(0.5 * lw)
    tit.height = int(0.04 * lh)
    tit.translation = [cxIzq - int(0.25 * lw), py0 + int(0.016 * lh)]
    tit.font = "font:LargeBoldSystemFont"
    tit.font.size = int(0.021 * lh)

    num = m.top.findNode("tNumero")
    num.width = int(0.5 * lw)
    num.height = int(0.075 * lh)
    num.translation = [cxIzq - int(0.25 * lw), py0 + int(0.058 * lh)]
    num.font = "font:LargeBoldSystemFont"
    num.font.size = int(0.0625 * lh)

    est = m.top.findNode("tEstacion")
    est.width = int(0.5 * lw)
    est.height = int(0.04 * lh)
    est.translation = [cxIzq - int(0.25 * lw), py0 + int(0.142 * lh)]
    est.font = "font:LargeBoldSystemFont"
    est.font.size = int(0.023 * lh)

    div = m.top.findNode("tDivisor")
    div.width = 3
    div.height = ph - int(0.046 * lh)
    div.translation = [int(0.505 * lw), py0 + int(0.023 * lh)]

    at = m.top.findNode("tAntTit")
    at.width = int(0.42 * lw)
    at.height = int(0.04 * lh)
    at.translation = [int(0.53 * lw), py0 + int(0.016 * lh)]
    at.font = "font:LargeBoldSystemFont"
    at.font.size = int(0.019 * lh)

    an = m.top.findNode("tAntNums")
    an.width = int(0.16 * lw)
    an.height = ph - int(0.07 * lh)
    an.translation = [int(0.565 * lw), py0 + int(0.062 * lh)]
    an.font = "font:LargeBoldSystemFont"
    an.font.size = int(0.023 * lh)
    an.lineSpacing = int(0.019 * lh)

    ae = m.top.findNode("tAntEsts")
    ae.width = int(0.22 * lw)
    ae.height = ph - int(0.07 * lh)
    ae.translation = [int(0.73 * lw), py0 + int(0.062 * lh)]
    ae.font = "font:LargeBoldSystemFont"
    ae.font.size = int(0.023 * lh)
    ae.lineSpacing = int(0.019 * lh)

    foot = m.top.findNode("tFooter")
    foot.width = lw
    foot.height = fh
    foot.translation = [0, lh - fh]

    esp = m.top.findNode("tEspera")
    esp.width = lw
    esp.height = fh
    esp.translation = [0, lh - fh]
    esp.font = "font:LargeBoldSystemFont"
    esp.font.size = int(0.02 * lh)
end sub

' ---------- Pantalla pendiente de aprobación ----------

sub modoPendiente(datos as object)
    configurarFoto(datos) ' aplica tambien la orientacion de textos
    m.video.control = "stop"
    m.video.visible = false
    ocultarFotos()
    if m.enRespaldo then ocultarRespaldo()
    m.timerArranqueRespaldo.control = "stop"
    m.top.findNode("barra").visible = false
    m.barraClave = ""
    m.timerFoto.control = "stop"
    m.pendienteActivo = true

    m.estado.text = "Pantalla no activada" + chr(10) + "Ingresa este código en el panel LUMIN TV:"
    cod = ""
    if datos.codigo <> invalid then cod = datos.codigo
    espaciado = ""
    for i = 0 to cod.Len() - 1
        espaciado = espaciado + Mid(cod, i + 1, 1)
        if i < cod.Len() - 1 then espaciado = espaciado + "  "
    end for
    m.codigoLbl.text = espaciado
    m.ayuda.text = ""
end sub

' ---------- Textos: orientación según la TV ----------

sub orientarTextos(vertical as boolean, giro as string)
    clave = giro + "|" + vertical.toStr()
    if clave = m.textosClave then return
    m.textosClave = clave

    if vertical
        m.estado.width = m.alto
        m.estado.height = 400
        m.ayuda.width = m.alto
        m.ayuda.height = 50
        m.codigoLbl.width = m.alto
        m.codigoLbl.height = 260
        if giro = "horario"
            m.estado.rotation = 1.5708
            m.ayuda.rotation = 1.5708
            m.codigoLbl.rotation = 1.5708
            m.estado.translation = [(m.ancho / 2) + 40, m.alto]
            m.codigoLbl.translation = [(m.ancho / 2) - 320, m.alto]
            m.ayuda.translation = [m.ancho - 150, m.alto]
        else
            m.estado.rotation = -1.5708
            m.ayuda.rotation = -1.5708
            m.codigoLbl.rotation = -1.5708
            m.estado.translation = [(m.ancho / 2) - 40, 0]
            m.codigoLbl.translation = [(m.ancho / 2) + 320, 0]
            m.ayuda.translation = [150, 0]
        end if
    else
        m.estado.rotation = 0
        m.ayuda.rotation = 0
        m.codigoLbl.rotation = 0
        m.estado.width = m.ancho
        m.estado.height = 200
        m.estado.translation = [0, (m.alto / 2) - 260]
        m.codigoLbl.width = m.ancho
        m.codigoLbl.height = 260
        m.codigoLbl.translation = [0, (m.alto / 2) - 40]
        m.ayuda.width = m.ancho
        m.ayuda.height = 50
        m.ayuda.translation = [0, m.alto - 70]
    end if
end sub

' ---------- Fotos y capa de continuidad: orientación según la TV ----------

sub configurarFoto(datos as object)
    vertical = (datos.vertical = true)
    giro = "horario"
    if datos.giro <> invalid then giro = datos.giro
    orientarTextos(vertical, giro)
    clave = giro + "|" + vertical.toStr()
    if clave = m.fotoClave then return
    m.fotoClave = clave

    for each p in [m.foto, m.fotoB, m.capaEstado]
        if vertical
            if p.hasField("width")
                p.width = m.alto
                p.height = m.ancho
            end if
            if giro = "horario"
                p.rotation = 1.5708
                p.translation = [0, m.alto]
            else
                p.rotation = -1.5708
                p.translation = [m.ancho, 0]
            end if
        else
            if p.hasField("width")
                p.width = m.ancho
                p.height = m.alto
            end if
            p.rotation = 0
            p.translation = [0, 0]
        end if
    end for

    ' hijos de la capa, en coordenadas de la pantalla fisica
    if vertical
        lw = m.alto
        lh = m.ancho
        m.respaldo.uri = "pkg:/images/respaldo_vertical.png"
    else
        lw = m.ancho
        lh = m.alto
        m.respaldo.uri = "pkg:/images/respaldo_horizontal.png"
    end if
    m.respaldo.width = lw
    m.respaldo.height = lh
    m.respaldo.translation = [0, 0]

    margen = int(0.03 * lw)
    punto = 24
    m.indicador.width = punto
    m.indicador.height = punto
    m.indicador.translation = [lw - margen - punto, lh - margen - punto]

    m.detalle.width = lw - (2 * margen) - punto - 20
    m.detalle.height = 40
    m.detalle.translation = [margen, lh - margen - 32]
end sub

' ---------- Orientacion recordada entre arranques (registro, ~20 bytes) ----------

function orientacionGuardada() as object
    reg = CreateObject("roRegistrySection", "config")
    vertical = true
    giro = "horario"
    if reg.Exists("vertical") then vertical = (reg.Read("vertical") = "1")
    if reg.Exists("giro") and reg.Read("giro") <> "" then giro = reg.Read("giro")
    return {vertical: vertical, giro: giro}
end function

sub guardarOrientacion(datos as object)
    v = "1"
    if datos.vertical <> true then v = "0"
    g = "horario"
    if datos.giro <> invalid then g = datos.giro
    reg = CreateObject("roRegistrySection", "config")
    cambio = false
    if not reg.Exists("vertical") or reg.Read("vertical") <> v
        reg.Write("vertical", v)
        cambio = true
    end if
    if not reg.Exists("giro") or reg.Read("giro") <> g
        reg.Write("giro", g)
        cambio = true
    end if
    if cambio then reg.Flush()
end sub

' ---------- Barra de mensajes ----------

sub actualizarBarra(datos as object)
    texto = ""
    if datos.mensaje <> invalid then texto = datos.mensaje.Trim()
    vertical = (datos.vertical = true)
    giro = "horario"
    if datos.giro <> invalid then giro = datos.giro
    animado = true
    if datos.cintillo <> invalid then animado = (datos.cintillo = true)
    velocidad = 130
    if datos.velocidad <> invalid then velocidad = datos.velocidad
    if velocidad < 40 then velocidad = 40

    clave = texto + "|" + giro + "|" + vertical.toStr() + "|" + animado.toStr() + "|" + velocidad.toStr()
    if clave = m.barraClave then return
    m.barraClave = clave

    barra = m.top.findNode("barra")
    if texto = ""
        if m.animBarra <> invalid then m.animBarra.control = "stop"
        barra.visible = false
        return
    end if

    grosor = 76
    fondoB = m.top.findNode("barraFondo")
    etiqueta = m.top.findNode("barraTexto")

    if vertical
        largo = m.alto
        if giro = "horario"
            barra.rotation = 1.5708
            barra.translation = [m.ancho - grosor, m.alto]
        else
            barra.rotation = -1.5708
            barra.translation = [grosor, 0]
        end if
    else
        largo = m.ancho
        barra.rotation = 0
        barra.translation = [0, m.alto - grosor]
    end if

    fondoB.width = largo
    fondoB.height = grosor

    if m.animBarra <> invalid
        m.animBarra.control = "stop"
    end if

    if animado
        ' Cintillo tipo noticias: el texto cruza la pantalla en bucle.
        ' La barra ocupa el ancho completo, así que lo que sale de sus
        ' extremos queda fuera de pantalla automáticamente.
        etiqueta.width = 0 ' tamaño automático, una sola línea
        etiqueta.height = grosor
        etiqueta.text = texto
        anchoTexto = etiqueta.boundingRect().width
        etiqueta.translation = [largo, 0]

        if m.animBarra = invalid
            m.animBarra = m.top.createChild("Animation")
            m.animBarra.easeFunction = "linear"
            m.animBarra.repeat = true
            m.interpBarra = m.animBarra.createChild("Vector2DFieldInterpolator")
            m.interpBarra.fieldToInterp = "barraTexto.translation"
            m.interpBarra.key = [0.0, 1.0]
        end if
        m.animBarra.duration = (largo + anchoTexto) / velocidad
        m.interpBarra.keyValue = [[largo, 0], [-anchoTexto, 0]]
        m.animBarra.control = "start"
    else
        ' Texto fijo centrado
        etiqueta.width = largo - 60
        etiqueta.height = grosor
        etiqueta.translation = [30, 0]
        etiqueta.text = texto
    end if

    barra.visible = true
end sub

' ---------- Utilidades de tiempo ----------

function ahoraSegundos() as integer
    dt = CreateObject("roDateTime")
    return dt.AsSeconds()
end function

function horaLocal() as string
    dt = CreateObject("roDateTime")
    dt.ToLocalTime()
    h = dt.GetHours().toStr()
    mi = dt.GetMinutes().toStr()
    if h.Len() < 2 then h = "0" + h
    if mi.Len() < 2 then mi = "0" + mi
    return h + ":" + mi
end function

' ---------- Control remoto ----------

function onKeyEvent(key as string, press as boolean) as boolean
    if press and key = "options"
        mostrarDialogoUrl(m.task.serverUrl)
        return true
    end if
    return false
end function
