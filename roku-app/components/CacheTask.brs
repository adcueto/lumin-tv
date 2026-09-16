' CacheTask — copia el contenido de la lista a cachefs:/ para sobrevivir una
' caida de internet CON LA APP ABIERTA.
'
' Limites reales de Roku, verificados en su documentacion:
'   - cachefs: vive en RAM. Se pierde al REINICIAR el equipo y el sistema la
'     desaloja cuando otra app necesita espacio. Sobrevive a cerrar la app.
'   - tmp: se borra al cerrar la app. No sirve para esto.
' Por eso esta cache NO promete reproducir sin internet tras reiniciar la TV.
'
' Reglas (revisadas tras B1-QA-01 y B1-QA-02):
'   - PRESUPUESTO ANTES Y DURANTE. Antes de bajar se pregunta el tamano (HEAD);
'     si no cabe, se desaloja primero; si aun asi no cabe, no se baja. Durante
'     la descarga se vigila el temporal cada 2 s: si rebasa el tope por archivo
'     o el presupuesto restante, se cancela. Al confirmar, se revalida el total.
'   - REINTENTOS ACOTADOS. Una descarga fallida vuelve a la cola con espera
'     creciente (30 s, 60, 120, 240, 300) hasta 5 intentos. Un archivo que no
'     existe (404) o no cabe por tamano no se reintenta.
'   - TRABAJOS OBSOLETOS. Si mientras baja llega una lista nueva y este archivo
'     ya no esta en ella, se cancela.
'   - Descarga a nombre temporal y renombra al final: un archivo con nombre
'     definitivo esta COMPLETO. Nunca se reproduce uno a medias.
'   - Desalojo: primero lo que ya no esta en la lista, luego lo mas viejo.

sub init()
    m.top.functionName = "ejecutar"
end sub

sub ejecutar()
    m.TOPE_TOTAL = 250 * 1024 * 1024      ' 250 MB en RAM compartida: conservador
    m.MARGEN = 20 * 1024 * 1024           ' reservado para la reproduccion en curso
    m.TOPE_ARCHIVO = 80 * 1024 * 1024
    m.TASA_MINIMA_BPS = 8 * 1024          ' 8 KB/s durante 20 s => descarga colgada
    m.PERIODO_TASA_S = 20
    m.MAX_INTENTOS = 5

    m.fs = CreateObject("roFileSystem")
    m.port = CreateObject("roMessagePort")
    m.top.observeField("deseados", m.port)

    limpiarTemporales()
    m.top.bytesEnCache = bytesEnCache()

    m.cola = []            ' [{url, intentos, noAntesDe}]
    m.deseadas = {}        ' url -> true

    while true
        ' ---- esperar: sin trabajo, hasta que llegue algo; con trabajo diferido,
        '      hasta que le toque; con trabajo listo, seguir de inmediato ----
        espera = milisegundosHastaElSiguiente()
        if espera < 0
            msg = wait(0, m.port)
        else if espera > 0
            msg = wait(espera, m.port)
        else
            msg = m.port.GetMessage()
        end if
        if type(msg) = "roSGNodeEvent" and msg.getField() = "deseados"
            aplicarDeseados(msg.getData())
        end if

        it = siguienteListo()
        if it <> invalid
            ruta = rutaDeCache(it.url)
            if m.fs.Exists(ruta)
                m.top.listo = {url: it.url, ruta: ruta}
            else
                resultado = descargar(it.url, ruta)
                if resultado = "ok"
                    revalidarTotal()
                    m.top.listo = {url: it.url, ruta: ruta}
                else if resultado <> "obsoleto"
                    m.top.fallo = {url: it.url, motivo: resultado, intento: it.intentos + 1}
                    if esReintentable(resultado) and it.intentos + 1 < m.MAX_INTENTOS
                        it.intentos = it.intentos + 1
                        it.noAntesDe = ahoraMs() + esperaReintento(it.intentos)
                        m.cola.Push(it)
                    end if
                end if
            end if
        end if
    end while
end sub

' ---- cola ----

sub aplicarDeseados(d as object)
    ' La lista nueva reemplaza la cola. Se conservan los intentos y esperas de
    ' lo que sigue deseado, para no reiniciar el retroceso a cada latido.
    previos = {}
    for each x in m.cola
        previos[x.url] = x
    end for
    m.cola = []
    m.deseadas = {}
    if d <> invalid and d.lista <> invalid
        for each it in d.lista
            if it.url <> invalid and it.url <> ""
                m.deseadas[it.url] = true
                if not m.fs.Exists(rutaDeCache(it.url))
                    if previos.DoesExist(it.url)
                        m.cola.Push(previos[it.url])
                    else
                        m.cola.Push({url: it.url, intentos: 0, noAntesDe: 0})
                    end if
                end if
            end if
        end for
    end if
    desalojar(m.TOPE_TOTAL)
