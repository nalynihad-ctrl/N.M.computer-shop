import os
import textwrap

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "static", "uploads")

W = H = 600

STYLES = {
    "gpu": ("#7c5cff", "#22d3ee", "Graphics Card"),
    "cpu": ("#4f8cff", "#a855f7", "Processor"),
    "ram": ("#22d3ee", "#34d399", "Memory"),
    "motherboard": ("#34d399", "#facc15", "Motherboard"),
    "ssd": ("#f472b6", "#8b5cf6", "Solid State Drive"),
    "hdd": ("#38bdf8", "#6366f1", "Hard Disk Drive"),
    "psu": ("#fb7185", "#f59e0b", "Power Supply"),
    "case": ("#a855f7", "#ec4899", "PC Case"),
    "cooler": ("#22d3ee", "#60a5fa", "CPU Cooler"),
    "monitor": ("#60a5fa", "#c084fc", "Monitor"),
    "keyboard": ("#f59e0b", "#ef4444", "Keyboard"),
    "mouse": ("#34d399", "#06b6d4", "Mouse"),
    "headset": ("#f472b6", "#a855f7", "Headset"),
    "laptop": ("#818cf8", "#22d3ee", "Laptop"),
    "accessories": ("#facc15", "#fb7185", "Accessories"),
    "router": ("#38bdf8", "#a855f7", "Networking"),
}


def icon(kind):
    """Return an SVG fragment (white line-art) for the given hardware kind."""
    white = 'fill="none" stroke="#ffffff" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"'
    solid = 'fill="#ffffff" fill-opacity="0.92"'
    soft = 'fill="#ffffff" fill-opacity="0.25"'

    if kind == "gpu":
        return f'''
        <rect x="120" y="230" width="360" height="150" rx="14" {white}/>
        <circle cx="205" cy="305" r="45" {white}/>
        <circle cx="395" cy="305" r="45" {white}/>
        <line x1="120" y1="380" x2="480" y2="380" {white}/>
        <rect x="140" y="392" width="30" height="24" {solid}/>
        <rect x="300" y="210" width="120" height="20" rx="6" {soft}/>'''
    if kind == "cpu":
        return f'''
        <rect x="190" y="190" width="220" height="220" rx="18" {white}/>
        <rect x="245" y="245" width="110" height="110" rx="10" {soft}/>
        <rect x="275" y="275" width="50" height="50" rx="6" {white}/>
        <line x1="230" y1="160" x2="230" y2="190" {white}/>
        <line x1="300" y1="160" x2="300" y2="190" {white}/>
        <line x1="370" y1="160" x2="370" y2="190" {white}/>
        <line x1="230" y1="410" x2="230" y2="440" {white}/>
        <line x1="300" y1="410" x2="300" y2="440" {white}/>
        <line x1="370" y1="410" x2="370" y2="440" {white}/>'''
    if kind == "ram":
        return f'''
        <rect x="130" y="250" width="340" height="110" rx="10" {white}/>
        <rect x="165" y="280" width="55" height="50" {soft}/>
        <rect x="235" y="280" width="55" height="50" {soft}/>
        <rect x="305" y="280" width="55" height="50" {soft}/>
        <rect x="375" y="280" width="55" height="50" {soft}/>
        <line x1="165" y1="360" x2="165" y2="385" {white}/>
        <line x1="210" y1="360" x2="210" y2="385" {white}/>
        <line x1="390" y1="360" x2="390" y2="385" {white}/>
        <line x1="435" y1="360" x2="435" y2="385" {white}/>'''
    if kind == "motherboard":
        return f'''
        <rect x="140" y="150" width="320" height="300" rx="16" {white}/>
        <rect x="185" y="195" width="90" height="90" rx="8" {soft}/>
        <rect x="185" y="195" width="90" height="90" rx="8" {white}/>
        <line x1="320" y1="200" x2="430" y2="200" {white}/>
        <line x1="320" y1="230" x2="430" y2="230" {white}/>
        <line x1="320" y1="260" x2="430" y2="260" {white}/>
        <circle cx="400" cy="370" r="30" {soft}/>'''
    if kind == "ssd":
        return f'''
        <rect x="180" y="210" width="240" height="180" rx="14" {white}/>
        <line x1="180" y1="290" x2="420" y2="290" {white}/>
        <circle cx="230" cy="250" r="14" {soft}/>
        <rect x="330" y="235" width="60" height="30" rx="6" {soft}/>
        <line x1="230" y1="330" x2="370" y2="330" {white}/>'''
    if kind == "hdd":
        return f'''
        <rect x="160" y="210" width="280" height="180" rx="14" {white}/>
        <circle cx="300" cy="300" r="60" {white}/>
        <circle cx="300" cy="300" r="18" {soft}/>
        <line x1="150" y1="345" x2="450" y2="345" {white}/>'''
    if kind == "psu":
        return f'''
        <rect x="170" y="210" width="260" height="180" rx="12" {white}/>
        <circle cx="300" cy="300" r="55" {white}/>
        <circle cx="300" cy="300" r="14" {soft}/>
        <line x1="300" y1="245" x2="300" y2="355" {white}/>
        <line x1="245" y1="300" x2="355" y2="300" {white}/>'''
    if kind == "case":
        return f'''
        <rect x="200" y="140" width="200" height="320" rx="14" {white}/>
        <circle cx="300" cy="215" r="35" {white}/>
        <circle cx="300" cy="215" r="10" {soft}/>
        <rect x="245" y="280" width="110" height="40" rx="6" {soft}/>
        <rect x="245" y="345" width="110" height="40" rx="6" {soft}/>'''
    if kind == "cooler":
        return f'''
        <circle cx="300" cy="290" r="120" {white}/>
        <circle cx="300" cy="290" r="28" {soft}/>
        <path d="M300 170 Q340 230 300 290 Q260 350 300 410" {white}/>
        <path d="M420 290 Q360 330 300 290 Q240 250 180 290" {white}/>'''
    if kind == "monitor":
        return f'''
        <rect x="140" y="160" width="320" height="210" rx="12" {white}/>
        <rect x="170" y="190" width="260" height="150" rx="6" {soft}/>
        <line x1="300" y1="370" x2="300" y2="420" {white}/>
        <line x1="235" y1="425" x2="365" y2="425" {white}/>'''
    if kind == "keyboard":
        return f'''
        <rect x="110" y="230" width="380" height="160" rx="14" {white}/>
        <line x1="110" y1="310" x2="490" y2="310" {white}/>
        <line x1="110" y1="360" x2="490" y2="360" {white}/>
        <line x1="200" y1="230" x2="200" y2="390" {white}/>
        <line x1="290" y1="230" x2="290" y2="390" {white}/>
        <line x1="380" y1="230" x2="380" y2="390" {white}/>'''
    if kind == "mouse":
        return f'''
        <rect x="220" y="170" width="160" height="260" rx="80" {white}/>
        <line x1="300" y1="170" x2="300" y2="255" {white}/>
        <line x1="245" y1="255" x2="355" y2="255" {white}/>
        <circle cx="300" cy="215" r="16" {soft}/>'''
    if kind == "headset":
        return f'''
        <path d="M180 320 L180 260 A120 120 0 0 1 420 260 L420 320" {white}/>
        <rect x="150" y="315" width="70" height="110" rx="26" {white}/>
        <rect x="380" y="315" width="70" height="110" rx="26" {white}/>
        <path d="M420 400 Q380 450 320 450" {white}/>'''
    if kind == "laptop":
        return f'''
        <rect x="160" y="180" width="280" height="180" rx="12" {white}/>
        <rect x="190" y="210" width="220" height="120" rx="6" {soft}/>
        <path d="M120 400 L480 400 L450 360 L150 360 Z" {white}/>
        <line x1="270" y1="382" x2="330" y2="382" {white}/>'''
    if kind == "accessories":
        return f'''
        <rect x="270" y="150" width="60" height="120" rx="10" {white}/>
        <rect x="270" y="270" width="60" height="180" rx="14" {white}/>
        <line x1="300" y1="300" x2="300" y2="420" {soft}/>
        <path d="M200 210 l70 60 l-70 60" {white}/>'''
    if kind == "router":
        return f'''
        <rect x="150" y="280" width="300" height="140" rx="18" {white}/>
        <line x1="210" y1="280" x2="150" y2="160" {white}/>
        <line x1="390" y1="280" x2="450" y2="160" {white}/>
        <circle cx="230" cy="350" r="12" {soft}/>
        <circle cx="300" cy="350" r="12" {soft}/>
        <circle cx="370" cy="350" r="12" {soft}/>'''
    return '<circle cx="300" cy="300" r="130" ' + white + '/>'


