"""Draws the mod icon variants as SVG inside HTML pages (rendered to PNG by render_icon.js)."""
import os
import sys

FONT = sys.argv[2] if len(sys.argv) > 2 else ""

BACKGROUND = """
  <defs>
    <radialGradient id="bg" cx="50%" cy="38%" r="75%">
      <stop offset="0" stop-color="#4b494b"/><stop offset="0.65" stop-color="#2a292a"/><stop offset="1" stop-color="#1b1a1b"/>
    </radialGradient>
    <linearGradient id="arm" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#ffd257"/><stop offset="1" stop-color="#e09a12"/>
    </linearGradient>
    <linearGradient id="metal" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#b9b9b9"/><stop offset="1" stop-color="#6d6d6d"/>
    </linearGradient>
    <linearGradient id="plate" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0" stop-color="#dbe6f0"/><stop offset="1" stop-color="#8195a8"/>
    </linearGradient>
    <linearGradient id="badge" x1="0" y1="0" x2="0" y2="1">
      <stop offset="0" stop-color="#ffb347"/><stop offset="1" stop-color="#e3720b"/>
    </linearGradient>
    <filter id="shadow" x="-20%" y="-20%" width="140%" height="140%">
      <feDropShadow dx="0" dy="2" stdDeviation="1.6" flood-color="#000" flood-opacity="0.7"/>
    </filter>
  </defs>
  <rect x="3" y="3" width="138" height="138" rx="18" fill="url(#bg)" stroke="#0b0b0b" stroke-width="4"/>
  <rect x="6.5" y="6.5" width="131" height="131" rx="15" fill="none" stroke="#5e5c5e" stroke-width="1.5"/>
"""


def inserter(base_x, base_y, elbow, grip, scale=1.0):
    """A yellow inserter arm: base platform, two segments, gripper holding an iron plate."""
    s = scale
    ex, ey = elbow
    gx, gy = grip
    return f"""
  <g filter="url(#shadow)">
    <rect x="{base_x - 22*s}" y="{base_y - 9*s}" width="{44*s}" height="{20*s}" rx="{6*s}" fill="url(#metal)" stroke="#2b2b2b" stroke-width="{2.5*s}"/>
    <rect x="{base_x - 14*s}" y="{base_y - 3*s}" width="{28*s}" height="{5*s}" rx="{2*s}" fill="#4d4d4d"/>
    <line x1="{base_x}" y1="{base_y - 4*s}" x2="{ex}" y2="{ey}" stroke="#5a3d05" stroke-width="{15*s}" stroke-linecap="round"/>
    <line x1="{base_x}" y1="{base_y - 4*s}" x2="{ex}" y2="{ey}" stroke="url(#arm)" stroke-width="{10*s}" stroke-linecap="round"/>
    <line x1="{ex}" y1="{ey}" x2="{gx}" y2="{gy}" stroke="#5a3d05" stroke-width="{13*s}" stroke-linecap="round"/>
    <line x1="{ex}" y1="{ey}" x2="{gx}" y2="{gy}" stroke="url(#arm)" stroke-width="{8.5*s}" stroke-linecap="round"/>
    <circle cx="{base_x}" cy="{base_y - 4*s}" r="{6*s}" fill="#3b3b3b" stroke="#1d1d1d" stroke-width="{1.5*s}"/>
    <circle cx="{ex}" cy="{ey}" r="{6.5*s}" fill="#3b3b3b" stroke="#1d1d1d" stroke-width="{1.5*s}"/>
    <rect x="{gx - 11*s}" y="{gy - 15*s}" width="{22*s}" height="{17*s}" rx="{2.5*s}" fill="url(#plate)" stroke="#2f3b47" stroke-width="{2*s}"/>
    <line x1="{gx - 7*s}" y1="{gy - 11*s}" x2="{gx + 5*s}" y2="{gy - 11*s}" stroke="#f4f8fb" stroke-width="{1.5*s}" stroke-linecap="round" opacity="0.8"/>
  </g>"""


def text_style():
    return f"""<style>@font-face {{ font-family: 'Titillium Web'; font-weight: 700; src: url('file://{FONT}'); }}
text {{ font-family: 'Titillium Web', sans-serif; font-weight: 700; }}</style>"""


