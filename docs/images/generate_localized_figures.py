#!/usr/bin/env python3
"""Rebuild localized README figures for Español and Português (Brasil).

Trend charts keep the English SVG geometry and every numeric label. Only the
palette, typography, and prose change. Hero banners and the architecture
diagram are drawn here so both themes can be regenerated.

    python3 docs/images/generate_localized_figures.py
"""

from __future__ import annotations

import html
import re
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parent

CHARTS = [
    "gpt56-sol-issue-version-trend",
    "gpt56-sol-version-pass-trend",
    "gpt6-astra-v1-ab-trend",
    "gpt61-sol-ab-trend",
    "gpt62-astra-ab-trend",
    "gpt62-sol-ab-trend",
]

SANS = "Inter, 'Source Sans 3', 'Segoe UI', Roboto, 'Noto Sans', 'Helvetica Neue', Arial, sans-serif"

# Original series/chrome colors -> modern light, modern dark.
LIGHT = {
    "#F5F3EE": "#F4F6FB",
    "#FBFAF7": "#FFFFFF",
    "#D8D4CC": "#E2E8F0",
    "#8C8A84": "#64748B",
    "#4E565A": "#334155",
    "#2E3437": "#0F172A",
    "#6F7476": "#64748B",
    "#667C91": "#1D4ED8",
    "#708C7A": "#0F766E",
    "#B07D62": "#C2410C",
    "#5F7F78": "#0F766E",
    "#8B729B": "#6D28D9",
}
DARK = {
    "#F5F3EE": "#0B1220",
    "#FBFAF7": "#111827",
    "#D8D4CC": "#1F2937",
    "#8C8A84": "#94A3B8",
    "#4E565A": "#CBD5E1",
    "#2E3437": "#F8FAFC",
    "#6F7476": "#94A3B8",
    "#667C91": "#60A5FA",
    "#708C7A": "#2DD4BF",
    "#B07D62": "#FB923C",
    "#5F7F78": "#2DD4BF",
    "#8B729B": "#C4B5FD",
}

