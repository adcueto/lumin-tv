' PlaylistTask — consulta el servidor con LIMITE DE ESPERA e histeresis.
'
' Antes: GetToString() sincrono y sin tope. Al caerse el internet la llamada se
' quedaba colgada el tiempo de espera del sistema operativo y el bucle de 4 s
' dejaba de latir; la TV no se enteraba de nada.
'
' Ahora: consulta asincrona con tope de 8 s y cancelacion explicita. Si falla,
' el intervalo crece (4 -> 8 -> 15 -> 30 s) para no martillar una red caida, y
' vuelve a 4 s en cuanto responde. El estado "conectado" solo cambia tras DOS
' fallos seguidos, para que una red intermitente no haga parpadear el aviso.
'
' Contrato con el servidor: SIN CAMBIOS. Sigue siendo GET /playlist.json?id=...

sub init()
    m.top.functionName = "ejecutar"
end sub

sub ejecutar()
    di = CreateObject("roDeviceInfo")
    m.idTv = di.GetChannelClientId()

    reg = CreateObject("roRegistrySection", "config")
    if reg.Exists("serverUrl") and reg.Read("serverUrl") <> ""
        m.top.serverUrl = reg.Read("serverUrl")
    else
        m.top.serverUrl = "https://tv.luminbelleza.com"
        reg.Write("serverUrl", "https://tv.luminbelleza.com")
        reg.Flush()
    end if

    m.port = CreateObject("roMessagePort")
    m.top.observeField("saveUrl", m.port)
    m.top.observeField("consultarAhora", m.port)

    ' B5a: datos fijos del equipo que viajan en cada latido
    ai = CreateObject("roAppInfo")
    osv = di.GetOSVersion()
    m.fijo = {
        v: ai.GetVersion(),
        m: di.GetModel(),
        os: osv.major + "." + osv.minor + "." + osv.revision + "." + osv.build
    }

    INTERVALO_BASE = 4000
    INTERVALO_MAX = 30000
    TOPE_RESPUESTA_MS = 8000

    intervalo = INTERVALO_BASE
    fallosSeguidos = 0
    m.top.conectado = true   ' optimista al arrancar: se corrige al primer fallo
    m.fs = CreateObject("roFileSystem")
    huboRespuestaEnVivo = false
    m.ultimaGuardada = ""
    arranque = CreateObject("roTimespan")
    LIMITE_ARRANQUE_MS = 12000

    while true
        ' Esperar el intervalo vigente, atendiendo un cambio de URL si llega
        msg = wait(intervalo, m.port)
        if type(msg) = "roSGNodeEvent" and msg.getField() = "saveUrl"
            nueva = msg.getData()
            if nueva <> invalid and nueva <> ""
                reg = CreateObject("roRegistrySection", "config")
                reg.Write("serverUrl", nueva)
                reg.Flush()
                m.top.serverUrl = nueva
                intervalo = INTERVALO_BASE
                fallosSeguidos = 0
            end if
        end if

        url = m.top.serverUrl
        if url <> invalid and url <> ""
            respuesta = consultarConTope(url, TOPE_RESPUESTA_MS)
            if respuesta <> invalid and respuesta <> ""
                huboRespuestaEnVivo = true
                if m.top.desdeCache then m.top.desdeCache = false
                m.top.playlistJson = respuesta
                m.top.ultimaSincronizacion = ahoraTexto()
                guardarPlaylistEnCache(respuesta)
                fallosSeguidos = 0
                intervalo = INTERVALO_BASE
                if not m.top.conectado then m.top.conectado = true
            else
                fallosSeguidos = fallosSeguidos + 1
                ' histeresis: un solo fallo no cambia el estado visible
                if fallosSeguidos >= 2 and m.top.conectado then m.top.conectado = false
                ' retroceso: 4, 8, 15, 30, 30, 30...
                if intervalo < 8000
                    intervalo = 8000
                else if intervalo < 15000
                    intervalo = 15000
                else
                    intervalo = INTERVALO_MAX
                end if
                ' Solo se usa en la fase de configuracion (sin pantalla activada):
                ' en operacion normal la escena muestra la lamina de respaldo.
                m.top.errorMsg = "Sin conexión con el servidor"
                if not huboRespuestaEnVivo and arranque.TotalMilliseconds() >= LIMITE_ARRANQUE_MS
                    ' Arranque sin red: si la cache sobrevivio (cierre de app),
                    ' arrancar con la ultima lista buena. Solo una vez.
                    guardada = leerPlaylistDeCache()
                    if guardada <> ""
                        m.top.desdeCache = true
                        m.top.playlistJson = guardada
                    end if
                    huboRespuestaEnVivo = true  ' no volver a intentarlo
                end if
            end if
        end if
    end while
