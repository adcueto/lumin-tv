"""Genera vistas Markdown de backlog.json; no lee ni cambia código de producto."""
import json
import re
from collections import Counter
from pathlib import Path

BASE=Path(__file__).resolve().parent
DOCS=BASE.parent
DATA=json.loads((BASE/'backlog.json').read_text(encoding='utf-8'))
TASKS=DATA['tareas']; REQS=DATA['requisitos']
LABEL={'verificado':'🟢 VERIFICADO ACOTADO','parcial':'🟡 PARCIAL','decision':'🟡 DECISIÓN','correcciones':'🔴 CORRECCIONES','pendiente':'⚪ PENDIENTE','diferido':'🔵 DIFERIDO'}
TI={t['id']:t for t in TASKS}; RI={r['id']:r for r in REQS}
assert len(TI)==len(TASKS) and len(RI)==len(REQS)
def walk(i,seen):
    assert i not in seen,('Dependencias circulares',i)
    for x in TI[i]['dependencias']:walk(x,seen+[i])
for t in TASKS:
    assert t['estado'] in LABEL
    assert set(t['dependencias'])<=TI.keys()
    assert set(t['requisitos'])<=RI.keys()
    assert t['estado']!='verificado' or t['evidencia']
    walk(t['id'],[])
assert RI.keys()=={r for t in TASKS for r in t['requisitos']}
def esc(s):return str(s).replace('|','/').replace('\n',' ')
def tasklink(i):return f'[{i}](17-backlog-maestro.md#{i.lower()})'
def req_links(ids):return ', '.join(f'[{i}](../requisitos/REQUISITOS-PRODUCTO.md#{i.lower()})' for i in ids)
def evidence(p):
    if not p:return 'Sin evidencia de cierre; criterio pendiente.'
    assert p.startswith('docs/')
    return f'[{p}](../{p[5:]})'
def render(parts):
    text='\n'.join(parts)+'\n'
    text=re.sub(r'(?m)^(#{1,6} .+)\n(?!\n)',r'\1\n\n',text)
    text=re.sub(r'(?m)(?<=\S)\n(#{1,6} )',r'\n\n\1',text)
    return text
header=f"Fecha: {DATA['fecha']} · Versión: {DATA['version']} · Responsable: 00 — Coordinación y QA.\n\nÚltimo SHA revisado: `{DATA['ultimo_sha_revisado']}`. No es una consulta en vivo a GitHub.\n"

back=['# Backlog maestro — LUMIN TV',header,
'## Cómo usarlo\n\nFuente editable de tareas/requisitos: [backlog.json](backlog.json). Esta vista, los requisitos y el semáforo se generan con `python actualizar_tablero.py`; no editar sus tablas por separado. IDs BL-* son nuevos y no reutilizan los LTV-* del plan histórico. Cambiar estado requiere evidencia, SHA y responsable; no basta un reporte verbal de finalización.',
'Registrar lo pendiente no lo autoriza. `actual` señala correcciones/documentación dentro del encargo vigente; `planificado` requiere el encargo correspondiente; `diferido` no se activa ahora. Los responsables futuros 02/03 son propuestas hasta asignación. No se inventaron fechas ni estimaciones.',
'Prioridades: P0 = integridad/seguridad o condición de cierre del bloque aplicable; P1 = modernización/operación; P2 = expansión. Una prioridad P0 en B4 no autoriza saltarse el diseño o la transición de B3.',
'## Índice de tareas\n\n| ID | Bloque | Tarea | Estado | Prioridad | Responsable |\n|---|---|---|---|---|---|']
for t in TASKS:
    back.append(f"| [{t['id']}](#{t['id'].lower()}) | {esc(t['bloque'])} | {esc(t['titulo'])} | {LABEL[t['estado']]} | {t['prioridad']} | {esc(t['responsable'])} |")
back+=['\n## Fichas y criterios de cierre']
for t in TASKS:
    back += [f"\n<a id=\"{t['id'].lower()}\"></a>\n### {t['id']} — {t['titulo']}\n",
        f"**Estado:** {LABEL[t['estado']]} · **Prioridad:** {t['prioridad']} · **Bloque:** {t['bloque']} · **Alcance:** {t['alcance']}.",
        f"\n**Responsable:** {t['responsable']}. **Dependencias:** {', '.join(tasklink(i) for i in t['dependencias']) or 'Sin dependencia técnica listada; respetar el encargo y las decisiones aplicables.'}",
        f"\n**Requisitos:** {req_links(t['requisitos'])}.",
        f"\n**Aceptación:** {t['aceptacion']}",
        f"\n**Evidencia/referencia:** {evidence(t['evidencia'])}"]
    if t['hallazgo']:back.append(f"\n**Hallazgo:** {t['hallazgo']}.")
    if t['sha_evidencia']:back.append(f"\n**SHA al que se refiere esa evidencia:** `{t['sha_evidencia']}`.")