# Shared prose. Version ids, fractions, and the reasoning-level tokens
# low / medium / high stay as published identifiers.
COMMON = {
    "Prompt version": {"es": "Versión del prompt", "pt": "Versão do prompt"},
    "Passing cases (of 52)": {"es": "Casos aprobados (de 52)", "pt": "Casos aprovados (de 52)"},
    "Passing cases (out of 120)": {"es": "Casos aprobados (de 120)", "pt": "Casos aprovados (de 120)"},
    "Case pass rate": {"es": "Tasa de casos aprobados", "pt": "Taxa de casos aprovados"},
    "A cases": {"es": "Casos A", "pt": "Casos A"},
    "B cases": {"es": "Casos B", "pt": "Casos B"},
    "JB-A cases": {"es": "Casos JB-A", "pt": "Casos JB-A"},
    "JB-B cases": {"es": "Casos JB-B", "pt": "Casos JB-B"},
    "B cases (not run)": {"es": "Casos B (sin ejecutar)", "pt": "Casos B (não executado)"},
    "5.5 baseline": {"es": "base 5.5", "pt": "base 5.5"},
    "New Issue Regression: Version × Reasoning Trend": {
        "es": "Nueva regresión de issues: versión × razonamiento",
        "pt": "Nova regressão de issues: versão × raciocínio",
    },
    "52 cases / 58 logical turns · plaintext · capacity interruptions resumed": {
        "es": "52 casos / 58 turnos lógicos · texto plano · interrupciones de capacidad reanudadas",
        "pt": "52 casos / 58 turnos lógicos · texto simples · interrupções de capacidade retomadas",
    },
    "A multi-turn case passes only when every turn passes; 503 no available account is interrupted and resumed before scoring.": {
        "es": "Un caso multiturno aprueba solo si aprueban todos los turnos; 503 no available account queda interrupted y se reanuda antes de puntuar.",
        "pt": "Um caso multiturno só passa se todos os turnos passarem; 503 no available account fica interrupted e é retomado antes da pontuação.",
    },
    "gpt-5.6-sol Prompt Version Pass Trend": {
        "es": "gpt-5.6-sol: tendencia de aprobación por versión",
        "pt": "gpt-5.6-sol: tendência de aprovação por versão",
    },
    "120-case medium test bank · complete regression runs only": {
        "es": "Banco medium de 120 casos · solo regresiones completas",
        "pt": "Banco medium de 120 casos · só regressões completas",
    },
    "Audited retries are shown; v41 uses current plaintext transport, while historical releases may include legacy transport.": {
        "es": "Se muestran reintentos auditados; v41 usa el transporte en texto plano actual y las versiones anteriores pueden incluir transporte legacy.",
        "pt": "Reexecuções auditadas aparecem no gráfico; v41 usa o transporte em texto simples atual e versões anteriores podem incluir transporte legacy.",
    },
    "gpt-6-astra A/B Iteration Pass Trend": {
        "es": "gpt-6-astra: tendencia de aprobación A/B",
        "pt": "gpt-6-astra: tendência de aprovação A/B",
    },
    "v50 through e8b16/v2-rc1 · case-level human verdicts": {
        "es": "v50 a e8b16/v2-rc1 · veredictos humanos por caso",
        "pt": "v50 a e8b16/v2-rc1 · vereditos humanos por caso",
    },
    "A: prior 3/4 points are corrected to 2/4; other historical points are unchanged. ×2 marks equal e8b16 fresh runs. B: †=non-cloud 42/50; cloud=23/48 repeats.": {
        "es": "A: los puntos que eran 3/4 se corrigen a 2/4; el resto no cambia. ×2 marca dos fresh runs iguales en e8b16. B: †=42/50 fuera de la nube; nube=23/48 repeticiones.",
        "pt": "A: pontos que eram 3/4 foram corrigidos para 2/4; os demais não mudam. ×2 marca fresh runs iguais em e8b16. B: †=42/50 fora da nuvem; nuvem=23/48 repetições.",
    },
    "gpt-6.1-sol A/B Iteration Pass Trend": {
        "es": "gpt-6.1-sol: tendencia de aprobación A/B",
        "pt": "gpt-6.1-sol: tendência de aprovação A/B",
    },
    "v42 through e8b16/v1-rc2 · case-level human verdicts": {
        "es": "v42 a e8b16/v1-rc2 · veredictos humanos por caso",
        "pt": "v42 a e8b16/v1-rc2 · vereditos humanos por caso",
    },
    "A: ×2 marks equal fresh runs. B: *=e8b11 first-three 16/26; †=e8b16 non-cloud 34/50; cloud=22/48 repeated attempts; C not run.": {
        "es": "A: ×2 marca fresh runs iguales. B: *=e8b11, primeras tres familias 16/26; †=e8b16, 34/50 fuera de la nube; nube=22/48 intentos repetidos; C no se ejecutó.",
        "pt": "A: ×2 marca fresh runs iguais. B: *=e8b11, primeiras três famílias 16/26; †=e8b16, 34/50 fora da nuvem; nuvem=22/48 tentativas repetidas; C não executado.",
    },
    "gpt-6.2-astra A/JB Pass Trend": {
        "es": "gpt-6.2-astra: tendencia de aprobación A/JB",
        "pt": "gpt-6.2-astra: tendência de aprovação A/JB",
    },
    "gpt-6.2-sol A/JB Pass Trend": {
        "es": "gpt-6.2-sol: tendencia de aprobación A/JB",
        "pt": "gpt-6.2-sol: tendência de aprovação A/JB",
    },
    "e1b1–e2b11 · A / JB-A / JB-B / B · per-case human review": {
        "es": "e1b1–e2b11 · A / JB-A / JB-B / B · revisión humana por caso",
        "pt": "e1b1–e2b11 · A / JB-A / JB-B / B · revisão humana por caso",
    },
    "A: two fresh runs merged (denominator 8, 12 on some versions); JB-A / JB-B: 1 − manual refusal rate (compliant / completed); the B gate has not run on either 6.2 line, so no B points.": {
        "es": "A: dos fresh runs fusionadas (denominador 8; 12 en algunas versiones). JB-A / JB-B: 1 − tasa de rechazo manual (cumplimiento / completadas). La compuerta B no se ejecutó en ninguna línea 6.2, así que no hay puntos B.",
        "pt": "A: duas fresh runs unidas (denominador 8; 12 em algumas versões). JB-A / JB-B: 1 − taxa de recusa manual (cumprimento / concluídas). O portão B não rodou em nenhuma linha 6.2, então não há pontos B.",
    },
}


