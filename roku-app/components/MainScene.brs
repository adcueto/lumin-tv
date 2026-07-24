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

    ' Tarea que maneja registro (URL guardada) y consulta el servidor
    m.task = createObject("roSGNode", "PlaylistTask")
    m.task.observeField("playlistJson", "onPlaylistJson")
    m.task.observeField("serverUrl", "onServerUrlLoaded")
    m.task.observeField("errorMsg", "onTaskError")
    m.task.control = "RUN"

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

    if datos.pendiente <> invalid and datos.pendiente = true
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

    actualizarBarra(datos)
    configurarFoto(datos)

    videosStr = FormatJson(datos.videos)
    if videosStr <> m.playlistActual
        m.playlistActual = videosStr
        reconstruirSegmentos(datos)
    end if

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
    if m.segmentos.Count() = 0
        m.video.control = "stop"
        m.video.visible = false
        ocultarFotos()
        m.estado.text = "Sin contenido. Sube videos o fotos desde el panel web."
        return
    end if

    m.ayuda.text = ""
    if hayFotoEnPantalla() or m.video.state = "playing" or m.video.state = "paused"
        ' ya hay algo en pantalla: no ensuciar con mensajes
        m.estado.text = ""
    else
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
        mostrarFoto(seg.url, seg.duracion, false)
    else
        m.timerFoto.control = "stop"
        ' la foto actual se queda visible hasta que el video empiece;
        ' si no hay foto, usar la miniatura del video como cortina
        if not hayFotoEnPantalla() and seg.mini <> invalid and seg.mini <> ""
            mostrarFoto(seg.mini, 0, false, true)
        end if
        raiz = createObject("roSGNode", "ContentNode")
        for each u in seg.urls
            hijo = raiz.createChild("ContentNode")
            hijo.url = u
            hijo.streamFormat = "mp4"
        end for
        m.video.visible = true
        m.video.control = "stop"
        m.video.contentIsPlaylist = true
        m.video.content = raiz
        ' si todo el contenido son videos, repetir sin cortes
        m.video.loop = (m.segmentos.Count() = 1)
        m.video.control = "play"
    end if
end sub

function hayFotoEnPantalla() as boolean
    return m.fotoVisible.visible
end function

sub mostrarFoto(url as string, dur as integer, fija as boolean, cortina = false as boolean)
    m.fotoPendiente = {dur: dur, fija: fija, cortina: cortina}
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
        m.fotoPendiente = invalid
        reproducirSiguiente()
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
    else if p.fija
        m.fotoRapida = true
        m.timerFoto.control = "stop"
    else
        m.fotoRapida = false
        m.timerFoto.duration = p.dur
        m.timerFoto.control = "start"
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

' ---------- Comandos en vivo desde el panel ----------

sub manejarComando(datos as object)
    c = datos.comando
    if c = invalid or c.n = invalid then return
    if m.ultimoComando = invalid or m.ultimoComando = -1
        ' primer ciclo tras abrir la app: ignorar comandos viejos
        m.ultimoComando = c.n
        return
    end if
    if c.n = m.ultimoComando then return
    m.ultimoComando = c.n

    if c.accion = "pausa"
        if m.video.visible and (m.video.state = "playing" or m.video.state = "buffering")
            m.video.control = "pause"
        end if
        m.timerFoto.control = "stop"
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
            mostrarFoto(c.url, dur, dur <= 0)
        else
            m.timerFoto.control = "stop"
            raiz = createObject("roSGNode", "ContentNode")
            hijo = raiz.createChild("ContentNode")
            hijo.url = c.url
            hijo.streamFormat = "mp4"
            m.video.visible = true
            m.video.control = "stop"
            m.video.contentIsPlaylist = true
            m.video.content = raiz
            m.video.loop = false
            m.video.control = "play"
        end if
        ' al terminar, onVideoState/onFotoTimer continúan el bucle normal
    end if
end sub

sub onVideoState()
    estado = m.video.state
    if estado = "playing"
        ocultarFotos()
        m.estado.text = ""
        m.ayuda.text = ""
    else if estado = "finished"
        reproducirSiguiente()
    else if estado = "error"
        m.estado.text = "Error al reproducir. Saltando..."
        m.timerReintento.control = "start"
    end if
end sub

sub onReintento()
    m.estado.text = ""
    reproducirSiguiente()
end sub

sub onTaskError()
    if m.video.state <> "playing" and m.video.state <> "buffering" and not hayFotoEnPantalla()
        m.estado.text = m.task.errorMsg
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
    mostrarTurnoPanel(datos, t)
end sub

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

' ---------- Fotos: orientación según la TV ----------

sub configurarFoto(datos as object)
    vertical = (datos.vertical = true)
    giro = "horario"
    if datos.giro <> invalid then giro = datos.giro
    orientarTextos(vertical, giro)
    clave = giro + "|" + vertical.toStr()
    if clave = m.fotoClave then return
    m.fotoClave = clave

    for each p in [m.foto, m.fotoB]
        if vertical
            p.width = m.alto
            p.height = m.ancho
            if giro = "horario"
                p.rotation = 1.5708
                p.translation = [0, m.alto]
            else
                p.rotation = -1.5708
                p.translation = [m.ancho, 0]
            end if
        else
            p.width = m.ancho
            p.height = m.alto
            p.rotation = 0
            p.translation = [0, 0]
        end if
    end for
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

' ---------- Control remoto ----------

function onKeyEvent(key as string, press as boolean) as boolean
    if press and key = "options"
        mostrarDialogoUrl(m.task.serverUrl)
        return true
    end if
    return false
end function
