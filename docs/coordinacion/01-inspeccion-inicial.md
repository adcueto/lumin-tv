# LTV-QA-001 — Inspección inicial

Fecha: 2026-09-15. Registro de la inspección ANTERIOR al clonado, conservado como historia. BLK-001 quedó resuelto cuando el propietario indicó clonar GitHub. El estado vigente, la arquitectura y los resultados se encuentran en 09-auditoria-codigo.md. Las conclusiones de falta de fuente de este archivo no describen el estado actual.

## Evidencia reproducible

| Comprobación | Resultado observado |
|---|---|
| `Test-Path -LiteralPath 'C:\Users\adcueto\Claude\lumin-tv'` | True |
| `Get-Item` sobre esa ruta | Directorio, sin LinkType ni Target |
| `Get-ChildItem` sobre esa ruta, con `-Force -ErrorAction Stop` | 0 entradas, incluidos archivos ocultos |
| `git -C 'C:\Users\adcueto\Claude\lumin-tv' rev-parse --show-toplevel` | Fatal: not a git repository |
| `git -C 'C:\Users\adcueto\Claude\lumin-tv' status --short --branch` | Fatal: not a git repository |
| AGENTS.md en raíz, Users, usuario, Claude y carpeta principal | No encontrados |
| `Test-Path -LiteralPath 'C:\Users\adcueto\Claude\Lumin\_Proyecto\_Cowork\06-belia-app'` | False |

Estas observaciones preceden a la instalación de este paquete documental. No se buscaron rutas sustitutas de LUMIA. No se accedió a producción, bases de datos ni secretos.

## Inventario y diferencias frente al encargo

| Área | Información aportada | Evidencia de código / resultado |
|---|---|---|
| Aplicación y arquitectura | LUMIN TV existente | Fuente ausente; stack y estructura desconocidos |
| Git | Sin rama/commit aportados | Sin repositorio válido en ruta principal; SHA no disponible |
| GET/POST | Endpoints existentes | Rutas, métodos concretos, esquemas y autorización no verificables |
| Roku | Reproductor existente | Fuentes, versión, contratos y funcionamiento no verificables |
| Android TV/Google TV | Pendiente de desarrollo | No probado; no anunciar disponibilidad |
| Auth, roles, multiempresa | Requisitos del objetivo SaaS | Implementación no evaluada |
| Modelos, migraciones, archivos y trabajos de fondo | Deben aislar empresas | No evaluados |
| Planes, cuotas y complementos | Propuesta funcional y comercial | Implementación no evaluada; precios no publicados |
| Frontend, web y estadísticas | Alcance objetivo | No evaluados; no existen capturas verificadas |
| Integración LUMIA | Opcional, por sucursal | Sin contratos comprobados; ruta de referencia ausente |
| Tests, CI y dispositivos físicos | Necesarios para QA | No ejecutados; sin evidencia aportada |

No se ha demostrado ningún defecto funcional: la ausencia de fuente es un bloqueo de auditoría, no un fallo del producto.

## Registro de incidencias

- LTV-BLK-001, bloqueante, pendiente: falta código en la ruta principal. Cierre: fuente existente disponible, instrucciones leídas, Git identificado y estado de cambios registrado. Responsable de ubicación: propietario; inventario técnico: Claude; verificación: Codex.
- LTV-BLK-002, pendiente para integración: ruta exacta de LUMIA inexistente. Cierre: propietario confirma ubicación accesible o entrega documentación contractual depurada. No bloquea planificación general.

## Siguiente inspección

Leer instrucciones antes de ejecutar scripts. Registrar raíz Git, rama, SHA, archivos modificados y nuevos; no restaurar ni sobrescribir. Identificar manifiestos, rutas, middleware, modelos, migraciones, almacenamiento, jobs, frontend y reproductor Roku. Revisar scripts y configuración de pruebas antes de instalar o ejecutar dependencias. Separar análisis estático de pruebas locales, CI y validación física.