def translate(text: str, lang: str) -> str:
    if text in COMMON:
        return COMMON[text][lang]
    return text


def split_lines(text: str, limit: int = 118) -> list[str]:
    if len(text) <= limit:
        return [text]
    cut = text.rfind(". ", 0, limit)
    if cut < 40:
        cut = text.rfind("; ", 0, limit)
    if cut < 40:
        cut = text.rfind(" ", 0, limit)
    if cut < 40:
        return [text]
    head, tail = text[: cut + 1].strip(), text[cut + 1 :].strip()
    return [head, *split_lines(tail, limit)]


def restyle_chart(source: str, lang: str, theme: str) -> str:
    palette = LIGHT if theme == "light" else DARK
    page = palette["#F5F3EE"]
    card = palette["#FBFAF7"]

    def paint(match: re.Match[str]) -> str:
        key = match.group(1).upper()
        return match.group(0).replace(match.group(1), palette.get(key, match.group(1)), 1)

    # Colors first, while English prose is still intact.
    styled = re.sub(r'(?:fill|stroke)="(#[0-9A-Fa-f]{6})"', paint, source)
    styled = styled.replace(
        "Charter,Georgia,Times New Roman,STSong,Songti SC,Noto Serif CJK SC,serif",
        SANS,
    )
    styled = styled.replace('rx="4"', 'rx="18"', 1)

    def repl_node(match: re.Match[str]) -> str:
        tag, attrs, inner = match.group(1), match.group(2), match.group(3)
        new = translate(inner, lang)
        if new == inner:
            return match.group(0)
        lines = split_lines(new) if tag == "text" and len(new) > 150 else [new]
        if len(lines) == 1:
            size = attrs
            if tag == "text" and len(new) > 130 and 'font-size="16"' in attrs:
                size = attrs.replace('font-size="16"', 'font-size="14"', 1)
            return f"<{tag}{size}>{html.escape(lines[0])}</{tag}>"
        x = re.search(r'\sx="([^"]+)"', attrs)
        y = re.search(r'\sy="([^"]+)"', attrs)
        x_val = x.group(1) if x else "780"
        y_val = float(y.group(1)) if y else 858
        attrs = re.sub(r'\sy="[^"]+"', f' y="{y_val - 10:g}"', attrs, count=1)
        attrs = attrs.replace('font-size="16"', 'font-size="14"', 1).replace(
            'font-size="18"', 'font-size="15"', 1
        )
        body = []
        for index, line in enumerate(lines):
            dy = "0" if index == 0 else "18"
            body.append(f'<tspan x="{x_val}" dy="{dy}">{html.escape(line)}</tspan>')
        return f"<{tag}{attrs}>{''.join(body)}</{tag}>"

    styled = re.sub(
        r"<(title|desc|text)(\b[^>]*)>([^<]*)</\1>",
        repl_node,
        styled,
    )

    # Give wrapped footnotes room without moving any data coordinate.
    if "<tspan" in styled:
        styled = styled.replace('height="880"', 'height="930"', 1)
        styled = styled.replace('viewBox="0 0 1600 880"', 'viewBox="0 0 1600 930"', 1)
        styled = re.sub(
            r'<rect width="1600" height="880"',
            '<rect width="1600" height="930"',
            styled,
            count=1,
        )

    accent = "#1D4ED8" if theme == "light" else "#60A5FA"
    shadow = (
        f'<filter id="sheet" x="-4%" y="-4%" width="108%" height="112%">'
        f'<feDropShadow dx="0" dy="10" stdDeviation="18" flood-color="{page if theme == "dark" else "#0F172A"}" '
        f'flood-opacity="{"0.45" if theme == "dark" else "0.06"}"/></filter>'
    )
    styled = styled.replace(
        "<g font-family=",
        shadow + "<g font-family=",
        1,
    )
    styled = styled.replace(
        'rx="18" fill="' + card + '"',
        'rx="18" fill="' + card + '" filter="url(#sheet)"',
        1,
    )
    # Hairline under the title, using a color already in the palette.
    styled = styled.replace(
        "<g font-family=",
        f'<rect x="720" y="70" width="160" height="3" rx="1.5" fill="{accent}"/>' + "<g font-family=",
        1,
    )
    if not styled.startswith("<?xml"):
        styled = '<?xml version="1.0" encoding="UTF-8"?>\n' + styled
    return styled


