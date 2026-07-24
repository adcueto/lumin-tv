# Vigilante LUMIN — instalación en Raspberry Pi

Un Raspberry por sucursal, conectado al WiFi del local. Enciende las TVs y abre
LUMIN TV en horario; las apaga al cierre. Nadie vuelve a tocar un control.

## Hardware por sucursal
Raspberry Pi Zero 2 W (recomendado; el Zero W original también sirve), microSD
de 8 GB o más, y fuente USB de 5V. Todo junto ronda los $600-800 MXN.

## Preparar las TVs (una vez, con el control)
1. Configuración → Sistema → Energía → **Inicio rápido: ACTIVADO** — sin esto la
   TV dormida no escucha comandos de red y no podrá encenderse sola.
2. Configuración → Sistema → Avanzado → Control por apps móviles →
   **Acceso de red: Predeterminado**.
3. En el router del local, fija la IP de cada TV (reservación DHCP) para que no
   cambien con el tiempo. Anota esas IPs.

## Preparar el Raspberry
1. En tu computadora instala **Raspberry Pi Imager**, elige el sistema
   "Raspberry Pi OS Lite (32-bit)" y, antes de grabar, en el engrane ⚙️
   configura: nombre de usuario y contraseña, el **WiFi del local**, y
   habilita **SSH**. Graba la microSD.
2. Enchufa el Pi en la sucursal. Desde tu laptop en el mismo WiFi:
   `ssh usuario@raspberrypi.local`
3. Zona horaria: `sudo raspi-config` → Localisation → Timezone →
   America → Mexico_City.
4. Crea la carpeta y copia los dos archivos (desde tu laptop):
   `scp vigilante_lumin.py config.json usuario@raspberrypi.local:/home/usuario/`
5. Edita `config.json` con las IPs reales de las TVs de ESA sucursal y su
   horario: `nano config.json`

## Probar a mano (antes de dejarlo fijo)
```
python3 vigilante_lumin.py
```
Debe listar las TVs y verás en vivo cómo las enciende y abre la app. Ctrl+C
para salir. Prueba rápida de una TV suelta:
`curl -d '' http://IP-DE-LA-TV:8060/keypress/PowerOn`

## Dejarlo automático (systemd)
```
sudo tee /etc/systemd/system/vigilante-lumin.service << 'UNIT'
[Unit]
Description=Vigilante LUMIN
After=network-online.target
Wants=network-online.target

[Service]
ExecStart=/usr/bin/python3 /home/usuario/vigilante_lumin.py
WorkingDirectory=/home/usuario
Restart=always
RestartSec=15

[Install]
WantedBy=multi-user.target
UNIT
sudo systemctl daemon-reload
sudo systemctl enable --now vigilante-lumin
```
Ver su bitácora: `journalctl -u vigilante-lumin -f`

## Notas
- El mismo script corre en cualquier equipo del local que quede encendido
  (por ejemplo la computadora del POS): mismos pasos 4-6, sin comprar nada.
- Si una TV está apagada del interruptor físico o desconectada, ningún
  comando de red puede revivirla — el vigilante lo anota en su bitácora.
- El horario del vigilante conviene 5 minutos antes de abrir y después de
  cerrar (ej. 09:55–20:05) para que las pantallas ya estén listas al abrir.
