# Control de pantallas Roku desde el POS (protocolo ECP)

Cómo encender las TVs de una sucursal y abrir el canal LUMIN TV sin control
remoto. No requiere instalar nada en las TVs ni pasar por internet: son
peticiones HTTP dentro de la red local.

**Requisito:** el equipo que envía los comandos (servidor del POS, laptop de
recepción o Raspberry) debe estar en la MISMA red WiFi/LAN que las TVs.

## Datos de LUMIN

| Dato | Valor |
|------|-------|
| ID del canal LUMIN TV (tienda) | `782875` |
| Puerto ECP de Roku | `8060` |
| ID si la TV tiene versión sideload | `dev` |

El ID `782875` es el mismo en todas las TVs, porque es el identificador del
canal en la tienda de Roku. Lo que cambia por pantalla es la IP.

## Preparación de cada TV (una vez, con el control remoto)

1. Configuración → Sistema → Energía → **Inicio rápido: ACTIVADO**.
   Sin esto, una TV dormida no responde a comandos de red.
2. Configuración → Sistema → Avanzado → Control por apps móviles →
   **Acceso de red: Predeterminado**.
3. Reservar la IP de la TV en el módem (reservación DHCP por MAC) para que no
   cambie con el tiempo. La IP actual se ve en Configuración → Red → Acerca de.

## Endpoints

Base: `http://{IP_TV}:8060`

| Acción | Método | Ruta |
|--------|--------|------|
| Encender | POST | `/keypress/PowerOn` |
| Apagar | POST | `/keypress/PowerOff` |
| Abrir LUMIN TV | POST | `/launch/782875` |
| Listar apps instaladas | GET | `/query/apps` |
| Ver app activa | GET | `/query/active-app` |
| Info del dispositivo | GET | `/query/device-info` |

Los POST se envían con cuerpo vacío. No hay autenticación (por eso conviene
separar la red de operación de la red de clientas).

## Secuencia correcta de arranque

El orden y la espera importan: si la TV está dormida y se manda `launch`
directo, el comando se pierde.

```
POST /keypress/PowerOn      → esperar 3 s
GET  /query/active-app      → ¿ya está el canal 782875?
POST /launch/782875         → solo si no lo está
```

Ejemplo con curl (una TV):

```bash
IP=192.168.1.45
curl -m 4 -d '' http://$IP:8060/keypress/PowerOn
sleep 3
curl -m 4 -d '' http://$IP:8060/launch/782875
# verificar
curl -m 4 http://$IP:8060/query/active-app
```

Ejemplo en Python (varias TVs, que es el caso real):

```python
import time, urllib.request

TVS = ["192.168.1.45", "192.168.1.46", "192.168.1.47",
       "192.168.1.48", "192.168.1.49"]
CANAL = "782875"

def ecp(ip, ruta):
    req = urllib.request.Request(f"http://{ip}:8060/{ruta}",
                                 method="POST", data=b"")
    urllib.request.urlopen(req, timeout=4)

def abrir_lumin(ip):
    try:
        ecp(ip, "keypress/PowerOn")
        time.sleep(3)
        ecp(ip, f"launch/{CANAL}")
        return True
    except Exception as e:
        print(f"{ip}: sin respuesta ({e})")
        return False

for ip in TVS:
    abrir_lumin(ip)
```

## Notas de implementación

- **Varias pantallas por sucursal:** el POS debe aceptar una LISTA de IPs y
  recorrerlas, no una sola. Un fallo en una TV no debe detener las demás
  (envolver cada una en try/except, timeout de 3-5 s).
- **Sin respuesta:** una TV desconectada de la corriente o del interruptor
  físico no puede encenderse por red. Registrar el fallo y continuar.
- **Reintentos:** limitar a uno por TV en cada disparo; no dejar ciclos
  reintentando indefinidamente.
- **Descubrimiento del ID:** si en alguna TV el canal está instalado por modo
  desarrollador, su ID es `dev`. Para detectarlo automáticamente, consultar
  `GET /query/apps` y buscar la app cuyo nombre contenga "LUMIN".
- **Apagado al cierre (opcional):** `POST /keypress/PowerOff` a cada TV.
- **Seguridad:** el protocolo ECP no pide credenciales. Cualquiera en la misma
  red puede controlar las TVs; conviene una red de operación separada de la
  red de clientas.

## Prueba mínima (antes de integrar)

Desde una terminal en la red del local, con la IP de UNA TV:

```bash
curl -m 4 http://IP-DE-LA-TV:8060/query/apps
```

Debe listar las apps instaladas, incluida LUMIN. Si no responde, revisar en
ese orden: misma red, "Inicio rápido" activado, y acceso de red en
Predeterminado.