TEMPLATE = '''<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}" role="img" aria-label="{label}">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="1">
      <stop offset="0%" stop-color="{c1}"/>
      <stop offset="100%" stop-color="{c2}"/>
    </linearGradient>
    <radialGradient id="glow" cx="50%" cy="40%" r="65%">
      <stop offset="0%" stop-color="#ffffff" stop-opacity="0.28"/>
      <stop offset="100%" stop-color="#ffffff" stop-opacity="0"/>
    </radialGradient>
    <pattern id="grid" width="40" height="40" patternUnits="userSpaceOnUse">
      <path d="M40 0 H0 V40" fill="none" stroke="#ffffff" stroke-opacity="0.07" stroke-width="1"/>
    </pattern>
  </defs>
  <rect width="{w}" height="{h}" fill="url(#bg)"/>
  <rect width="{w}" height="{h}" fill="url(#grid)"/>
  <rect width="{w}" height="{h}" fill="url(#glow)"/>
  <circle cx="{w}" cy="0" r="220" fill="#000000" fill-opacity="0.10"/>
  {icon}
  <text x="50%" y="92%" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif"
        font-size="30" font-weight="700" fill="#ffffff" fill-opacity="0.95">{label}</text>
</svg>
'''


def main():
    os.makedirs(OUT, exist_ok=True)
    for kind, (c1, c2, label) in STYLES.items():
        svg = TEMPLATE.format(w=W, h=H, c1=c1, c2=c2, label=label, icon=textwrap.indent(icon(kind), "  "))
        with open(os.path.join(OUT, f"{kind}.svg"), "w", encoding="utf-8") as f:
            f.write(svg)
    # brand logo
    logo = '''<svg xmlns="http://www.w3.org/2000/svg" width="64" height="64" viewBox="0 0 64 64">
  <defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1">
    <stop offset="0%" stop-color="#7c5cff"/><stop offset="100%" stop-color="#22d3ee"/>
  </linearGradient></defs>
  <rect width="64" height="64" rx="16" fill="url(#g)"/>
  <rect x="16" y="16" width="32" height="32" rx="7" fill="none" stroke="#fff" stroke-width="4"/>
  <rect x="26" y="26" width="12" height="12" rx="3" fill="#fff"/>
  <path d="M32 8v8M32 48v8M8 32h8M48 32h8" stroke="#fff" stroke-width="4" stroke-linecap="round"/>
</svg>'''
    with open(os.path.join(OUT, "logo.svg"), "w", encoding="utf-8") as f:
        f.write(logo)
    print(f"Generated {len(STYLES) + 1} SVG images in {OUT}")


if __name__ == "__main__":
    main()