end sub

' Devuelve el cuerpo o invalid. NUNCA bloquea mas de topeMs.
function consultarConTope(baseUrl as string, topeMs as integer) as dynamic
    xfer = CreateObject("roUrlTransfer")
    xfer.SetCertificatesFile("common:/certs/ca-bundle.crt")
    xfer.InitClientCertificates()
    xfer.RetainBodyOnError(false)
    xfer.EnableFreshConnection(false)
    xfer.SetUrl(baseUrl + "/playlist.json?id=" + m.idTv + parametrosDeEstado(xfer))

    puerto = CreateObject("roMessagePort")
    xfer.SetMessagePort(puerto)
    if not xfer.AsyncGetToString() then return invalid

    evento = wait(topeMs, puerto)
    if type(evento) <> "roUrlEvent"
        ' tope alcanzado: cancelar para no dejar una transferencia colgada
        xfer.AsyncCancel()
        return invalid
    end if
    if evento.GetResponseCode() <> 200 then return invalid
    cuerpo = evento.GetString()
    if cuerpo = invalid or cuerpo = "" then return invalid
    return cuerpo
end function

' B5a: estado real de la pantalla, como parametros del mismo latido. El
' servidor 6.9 los ignora; el 6.10 los guarda para el panel. Todo corto: el
' latido sigue siendo una peticion pequena cada 4 s.
function parametrosDeEstado(xfer as object) as string
    q = "&v=" + xfer.Escape(m.fijo.v) + "&m=" + xfer.Escape(m.fijo.m) + "&os=" + xfer.Escape(m.fijo.os)
    ip = ipLocal()
    if ip <> "" then q = q + "&ip=" + xfer.Escape(ip)
    e = m.top.estado
    if e <> invalid
        if e.r <> invalid and e.r <> "" then q = q + "&r=" + xfer.Escape(Left(e.r, 60))
        if e.c <> invalid then q = q + "&c=" + e.c.ToStr()
        if e.k <> invalid and e.k = true then q = q + "&k=1"
        if e.e <> invalid and e.e <> "" then q = q + "&e=" + xfer.Escape(Left(e.e, 80))
        if e.et <> invalid and e.et > 0
            hace = CreateObject("roDateTime").AsSeconds() - e.et
            if hace < 0 then hace = 0
            q = q + "&eh=" + hace.ToStr()
        end if
    end if
    return q
end function

function ipLocal() as string
    di = CreateObject("roDeviceInfo")
    ips = di.GetIPAddrs()
    if ips = invalid then return ""
    for each k in ips
        if ips[k] <> invalid and ips[k] <> "" then return ips[k]
    end for
    return ""
end function

function ahoraTexto() as string
    dt = CreateObject("roDateTime")
    dt.ToLocalTime()
    h = dt.GetHours().toStr()
    mi = dt.GetMinutes().toStr()
    if h.Len() < 2 then h = "0" + h
    if mi.Len() < 2 then mi = "0" + mi
    return h + ":" + mi
end function

' ---- ultima lista buena en cachefs (misma vida que los medios) ----

sub guardarPlaylistEnCache(json as string)
    ' Se guarda solo si trae videos: una respuesta "pendiente" no sirve offline
    if json.Instr(Chr(34) + "videos" + Chr(34)) < 0 then return
    ' y solo si cambio: el latido llega cada 4 s, no hay que escribir cada vez
    if json = m.ultimaGuardada then return
    if WriteAsciiFile(rutaPlaylistCache(), json) then m.ultimaGuardada = json
end sub

function leerPlaylistDeCache() as string
    if not m.fs.Exists(rutaPlaylistCache()) then return ""
    contenido = ReadAsciiFile(rutaPlaylistCache())
    if contenido = invalid then return ""
    return contenido
end function
