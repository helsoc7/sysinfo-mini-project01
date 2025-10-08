#!/usr/bin/env python3
import argparse, json, os, subprocess, time
from datetime import datetime

# --- kleine Hilfen -----------------------------------------------------------
def ts():
    return datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

def run(cmd: list[str]) -> str:
    try:
        return subprocess.check_output(cmd, text=True, stderr=subprocess.STDOUT).strip()
    except Exception:
        return ""

def safe_write(path: str, text: str):
    try:
        with open(path, "w") as f: f.write(text)
        return path
    except OSError:
        p2 = f"/tmp/{os.path.basename(path)}"
        with open(p2, "w") as f: f.write(text)
        return p2

# --- Daten sammeln -----------------------------------------------------------
def cpu_usage(interval=0.2) -> float:
    def snap():
        with open("/proc/stat") as f:
            p = f.readline().split()
            u,n,s,idle,iow,irq,sirq = map(int, p[1:8])
            total = u+n+s+idle+iow+irq+sirq
            idle_all = idle+iow
            return total, idle_all
    t1,i1 = snap(); time.sleep(interval); t2,i2 = snap()
    dt, di = (t2-t1), (i2-i1)
    if dt <= 0: return 0.0
    return round((1 - (di/dt)) * 100, 1)

def mem_info():
    out = run(["free", "-m"])
    for line in out.splitlines():
        if line.lower().startswith("mem:"):
            _, total, used, free, *_ = line.split()
            return {"total_mb": int(total), "used_mb": int(used), "free_mb": int(free)}
    return {"total_mb":0,"used_mb":0,"free_mb":0}

def disk_root():
    out = run(["df", "-h", "/"])
    lines = out.splitlines()
    if len(lines) >= 2:
        fs,size,used,avail,usep,mount = lines[1].split()[:6]
        return {"size": size, "used": used, "avail": avail, "use_percent": usep, "mount": mount}
    return {}

def net_ping(target="8.8.8.8"):
    out = run(["ping", "-c", "1", "-W", "1", target])
    ok = ", 0% packet loss" in out or "1 received" in out
    return {"target": target, "reachable": bool(ok)}

def collect(skip_ping=False):
    return {
        "cpu": {"usage_percent": cpu_usage()},
        "memory": mem_info(),
        "disk": {"root": disk_root()},
        "network": ({"skipped": True} if skip_ping else net_ping()),
        "timestamp": ts(),
    }

# --- Ausgabe -----------------------------------------------------------------
def render_text(d):
    m = d["memory"]; r = d["disk"]["root"]; n = d["network"]
    lines = [
        "=== System Report ===",
        f"Timestamp   : {d['timestamp']}",
        "",
        "[CPU]",
        f"  Usage     : {d['cpu']['usage_percent']}%",
        "",
        "[Memory]",
        f"  Total     : {m['total_mb']} MB",
        f"  Used      : {m['used_mb']} MB",
        f"  Free      : {m['free_mb']} MB",
        "",
        "[Disk /]",
        f"  Used      : {r.get('used','?')} / {r.get('size','?')} ({r.get('use_percent','?')})",
        "",
        "[Network]",
        ("  Ping      : skipped" if "skipped" in n else f"  Reachable : {n['reachable']}"),
    ]
    return "\n".join(lines)

def render_html(d):
    m = d["memory"]; r = d["disk"]["root"]; n = d["network"]
    cpu = d["cpu"]["usage_percent"]
    mem_total, mem_used = m["total_mb"] or 0, m["used_mb"] or 0
    mem_pct = (mem_used / mem_total * 100) if mem_total else 0
    try: disk_pct = float(r.get("use_percent","0%").rstrip("%"))
    except: disk_pct = 0.0
    net_str = "skipped" if "skipped" in n else ("online" if n.get("reachable") else "offline")

    def bar(pct):
        pct = max(0, min(100, pct))
        return f'<div style="background:#eee;width:100%;height:10px;border-radius:6px"><div style="width:{pct}%;height:10px;border-radius:6px;background:#4a7"></div></div>'

    return f"""<!doctype html><html lang="de"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>System Report</title>
<style>body{{font-family:system-ui,sans-serif;margin:2rem}}.card{{border:1px solid #ddd;border-radius:12px;padding:1rem;margin:.8rem 0}}</style>
</head><body>
<h1>System Report</h1>
<p><b>Timestamp:</b> {d['timestamp']}</p>
<div class="card"><h2>CPU</h2><p>{cpu}%</p>{bar(cpu)}</div>
<div class="card"><h2>Speicher</h2><p>{mem_used} / {mem_total} MB</p>{bar(mem_pct)}</div>
<div class="card"><h2>Disk (/)</h2><p>{r.get("used","?")} / {r.get("size","?")} ({r.get("use_percent","?")})</p>{bar(disk_pct)}</div>
<div class="card"><h2>Netzwerk</h2><p>{net_str}</p></div>
</body></html>"""

# --- CLI ---------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Sysinfo Mini")
    ap.add_argument("--json", action="store_true", help="JSON-Report speichern")
    ap.add_argument("--html", action="store_true", help="HTML-Report speichern")
    ap.add_argument("--outdir", default="reports", help="Zielordner")
    ap.add_argument("--no-ping", action="store_true", help="Ping überspringen")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)
    data = collect(skip_ping=args.no_ping)

    # Terminal
    print(render_text(data))

    # Optional speichern
    stamp = data["timestamp"]
    if args.json:
        path = os.path.join(args.outdir, f"report_{stamp}.json")
        saved = safe_write(path, json.dumps(data, indent=2, ensure_ascii=False))
        print(f"JSON gespeichert: {saved}")
    if args.html:
        path = os.path.join(args.outdir, f"report_{stamp}.html")
        saved = safe_write(path, render_html(data))
        print(f"HTML gespeichert: {saved}")

if __name__ == "__main__":
    main()