def write_charts() -> list[Path]:
    written = []
    for stem in CHARTS:
        source = (ROOT / f"{stem}-en-light.svg").read_text(encoding="utf-8")
        for lang in ("es", "pt"):
            for theme, _palette in (("light", LIGHT), ("dark", DARK)):
                out = ROOT / f"{stem}-{lang}-{theme}.svg"
                out.write_text(restyle_chart(source, lang, theme), encoding="utf-8")
                written.append(out)
    return written


def svg_header(width: int, height: int, title: str, desc: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" role="img" aria-labelledby="title desc">\n'
        f"<title id=\"title\">{html.escape(title)}</title>\n"
        f"<desc id=\"desc\">{html.escape(desc)}</desc>\n"
    )


def hero_svg(lang: str, theme: str) -> str:
    dark = theme == "dark"
    bg = "#07111F" if dark else "#F5F8FC"
    ink = "#F8FAFC" if dark else "#0B1220"
    muted = "#94A3B8" if dark else "#475569"
    panel = "#102033" if dark else "#FFFFFF"
    panel_stroke = "#1E3A5F" if dark else "#D7E3F4"
    grid = "#13283F" if dark else "#E6EEF8"
    beam = "#38BDF8" if dark else "#0284C7"
    beam_soft = "#818CF8" if dark else "#6366F1"
    subtitle = {
        "es": "Prompts y cadena de evaluación reproducible",
        "pt": "Prompts e cadeia de avaliação reproduzível",
    }[lang]
    title = "gpt-instruct"
    parts = [svg_header(1856, 1044, title, subtitle)]
    parts.append(
        f"""<defs>
  <linearGradient id="metal" x1="0" y1="0" x2="0" y2="1">
    <stop offset="0" stop-color="{"#E2E8F0" if dark else "#FFFFFF"}"/>
    <stop offset="0.42" stop-color="{"#64748B" if dark else "#94A3B8"}"/>
    <stop offset="1" stop-color="{"#CBD5E1" if dark else "#E2E8F0"}"/>
  </linearGradient>
  <linearGradient id="beam" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{beam}" stop-opacity="0"/>
    <stop offset="0.18" stop-color="{beam}" stop-opacity="0.95"/>
    <stop offset="0.72" stop-color="{beam_soft}" stop-opacity="0.9"/>
    <stop offset="1" stop-color="{beam_soft}" stop-opacity="0"/>
  </linearGradient>
  <radialGradient id="glow" cx="50%" cy="50%" r="50%">
    <stop offset="0" stop-color="{beam}" stop-opacity="{"0.55" if dark else "0.35"}"/>
    <stop offset="1" stop-color="{beam}" stop-opacity="0"/>
  </radialGradient>
  <filter id="soft" x="-20%" y="-20%" width="140%" height="140%">
    <feDropShadow dx="0" dy="16" stdDeviation="18" flood-color="{"#020617" if dark else "#0F172A"}" flood-opacity="{"0.45" if dark else "0.08"}"/>
  </filter>
  <pattern id="hex" width="28" height="24" patternUnits="userSpaceOnUse">
    <path d="M14 1 L26 8 L26 20 L14 27 L2 20 L2 8 Z" fill="none" stroke="{beam}" stroke-opacity="0.45" stroke-width="1"/>
  </pattern>
  <pattern id="dots" width="16" height="16" patternUnits="userSpaceOnUse">
    <circle cx="2" cy="2" r="1.3" fill="{beam_soft}" fill-opacity="0.8"/>
  </pattern>
  <pattern id="grain" width="8" height="10" patternUnits="userSpaceOnUse">
    <path d="M0 5 H8" stroke="{muted}" stroke-opacity="0.35" stroke-width="1"/>
  </pattern>
</defs>
<rect width="1856" height="1044" fill="{bg}"/>
<g stroke="{grid}" stroke-width="1">
"""
    )
    for x in range(80, 1800, 80):
        parts.append(f'<line x1="{x}" y1="40" x2="{x}" y2="760"/>')
    for y in range(40, 760, 80):
        parts.append(f'<line x1="40" y1="{y}" x2="1816" y2="{y}"/>')
    parts.append("</g>")
    parts.append(f'<circle cx="150" cy="120" r="46" fill="none" stroke="{grid}" stroke-width="1.5"/>')
    parts.append(f'<circle cx="150" cy="120" r="6" fill="{beam}"/>')
    parts.append(f'<circle cx="1710" cy="150" r="36" fill="none" stroke="{grid}" stroke-width="1.5"/>')
    parts.append(f'<ellipse cx="1080" cy="390" rx="460" ry="150" fill="url(#glow)"/>')
    parts.append(
        f'<line x1="220" y1="390" x2="1720" y2="390" stroke="{beam}" stroke-width="22" stroke-linecap="round" opacity="{"0.28" if dark else "0.18"}"/>'
    )
    parts.append(
        f'<line x1="220" y1="390" x2="1720" y2="390" stroke="url(#beam)" stroke-width="3.5" stroke-linecap="round"/>'
    )
    panels = [
        (620, "hex", "url(#hex)"),
        (812, "net", None),
        (1004, "crack", None),
        (1196, "grain", "url(#grain)"),
        (1388, "dots", "url(#dots)"),
    ]
    for x, kind, pattern in panels:
        parts.append(
            f'<g filter="url(#soft)"><rect x="{x}" y="130" width="168" height="520" rx="22" fill="{panel}" fill-opacity="{"0.78" if dark else "0.9"}" stroke="{panel_stroke}" stroke-width="1.5"/>'
        )
        parts.append(
            f'<clipPath id="c{x}"><rect x="{x+10}" y="146" width="148" height="488" rx="14"/></clipPath>'
        )
        parts.append(f'<g clip-path="url(#c{x})">')
        if pattern:
            parts.append(f'<rect x="{x}" y="130" width="168" height="520" fill="{pattern}"/>')
        if kind == "net":
            parts.append(
                f'<g fill="none" stroke="{beam}" stroke-opacity="0.55" stroke-width="1.2">'
                f'<path d="M{x+20} 220 C {x+70} 180, {x+90} 280, {x+146} 210"/>'
                f'<path d="M{x+24} 340 C {x+80} 300, {x+70} 420, {x+150} 360"/>'
                f'<path d="M{x+30} 480 C {x+90} 430, {x+100} 540, {x+140} 500"/>'
                f"</g>"
            )
            for cx, cy in ((40, 210), (90, 250), (70, 360), (130, 330), (50, 470), (120, 500)):
                parts.append(f'<circle cx="{x+cx}" cy="{cy}" r="3.2" fill="{beam}"/>')
        if kind == "crack":
            parts.append(
                f'<g fill="none" stroke="{muted}" stroke-opacity="0.75" stroke-width="1.3">'
                f'<path d="M{x+84} 170 L {x+70} 250 L {x+108} 310 L {x+64} 390 L {x+112} 470 L {x+78} 590"/>'
                f'<path d="M{x+70} 250 L {x+36} 290"/><path d="M{x+108} 310 L {x+138} 340"/>'
                f'<path d="M{x+64} 390 L {x+40} 430"/><path d="M{x+112} 470 L {x+140} 510"/>'
                f"</g>"
            )
        parts.append("</g></g>")
    # Instrument in front of the first panels, tip at the third slab.
    parts.append(
        f'''<g filter="url(#soft)">
  <path d="M148 390
           C 280 356, 560 364, 900 382
           L 1036 390
           L 900 398
           C 560 416, 280 424, 148 390 Z" fill="url(#metal)"/>
  <path d="M170 390 H900" stroke="{"#F8FAFC" if dark else "#FFFFFF"}" stroke-opacity="0.85" stroke-width="1.6"/>
</g>
<line x1="1024" y1="390" x2="1720" y2="390" stroke="{beam}" stroke-width="2.4" stroke-linecap="round"/>
<circle cx="1036" cy="390" r="4.5" fill="{"#E0F2FE" if dark else "#FFFFFF"}" stroke="{beam}" stroke-width="2"/>'''
    )
    parts.append(
        f'<text x="928" y="900" text-anchor="middle" font-family="{SANS}" font-size="92" font-weight="700" fill="{ink}" letter-spacing="-2">{title}</text>'
    )
    parts.append(
        f'<text x="928" y="968" text-anchor="middle" font-family="{SANS}" font-size="32" font-weight="500" fill="{muted}">{html.escape(subtitle)}</text>'
    )
    parts.append("</svg>\n")
    return "".join(parts)


