' Sustituto de components/Cache.brs para el arnes fuera del dispositivo.
' El interprete brs no implementa roEVPDigest, asi que la "huella" es la URL
' saneada. Solo importa que sea estable y distinta por URL: CacheTask.brs
' nunca interpreta el nombre, solo lo compara.

function rutaDeCache(url as string) as string
    return "cachefs:/lumin_" + huellaDe(url)
end function

function huellaDe(texto as string) as string
    salida = ""
    for i = 1 to texto.Len()
        c = Mid(texto, i, 1)
        if c = "/" or c = ":" or c = "?" or c = "." then c = "_"
        salida = salida + c
    end for
    return salida
end function

function extensionDeUrl(url as string) as string
    return ""
end function

function rutaPlaylistCache() as string
    return "cachefs:/lumin_playlist.json"
end function
