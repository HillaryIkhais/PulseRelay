#!/usr/bin/env python3
"""Generate PulseRelay architecture diagram as PNG."""
from PIL import Image, ImageDraw, ImageFont
import os

W, H = 1200, 800
img = Image.new('RGB', (W, H), '#0a0e1a')
draw = ImageDraw.Draw(img)

# Try to get a font
try:
    font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 16)
    font_sm = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 13)
    font_lg = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 22)
    font_title = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 28)
except:
    font = ImageFont.load_default()
    font_sm = font
    font_lg = font
    font_title = font

def box(x, y, w, h, label, color, sublabel=None):
    draw.rounded_rectangle([x, y, x+w, y+h], radius=10, fill='#1a1f35', outline=color, width=2)
    bbox = draw.textbbox((0,0), label, font=font)
    tw = bbox[2] - bbox[0]
    draw.text((x + (w-tw)//2, y + (h//2) - (12 if sublabel else 6)), label, fill=color, font=font)
    if sublabel:
        bbox2 = draw.textbbox((0,0), sublabel, font=font_sm)
        tw2 = bbox2[2] - bbox2[0]
        draw.text((x + (w-tw2)//2, y + h//2 + 8), sublabel, fill='#8892b0', font=font_sm)

def arrow(x1, y1, x2, y2, color='#4a9eff'):
    draw.line([(x1, y1), (x2, y2)], fill=color, width=2)
    # arrowhead
    import math
    angle = math.atan2(y2-y1, x2-x1)
    size = 8
    draw.polygon([
        (x2, y2),
        (x2 - size*math.cos(angle-0.4), y2 - size*math.sin(angle-0.4)),
        (x2 - size*math.cos(angle+0.4), y2 - size*math.sin(angle+0.4)),
    ], fill=color)

# Title
draw.text((W//2 - 180, 20), "PulseRelay Architecture", fill='#e6f1ff', font=font_title)

# Layer labels
draw.text((30, 85), "INPUT", fill='#4a9eff', font=font_sm)
draw.text((30, 230), "PROCESSING", fill='#f59e0b', font=font_sm)
draw.text((30, 400), "STATE & SAFETY", fill='#10b981', font=font_sm)
draw.text((30, 560), "OUTPUT", fill='#a78bfa', font=font_sm)
draw.text((30, 700), "INFRASTRUCTURE", fill='#ef4444', font=font_sm)

# INPUT layer
box(180, 75, 180, 50, "Paramedic Voice", '#4a9eff', "Browser Microphone")
box(420, 75, 180, 50, "Web Speech API", '#4a9eff', "Speech-to-Text")
box(660, 75, 180, 50, "Gemini 3.5 Flash", '#4a9eff', "Clinical Extraction")

# PROCESSING layer
box(180, 220, 180, 50, "Event Processor", '#f59e0b', "Regex + NLP")
box(420, 220, 180, 50, "Extraction Agent", '#f59e0b', "Gemini API Call")
box(660, 220, 180, 50, "Monitoring Agent", '#f59e0b', "Trend Detection")
box(900, 220, 180, 50, "Handoff Agent", '#f59e0b', "Summary Generation")

# STATE & SAFETY layer
box(180, 390, 180, 50, "Patient State", '#10b981', "Dataclass Store")
box(420, 390, 180, 50, "Trends Engine", '#10b981', "Deterministic")
box(660, 390, 180, 50, "Safety Rules", '#10b981', "Validation")
box(900, 390, 180, 50, "Confidence", '#10b981', "Scoring")

# OUTPUT layer
box(180, 550, 180, 50, "Dashboard UI", '#a78bfa', "HTML/CSS/JS")
box(420, 550, 180, 50, "REST API", '#a78bfa', "FastAPI")
box(660, 550, 180, 50, "Handoff Report", '#a78bfa', "Structured JSON")
box(900, 550, 180, 50, "Proactive Alerts", '#a78bfa', "Agent Surfacing")

# INFRASTRUCTURE layer
box(180, 690, 220, 50, "Cloud Run", '#ef4444', "Container Deployment")
box(460, 690, 220, 50, "Firestore", '#ef4444', "Patient State DB")
box(740, 690, 220, 50, "Pub/Sub", '#ef4444', "Event Streaming")

# Arrows — INPUT flow
arrow(270, 125, 510, 125, '#4a9eff')
arrow(510, 125, 750, 125, '#4a9eff')

# INPUT → PROCESSING
arrow(750, 125, 750, 220, '#4a9eff')

# PROCESSING flow
arrow(270, 270, 510, 270, '#f59e0b')
arrow(510, 270, 750, 270, '#f59e0b')
arrow(750, 270, 990, 270, '#f59e0b')

# PROCESSING → STATE
arrow(270, 270, 270, 390, '#f59e0b')
arrow(750, 270, 750, 390, '#f59e0b')

# STATE flow
arrow(270, 440, 510, 440, '#10b981')
arrow(510, 440, 750, 440, '#10b981')
arrow(750, 440, 990, 440, '#10b981')

# STATE → OUTPUT
arrow(270, 440, 270, 550, '#10b981')
arrow(510, 440, 510, 550, '#10b981')
arrow(750, 440, 750, 550, '#10b981')
arrow(990, 440, 990, 550, '#10b981')

# OUTPUT → INFRASTRUCTURE
arrow(290, 600, 290, 690, '#ef4444')
arrow(570, 600, 570, 690, '#ef4444')
arrow(850, 600, 850, 690, '#ef4444')

# Legend
draw.text((950, 85), "KEY DESIGN", fill='#e6f1ff', font=font_sm)
draw.text((950, 108), "AI understands language", fill='#4a9eff', font=font_sm)
draw.text((950, 128), "Code handles state/safety", fill='#10b981', font=font_sm)
draw.text((950, 148), "Never hallucinated vitals", fill='#f59e0b', font=font_sm)
draw.text((950, 168), "Deterministic trends", fill='#a78bfa', font=font_sm)

out = os.path.join(os.path.dirname(__file__), 'ARCHITECTURE.png')
img.save(out, 'PNG')
print(f"Saved: {out}")
