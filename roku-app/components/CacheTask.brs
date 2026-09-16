' CacheTask — copia el contenido de la lista a cachefs:/ para sobrevivir una
' caida de internet CON LA APP ABIERTA.
'
' Limites reales de Roku, verificados en su documentacion:
'   - cachefs: vive en RAM. Se pierde al REINICIAR el equipo y el sistema la
'     desaloja cuando otra app necesita espacio. Sobrevive a cerrar la app.
'   - tmp: se borra al cerrar la app. No sirve para esto.
' Por eso esta cache NO promete reproducir sin internet tras reiniciar la TV.
'
' Estructura (revisada tras R2-B1-01 y R2-B1-02):
'   m.registro  estado por URL, INDEPENDIENTE de la cola: intentos, proxima
'               fecha, fallo terminal y su motivo. Reconciliar no lo reinicia.
'   m.cola      solo URLs, sin duplicados, sin la activa, sin terminales.
'   m.activo    la URL que se esta bajando ahora; una reconciliacion nunca la
'               vuelve a encolar.
'
' Reglas:
'   - Al cambiar la lista se borra de inmediato lo que ya no esta en ella:
'     contenido obsoleto no ocupa el presupuesto de contenido nuevo.
'   - Presupuesto ANTES y DURANTE: tamano por HEAD (el servidor 6.10 lo
'     soporta); si el tamano es desconocido se reserva el tope por archivo,
'     conservador, y se desaloja lo mas viejo hasta que quepa. Durante la
'     descarga se vigila el temporal cada 2 s. Al confirmar se revalida.
'   - Reintentos: 30, 60, 120, 240 y 300 s; a la sexta falla queda "agotado".
'   - Fallos terminales y cuando vuelven a intentarse:
'       404/403/410 y demasiado grande ....... a los 30 min
'       sin espacio .......................... cuando cambia el conjunto de la
'                                              lista o se libera espacio
'       agotado / red ........................ cuando vuelve la conexion
'       la URL sale de la lista .............. su estado se olvida; si vuelve,
'                                              empieza de cero
'   - Descarga a nombre temporal y renombra al final: un archivo con nombre
'     definitivo esta COMPLETO. Una lista nueva cancela la descarga en curso si
'     ese archivo ya no esta en ella.

sub init()
    m.top.functionName = "ejecutar"
end sub

' Parametros y estado inicial. Separado de ejecutar() para que el arnes de
' roku-app/pruebas/ pueda ejercitar la planificacion sin el bucle infinito.
sub configurar()
    m.TOPE_TOTAL = 250 * 1024 * 1024      ' 250 MB en RAM compartida: conservador
    m.MARGEN = 20 * 1024 * 1024           ' reservado para la reproduccion en curso
    m.TOPE_ARCHIVO = 80 * 1024 * 1024
    m.TASA_MINIMA_BPS = 8 * 1024          ' 8 KB/s durante 20 s => descarga colgada
    m.PERIODO_TASA_S = 20
    m.MAX_INTENTOS = 6                    ' 5 esperas: 30, 60, 120, 240, 300 s
    m.CUARENTENA_404_MS = 30 * 60 * 1000

    m.registro = {}
    m.cola = []
    m.activo = ""
    m.deseadas = {}
end sub

sub ejecutar()
    configurar()
    m.fs = CreateObject("roFileSystem")
    m.port = CreateObject("roMessagePort")
    m.top.observeField("deseados", m.port)
    m.top.observeField("reconectado", m.port)

    limpiarTemporales()
    bytesEnCache()

    while true
        espera = milisegundosHastaElSiguiente()
        if espera < 0
            msg = wait(0, m.port)
        else if espera > 0
            msg = wait(espera, m.port)
        else
            msg = m.port.GetMessage()
        end if
        atenderMensaje(msg)
        procesarSiguiente()
    end while
end sub