back+=['\n## Regla de cierre\n\n00 registra el dictamen por alcance después de revisar la entrega. Si hay un nuevo SHA, evaluar qué tareas afecta y reabrir lo necesario. Pruebas de equipo físico, CI y producción llevan evidencia propia. No cerrar padres automáticamente porque una subtarea esté verde. El manifiesto de consolidación acredita copias, no funcionalidad del producto.']
(BASE/'17-backlog-maestro.md').write_text(render(back),encoding='utf-8')

counts=Counter(t['estado'] for t in TASKS)
dash=['# Semáforo del proyecto — LUMIN TV',header,
f"**Estado global:** {DATA['estado_global']}",
'## Leyenda\n\n| Señal | Significado |\n|---|---|\n| 🟢 Verde | Verificado solo para el alcance/evidencia de la tarea. |\n| 🟡 Amarillo | Parcial o decisión pendiente; no implica que un agente esté ejecutándolo ahora. |\n| 🔴 Rojo | Corrección identificada pendiente de cierre. |\n| ⚪ Blanco | No iniciado/no probado; revisar dependencias antes de asignar. |\n| 🔵 Azul | Futuro diferido; sin encargo de implementación. |',
'## Resumen de tareas\n\nLos conteos son inventario, **no porcentaje de avance ni estimación de esfuerzo**.\n\n| Estado | Tareas |\n|---|---|']
for s in LABEL:dash.append(f'| {LABEL[s]} | {counts[s]} |')
dash.append(f'| **Total** | **{len(TASKS)}** |')
dash+=['\n## Semáforo por bloque\n\nLa señal es la condición más restrictiva registrada en cada bloque; leer los pendientes. Un bloque compuesto no recibe verde porque tenga una prueba aprobada.\n\n| Bloque | Señal | Verificado | Parcial/decisión | Correcciones | Pendiente | Diferido |']
for b in dict.fromkeys(t['bloque'] for t in TASKS):
    c=Counter(t['estado'] for t in TASKS if t['bloque']==b)
    signal='🔴 CORRECCIONES' if c['correcciones'] else ('🟡 INCOMPLETO' if c['parcial']+c['decision'] or (c['verificado'] and c['pendiente']) else ('⚪ PENDIENTE' if c['pendiente'] else ('🔵 DIFERIDO' if c['diferido'] else '🟢 ALCANCE VERIFICADO')))
    dash.append(f"| {b} | {signal} | {c['verificado']} | {c['parcial']+c['decision']} | {c['correcciones']} | {c['pendiente']} | {c['diferido']} |")
dash+=['\n## Siguiente trabajo concreto\n\n| Tarea | Responsable | Cierre esperado |\n|---|---|---|']
for t in TASKS:
    if t['alcance']=='actual' and t['estado'] in ('correcciones','parcial'):
        dash.append(f"| {tasklink(t['id'])} — {t['titulo']} | {t['responsable']} | {esc(t['aceptacion'])} |")
dash+=['\n## Decisiones del propietario\n\n| Tarea | Decisión | Dependencias |\n|---|---|---|']
for t in TASKS:
    if t['estado']=='decision':dash.append(f"| {tasklink(t['id'])} | {esc(t['titulo'])} | {', '.join(tasklink(i) for i in t['dependencias']) or 'Definir con el equipo'} |")
dash+=['\n## Qué sí está comprobado\n\n| Tarea | Alcance exacto | Evidencia |\n|---|---|---|']
for t in TASKS:
    if t['estado']=='verificado':dash.append(f"| {tasklink(t['id'])} | {esc(t['aceptacion'])} | {evidence(t['evidencia'])} |")
dash+=['\n## Qué sigue sin verificarse\n\nRoku físico, nueva persistencia PostgreSQL, migración/rollback implementados, frontend nuevo, autenticación por correo nueva, multiempresa operativa y módulos comerciales. La operación previa informada por Adrián no sustituye validar estos cambios.',
'\n## Actualización\n\n01 entrega SHA y evidencia por BL/QA; 00 evalúa y actualiza backlog.json, incrementa versión/fecha y regenera las vistas. 02/03 solo actualizan por el canal de entrega asignado. No hay sincronización automática con GitHub ni monitoreo de chats. El [documento común](16-coordinacion-agentes.md) define roles y autorizaciones; este tablero registra avance.',
'\n[Backlog detallado](17-backlog-maestro.md) · [Requisitos](../requisitos/REQUISITOS-PRODUCTO.md) · [Fuente de datos](backlog.json).']
(BASE/'18-semaforo.md').write_text(render(dash),encoding='utf-8')

