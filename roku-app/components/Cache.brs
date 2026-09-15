' Cache.brs — funciones compartidas entre la escena y CacheTask.
' Las dos deben calcular EXACTAMENTE el mismo nombre para la misma URL.

function rutaDeCache(url as string) as string
    return "cachefs:/lumin_" + huellaDe(url) + extensionDeUrl(url)
end function

function huellaDe(texto as string) as string
    ba = CreateObject("roByteArray")
    ba.FromAsciiString(texto)
    digest = CreateObject("roEVPDigest")
    digest.Setup("sha1")
    return digest.Process(ba)
end function

function extensionDeUrl(url as string) as string
    limpio = url
    q = limpio.Instr("?")
    if q >= 0 then limpio = Left(limpio, q)
    p = limpio.Len() - 1
    while p >= 0 and Mid(limpio, p + 1, 1) <> "." and Mid(limpio, p + 1, 1) <> "/"
        p = p - 1
    end while
    if p < 0 or Mid(limpio, p + 1, 1) <> "." then return ""
    ext = LCase(Mid(limpio, p + 1))
    if ext.Len() > 6 then return ""
    return ext
end function

' Ruta donde se guarda la ultima playlist buena. Vive en cachefs, igual que
' los medios: si la cache sobrevivio (cierre de app), la lista tambien; si
' se perdio (reinicio del equipo), tambien. Nunca hay lista sin medios.
function rutaPlaylistCache() as string
    return "cachefs:/lumin_playlist.json"
end function