' Un ciclo de trabajo: toma la siguiente URL lista, la baja y registra el
' resultado. Devuelve false si no habia nada listo.
function procesarSiguiente() as boolean
    url = siguienteListo()
    if url = "" then return false
    m.activo = url
    ruta = rutaDeCache(url)
    yaEstaba = m.fs.Exists(ruta)
    if yaEstaba
        resultado = "ok"
    else
        resultado = descargar(url, ruta)
    end if
    ' R3-B1-01: la transferencia termino. Se cierra el estado activo ANTES de
    ' programar el siguiente intento; si no, encolar() rechazaria el reintento
    ' por creer que la URL sigue bajando y la espera de 30 s nunca vencia.
    m.activo = ""
    if resultado = "ok"
        m.registro.Delete(url)
        if not yaEstaba then revalidarTotal()
        m.top.listo = {url: url, ruta: ruta}
    else if resultado <> "obsoleto"
        registrarFallo(url, resultado)
    end if
    return true
end function

sub atenderMensaje(msg as dynamic)
    if type(msg) <> "roSGNodeEvent" then return
    if msg.getField() = "deseados"
        aplicarDeseados(msg.getData())
    else if msg.getField() = "reconectado"
        reanimarAgotados()
    end if
end sub

' Volvio la red: lo que se agoto por red merece otra oportunidad.
sub reanimarAgotados()
    for each url in m.registro.Keys()
        e = m.registro[url]
        if e.terminal and e.motivo = "agotado"
            e.terminal = false
            e.intentos = 0
            e.noAntesDe = 0
            encolar(url)
        end if
    end for
end sub

' ---- registro y cola ----

function entrada(url as string) as object
    e = m.registro[url]
    if e = invalid
        e = {intentos: 0, noAntesDe: 0, terminal: false, motivo: "", hasta: -1}
        m.registro[url] = e
    end if
    return e
end function

sub encolar(url as string)
    if url = m.activo then return
    for each u in m.cola
        if u = url then return
    end for
    m.cola.Push(url)
end sub

sub aplicarDeseados(d as object)
    nuevas = {}
    if d <> invalid and d.lista <> invalid
        for each it in d.lista
            if it.url <> invalid and it.url <> "" then nuevas[it.url] = true
        end for
    end if
    ' R3-B1-02: una reconciliacion con la MISMA lista no es un cambio. Solo
    ' un conjunto distinto de URLs, o espacio liberado de verdad, cambia la
    ' condicion de exito de un "sin espacio".
    cambioConjunto = conjuntosDistintos(m.deseadas, nuevas)
    m.deseadas = nuevas

    ' 1. lo que salio de la lista: se olvida su estado y se libera su espacio
    for each url in m.registro.Keys()
        if not nuevas.DoesExist(url) then m.registro.Delete(url)
    end for
    liberado = desalojarNoDeseados()

    ' 2. "sin espacio" se reintenta solo si cambio la lista o se libero espacio
    if cambioConjunto or liberado > 0
        for each url in m.registro.Keys()
            e = m.registro[url]
            if e.terminal and e.motivo = "sin_espacio"
                e.terminal = false
                e.noAntesDe = 0
            end if
        end for
    end if

    ' 3. reconstruir la cola sin tocar el registro (intentos y esperas se
    '    conservan) y sin volver a meter la descarga activa
    m.cola = []
    for each url in nuevas.Keys()
        if url <> m.activo and not m.fs.Exists(rutaDeCache(url))
            e = entrada(url)
            if not e.terminal then encolar(url)
        end if
    end for
end sub

function conjuntosDistintos(a as object, b as object) as boolean
    if a.Count() <> b.Count() then return true
    for each k in a.Keys()
        if not b.DoesExist(k) then return true
    end for
    return false
end function

