import json, os, sys, math, datetime as dt
import urllib.request

USER = os.environ.get("GH_USER", "Squi1ck")
TOKEN = os.environ.get("GH_TOKEN", "")
MESES = ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]
CORES = ["#161b22", "#0e4429", "#006d32", "#26a641", "#39d353"]
CELL, STEP = 12, 15


def buscar(ano):
    hoje = dt.date.today()
    inicio = dt.date(ano, 1, 1)
    fim = min(dt.date(ano, 12, 31), hoje)
    query = """query($u:String!,$f:DateTime!,$t:DateTime!){user(login:$u){contributionsCollection(from:$f,to:$t){contributionCalendar{totalContributions weeks{contributionDays{date contributionCount weekday}}}}}}"""
    dados = json.dumps({"query": query, "variables": {
        "u": USER, "f": inicio.isoformat() + "T00:00:00Z", "t": fim.isoformat() + "T23:59:59Z"}}).encode()
    req = urllib.request.Request("https://api.github.com/graphql", data=dados, headers={
        "Authorization": "bearer " + TOKEN, "Content-Type": "application/json", "User-Agent": "contribs"})
    with urllib.request.urlopen(req) as r:
        resp = json.load(r)
    if "errors" in resp:
        raise SystemExit(resp["errors"])
    cal = resp["data"]["user"]["contributionsCollection"]["contributionCalendar"]
    dias = {}
    for sem in cal["weeks"]:
        for d in sem["contributionDays"]:
            dias[d["date"]] = d["contributionCount"]
    return dias, cal["totalContributions"]


def svg(ano, dias, total):
    inicio = dt.date(ano, 1, 1)
    fim = dt.date(ano, 12, 31)
    offset = (inicio.weekday() + 1) % 7
    ncols = ((fim - inicio).days + offset) // 7 + 1
    mx = max(dias.values()) if dias else 0
    ml, mt = 44, 62
    gw, gh = ncols * STEP, 7 * STEP
    W, H = ml + gw + 24, mt + gh + 56
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Helvetica, Arial, sans-serif">',
           f'<rect x="1" y="1" width="{W-2}" height="{H-2}" rx="10" fill="#0d1117" stroke="#30363d"/>',
           f'<text x="{ml}" y="28" font-size="16" font-weight="600" fill="#e6edf3">{ano}</text>',
           f'<text x="{ml+52}" y="28" font-size="14" fill="#8b949e">{total} contribuições</text>']
    for i, nome in ((1, "Seg"), (3, "Qua"), (5, "Sex")):
        out.append(f'<text x="{ml-8}" y="{mt+i*STEP+10}" font-size="10" fill="#8b949e" text-anchor="end">{nome}</text>')
    tot_mes = [0] * 12
    d = inicio
    while d <= fim:
        tot_mes[d.month - 1] += dias.get(d.isoformat(), 0)
        d += dt.timedelta(days=1)
    for m in range(12):
        primeiro = dt.date(ano, m + 1, 1)
        col = ((primeiro - inicio).days + offset) // 7
        x = ml + col * STEP
        out.append(f'<text x="{x}" y="{mt-10}" font-size="11" fill="#8b949e">{MESES[m]}</text>')
        out.append(f'<text x="{x}" y="{mt+gh+22}" font-size="10" fill="#58a6ff">{tot_mes[m]}</text>')
    d = inicio
    while d <= fim:
        idx = (d - inicio).days + offset
        col, lin = idx // 7, idx % 7
        c = dias.get(d.isoformat(), 0)
        nivel = 0 if c == 0 or mx == 0 else max(1, math.ceil(4 * c / mx))
        out.append(f'<rect x="{ml+col*STEP}" y="{mt+lin*STEP}" width="{CELL}" height="{CELL}" rx="2" fill="{CORES[nivel]}"><title>{d.isoformat()}: {c}</title></rect>')
        d += dt.timedelta(days=1)
    p = 7
    x0, y0, x1, y1 = ml - p, mt - p, ml + gw + p - 3, mt + gh + p - 3
    caminho = f"M{x0},{y0} H{x1} V{y1} H{x0} Z"
    dur, seg, lag = 14, 9, 0.22
    for i in range(seg):
        r = 4.2 - i * 0.35
        op = 1 - i * 0.09
        cor = "#a855f7" if i else "#c084fc"
        b = -(dur - i * lag)
        out.append(f'<circle r="{r:.2f}" fill="{cor}" opacity="{op:.2f}"><animateMotion dur="{dur}s" begin="{b:.2f}s" repeatCount="indefinite" path="{caminho}"/></circle>')
    out.append("</svg>")
    return "\n".join(out)


def main():
    os.makedirs("dist", exist_ok=True)
    ano = dt.date.today().year
    for nome, a in (("atual", ano), ("anterior", ano - 1)):
        dias, total = buscar(a)
        open(f"dist/contrib-{nome}.svg", "w", encoding="utf-8").write(svg(a, dias, total))
        print(nome, a, total)


if __name__ == "__main__":
    main()
