' QA de recargar REAL, con nodos sustituidos por objetos; no emula Roku fisico.
sub main()
    m.timerFoto = {control: "start"}
    m.timerBuffer = {control: "start"}
    m.timerReintento = {control: "start"}
    m.video = {control: "play"}
    m.estado = {text: ""}
    m.estadoTv = {r: "qa.mp4", c: 0, k: false, e: "", et: 0}
    m.enRespaldo = false
    m.task = {desdeCache: false, conectado: true, consultarAhora: 0}
    recargar()
    print "VIDEO: " + m.video.control
    print "FOTO: " + m.timerFoto.control
    print "VIGILANTE: " + m.timerBuffer.control
    print "REINTENTO: " + m.timerReintento.control
    print "CONSULTAS: " + m.task.consultarAhora.ToStr()
    print "PLAYLIST_ESCENA_VACIA: " + (m.playlistActual = "").ToStr()
end sub
