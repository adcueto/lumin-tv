# LUMIN TV — índice del proyecto

Raíz: `C:/Users/adcueto/Claude/lumin-tv`. Consolidación documental local: 2026-09-16.

## Empezar aquí

- **[Semáforo de avance](coordinacion/18-semaforo.md)**: qué está verificado, qué requiere corrección y qué sigue pendiente.
- **[Backlog maestro](coordinacion/17-backlog-maestro.md)**: 84 tareas con responsables, dependencias y criterios de cierre (catálogo; consultar versión en el tablero).
- **[Requisitos del producto](requisitos/REQUISITOS-PRODUCTO.md)**: 36 requisitos trazables (catálogo; consultar versión en el tablero).
- [Fuente editable de seguimiento](coordinacion/backlog.json); regenerar las vistas con `python docs/coordinacion/actualizar_tablero.py`.

- [Instrucciones comunes](../AGENTS.md) y [entrada Claude](../CLAUDE.md).
- [Coordinación vigente v1.7](coordinacion/16-coordinacion-agentes.md): roles, tablero, decisiones y formato de mensajes.
- [Último informe QA registrado](qa/informes/25-qa-B3-rev7-RF26-050cc2d.md).

## Requisitos recientes

- [RF-26 — Playlists por TV y grupo](requisitos/RF-26-playlists-por-tv-y-grupo.md): solicitud del propietario del 2026-09-19; diseño e implementación pendientes.

## Estructura

```text
lumin-tv/
  AGENTS.md
  CLAUDE.md
  servidor/                     # backend y pruebas de producto
  roku-app/                     # reproductor Roku
  vigilante/                    # componente existente
  docs/
    INDICE-PROYECTO.md
    coordinacion/               # coordinación vigente, entregas y mensajes
      intercambio/
      historico-codex/           # encargos y análisis iniciales conservados
    requisitos/                 # catálogo RF/RNF
    qa/
      informes/                 # dictámenes por SHA
      evidencia/                # resultados, hashes y ejecutores
    arquitectura/
      referencias/              # copias identificadas de diseños/entregas
    investigacion/              # mercado, costos y decisiones de producto
```

[QA y evidencia](qa/README.md) · [Arquitectura: referencias](arquitectura/README.md) · [Intercambio](coordinacion/intercambio/README.md) · [Entrada de coordinación](coordinacion/LEEME-PRIMERO.md).

Se conservaron los archivos existentes de Claude y la estructura del código. Sus diseños vigentes se consultan en el SHA candidato. La reorganización no modifica el producto ni su dictamen, y no publica estos documentos en GitHub automáticamente.

La carpeta anterior de OneDrive queda como archivo histórico. Los enlaces absolutos de los informes antiguos son parte de la evidencia original; usar este índice para encontrar sus copias en el repositorio.
