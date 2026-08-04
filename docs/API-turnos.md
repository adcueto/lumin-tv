# API de turnos — LUMIN TV

Contrato para sistemas externos (POS / recepción) que anuncian turnos en las
pantallas de las sucursales.

**Base:** `https://tv.luminbelleza.com` (siempre HTTPS; nunca IP directa).

## 1. Autenticación (una vez por sesión)

```
POST /api/login
Content-Type: application/json

{"usuario": "pos-plaza", "contrasena": "********"}
```

Respuesta `200 {"ok":true}` y una cookie de sesión `sesion` (HttpOnly) con
vigencia de ~30 días. El cliente debe conservar y reenviar esa cookie en cada
petición. Si cualquier llamada regresa `401`, la sesión expiró: repetir el
login y reintentar.

Recomendación: usar una cuenta dedicada por sucursal con rol **Usuario**
(se crea desde el panel, tarjeta Usuarios). Ese rol solo puede anunciar en su
propia sucursal; el servidor fuerza la sucursal del lado servidor aunque el
cuerpo diga otra.

## 2. Anunciar turno

```
POST /api/turno        (también acepta PUT)
Content-Type: application/json
Cookie: sesion=...

{
  "sucursal": "plaza-de-la-mujer",
  "numero":   "L142",
  "estacion": "U4",
  "espera":   "5",
  "duracion": 60,
  "proximos": [
    {"numero": "L143", "estacion": "U1"},
    {"numero": "L144", "estacion": "U5"},
    {"numero": "L145", "estacion": "U2"}
  ]
}
```

Respuesta: `200 {"ok":true}`.

### Campos

| Campo    | Tipo   | Obligatorio | Notas |
|----------|--------|-------------|-------|
| sucursal | string | sí (admin)  | CLAVE exacta, ver lista abajo. Con rol Usuario se ignora y se usa la suya. También puede ir como query: `/api/turno?sucursal=...` |
| numero   | string | sí          | Máx. 8 caracteres. Texto libre: "142", "L142", "C42". |
| estacion | string | no          | Máx. 20. Se muestra como "ESTACIÓN {valor}". |
| espera   | string | no          | Minutos estimados. Si va vacío, la franja de espera no se muestra. |
| duracion | número | no          | Segundos en pantalla, 5–300. Por defecto 60. |
| proximos | lista  | no          | Hasta 3 objetos {numero, estacion}. El excedente se descarta. |

### Claves de sucursal

`home` · `plaza-de-la-mujer` · `juriquilla` · `campanario` · `plaza-victoria`

Usar la clave exacta (minúsculas y guiones). Un nombre con espacios como
"Plaza de la Mujer" NO es válido y el turno caería en la sucursal por defecto.

## 3. Comportamiento en pantalla

- El anuncio aparece únicamente en las pantallas de esa sucursal que tengan el
  interruptor **Turnos** activado en el panel.
- Latencia máxima ~4 segundos (las TVs consultan al servidor cada 4 s).
- El panel se desliza desde abajo, permanece `duracion` segundos y se retira
  solo; la publicidad no se interrumpe ni pierde su posición.
- Un nuevo POST mientras el panel está visible lo actualiza al instante y
  reinicia su tiempo. Solo existe "el turno vigente": no hay cola en el
  servidor; la fila visible es la lista `proximos` que envía el POS.
- Cuándo enviar: cada vez que se libere una estación y pase el siguiente turno.

## 4. Ejemplo completo (curl)

```bash
# login (guarda cookie)
curl -c cookies.txt -X POST https://tv.luminbelleza.com/api/login \
  -H "Content-Type: application/json" \
  -d '{"usuario":"pos-plaza","contrasena":"********"}'

# anunciar turno (usa cookie)
curl -b cookies.txt -X POST https://tv.luminbelleza.com/api/turno \
  -H "Content-Type: application/json" \
  -d '{"sucursal":"plaza-de-la-mujer","numero":"L142","estacion":"U4",
       "espera":"5","proximos":[{"numero":"L143","estacion":"U1"}]}'
```

## 5. Manejo de errores sugerido

```
respuesta = post(/api/turno, cuerpo)
si respuesta == 401:
    post(/api/login, credenciales)   # renovar sesión
    respuesta = post(/api/turno, cuerpo)  # un reintento
si respuesta != 200:
    registrar en bitácora y continuar (no bloquear el cobro por la pantalla)
```

El anuncio en pantalla es informativo: ante cualquier fallo, el POS debe
seguir operando con normalidad y solo registrar el error.