function siguienteListo() as string
    ahora = ahoraMs()
    ' primero: terminales cuya cuarentena venció vuelven a ser candidatos
    for each url in m.registro.Keys()
        e = m.registro[url]
        if e.terminal and e.hasta >= 0 and ahora >= e.hasta and m.deseadas.DoesExist(url)
            e.terminal = false
            e.intentos = 0
            e.noAntesDe = 0
            e.hasta = -1
            encolar(url)
        end if
    end for
    for i = 0 to m.cola.Count() - 1
        url = m.cola[i]
        e = entrada(url)
        if e.noAntesDe <= ahora
            m.cola.Delete(i)
            return url
        end if
    end for
    return ""
end function

' -1 = nada; 0 = hay algo listo; >0 = ms hasta lo mas proximo (tope 5 s)
function milisegundosHastaElSiguiente() as integer
    ahora = ahoraMs()
    minimo = -1
    for each url in m.cola
        e = entrada(url)
        falta = e.noAntesDe - ahora
        if falta <= 0 then return 0
        if minimo < 0 or falta < minimo then minimo = falta
    end for
    for each url in m.registro.Keys()
        e = m.registro[url]
        if e.terminal and e.hasta >= 0
            falta = e.hasta - ahora
            if falta <= 0 then return 0
            if minimo < 0 or falta < minimo then minimo = falta
        end if
    end for
    if minimo > 5000 then minimo = 5000
    return minimo
end function

sub registrarFallo(url as string, motivo as string)
    e = entrada(url)
    e.intentos = e.intentos + 1
    m.top.fallo = {url: url, motivo: motivo, intento: e.intentos}

    if motivo = "demasiado_grande" or motivo = "http_404" or motivo = "http_403" or motivo = "http_410"
        ' el archivo no esta o no cabe: no tiene sentido insistir pronto
        e.terminal = true
        e.motivo = motivo
        e.hasta = ahoraMs() + m.CUARENTENA_404_MS
    else if motivo = "sin_espacio"
        ' sin cambiar el presupuesto, repetir daria lo mismo
        e.terminal = true
        e.motivo = motivo
        e.hasta = -1
    else if e.intentos >= m.MAX_INTENTOS
        e.terminal = true
        e.motivo = "agotado"
        e.hasta = -1
    else
        e.noAntesDe = ahoraMs() + esperaReintento(e.intentos)
        if m.deseadas.DoesExist(url) then encolar(url)
    end if
end sub

function esperaReintento(intento as integer) as integer
    ' 1 -> 30 s, 2 -> 60, 3 -> 120, 4 -> 240, 5 -> 300
    ms = 30000
    for i = 2 to intento
        ms = ms * 2
    end for
    if ms > 300000 then ms = 300000
    return ms
end function

' ---- descarga con presupuesto ----

