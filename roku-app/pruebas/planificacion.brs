' Arnes fuera del dispositivo para la PLANIFICACION de CacheTask.brs
' (reintentos, cola, registro, cuarentenas). Ejecuta el codigo BrightScript
' real de components/CacheTask.brs con el interprete brs, sustituyendo solo:
'   - roFileSystem  -> disco falso en memoria (m.fs)
'   - roTimespan    -> reloj controlado (m.reloj)
'   - la transferencia HTTP -> m.simulacion.descargar, que devuelve el
'     resultado que cada prueba decide y anota cuando ocurrio cada intento
'   - Cache.brs     -> Cache_simulado.brs (brs no tiene roEVPDigest)
' No sustituye nada de la logica de CacheTask.brs. Ver correr.py.
'
' Lo que NO cubre: la transferencia real (roUrlTransfer), cachefs:, el nodo
' de video y el comportamiento del reloj del equipo. Eso sigue siendo F1-F21.

sub main()
    m.comprobaciones = 0
    m.fallos = 0

    prueba_R3_B1_01_reintento_autonomo()
    prueba_R3_B1_01_seis_intentos_y_agotado()
    prueba_R3_B1_01_reanimar_al_reconectar()
    prueba_R2_B1_02_reconciliar_durante_la_descarga_no_duplica()
    prueba_R2_B1_02_reconciliar_no_reinicia_intentos()
    prueba_R3_B1_02_sin_espacio_no_se_libera_con_la_misma_lista()
    prueba_R3_B1_02_sin_espacio_se_libera_al_cambiar_la_lista()
    prueba_R3_B1_02_sin_espacio_se_libera_si_se_libero_espacio()
    prueba_404_cuarentena_30_min()
    prueba_url_que_sale_de_la_lista_se_olvida()
    prueba_B5a_vaciar_cache_conserva_la_lista_y_rellena()

    print "RESUMEN: " + m.comprobaciones.ToStr() + " comprobaciones, " + m.fallos.ToStr() + " fallos"
end sub

' ---------------------------------------------------------------- utilerias

sub preparar()
    m.top = {vaciado: 0, bytesEnCache: 0}
    m.fs = nuevoDiscoFalso()
    m.reloj = {ms: 0, TotalMilliseconds: function() as integer
        return m.ms
    end function}
    m.simulacion = {
        respuestas: [],      ' resultados a devolver, en orden; el ultimo se repite
        intentos: [],        ' {url, t} de cada llamada a descargar
        alDescargar: invalid ' lista a aplicar en medio de la descarga (simula reconciliacion)
        descargar: function(url as string, destino as string) as string
            m.intentos.Push({url: url, t: ahoraMs()})
            if m.alDescargar <> invalid then aplicarDeseados(m.alDescargar)
            if m.respuestas.Count() = 0 then return "ok"
            r = m.respuestas[0]
            if m.respuestas.Count() > 1 then m.respuestas.Shift()
            if r = "ok" then escribirArchivo(destino, 1000)
            return r
        end function
    }
    configurar()
end sub

function nuevoDiscoFalso() as object
    return {
        archivos: {}
        Exists: function(ruta as string) as boolean
            return m.archivos.DoesExist(ruta)
        end function
        Delete: function(ruta as string) as boolean
            if not m.archivos.DoesExist(ruta) then return false
            m.archivos.Delete(ruta)
            return true
        end function
        GetDirectoryListing: function(dir as string) as object
            nombres = []
            for each ruta in m.archivos.Keys()
                nombres.Push(Mid(ruta, 10)) ' quita "cachefs:/"
            end for
            return nombres
        end function
        Stat: function(ruta as string) as object
            a = m.archivos[ruta]
            if a = invalid then return invalid
            return {size: a.bytes, mtime: {seg: a.mtime, AsSeconds: function() as integer
                return m.seg
            end function}}
        end function
    }
end function

sub escribirArchivo(ruta as string, bytes as integer)
    m.fs.archivos[ruta] = {bytes: bytes, mtime: ahoraMs() / 1000}
