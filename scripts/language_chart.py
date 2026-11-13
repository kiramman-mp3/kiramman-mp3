"""Genera un gráfico de dona con los lenguajes más usados en los repos públicos del usuario."""
import json
import math
import os
import sys
import urllib.request

API = "https://api.github.com"
TOP = 8
COLORS = {
    "TypeScript": "#3178c6", "JavaScript": "#f1e05a", "PHP": "#8892bf", "Python": "#4584b6",
    "HTML": "#e34c26", "CSS": "#9b6dd6", "C#": "#3fae2a", "SCSS": "#c6538c", "Blade": "#f7523f",
    "Java": "#b07219", "Kotlin": "#a97bff", "Shell": "#89e051", "PLpgSQL": "#336790", "TSQL": "#e38c00",
}
FALLBACK = ["#14b8a6", "#f59e0b", "#ec4899", "#84cc16", "#06b6d4", "#f97316"]
OTHERS = "#8b949e"


def get(path):
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "profile-language-chart"}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with urllib.request.urlopen(urllib.request.Request(API + path, headers=headers), timeout=30) as res:
        return json.load(res)


def collect(owner):
    totals, page = {}, 1
    while True:
        repos = get(f"/users/{owner}/repos?per_page=100&type=owner&page={page}")
        if not repos:
            break
        for repo in repos:
            if repo["fork"] or repo["name"] == owner:
                continue
            for lang, size in get(f"/repos/{owner}/{repo['name']}/languages").items():
                totals[lang] = totals.get(lang, 0) + size
        page += 1
    return totals


def render(totals):
    ranked = sorted(totals.items(), key=lambda kv: -kv[1])
    items = ranked[:TOP]
    rest = sum(v for _, v in ranked[TOP:])
    if rest:
        items.append(("Otros", rest))
    total = sum(v for _, v in items)
    colors, spare = {}, iter(FALLBACK)
    for name, _ in items:
        colors[name] = OTHERS if name == "Otros" else COLORS.get(name) or next(spare, OTHERS)

    width, height, cx, cy, r, sw = 460, 390, 118, 215, 72, 34
    circ = 2 * math.pi * r
    segments, rows, offset = [], [], 0.0
    for i, (name, value) in enumerate(items):
        length = circ * value / total
        drawn = max(length - 1.6, 0.5)
        segments.append(
            f'    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="{colors[name]}" stroke-width="{sw}" '
            f'stroke-dasharray="0 {circ:.2f}" stroke-dashoffset="{-offset:.2f}" transform="rotate(-90 {cx} {cy})">\n'
            f'      <animate attributeName="stroke-dasharray" from="0 {circ:.2f}" to="{drawn:.2f} {circ - drawn:.2f}" '
            f'dur="0.7s" begin="{0.15 * i:.2f}s" fill="freeze"/>\n    </circle>'
        )
        offset += length
        y = 132 + i * 26
        label = name.replace("&", "&amp;").replace("#", "&#35;")
        rows.append(
            f'    <g opacity="0"><animate attributeName="opacity" from="0" to="1" dur="0.5s" begin="{0.15 * i + 0.3:.2f}s" fill="freeze"/>\n'
            f'      <rect x="236" y="{y - 11}" width="12" height="12" rx="3" fill="{colors[name]}"/>\n'
            f'      <text x="258" y="{y}" font-size="14" fill="#e6edf3">{label}</text>\n'
            f'      <text x="436" y="{y}" font-size="14" fill="#a78bfa" text-anchor="end" font-weight="600">{100 * value / total:.1f}%</text>\n'
            f"    </g>"
        )
    summary = ", ".join(f"{n} {100 * v / total:.1f}%" for n, v in items)
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}" role="img" aria-label="Lenguajes más usados: {summary}">
  <title>Lenguajes más usados</title>
  <rect x="0.5" y="0.5" width="{width - 1}" height="{height - 1}" rx="14" fill="#0d1117" stroke="#30363d"/>
  <g font-family="'Segoe UI', 'Helvetica Neue', Arial, sans-serif">
    <text x="24" y="38" font-size="18" font-weight="700" fill="#c4b5fd">Lenguajes más usados</text>
    <circle cx="{cx}" cy="{cy}" r="{r}" fill="none" stroke="#161b22" stroke-width="{sw}"/>
{chr(10).join(segments)}
    <text x="{cx}" y="{cy - 2}" font-size="13" fill="#8b949e" text-anchor="middle">% del código</text>
    <text x="{cx}" y="{cy + 16}" font-size="13" fill="#8b949e" text-anchor="middle">en mis repos</text>
{chr(10).join(rows)}
  </g>
</svg>
'''


def main():
    out = sys.argv[1]
    owner = os.environ.get("GITHUB_REPOSITORY_OWNER") or sys.argv[2]
    totals = collect(owner)
    if not totals:
        sys.exit("No se encontraron lenguajes; no se escribe el gráfico.")
    os.makedirs(os.path.dirname(out) or ".", exist_ok=True)
    with open(out, "w", encoding="utf-8", newline="\n") as handle:
        handle.write(render(totals))


if __name__ == "__main__":
    main()