function descargar(url as string, destino as string) as string
    ' Arnes fuera del dispositivo (roku-app/pruebas/): simula el resultado de
    ' la transferencia para ejercitar la planificacion real. En la TV
    ' m.simulacion no existe nunca.
    if m.simulacion <> invalid then return m.simulacion.descargar(url, destino)

    ' 1. tamano anunciado. Si el servidor no lo dice, se reserva el tope por
    '    archivo: conservador, pero nunca deja de desalojar lo viejo.
    tamano = tamanoRemoto(url)
    if tamano > m.TOPE_ARCHIVO then return "demasiado_grande"
    reserva = tamano
    if reserva <= 0 then reserva = m.TOPE_ARCHIVO

    ' 2. presupuesto: desalojar lo mas viejo hasta que quepa la reserva
    presupuesto = m.TOPE_TOTAL - m.MARGEN
    if bytesEnCache() + reserva > presupuesto
        desalojar(presupuesto - reserva)
    end if
    disponible = presupuesto - bytesEnCache()
    if disponible <= 0 then return "sin_espacio"
    if tamano > 0 and tamano > disponible then return "sin_espacio"
    topeEsteArchivo = m.TOPE_ARCHIVO
    if disponible < topeEsteArchivo then topeEsteArchivo = disponible

    temporal = "cachefs:/tmp_" + huellaDe(url)
    borrarSiExiste(temporal)

    xfer = CreateObject("roUrlTransfer")
    xfer.SetCertificatesFile("common:/certs/ca-bundle.crt")
    xfer.InitClientCertificates()
    xfer.RetainBodyOnError(false)
    xfer.SetMinimumTransferRate(m.TASA_MINIMA_BPS, m.PERIODO_TASA_S)
    xfer.SetUrl(url)
    puerto = CreateObject("roMessagePort")
    xfer.SetMessagePort(puerto)
    if not xfer.AsyncGetToFile(temporal) then return "no_inicio"

    ' 3. vigilar DURANTE la transferencia, cada 2 s, hasta 10 min
    inicio = ahoraMs()
    while true
        evento = wait(2000, puerto)
        if type(evento) = "roUrlEvent" then exit while
        if ahoraMs() - inicio > 600000
            xfer.AsyncCancel()
            borrarSiExiste(temporal)
            return "tiempo_agotado"
        end if
        st = m.fs.Stat(temporal)
        if st <> invalid and st.size <> invalid and st.size > topeEsteArchivo
            xfer.AsyncCancel()
            borrarSiExiste(temporal)
            if st.size > m.TOPE_ARCHIVO then return "demasiado_grande"
            return "sin_espacio"
        end if
        ' trabajo obsoleto: llego una lista nueva y este archivo ya no esta
        msg = m.port.GetMessage()
        if type(msg) = "roSGNodeEvent"
            atenderMensaje(msg)
            if msg.getField() = "deseados" and not m.deseadas.DoesExist(url)
                xfer.AsyncCancel()
                borrarSiExiste(temporal)
                m.registro.Delete(url)
                return "obsoleto"
            end if
        end if
    end while

    if evento.GetResponseCode() <> 200
        borrarSiExiste(temporal)
        return "http_" + evento.GetResponseCode().toStr()
    end if
    st = m.fs.Stat(temporal)
    if st = invalid or st.size = invalid or st.size <= 0
        borrarSiExiste(temporal)
        return "vacio"
    end if
    if st.size > topeEsteArchivo
        m.fs.Delete(temporal)
        if st.size > m.TOPE_ARCHIVO then return "demasiado_grande"
        return "sin_espacio"
    end if

    ' 4. renombrar al final: si existe con nombre definitivo, esta completo
    if not m.fs.Rename(temporal, destino)
        borrarSiExiste(temporal)
        return "no_renombro"
    end if
    return "ok"
end function

' Content-Length por HEAD, con tope de 8 s. 0 = desconocido (servidores viejos
' responden 501 al HEAD; el 6.10 responde igual que GET, sin contar).
function tamanoRemoto(url as string) as integer
    xfer = CreateObject("roUrlTransfer")
    xfer.SetCertificatesFile("common:/certs/ca-bundle.crt")
    xfer.InitClientCertificates()
    xfer.SetUrl(url)
    puerto = CreateObject("roMessagePort")
    xfer.SetMessagePort(puerto)
    if not xfer.AsyncHead() then return 0
    evento = wait(8000, puerto)
    if type(evento) <> "roUrlEvent"
        xfer.AsyncCancel()
        return 0
    end if
    if evento.GetResponseCode() <> 200 then return 0
    cab = evento.GetResponseHeaders()
    if cab = invalid then return 0
    largo = cab["content-length"]
    if largo = invalid then largo = cab["Content-Length"]
    if largo = invalid then return 0
    n = largo.ToInt()
    if n < 0 then return 0
    return n
end function

sub borrarSiExiste(ruta as string)
    if m.fs.Exists(ruta) then m.fs.Delete(ruta)
end sub

' ---- espacio ----

