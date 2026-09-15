' CacheTask — copia el contenido de la lista a cachefs:/ para sobrevivir una
' caida de internet CON LA APP ABIERTA.
'
' Limites reales de Roku, verificados en su documentacion:
'   - cachefs: vive en RAM. Se pierde al REINICIAR el equipo y el sistema la
'     desaloja cuando otra app necesita espacio. Sobrevive a cerrar la app.
'   - tmp: se borra al cerrar la app. No sirve para esto.
' Por eso esta cache NO promete reproducir sin internet tras reiniciar la TV.
' Lo que si logra: que una caida de red a mitad del dia no deje la pantalla
' cargando, porque lo que ya se reprodujo una vez esta en cache.
'
' Reglas:
'   - Descarga de una en una, con tasa minima: si la red se cae a media
'     descarga, la transferencia se cancela sola en vez de colgarse.
'   - Descarga a un nombre temporal y renombra al final: un archivo que existe
'     con su nombre definitivo esta COMPLETO. Nunca se reproduce uno a medias.
'   - Tope total (MB) y tope por archivo. Al pasarse, se desalojan primero los
'     archivos que ya no estan en la lista, luego los mas viejos.

sub init()
    m.top.functionName = "ejecutar"
end sub

sub ejecutar()
    TOPE_TOTAL_BYTES = 250 * 1024 * 1024   ' 250 MB en RAM compartida: conservador
    TOPE_ARCHIVO_BYTES = 80 * 1024 * 1024  ' un video de salon rara vez pasa de 30 MB
    TASA_MINIMA_BPS = 8 * 1024             ' 8 KB/s durante 20 s => descarga colgada
    PERIODO_TASA_S = 20

    m.fs = CreateObject("roFileSystem")
    m.port = CreateObject("roMessagePort")
    m.top.observeField("deseados", m.port)

    limpiarTemporales()
    m.top.bytesEnCache = bytesEnCache()

    cola = []
    urlsDeseadas = {}

    while true
        ' Si no hay nada que bajar, dormir hasta que la escena mande otra lista
        if cola.Count() = 0
            msg = wait(0, m.port)
        else
            msg = wait(50, m.port)
        end if

        if type(msg) = "roSGNodeEvent" and msg.getField() = "deseados"
            d = msg.getData()
            cola = []
            urlsDeseadas = {}
            if d <> invalid and d.lista <> invalid
                for each it in d.lista
                    if it.url <> invalid and it.url <> ""
                        urlsDeseadas[it.url] = true
                        if not m.fs.Exists(rutaDeCache(it.url))
                            cola.Push(it)
                        end if
                    end if
                end for
            end if
            desalojar(urlsDeseadas, TOPE_TOTAL_BYTES)
        end if

        if cola.Count() > 0
            it = cola.Shift()
            ruta = rutaDeCache(it.url)
            if m.fs.Exists(ruta)
                m.top.listo = {url: it.url, ruta: ruta}
            else
                resultado = descargar(it.url, ruta, TOPE_ARCHIVO_BYTES, TASA_MINIMA_BPS, PERIODO_TASA_S)
                if resultado = "ok"
                    m.top.bytesEnCache = bytesEnCache()
                    m.top.listo = {url: it.url, ruta: ruta}
                else
                    m.top.fallo = {url: it.url, motivo: resultado}
                end if
            end if
        end if
    end while
end sub

' ---- descarga ----

function descargar(url as string, destino as string, topeBytes as integer, tasaMin as integer, periodo as integer) as string
    temporal = "cachefs:/tmp_" + huellaDe(url)
    if m.fs.Exists(temporal) then m.fs.Delete(temporal)

    xfer = CreateObject("roUrlTransfer")
    xfer.SetCertificatesFile("common:/certs/ca-bundle.crt")
    xfer.InitClientCertificates()
    xfer.RetainBodyOnError(false)
    xfer.SetMinimumTransferRate(tasaMin, periodo)
    xfer.SetUrl(url)
    puerto = CreateObject("roMessagePort")
    xfer.SetMessagePort(puerto)

    if not xfer.AsyncGetToFile(temporal) then return "no_inicio"

    ' Tope duro de 10 minutos por archivo, ademas de la tasa minima
    evento = wait(600000, puerto)
    if type(evento) <> "roUrlEvent"
        xfer.AsyncCancel()
        if m.fs.Exists(temporal) then m.fs.Delete(temporal)
        return "tiempo_agotado"
    end if
    if evento.GetResponseCode() <> 200
        if m.fs.Exists(temporal) then m.fs.Delete(temporal)
        return "http_" + evento.GetResponseCode().toStr()
    end if

    st = m.fs.Stat(temporal)
    if st = invalid or st.size = invalid or st.size <= 0
        if m.fs.Exists(temporal) then m.fs.Delete(temporal)
        return "vacio"
    end if
    if st.size > topeBytes
        m.fs.Delete(temporal)
        return "demasiado_grande"
    end if

    ' renombrar al final: si existe con nombre definitivo, esta completo
    if not m.fs.Rename(temporal, destino)
        if m.fs.Exists(temporal) then m.fs.Delete(temporal)
        return "no_renombro"
    end if
    return "ok"
end function

' ---- espacio ----

function listarCache() as object
    salida = []
    lista = m.fs.GetDirectoryListing("cachefs:/")
    if lista = invalid then return salida
    for each nombre in lista
        if Left(nombre, 6) = "lumin_"
            st = m.fs.Stat("cachefs:/" + nombre)
            tam = 0
            mt = 0
            if st <> invalid
                if st.size <> invalid then tam = st.size
                if st.mtime <> invalid then mt = st.mtime.AsSeconds()
            end if
            salida.Push({ruta: "cachefs:/" + nombre, bytes: tam, mtime: mt})
        end if
    end for
    return salida
end function

function bytesEnCache() as integer
    total = 0
    for each a in listarCache()
        total = total + a.bytes
    end for
    return total
end function

sub desalojar(deseadas as object, topeTotal as integer)
    archivos = listarCache()
    total = 0
    for each a in archivos
        total = total + a.bytes
    end for
    if total <= topeTotal then return

    ' rutas que SI siguen en la lista: se protegen mientras se pueda
    protegidas = {}
    for each u in deseadas.Keys()
        protegidas[rutaDeCache(u)] = true
    end for

    ' primero lo que ya no esta en la lista, luego lo mas viejo
    orden = []
    for each a in archivos
        if not protegidas.DoesExist(a.ruta) then orden.Push(a)
    end for
    for each a in archivos
        if protegidas.DoesExist(a.ruta) then orden.Push(a)
    end for
    ordenarPorAntiguedad(orden)

    for each a in orden
        if total <= topeTotal then exit for
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
