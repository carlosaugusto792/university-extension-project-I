"""Recalcula, em SQL (SQLite) e em Python (pandas), os valores citados no relatório
e compara com o valor do relatório. Uso: python conferencia_valores_relatorio.py [pasta_dos_csv]
Requer: pandas. Gera conferencia_valores.csv na mesma pasta."""
import sys, sqlite3, pathlib
import pandas as pd

pasta = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else ".")
ev = pd.read_csv(pasta / "base_eventos.csv", parse_dates=["inicio", "fim"])
es = pd.read_csv(pasta / "estacoes.csv")
tu = pd.read_csv(pasta / "turnos.csv")
ev["dur"] = (ev["fim"] - ev["inicio"]).dt.total_seconds()
ev["data"] = ev["inicio"].dt.strftime("%Y-%m-%d")

con = sqlite3.connect(":memory:")
ev.assign(inicio=ev.inicio.astype(str), fim=ev.fim.astype(str)).to_sql("eventos", con, index=False)
es.to_sql("estacoes", con, index=False); tu.to_sql("turnos", con, index=False)
q = lambda sql, *a: con.execute(sql, a).fetchone()[0]

def ind(est=None, dia=None):
    """Indicadores como as medidas do Power BI, para uma estação e/ou um dia (ou todos)."""
    f = (ev.estacao_id == est) if est else pd.Series(True, index=ev.index)
    f &= (ev.data == dia) if dia else True
    d = ev[f]; cic = d[d.tipo_evento == "ciclo"]
    dias = tu[tu.data == dia] if dia else tu
    nest = 1 if est else es.estacao_id.nunique()
    plan = dias.planejado_s.sum() * nest
    par = d[d.tipo_evento == "parada"].dur.sum()
    return dict(disp=100*(plan-par)/plan, aprov=100*cic.quantidade_aprovada.sum()/cic.quantidade_total.sum(),
                ciclo=cic.dur.mean(), parada_min=par/60)

def sql_ind(est=None, dia=None):
    w = "1=1" + (f" AND estacao_id='{est}'" if est else "") + (f" AND substr(inicio,1,10)='{dia}'" if dia else "")
    nest = 1 if est else q("SELECT COUNT(*) FROM estacoes")
    plan = q(f"SELECT SUM(planejado_s) FROM turnos WHERE 1=1" + (f" AND data='{dia}'" if dia else "")) * nest
    par = q(f"SELECT COALESCE(SUM(dur),0) FROM eventos WHERE {w} AND tipo_evento='parada'")
    return dict(disp=100*(plan-par)/plan,
                aprov=100*q(f"SELECT SUM(quantidade_aprovada)*1.0/SUM(quantidade_total) FROM eventos WHERE {w} AND tipo_evento='ciclo'"),
                ciclo=q(f"SELECT AVG(dur) FROM eventos WHERE {w} AND tipo_evento='ciclo'"), parada_min=par/60)

linhas = []
def add(nome, rel, sql, py, casas=2):
    ok = abs(sql - py) < 1e-9 and round(sql, casas) == rel
    linhas.append((nome, rel, round(sql, casas), round(py, casas), "confere" if ok else "DIVERGE"))

cic = ev[ev.tipo_evento == "ciclo"]
# Base
add("Registros", 2075, q("SELECT COUNT(*) FROM eventos"), len(ev), 0)
for t, v in (("ciclo", 1726), ("espera", 256), ("parada", 93)):
    add(f"Registros de {t}", v, q("SELECT COUNT(*) FROM eventos WHERE tipo_evento=?", t), (ev.tipo_evento == t).sum(), 0)
# Indicadores da semana (Tabela 4)
a, b = sql_ind(), ind()
add("Tempo de ciclo médio (s)", 221.33, a["ciclo"], b["ciclo"])
add("Horas em operação (h)", 106.12, q("SELECT SUM(dur) FROM eventos WHERE tipo_evento='ciclo'")/3600, cic.dur.sum()/3600)
add("Produção por hora", 16.27, q("SELECT SUM(quantidade_total)*3600.0/SUM(dur) FROM eventos WHERE tipo_evento='ciclo'"), cic.quantidade_total.sum()*3600/cic.dur.sum())
add("Disponibilidade (%)", 87.59, a["disp"], b["disp"])
add("Aprovação (%)", 98.78, a["aprov"], b["aprov"])
real_sql = q("SELECT SUM(quantidade_aprovada) FROM eventos WHERE estacao_id='EST-04' AND tipo_evento='ciclo'")
real_py = ev[(ev.estacao_id == "EST-04") & (ev.tipo_evento == "ciclo")].quantidade_aprovada.sum()
meta = q("SELECT SUM(meta_macetes) FROM turnos")
add("Macetes realizados", 224, real_sql, real_py, 0)
add("Meta (macetes)", 300, meta, tu.meta_macetes.sum(), 0)
add("Atingimento da meta (%)", 74.7, 100*real_sql/meta, 100*real_py/tu.meta_macetes.sum(), 1)
# Por dia
for dia, v in zip(sorted(ev.data.unique()), (43, 45, 40, 49, 47)):
    add(f"Macetes em {dia}", v, q("SELECT SUM(quantidade_aprovada) FROM eventos WHERE estacao_id='EST-04' AND tipo_evento='ciclo' AND substr(inicio,1,10)=?", dia),
        ev[(ev.estacao_id == "EST-04") & (ev.tipo_evento == "ciclo") & (ev.data == dia)].quantidade_aprovada.sum(), 0)