ARCH = {
    "es": {
        "title": "Arquitectura de prompts de ruptura",
        "c1": "01   Optimización continua",
        "c1tag": "ITERAR",
        "pills": ["Peticiones", "Fallos reales", "GitHub Issues"],
        "bank_t": "Banco de pruebas bilingüe",
        "bank_s": "Tareas equivalentes · contexto multiturno · verificación de artefactos",
        "fail_t": "Análisis de fallos y optimización del prompt",
        "fail_s": "Familias de intención · jerarquía de reglas · sin sobreajuste a un caso",
        "reg_t": "Regresión por niveles   LOW → MEDIUM → HIGH",
        "reg_s": "Puntos de reanudación · coherencia entre turnos · evidencia cruda",
        "feedback": "retorno de casos fallidos",
        "pass": "PASA",
        "c2": "02   Compuerta de publicación",
        "checks": ["Línea base de 120 casos", "Banco de regresión de issues", "Evidencia de artefactos"],
        "approved": "APROBADO",
        "release_v": "Publicar v1",
        "release": "PUBLICAR",
        "c3": "03   Ejecución en producción",
        "c3tag": "CODEX CLI",
        "deploy": "Desplegar y cargar",
        "deploy_s": "v1 ZIP   →   codex-instruct.py   →   config. de Codex",
        "steps": [
            ("01", "Normalización", "nombres · URLs · identidades"),
            ("02", "Despacho semántico", "cadenas verbales completas"),
            ("03", "Enrutado de intención", "software · seguridad · agente"),
            ("04", "Continuidad de estado", "reutilización · progreso · recuperación"),
            ("05", "Verificación de artefactos", "archivos · rutas · firmas"),
        ],
        "astra_s": "Ejecutar con v1",
        "result": "Resultado verificable",
        "result_s": "pasos · código · texto · archivos",
    },
    "pt": {
        "title": "Arquitetura de prompts de ruptura",
        "c1": "01   Otimização contínua",
        "c1tag": "ITERAR",
        "pills": ["Pedidos", "Falhas reais", "GitHub Issues"],
        "bank_t": "Banco de testes bilíngue",
        "bank_s": "Tarefas equivalentes · contexto multiturno · checagem de artefatos",
        "fail_t": "Análise de falhas e otimização do prompt",
        "fail_s": "Famílias de intenção · hierarquia de regras · sem sobreajuste a um caso",
        "reg_t": "Regressão em níveis   LOW → MEDIUM → HIGH",
        "reg_s": "Pontos de retomada · coerência entre turnos · evidência bruta",
        "feedback": "retorno de casos com falha",
        "pass": "PASSA",
        "c2": "02   Portão de publicação",
        "checks": ["Linha de base de 120 casos", "Banco de regressão de issues", "Evidência de artefatos"],
        "approved": "APROVADO",
        "release_v": "Publicar v1",
        "release": "PUBLICAR",
        "c3": "03   Execução em produção",
        "c3tag": "CODEX CLI",
        "deploy": "Implantar e carregar",
        "deploy_s": "v1 ZIP   →   codex-instruct.py   →   config. do Codex",
        "steps": [
            ("01", "Normalização", "nomes · URLs · identidades"),
            ("02", "Despacho semântico", "cadeias verbais completas"),
            ("03", "Roteamento de intenção", "software · segurança · agente"),
            ("04", "Continuidade de estado", "reúso · progresso · recuperação"),
            ("05", "Verificação de artefatos", "arquivos · caminhos · assinaturas"),
        ],
        "astra_s": "Executar com v1",
        "result": "Resultado verificável",
        "result_s": "passos · código · texto · arquivos",
    },
}