end sub

function siguienteListo() as dynamic
    ahora = ahoraMs()
    for i = 0 to m.cola.Count() - 1
        if m.cola[i].noAntesDe <= ahora
            it = m.cola[i]
            m.cola.Delete(i)
            return it
        end if
    end for
    return invalid
end function

' -1 = nada en cola; 0 = hay algo listo; >0 = ms hasta el mas proximo
function milisegundosHastaElSiguiente() as integer
    if m.cola.Count() = 0 then return -1
    ahora = ahoraMs()
    minimo = -1
    for each x in m.cola
        falta = x.noAntesDe - ahora
        if falta <= 0 then return 0
        if minimo < 0 or falta < minimo then minimo = falta
    end for
    if minimo > 5000 then minimo = 5000
    return minimo
end function

function esReintentable(motivo as string) as boolean
    if motivo = "demasiado_grande" then return false
    if motivo = "http_404" or motivo = "http_403" or motivo = "http_410" then return false
    return true
end function

function esperaReintento(intento as integer) as integer
    ' 30 s, 60, 120, 240, tope 300
    ms = 30000
    for i = 2 to intento
        ms = ms * 2
    end for
    if ms > 300000 then ms = 300000
    return ms
end function

' ---- descarga con presupuesto ----

function descargar(url as string, destino as string) as string
    ' 1. tamano anunciado, para decidir ANTES de gastar red y RAM
    tamano = tamanoRemoto(url)
    if tamano > m.TOPE_ARCHIVO then return "demasiado_grande"

    ' 2. presupuesto: si no cabe, desalojar; si aun asi no cabe, esperar
    disponible = m.TOPE_TOTAL - m.MARGEN - bytesEnCache()
    if tamano > 0 and tamano > disponible
        desalojar(m.TOPE_TOTAL - m.MARGEN - tamano)
        disponible = m.TOPE_TOTAL - m.MARGEN - bytesEnCache()
        if tamano > disponible then return "sin_espacio"
    end if
    if disponible <= 0 then return "sin_espacio"
    topeEsteArchivo = m.TOPE_ARCHIVO
    if disponible < topeEsteArchivo then topeEsteArchivo = disponible

    temporal = "cachefs:/tmp_" + huellaDe(url)
    if m.fs.Exists(temporal) then m.fs.Delete(temporal)

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
        if type(evento) = "roUrlEvent"
            exit while
        end if
        ' a) tope de tiempo
        if ahoraMs() - inicio > 600000
            xfer.AsyncCancel()
            borrarSiExiste(temporal)
            return "tiempo_agotado"
        end if
        ' b) presupuesto: el temporal no puede rebasar su tope
        st = m.fs.Stat(temporal)
        if st <> invalid and st.size <> invalid and st.size > topeEsteArchivo
            xfer.AsyncCancel()
            borrarSiExiste(temporal)
            if st.size > m.TOPE_ARCHIVO then return "demasiado_grande"
            return "sin_espacio"
        end if
        ' c) trabajo obsoleto: llego una lista nueva y este archivo ya no esta
        msg = m.port.GetMessage()
        if type(msg) = "roSGNodeEvent" and msg.getField() = "deseados"
            aplicarDeseados(msg.getData())
            if not m.deseadas.DoesExist(url)
                xfer.AsyncCancel()
                borrarSiExiste(temporal)
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

' Content-Length por HEAD, con tope de 8 s. 0 = desconocido.
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
        ' se cuentan tambien los temporales: ocupan RAM igual
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
    ' tras confirmar un archivo: si por lo que sea se rebaso, corregir ya
    if bytesEnCache() > m.TOPE_TOTAL then desalojar(m.TOPE_TOTAL)
end sub

' Borra hasta que el total quede por debajo de `objetivo`. Protege lo que
' sigue en la lista mientras haya otra cosa que borrar; nunca borra temporales
' en curso (no hay: la descarga es de uno en uno y este metodo no corre dentro).
sub desalojar(objetivo as integer)
    archivos = listarCache()
    total = 0
    for each a in archivos
        total = total + a.bytes
    end for
    if total <= objetivo then return

    protegidas = {}
    for each u in m.deseadas.Keys()
        protegidas[rutaDeCache(u)] = true
    end for

    ' dos grupos ordenados por separado, para que un protegido viejo nunca
    ' se borre antes que un no protegido reciente
    libres = []
    protegidos = []
    for each a in archivos
        if a.temporal or not protegidas.DoesExist(a.ruta)
            libres.Push(a)
        else
            protegidos.Push(a)
        end if
    end for
    ordenarPorAntiguedad(libres)
    ordenarPorAntiguedad(protegidos)
    orden = []
    orden.Append(libres)
    orden.Append(protegidos)

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