function listarCache() as object
    salida = []
    lista = m.fs.GetDirectoryListing("cachefs:/")
    if lista = invalid then return salida
    for each nombre in lista
        ' los temporales tambien ocupan RAM: se cuentan
        if Left(nombre, 6) = "lumin_" or Left(nombre, 4) = "tmp_"
            st = m.fs.Stat("cachefs:/" + nombre)
            tam = 0
            mt = 0
            if st <> invalid
                if st.size <> invalid then tam = st.size
                if st.mtime <> invalid then mt = st.mtime.AsSeconds()
            end if
            salida.Push({ruta: "cachefs:/" + nombre, bytes: tam, mtime: mt,
                         temporal: (Left(nombre, 4) = "tmp_")})
        end if
    end for
    return salida
end function

function bytesEnCache() as integer
    total = 0
    for each a in listarCache()
        total = total + a.bytes
    end for
    m.top.bytesEnCache = total
    return total
end function

sub revalidarTotal()
    if bytesEnCache() > m.TOPE_TOTAL then desalojar(m.TOPE_TOTAL)
end sub

function rutasProtegidas() as object
    protegidas = {}
    for each u in m.deseadas.Keys()
        protegidas[rutaDeCache(u)] = true
    end for
    if m.activo <> "" then protegidas["cachefs:/tmp_" + huellaDe(m.activo)] = true
    protegidas[rutaPlaylistCache()] = true
    return protegidas
end function

' Borra todo lo que ya no esta en la lista, sin esperar a que falte espacio.
' Devuelve los bytes liberados de verdad.
function desalojarNoDeseados() as integer
    protegidas = rutasProtegidas()
    total = 0
    liberado = 0
    for each a in listarCache()
        if protegidas.DoesExist(a.ruta)
            total = total + a.bytes
        else if m.fs.Delete(a.ruta)
            liberado = liberado + a.bytes
        else
            total = total + a.bytes
        end if
    end for
    m.top.bytesEnCache = total
    return liberado
end function

' Borra hasta que el total quede por debajo de `objetivo`: primero lo que no
' esta en la lista, luego lo deseado mas viejo. Nunca el temporal activo.
sub desalojar(objetivo as integer)
    protegidas = rutasProtegidas()
    archivos = listarCache()
    total = 0
    for each a in archivos
        total = total + a.bytes
    end for
    if total <= objetivo then return

    libres = []
    viejos = []
    rutaActiva = ""
    if m.activo <> "" then rutaActiva = "cachefs:/tmp_" + huellaDe(m.activo)
    for each a in archivos
        if a.ruta <> rutaPlaylistCache() and a.ruta <> rutaActiva
            if protegidas.DoesExist(a.ruta)
                viejos.Push(a)
            else
                libres.Push(a)
            end if
        end if
    end for
    ordenarPorAntiguedad(libres)
    ordenarPorAntiguedad(viejos)
    orden = []
    orden.Append(libres)
    orden.Append(viejos)

    for each a in orden
        if total <= objetivo then exit for
        if m.fs.Delete(a.ruta) then total = total - a.bytes
    end for
    m.top.bytesEnCache = total
end sub

sub ordenarPorAntiguedad(arr as object)
    ' insercion simple: la cache tiene decenas de archivos, no miles
    n = arr.Count()
    for i = 1 to n - 1
        actual = arr[i]
        j = i - 1
        while j >= 0 and arr[j].mtime > actual.mtime
            arr[j + 1] = arr[j]
            j = j - 1
        end while
        arr[j + 1] = actual
    end for
end sub

sub limpiarTemporales()
    lista = m.fs.GetDirectoryListing("cachefs:/")
    if lista = invalid then return
    for each nombre in lista
        if Left(nombre, 4) = "tmp_" then m.fs.Delete("cachefs:/" + nombre)
    end for
end sub

function ahoraMs() as integer
    if m.reloj = invalid then m.reloj = CreateObject("roTimespan")
    return m.reloj.TotalMilliseconds()
end function