def variant_swing():
    """Arm with a swing trail and a rate badge."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 144 144" width="144" height="144">{text_style()}{BACKGROUND}
  <path d="M 30 70 A 46 46 0 0 1 112 52" fill="none" stroke="#ffe6c0" stroke-width="5" stroke-linecap="round" stroke-dasharray="1 10" opacity="0.55"/>
  <path d="M 104 40 L 116 51 L 101 57 Z" fill="#ffe6c0" opacity="0.75"/>
  {inserter(58, 112, (40, 76), (78, 48))}
  <g filter="url(#shadow)">
    <rect x="84" y="94" width="50" height="36" rx="9" fill="url(#badge)" stroke="#5a2a00" stroke-width="2.5"/>
    <text x="109" y="121" font-size="27" text-anchor="middle" fill="#2a1500">/s</text>
  </g>
</svg>"""


def variant_tooltip():
    """Arm next to a tooltip panel with a rate."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 144 144" width="144" height="144">{text_style()}{BACKGROUND}
  {inserter(40, 122, (22, 92), (46, 70), 0.85)}
  <g filter="url(#shadow)">
    <path d="M 70 70 L 82 70 L 60 86 Z" fill="#242324" stroke="#0b0b0b" stroke-width="2" stroke-linejoin="round"/>
    <rect x="62" y="14" width="72" height="58" rx="5" fill="#242324" stroke="#0b0b0b" stroke-width="2"/>
    <path d="M 63 26 L 63 19 Q 63 15 67 15 L 129 15 Q 133 15 133 19 L 133 30 L 63 30 Z" fill="#4a484a"/>
    <rect x="68" y="20" width="32" height="5" rx="2" fill="#ffe6c0" opacity="0.9"/>
    <rect x="66" y="66" width="18" height="5" fill="#242324"/>
    <text x="98" y="61" font-size="27" text-anchor="middle" fill="#ffffff">15/s</text>
  </g>
</svg>"""


def variant_gauge():
    """Speedometer with an inserter in the middle."""
    return f"""<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 144 144" width="144" height="144">{text_style()}{BACKGROUND}
  <path d="M 22 96 A 50 50 0 0 1 122 96" fill="none" stroke="#1a191a" stroke-width="14" stroke-linecap="round"/>
  <path d="M 22 96 A 50 50 0 0 1 47 52.7" fill="none" stroke="#5eb663" stroke-width="10" stroke-linecap="round"/>
  <path d="M 47 52.7 A 50 50 0 0 1 97 52.7" fill="none" stroke="#f2c230" stroke-width="10"/>
  <path d="M 97 52.7 A 50 50 0 0 1 122 96" fill="none" stroke="#e3720b" stroke-width="10" stroke-linecap="round"/>
  {inserter(72, 124, (56, 98), (86, 82), 0.62)}
  <g filter="url(#shadow)">
    <line x1="72" y1="96" x2="106" y2="62" stroke="#ffffff" stroke-width="5" stroke-linecap="round"/>
    <circle cx="72" cy="96" r="7" fill="#e8e8e8" stroke="#222" stroke-width="2"/>
  </g>
  <text x="72" y="40" font-size="22" text-anchor="middle" fill="#ffe6c0">/s</text>
</svg>"""


VARIANTS = {"b-tooltip": variant_tooltip, "a-swing": variant_swing, "c-gauge": variant_gauge}

if __name__ == "__main__":
    out = sys.argv[1]
    os.makedirs(out, exist_ok=True)
    for name, draw in VARIANTS.items():
        svg = draw()
        open(f"{out}/{name}.svg", "w").write(svg)
        page = "<!doctype html><html><head><meta charset='utf-8'><style>html,body{margin:0;background:transparent}</style></head><body>%s</body></html>"
        open(f"{out}/{name}.html", "w").write(page % svg)
    # Preview sheet: each variant large and at real size.
    cells = "".join(
        f"<div class='c'><div class='n'>{name}</div><div class='big'>{draw().replace('width=\"144\" height=\"144\"', 'width=\"288\" height=\"288\"')}</div>"
        f"<div class='small'>{draw()}<span>144 px</span></div></div>" for name, draw in VARIANTS.items())
    open(f"{out}/preview.html", "w").write(
        "<!doctype html><html><head><meta charset='utf-8'><style>body{margin:0;padding:24px;background:#16150f;color:#ccc;"
        "font-family:sans-serif;display:flex;gap:28px}.n{font-size:18px;margin-bottom:8px;color:#ffe6c0}"
        ".small{display:flex;align-items:end;gap:10px;margin-top:12px}.small span{font-size:13px}</style></head><body>"
        + cells + "</body></html>")