end sub

function lista(urls as object) as object
    l = []
    for each u in urls
        l.Push({url: u})
    end for
    return {lista: l}
end function

' Avanza el reloj y procesa lo que este listo, como haria el bucle real:
' espera lo que diga milisegundosHastaElSiguiente() y luego procesa.
sub avanzar(ms as integer)
    m.reloj.ms = m.reloj.ms + ms
    while procesarSiguiente()
    end while
end sub

function intentosDe(url as string) as integer
    n = 0
    for each i in m.simulacion.intentos
        if i.url = url then n = n + 1
    end for
    return n
end function

function tiemposDe(url as string) as string
    s = ""
    for each i in m.simulacion.intentos
        if i.url = url
            if s <> "" then s = s + ","
            s = s + (i.t / 1000).ToStr()
        end if
    end for
    return s
end function

sub comprobar(condicion as boolean, texto as string)
    m.comprobaciones = m.comprobaciones + 1
    if condicion
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

' R3-B1-01: una sola URL, falla transitoria, NINGUN mensaje mas. El segundo
' intento debe ocurrir solo a los 30 s.
sub prueba_R3_B1_01_reintento_autonomo()
    titulo("R3-B1-01 reintento autonomo a los 30 s sin nuevos mensajes")
    preparar()
    u = "http://s/v/a.mp4"
    m.simulacion.respuestas = ["http_500"]
    aplicarDeseados(lista([u]))
    avanzar(0)
    comprobar(intentosDe(u) = 1, "primer intento inmediato")
    comprobar(m.activo = "", "tras fallar, m.activo queda vacio")
    comprobar(m.cola.Count() = 1 and m.cola[0] = u, "la URL vuelve a la cola (antes: rechazada por creerse activa)")
    e = milisegundosHastaElSiguiente()
    ' la funcion acota la espera a 5 s (el bucle vuelve a mirar); lo que
    ' importa es que NO sea -1 (esperar un mensaje que puede no llegar)
    comprobar(e = 5000, "milisegundosHastaElSiguiente = 5000, no -1 (antes: -1, espera infinita); fue " + e.ToStr())
    avanzar(29999)
    comprobar(intentosDe(u) = 1, "a los 29.999 s todavia no reintenta")
    avanzar(1)
    comprobar(intentosDe(u) = 2, "a los 30 s reintenta sin que llegue ningun mensaje")
end sub

sub prueba_R3_B1_01_seis_intentos_y_agotado()
    titulo("R3-B1-01 secuencia 30/60/120/240/300 s, seis intentos, luego agotado")
    preparar()
    u = "http://s/v/a.mp4"
    m.simulacion.respuestas = ["tiempo"]
    aplicarDeseados(lista([u]))
    avanzar(0)
    ' 20 minutos en pasos de 1 s, sin mensajes
    for i = 1 to 1200
        avanzar(1000)
    end for
    comprobar(intentosDe(u) = 6, "exactamente 6 intentos; fueron " + intentosDe(u).ToStr())
    comprobar(tiemposDe(u) = "0,30,90,210,450,750", "instantes 0,30,90,210,450,750 s; fueron " + tiemposDe(u))
    e = m.registro[u]
    comprobar(e.terminal and e.motivo = "agotado", "estado final: terminal 'agotado'")
    comprobar(milisegundosHastaElSiguiente() = -1, "nada pendiente: el bucle esperaria un mensaje")
end sub

sub prueba_R3_B1_01_reanimar_al_reconectar()
    titulo("agotado se reanima al reconectar, no antes")
    preparar()
    u = "http://s/v/a.mp4"
    m.simulacion.respuestas = ["tiempo"]
    aplicarDeseados(lista([u]))
    avanzar(0)
    for i = 1 to 1200
        avanzar(1000)
    end for
    aplicarDeseados(lista([u]))
    avanzar(60000)
    comprobar(intentosDe(u) = 6, "reconciliar con la misma lista no reanima un agotado")
    m.simulacion.respuestas = ["ok"]
    reanimarAgotados()
    avanzar(0)
    comprobar(intentosDe(u) = 7, "reconectado: intento inmediato")
    comprobar(m.fs.Exists(rutaDeCache(u)), "y esta vez queda en cache")
    comprobar(m.registro[u] = invalid, "el registro olvida lo que ya esta en disco")