# Ciclo por estação
for e, v in (("EST-04", 327), ("EST-01", 317), ("EST-02", 204), ("EST-03", 152)):
    add(f"Ciclo médio {e} (s)", v, q("SELECT AVG(dur) FROM eventos WHERE estacao_id=? AND tipo_evento='ciclo'", e), cic[cic.estacao_id == e].dur.mean(), 0)
# Pareto de paradas (min)
par = ev[ev.tipo_evento == "parada"]
pq = con.execute("SELECT motivo, SUM(dur)/60.0 FROM eventos WHERE tipo_evento='parada' GROUP BY motivo ORDER BY 2 DESC").fetchall()
pp = (par.groupby("motivo").dur.sum()/60).sort_values(ascending=False)
for (m, s), (m2, p), v in zip(pq, pp.items(), (319, 275, 271, 119, 106, 28)):
    add(f"Parada: {m} (min)", v, s, p, 0)
add("Total parado (min)", 1117, q("SELECT SUM(dur)/60.0 FROM eventos WHERE tipo_evento='parada'"), par.dur.sum()/60, 0)
add("Troca de ferramenta (% do parado)", 28.6, 100*pq[0][1]/sum(x[1] for x in pq), 100*pp.iloc[0]/pp.sum(), 1)
# Esperas
esp = ev[ev.tipo_evento == "espera"]
add("Espera da Montagem (min)", 963, q("SELECT SUM(dur)/60.0 FROM eventos WHERE tipo_evento='espera' AND estacao_id='EST-04'"), esp[esp.estacao_id == "EST-04"].dur.sum()/60, 0)
add("Espera da Montagem por peça das Pontas (min)", 896, q("SELECT SUM(dur)/60.0 FROM eventos WHERE tipo_evento='espera' AND estacao_id='EST-04' AND motivo='Falta de peça: Pontas'"),
    esp[(esp.estacao_id == "EST-04") & (esp.motivo == "Falta de peça: Pontas")].dur.sum()/60, 0)
# Pontas
for rot, kw, vals in (("Pontas (semana)", dict(est="EST-02"), dict(ciclo=203.77, disp=79.66, aprov=99.15, parada_min=458)),
                      ("Pontas em 04/11", dict(est="EST-02", dia="2026-11-04"), dict(disp=64.19, aprov=97.59, parada_min=161)),
                      ("Cabeça em 05/11", dict(est="EST-01", dia="2026-11-05"), dict(aprov=87.0))):
    s, p = sql_ind(**kw), ind(**kw)
    for k, v in vals.items():
        add(f"{rot}: {k}", v, s[k], p[k], 0 if k == "parada_min" else (1 if rot.startswith("Cabeça") else 2))
# Pontas nos outros dias (médias do Tabela 12)
od = [d for d in sorted(ev.data.unique()) if d != "2026-11-04"]
add("Pontas, disponibilidade média nos outros dias (%)", 83.5, sum(sql_ind("EST-02", d)["disp"] for d in od)/4, sum(ind("EST-02", d)["disp"] for d in od)/4, 1)
add("Pontas, parada média nos outros dias (min)", 74, sum(sql_ind("EST-02", d)["parada_min"] for d in od)/4, sum(ind("EST-02", d)["parada_min"] for d in od)/4, 0)
# Verificações de integridade (Tabela 3)
add("Ids duplicados", 0, q("SELECT COUNT(*)-COUNT(DISTINCT evento_id) FROM eventos"), len(ev)-ev.evento_id.nunique(), 0)
add("Fim <= início", 0, q("SELECT COUNT(*) FROM eventos WHERE dur<=0"), (ev.dur <= 0).sum(), 0)
add("Aprovadas > total", 0, q("SELECT COUNT(*) FROM eventos WHERE quantidade_aprovada>quantidade_total"), (ev.quantidade_aprovada > ev.quantidade_total).sum(), 0)

out = pd.DataFrame(linhas, columns=["Valor", "No relatório", "SQL", "Python", "Situação"])
out.to_csv(pasta / "conferencia_valores.csv", index=False, encoding="utf-8-sig")
print(out.to_string(index=False))
print(f"\n{(out.Situação == 'confere').sum()} de {len(out)} valores conferem.")