spec=['# Requisitos de producto — LUMIN TV',header,
'## Objetivo y alcance\n\nMejorar LUMIN TV existente como plataforma de anuncios, listas y turnos por sucursal. Conservar Roku y la integración POS; preparar la base comercial futura. Este catálogo documenta necesidades y criterios, **no declara implementado el producto ni aprueba todo el roadmap**.',
'Instrucciones actuales del propietario y documento común prevalecen sobre el brief histórico. B1/B2, revisión del diseño B3 y correcciones de la entrega B5a son el foco de QA; el nuevo panel está en propuesta y los demás alcances B4–B8 siguen planificados; suscripciones, portal del dueño, alta pública, web, nuevos giros y Android siguen diferidos. La implementación B3 requiere cerrar diseño y encargo. No se hacen cambios en LUMIA.',
'## Usuarios y límites\n\n- Hoy: propietario/admin LUMIN, operadores de sucursal, TVs Roku e integración POS existente. El servidor usa sesiones; el flujo nuevo de correo aún no está implementado/verificado.\n- Futuro: administrador de empresa, operador restringido, dispositivo con credencial propia y propietario de plataforma con sesión separada.\n- LUMIN será el piloto persistente inicial. Empresas de prueba solo en entornos aislados. El servidor heredado no se presenta como multiempresa comercial.',
f'## Fuentes y precedencia\n\n- Conversación del propietario: preservar operación, navegación por secciones, correo por código, PostgreSQL, separación de SaaS futuro y exclusión de editor/plantillas.\n- [Brief íntegro](../coordinacion/08-encargo-original.txt): requisitos amplios y propuestas comerciales históricas.\n- [Plan por bloques](../coordinacion/10-diagnostico-y-plan-modernizacion.md): antecedentes B1–B8; las revisiones posteriores prevalecen en contradicciones (por ejemplo, medios permanecen locales en B3).\n- [Coordinación vigente](../coordinacion/16-coordinacion-agentes.md) y [último QA](../{DATA["informe_qa"][5:]}): alcance y limitaciones.\n- Estado de implementación únicamente en el [semáforo](../coordinacion/18-semaforo.md); no duplicarlo en los requisitos.',
'## Exclusiones y propuestas aún no aprobadas\n\nNo desarrollar editor gráfico/plantillas ni generación de anuncios como parte de esta modernización. La configuración de layouts/turnos no equivale a un editor tipo Canva. No reconstruir el POS para vender TV a otro giro. IA se registra solo como exploración. No anunciar compatibilidad universal, ventas atribuidas ni un SLA sin evidencia. Los precios/complementos del brief son propuestas; no son tarifas vigentes ni autorización de cobro. El nombre comercial y su disponibilidad requieren comprobación antes de elegirlos.',
'## Catálogo trazable\n\nCada requisito tiene aceptación observable y tareas. Los criterios amplios deben concretarse en el encargo de implementación antes de programar; no inventar contratos, umbrales o decisiones de negocio.']
for r in REQS:
    taskids=[t['id'] for t in TASKS if r['id'] in t['requisitos']]
    spec += [f"\n<a id=\"{r['id'].lower()}\"></a>\n### {r['id']} — {r['area']}\n",f"**Requisito:** {r['requisito']}",f"\n**Aceptación:** {r['aceptacion']}",f"\n**Fase:** {r['fase']}.",f"\n**Origen:** {r['fuente']}.", '\n**Tareas:** '+', '.join(f'[{i}](../coordinacion/17-backlog-maestro.md#{i.lower()})' for i in taskids)+'.']
spec+=['\n## Reglas para cambiar requisitos\n\nConservar IDs. Añadir o revisar un requisito con fuente, motivo, impacto en contratos/datos y tareas afectadas; actualizar la fuente backlog.json y regenerar. Un cambio de aceptación no cierra retroactivamente un hallazgo. Las decisiones del propietario deben quedar identificadas y no deducirse de que la propuesta esté escrita.','\n## Pendientes de definición\n\nTiempos/umbrales físicos, formatos y tamaños, capacidad/costos, entorno de correo, números/permisos D1/D2, política de recuperación y ventana de corte. Futuro: precios/impuestos, cobro manual o pasarela, gracia de pago, cancelaciones y tolerancia offline. Ver las tareas de decisiones y comerciales; ninguna se considera resuelta por este catálogo.']
(DOCS/'requisitos').mkdir(exist_ok=True)
(DOCS/'requisitos/REQUISITOS-PRODUCTO.md').write_text(render(spec),encoding='utf-8')
print(json.dumps({'requisitos':len(REQS),'tareas':len(TASKS),'estados':dict(counts),'cobertura':'completa','dependencias':'sin ciclos'},ensure_ascii=False))
