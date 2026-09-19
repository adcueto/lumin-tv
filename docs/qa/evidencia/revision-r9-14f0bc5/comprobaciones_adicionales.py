"""QA26: ejecuta SQL del candidato en el cluster sintetico exclusivo de QA."""
from pathlib import Path
import sys, os, json, threading, time
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT/'candidato/servidor/ensayos_b3'))
import psycopg
import test_ensayo_destinos as d
from comun import preparar_base, dsn_rol, contexto, EMPRESA_A
assert '127.0.0.1:55439' in os.environ['LUMIN_ENSAYO_PG']
results = {}
def setup():
    preparar_base()
    d.montar(d.DDL_REV8)
params = {'p':d.TV_PLAZA,'emp':EMPRESA_A,'l':d.LISTA_PLAZA,'v':1}
setup()
with psycopg.connect(dsn_rol('lumin_migracion'), autocommit=True) as c:
    first=c.execute(d.SQL_ENTREGAR,params).fetchone()[0]
    trace=[]
    applied=first
    for _ in range(3):
        with c.transaction():
            c.execute('UPDATE pantalla_e SET entrega_rec=%s WHERE id=%s AND (entrega_rec IS NULL OR entrega_rec < %s)',(applied,d.TV_PLAZA,applied))
            applied=c.execute(d.SQL_ENTREGAR,params).fetchone()[0]
        trace.append(c.execute('SELECT entrega_env,entrega_rec FROM pantalla_e WHERE id=%s',(d.TV_PLAZA,)).fetchone())
    results['consultas_sin_cambio']={'env_rec':trace,'filas_historial':c.execute('SELECT count(*) FROM pantalla_entrega').fetchone()[0]}
    assert all(env==rec+1 for env,rec in trace)
    try:
        c.execute('DELETE FROM lista_e WHERE id=%s',(d.LISTA_PLAZA,))
    except psycopg.Error as e:
        results['borrar_lista_referenciada']={'sqlstate':e.sqlstate,'mensaje':e.diag.message_primary,'columna':e.diag.column_name}
        assert e.sqlstate=='23502' and e.diag.column_name=='id'
    else:
        raise AssertionError('No se reprodujo el fallo de borrado')

setup()
# Mismo SQL, dos peticiones concurrentes como lumin_app. La primera mantiene
# la entrega sin commit para demostrar el choque de max(seq)+1 de forma determinista.
with psycopg.connect(dsn_rol('lumin_app')) as a, psycopg.connect(dsn_rol('lumin_app')) as b:
    contexto(a.cursor(),empresa=EMPRESA_A)
    contexto(b.cursor(),empresa=EMPRESA_A)
    pid=b.info.backend_pid
    n=a.execute(d.SQL_ENTREGAR,params).fetchone()[0]
    outcome={}
    def second():
        try:
            outcome['seq']=b.execute(d.SQL_ENTREGAR,params).fetchone()[0]
            b.commit()
        except psycopg.Error as e:
            outcome.update(sqlstate=e.sqlstate,mensaje=e.diag.message_primary)
            b.rollback()
    t=threading.Thread(target=second)
    t.start()
    blocked=False
    with psycopg.connect(dsn_rol('lumin_migracion'),autocommit=True) as observer:
        for _ in range(100):
            row=observer.execute('SELECT wait_event_type FROM pg_stat_activity WHERE pid=%s',(pid,)).fetchone()
            if row and row[0]=='Lock':
                blocked=True
                break
            time.sleep(.05)
    a.commit()
    t.join(10)
    assert not t.is_alive() and blocked and outcome.get('sqlstate')=='23505',outcome
    results['entrega_concurrente']={'primera':n,'segunda':outcome,'bloqueo_observado':blocked}

path=ROOT/'adicionales-resultados.json'
path.write_text(json.dumps(results,indent=2,ensure_ascii=False),encoding='utf-8')
print(path.read_text(encoding='utf-8'))
