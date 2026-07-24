sub init()
    m.top.functionName = "ejecutar"
end sub

sub ejecutar()
    ' Identificador único de esta TV (para que el servidor le asigne su orden)
    di = CreateObject("roDeviceInfo")
    m.idTv = di.GetChannelClientId()

    ' Leer URL guardada en el registro del dispositivo
    ' (de fábrica apunta al servidor de Lumin; con * se puede cambiar)
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

    while true
        ' Revisar si el usuario guardó una URL nueva (esperar hasta 4 s)
        msg = wait(4000, m.port)
        if type(msg) = "roSGNodeEvent" and msg.getField() = "saveUrl"
            nueva = msg.getData()
            if nueva <> invalid and nueva <> ""
                reg = CreateObject("roRegistrySection", "config")
                reg.Write("serverUrl", nueva)
                reg.Flush()
                m.top.serverUrl = nueva
            end if
        end if

        url = m.top.serverUrl
        if url <> invalid and url <> ""
            consultarPlaylist(url)
        end if
    end while
end sub

sub consultarPlaylist(baseUrl as string)
    xfer = CreateObject("roUrlTransfer")
    xfer.SetCertificatesFile("common:/certs/ca-bundle.crt")
    xfer.InitClientCertificates()
    xfer.RetainBodyOnError(false)
    xfer.SetUrl(baseUrl + "/playlist.json?id=" + m.idTv)
    respuesta = xfer.GetToString()
    if respuesta <> invalid and respuesta <> ""
        m.top.playlistJson = respuesta
    else
        m.top.errorMsg = "No hay conexión con " + baseUrl + chr(10) + "Verifica el servidor. Presiona * para cambiar la URL."
    end if
end sub