end sub

' R2-B1-02: reconciliacion en medio de una descarga que luego falla.
sub prueba_R2_B1_02_reconciliar_durante_la_descarga_no_duplica()
    titulo("R2-B1-02 reconciliar durante la descarga: sin duplicar el activo")
    preparar()
    u = "http://s/v/grande.mp4"
    m.simulacion.respuestas = ["tiempo"]
    m.simulacion.alDescargar = lista([u, "http://s/v/otro.jpg"])
    aplicarDeseados(lista([u]))
    avanzar(0)
    m.simulacion.alDescargar = invalid
    n = 0
    for each c in m.cola
        if c = u then n = n + 1
    end for
    comprobar(n = 1, "la URL aparece una sola vez en la cola; aparecio " + n.ToStr())
    comprobar(m.registro[u].intentos = 1, "un solo intento contado")
    comprobar(m.registro[u].noAntesDe = 30000, "reintento programado a 30 s, no inmediato")
    avanzar(29000)
    comprobar(intentosDe(u) = 1, "no salta la espera")
    avanzar(1000)
    comprobar(intentosDe(u) = 2, "segundo intento a los 30 s")
end sub

sub prueba_R2_B1_02_reconciliar_no_reinicia_intentos()
    titulo("R2-B1-02 reconciliar con la misma lista conserva intentos y espera")
    preparar()
    u = "http://s/v/a.mp4"
    m.simulacion.respuestas = ["tiempo"]
    aplicarDeseados(lista([u]))
    avanzar(0)
    avanzar(30000)
    comprobar(m.registro[u].intentos = 2, "dos intentos")
    antes = m.registro[u].noAntesDe
    for i = 1 to 5
        aplicarDeseados(lista([u]))
        avanzar(0)
    end for
    comprobar(m.registro[u].intentos = 2, "cinco reconciliaciones identicas: siguen siendo 2 intentos")
    comprobar(m.registro[u].noAntesDe = antes, "la fecha del reintento no cambia")
    comprobar(intentosDe(u) = 2, "no se lanzo ninguna descarga extra")
end sub

' R3-B1-02
sub prueba_R3_B1_02_sin_espacio_no_se_libera_con_la_misma_lista()
    titulo("R3-B1-02 sin_espacio no se libera con la misma lista")
    preparar()
    u = "http://s/v/a.mp4"
    m.simulacion.respuestas = ["sin_espacio"]
    aplicarDeseados(lista([u]))
    avanzar(0)
    comprobar(m.registro[u].terminal and m.registro[u].motivo = "sin_espacio", "queda terminal sin_espacio")
    for i = 1 to 10
        aplicarDeseados(lista([u]))
        avanzar(60000)
    end for
    comprobar(intentosDe(u) = 1, "diez reconciliaciones identicas en 10 min: sigue en 1 intento; fueron " + intentosDe(u).ToStr())
    comprobar(m.registro[u].terminal, "sigue terminal")
end sub

sub prueba_R3_B1_02_sin_espacio_se_libera_al_cambiar_la_lista()
    titulo("R3-B1-02 sin_espacio se reintenta al cambiar el conjunto de la lista")
    preparar()
    u = "http://s/v/a.mp4"
    m.simulacion.respuestas = ["sin_espacio"]
    aplicarDeseados(lista([u]))
    avanzar(0)
    m.simulacion.respuestas = ["ok"]
    aplicarDeseados(lista([u, "http://s/v/b.mp4"]))
    avanzar(0)
    comprobar(intentosDe(u) = 2, "lista distinta: nuevo intento de la URL en sin_espacio")
    comprobar(m.fs.Exists(rutaDeCache(u)), "y termina en cache")
