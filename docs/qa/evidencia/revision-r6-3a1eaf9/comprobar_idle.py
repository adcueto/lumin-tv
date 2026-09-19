"""Caso adicional QA: conexión de pool idle antes del drenaje. Solo PG aislado."""
import os,sys,json
from pathlib import Path
Q=Path(__file__).resolve().parent
sys.path.insert(0,str(Q/'servidor/ensayos_b3'))
import psycopg
from comun import preparar_base,dsn_rol,EMPRESA_A,mutar_sucursal
from test_ensayo_sesiones import drenar_lumin_app,reabrir_entrada_lumin_app
assert os.environ['LUMIN_ENSAYO_PG']=='postgresql://postgres@127.0.0.1:55432/postgres'
preparar_base()
with psycopg.connect(dsn_rol('lumin_app')) as app:
    pid=app.info.backend_pid
    with psycopg.connect(dsn_rol('lumin_migracion'),autocommit=True) as control:
        inicial=control.execute('SELECT state FROM pg_stat_activity WHERE pid=%s',(pid,)).fetchone()[0]
        drenar_lumin_app(timeout_s=0.1)
        nuevas_bloqueadas=False
        try:
            psycopg.connect(dsn_rol('lumin_app'),connect_timeout=2).close()
        except psycopg.OperationalError:
            nuevas_bloqueadas=True
        # Misma conexión preexistente, que el drenaje consideró segura.
        mutar_sucursal(app,EMPRESA_A,'despues-drenaje-qa','QA',confirmar=True)
        filas=control.execute("SELECT count(*) FROM sucursal WHERE clave='despues-drenaje-qa'").fetchone()[0]
        reabrir_entrada_lumin_app(control)
        out={'estado_inicial':inicial,'drenaje_retorno':True,'conexion_nueva_bloqueada':nuevas_bloqueadas,'escritura_nueva_en_conexion_preexistente':filas}
        assert inicial=='idle' and nuevas_bloqueadas and filas==1
(Q/'idle-resultados.json').write_text(json.dumps(out,indent=2),encoding='utf-8')
print(json.dumps(out))