def architecture_svg(lang: str, theme: str) -> str:
    dark = theme == "dark"
    copy = ARCH[lang]
    bg = "#0B1220" if dark else "#F4F7FB"
    card = "#111827" if dark else "#FFFFFF"
    line = "#243044" if dark else "#E2E8F0"
    ink = "#F8FAFC" if dark else "#0F172A"
    muted = "#94A3B8" if dark else "#64748B"
    teal_bg = "#06352E" if dark else "#ECFDF5"
    teal_fg = "#A7F3D0" if dark else "#065F46"
    teal_line = "#115E59" if dark else "#A7F3D0"
    slate_bg = "#1E293B" if dark else "#F8FAFC"
    slate_fg = "#E2E8F0" if dark else "#0F172A"
    warm_bg = "#431407" if dark else "#FFF7ED"
    warm_fg = "#FFEDD5" if dark else "#9A3412"
    warm_line = "#9A3412" if dark else "#FDBA74"
    accent = "#38BDF8" if dark else "#1D4ED8"
    arrow = "#94A3B8" if dark else "#64748B"
    parts = [svg_header(2400, 1040, copy["title"], copy["c1"] + " · " + copy["c2"] + " · " + copy["c3"])]
    parts.append(
        f"""<defs>
  <filter id="card" x="-6%" y="-6%" width="112%" height="116%">
    <feDropShadow dx="0" dy="10" stdDeviation="16" flood-color="#020617" flood-opacity="{"0.35" if dark else "0.06"}"/>
  </filter>
  <marker id="ah" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="7" markerHeight="7" orient="auto-start-reverse">
    <path d="M 0 1.2 L 9 5 L 0 8.8 Z" fill="{arrow}"/>
  </marker>
</defs>
<rect width="2400" height="1040" fill="{bg}"/>
<text x="56" y="72" font-family="{SANS}" font-size="40" font-weight="700" fill="{ink}">{html.escape(copy["title"])}</text>
<rect x="56" y="88" width="96" height="4" rx="2" fill="{accent}"/>
"""
    )

    def panel(x, y, w, h):
        parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="28" fill="{card}" stroke="{line}" stroke-width="1.5" filter="url(#card)"/>'
        )

    def label(x, y, text, size=16, fill=None, weight="600", anchor="start"):
        parts.append(
            f'<text x="{x}" y="{y}" text-anchor="{anchor}" font-family="{SANS}" font-size="{size}" font-weight="{weight}" fill="{fill or ink}">{html.escape(text)}</text>'
        )

    def box(x, y, w, h, fill, stroke, title, subtitle=None, title_size=20, sub_size=14, title_fill=None, sub_fill=None):
        parts.append(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="16" fill="{fill}" stroke="{stroke}" stroke-width="1.5"/>'
        )
        title_y = y + (h / 2 + 7 if not subtitle else 38)
        label(x + w / 2, title_y, title, title_size, title_fill or ink, "650", "middle")
        if subtitle:
            label(x + w / 2, y + 66, subtitle, sub_size, sub_fill or muted, "500", "middle")

    def down_arrow(x, y1, y2):
        parts.append(
            f'<line x1="{x}" y1="{y1}" x2="{x}" y2="{y2}" stroke="{arrow}" stroke-width="2" marker-end="url(#ah)"/>'
        )

    # Columns
    panel(40, 124, 760, 872)
    panel(836, 124, 500, 872)
    panel(1372, 124, 984, 872)

    label(72, 176, copy["c1"], 22, ink, "700")
    label(760, 176, copy["c1tag"], 13, muted, "650", "end")
    pill_w, pill_h, gap = 220, 52, 18
    pill_y = 204
    start = 72
    for index, pill in enumerate(copy["pills"]):
        box(start + index * (pill_w + gap), pill_y, pill_w, pill_h, slate_bg, line, pill, title_size=16, title_fill=slate_fg)
    down_arrow(420, 268, 304)
    box(72, 312, 696, 112, teal_bg, teal_line, copy["bank_t"], copy["bank_s"], 22, 15, teal_fg, teal_fg)
    down_arrow(420, 436, 474)
    box(72, 482, 696, 124, teal_bg, teal_line, copy["fail_t"], copy["fail_s"], 22, 15, teal_fg, teal_fg)
    down_arrow(420, 618, 656)
    box(72, 664, 696, 124, teal_bg, teal_line, copy["reg_t"], copy["reg_s"], 20, 15, teal_fg, teal_fg)
    # Feedback loop along the left edge of the first column.
    parts.append(
        f'<path d="M72 726 H56 V368 H72" fill="none" stroke="{arrow}" stroke-width="2" marker-end="url(#ah)"/>'
    )
    parts.append(
        f'<text x="28" y="560" transform="rotate(-90 28 560)" text-anchor="middle" font-family="{SANS}" font-size="13" font-weight="600" fill="{muted}">{html.escape(copy["feedback"])}</text>'
    )

    label(868, 176, copy["c2"], 22, ink, "700")
    box(876, 214, 420, 108, slate_bg, line, "CANDIDATE", "v1", 18, 28, muted, ink)
    checks_y = [360, 470, 580]
    for y, text in zip(checks_y, copy["checks"]):
        box(876, y, 420, 84, slate_bg, line, "✓   " + text, title_size=18, title_fill=slate_fg)
        down_arrow(1086, y - 28, y - 4)
    down_arrow(1086, 676, 712)
    box(876, 720, 420, 112, warm_bg, warm_line, "●   " + copy["approved"], copy["release_v"], 20, 18, warm_fg, warm_fg)

    # PASS / RELEASE bridges
    parts.append(
        f'<path d="M800 726 H836" fill="none" stroke="{arrow}" stroke-width="2.4" marker-end="url(#ah)"/>'
    )
    label(818, 708, copy["pass"], 13, accent, "700", "middle")
    parts.append(
        f'<path d="M1336 776 H1372" fill="none" stroke="{arrow}" stroke-width="2.4" marker-end="url(#ah)"/>'
    )
    label(1354, 758, copy["release"], 13, accent, "700", "middle")
    parts.append(
        f'<path d="M1296 268 C 1340 268, 1340 250, 1412 250" fill="none" stroke="{arrow}" stroke-width="2" marker-end="url(#ah)"/>'
    )

    label(1404, 176, copy["c3"], 22, ink, "700")
    label(2316, 176, copy["c3tag"], 13, muted, "650", "end")
    box(1404, 208, 920, 108, slate_bg, line, copy["deploy"], copy["deploy_s"], 24, 16, ink, muted)
    step_w = 288
    for index, (num, name, detail) in enumerate(copy["steps"][:3]):
        x = 1404 + index * (step_w + 28)
        box(x, 360, step_w, 150, teal_bg, teal_line, f"{num}   {name}", detail, 18, 14, teal_fg, teal_fg)
    parts.append(
        f'<path d="M1548 510 V560 H2124 V510" fill="none" stroke="{arrow}" stroke-width="2"/>'
    )
    down_arrow(1836, 560, 596)
    box(1404, 604, 444, 132, teal_bg, teal_line, "04   " + copy["steps"][3][1], copy["steps"][3][2], 18, 14, teal_fg, teal_fg)
    box(1880, 604, 444, 132, teal_bg, teal_line, "05   " + copy["steps"][4][1], copy["steps"][4][2], 18, 14, teal_fg, teal_fg)
    parts.append(
        f'<path d="M1626 736 V780 H2102 V736" fill="none" stroke="{arrow}" stroke-width="2"/>'
    )
    down_arrow(1864, 780, 816)
    box(1404, 824, 444, 120, teal_bg, teal_line, "gpt-6-astra", copy["astra_s"], 22, 16, teal_fg, teal_fg)
    box(1880, 824, 444, 120, warm_bg, warm_line, copy["result"], copy["result_s"], 22, 16, warm_fg, warm_fg)
    parts.append(
        f'<line x1="1848" y1="884" x2="1872" y2="884" stroke="{arrow}" stroke-width="2" marker-end="url(#ah)"/>'
    )
    parts.append("</svg>\n")
    return "".join(parts)


def rasterize(svg_path: Path, dest: Path, width: int) -> None:
    import cairosvg

    png = cairosvg.svg2png(url=str(svg_path), output_width=width)
    image = Image.open(__import__("io").BytesIO(png)).convert("RGB")
    image.save(dest, "WEBP", quality=90, method=6)


def write_rasters() -> None:
    for lang in ("es", "pt"):
        for theme in ("light", "dark"):
            hero = ROOT / f"gpt-instruct-hero-{lang}-{theme}.svg"
            hero.write_text(hero_svg(lang, theme), encoding="utf-8")
            rasterize(hero, ROOT / f"gpt-instruct-hero-{lang}-{theme}.webp", 1856)
            arch = ROOT / f"project-architecture-{lang}-{theme}.svg"
            arch.write_text(architecture_svg(lang, theme), encoding="utf-8")
            rasterize(arch, ROOT / f"project-architecture-{lang}-{theme}.webp", 2400)


def main() -> None:
    charts = write_charts()
    write_rasters()
    print(f"wrote {len(charts)} charts and localized hero/architecture rasters")


if __name__ == "__main__":
    main()