end sub

sub prueba_R3_B1_02_sin_espacio_se_libera_si_se_libero_espacio()
    titulo("R3-B1-02 sin_espacio se reintenta si la reconciliacion libero espacio")
    preparar()
    u = "http://s/v/a.mp4"
    m.simulacion.respuestas = ["sin_espacio"]
    aplicarDeseados(lista([u]))
    avanzar(0)
    ' aparece en cache un archivo que no es de la lista (p. ej. de una lista
    ' anterior a un reinicio de la app); la misma lista lo desaloja
    escribirArchivo("cachefs:/lumin_viejo", 50 * 1024 * 1024)
    m.simulacion.respuestas = ["ok"]
    aplicarDeseados(lista([u]))
    avanzar(0)
    comprobar(not m.fs.Exists("cachefs:/lumin_viejo"), "lo no deseado se desalojo")
    comprobar(intentosDe(u) = 2, "espacio liberado de verdad: nuevo intento")
end sub

sub prueba_404_cuarentena_30_min()
    titulo("404 sostenido: un intento, cuarentena de 30 min, luego uno mas")
    preparar()
    u = "http://s/v/borrado.mp4"
    m.simulacion.respuestas = ["http_404"]
    aplicarDeseados(lista([u]))
    avanzar(0)
    for i = 1 to 29
        aplicarDeseados(lista([u]))
        avanzar(60000)
    end for
    comprobar(intentosDe(u) = 1, "29 reconciliaciones en 29 min: un solo intento; fueron " + intentosDe(u).ToStr())
    avanzar(60000)
    comprobar(intentosDe(u) = 2, "a los 30 min, un intento mas")
end sub

sub prueba_url_que_sale_de_la_lista_se_olvida()
    titulo("una URL que sale de la lista se olvida y libera su espacio")
    preparar()
    u = "http://s/v/a.mp4"
    m.simulacion.respuestas = ["ok"]
    aplicarDeseados(lista([u]))
    avanzar(0)
    comprobar(m.fs.Exists(rutaDeCache(u)), "descargado")
    aplicarDeseados(lista(["http://s/v/b.mp4"]))
    comprobar(not m.fs.Exists(rutaDeCache(u)), "al salir de la lista se borra")
    comprobar(m.registro[u] = invalid, "y se olvida su registro")
end sub

' B5a: comando "vaciar cache" del panel
sub prueba_B5a_vaciar_cache_conserva_la_lista_y_rellena()
    titulo("B5a vaciar cache: borra medios, conserva la lista guardada y vuelve a bajar")
    preparar()
    a = "http://s/v/a.mp4"
    b = "http://s/v/b.jpg"
    escribirArchivo(rutaPlaylistCache(), 500)
    m.simulacion.respuestas = ["ok"]
    aplicarDeseados(lista([a, b]))
    avanzar(0)
    comprobar(m.fs.Exists(rutaDeCache(a)) and m.fs.Exists(rutaDeCache(b)), "los dos medios en cache")
    vaciarCache()
    comprobar(not m.fs.Exists(rutaDeCache(a)) and not m.fs.Exists(rutaDeCache(b)), "medios borrados")
    comprobar(m.fs.Exists(rutaPlaylistCache()), "la lista guardada NO se borra")
    comprobar(m.registro.Count() = 0 and m.cola.Count() = 0, "registro y cola vacios")
    comprobar(m.top.vaciado = 1 and m.top.bytesEnCache = 0, "se anuncia el vaciado y 0 bytes")
    ' la escena vuelve a pedir la misma lista
    aplicarDeseados(lista([a, b]))
    avanzar(0)
    comprobar(intentosDe(a) = 2 and intentosDe(b) = 2, "se vuelven a bajar los dos")
    comprobar(m.fs.Exists(rutaDeCache(a)) and m.fs.Exists(rutaDeCache(b)), "y quedan en cache otra vez")
end sub
