#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Subtitor-Local ✦ — Ultimate subtitle editor & exporter.
"""

# ══════════════════════════════════════════════════════════════
# IMPORTS
# ══════════════════════════════════════════════════════════════
import os
import sys
import threading
import tempfile
import time
import unicodedata
import subprocess
import tkinter as tk
from tkinter import filedialog, messagebox, colorchooser
from dataclasses import dataclass, asdict
from typing import Callable, List, Dict, Optional, Tuple
import logging

import customtkinter as ctk
import cv2
import numpy as np
from PIL import Image, ImageTk, ImageDraw, ImageFont, ImageFilter

try:
    import pygame
    pygame.mixer.init()
    HAS_PYGAME = True
except Exception:
    HAS_PYGAME = False

try:
    from moviepy import VideoFileClip
    HAS_MOVIEPY = True
except Exception:
    HAS_MOVIEPY = False

try:
    import torch
    import whisperx
    HAS_WHISPER = True
except Exception:
    HAS_WHISPER = False

logging.basicConfig(
    filename=os.path.join(tempfile.gettempdir(), "subtitor.log"),
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

ACCENT      = "#6C63FF"
BG_ROOT     = "#0D0D0F"
BG_PANEL    = "#13131A"
BG_CARD     = "#1E1E2E"
BG_CARD2    = "#252535"
TEXT_DIM    = "#6B7280"
TEXT_BRIGHT = "#F9FAFB"
GREEN_BTN   = "#059669"
GREEN_HOV   = "#047857"
BLUE_BTN    = "#1d4ed8"
BLUE_HOV    = "#1e40af"
WARNING     = "#F59E0B"
DANGER      = "#EF4444"


# ══════════════════════════════════════════════════════════════
# STYLE CONFIG
# ══════════════════════════════════════════════════════════════
@dataclass
class StyleConfig:
    font_size: int = 60
    text_color: str = "#FFFFFF"
    font_path: Optional[str] = None
    bold: bool = True
    italic: bool = False
    uppercase: bool = False
    outline_color: str = "#000000"
    outline_width: int = 2
    shadow: bool = False
    shadow_color: str = "#000000"
    shadow_opacity: int = 180
    shadow_offset_x: int = 3
    shadow_offset_y: int = 3
    shadow_blur: int = 4
    word_bg: bool = False
    word_bg_color: str = "#000000"
    word_bg_opacity: int = 160
    word_bg_padding: int = 10
    word_bg_radius: int = 8
    highlight: bool = True
    highlight_color: str = "#FFD700"
    highlight_outline: str = "#000000"
    highlight_done_color: str = "#AAAAAA"
    words_per_display: int = 1
    y_position: float = 0.82
    x_position: float = 0.5
    align: str = "center"
    animation_in: str = "pop"
    animation_duration: float = 0.12
    effect_mode: str = "fixed"
    gradient_color1: str = "#FF6B6B"
    gradient_color2: str = "#4ECDC4"
    export_resolution: str = "source"
    export_bg: str = "video"   # "video" | "green" | "black"


# ══════════════════════════════════════════════════════════════
# PRESETS (CapCut / TikTok inspired)
# ══════════════════════════════════════════════════════════════
PRESETS = {
    "TikTok Neon": {
        "text_color": "#FFFFFF", "outline_color": "#FF00FF", "outline_width": 4,
        "shadow": True, "shadow_color": "#000000", "shadow_opacity": 220,
        "shadow_offset_x": 3, "shadow_offset_y": 3, "shadow_blur": 6,
        "highlight": True, "highlight_color": "#FFD700",
        "animation_in": "bounce", "words_per_display": 1,
    },
    "CapCut Glow": {
        "text_color": "#FFFFFF", "outline_color": "#000000", "outline_width": 2,
        "shadow": True, "shadow_color": "#00BFFF", "shadow_opacity": 200,
        "shadow_offset_x": 2, "shadow_offset_y": 2, "shadow_blur": 10,
        "word_bg": True, "word_bg_color": "#1E1E2E", "word_bg_opacity": 180,
        "word_bg_padding": 15, "word_bg_radius": 12,
        "highlight": True, "highlight_color": "#FFD700", "animation_in": "pop",
    },
    "Minimal White": {
        "text_color": "#FFFFFF", "outline_color": "#000000", "outline_width": 2,
        "shadow": False, "word_bg": False, "highlight": True,
        "highlight_color": "#FFD700", "animation_in": "fade",
    },
    "Bold & Yellow": {
        "text_color": "#FFD700", "outline_color": "#000000", "outline_width": 3,
        "shadow": True, "shadow_opacity": 160, "highlight": False,
        "font_size": 70, "words_per_display": 2, "animation_in": "slide_up",
    },
    "Retro VHS": {
        "text_color": "#00FFCC", "outline_color": "#FF00AA", "outline_width": 3,
        "shadow": True, "shadow_color": "#FF00AA", "shadow_opacity": 140,
        "shadow_offset_x": 4, "shadow_offset_y": 4, "shadow_blur": 2,
        "word_bg": True, "word_bg_color": "#000000", "word_bg_opacity": 200,
        "animation_in": "none", "highlight": True,
    }
}


# ══════════════════════════════════════════════════════════════
# UTILS
# ══════════════════════════════════════════════════════════════
def _hex_to_rgb(h: str) -> Tuple[int, int, int]:
    h = h.strip().lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

def _rgb_to_hex(r, g, b) -> str:
    return f"#{int(r):02x}{int(g):02x}{int(b):02x}"

def _lerp_color(c1, c2, t):
    r1,g1,b1 = _hex_to_rgb(c1)
    r2,g2,b2 = _hex_to_rgb(c2)
    return _rgb_to_hex(r1+(r2-r1)*t, g1+(g2-g1)*t, b1+(b2-b1)*t)

def _negative_color(video_path, t, y_ratio, vid_w, vid_h):
    cap = cv2.VideoCapture(video_path)
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ret, frame = cap.read()
    cap.release()
    if not ret:
        return "#FFFFFF"
    bw, bh = 320, 100
    xc, yc = vid_w//2, int(vid_h*y_ratio)
    x1, x2 = max(0, xc-bw//2), min(vid_w, xc+bw//2)
    y1, y2 = max(0, yc-bh//2), min(vid_h, yc+bh//2)
    roi = frame[y1:y2, x1:x2]
    if roi.size == 0:
        return "#FFFFFF"
    avg = roi.mean(axis=(0,1))
    nr, ng, nb = int(255-avg[2]), int(255-avg[1]), int(255-avg[0])
    luma = 0.299*nr + 0.587*ng + 0.114*nb
    if luma < 80:
        f = 90 / max(luma, 1)
        nr, ng, nb = min(255, int(nr*f)), min(255, int(ng*f)), min(255, int(nb*f))
    return _rgb_to_hex(nr, ng, nb)

def strip_punctuation_from_words(words: List[Dict]) -> List[Dict]:
    """Remove punctuation at start/end of each word (keep apostrophes)."""
    punct = set("!\"#$%&'()*+,-./:;<=>?@[\\]^_`{|}~")
    new_words = []
    for w in words:
        word = w["word"].strip()
        # strip leading/trailing punctuation
        while word and word[0] in punct:
            word = word[1:]
        while word and word[-1] in punct:
            word = word[:-1]
        if word:  # keep only non-empty
            new_w = dict(w)
            new_w["word"] = word
            new_words.append(new_w)
    return new_words


# ══════════════════════════════════════════════════════════════
# FONT LOADING (with supersampling support)
# ══════════════════════════════════════════════════════════════
_SYSTEM_FONTS = [
    "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    "/usr/share/fonts/TTF/DejaVuSans-Bold.ttf",
    "/Library/Fonts/Arial Bold.ttf",
    "C:/Windows/Fonts/arialbd.ttf",
]

def _load_font(font_path, size):
    if font_path and os.path.exists(font_path):
        try:
            return ImageFont.truetype(font_path, size)
        except Exception:
            pass
    for p in _SYSTEM_FONTS:
        if os.path.exists(p):
            try:
                return ImageFont.truetype(p, size)
            except Exception:
                continue
    return ImageFont.load_default()


# ══════════════════════════════════════════════════════════════
# WORD GROUPING & PUNCTUATION HANDLING
# ══════════════════════════════════════════════════════════════
def _is_punct_only(word):
    s = word.strip()
    if not s:
        return True
    return all(unicodedata.category(c).startswith('P') or
               unicodedata.category(c).startswith('Z') for c in s)

def build_display_groups(words, n):
    if n <= 1:
        result = []
        for w in words:
            wc = dict(w)
            wc["group_start"] = w["start"]
            wc["group_end"] = w["end"]
            wc["group_words"] = [w]
            wc["group_idx"] = len(result)
            wc["word_idx_in_group"] = 0
            result.append(wc)
        return result

    merged = []
    for w in words:
        if _is_punct_only(w["word"]):
            if merged:
                merged[-1]["word"] = merged[-1]["word"].rstrip() + w["word"]
                merged[-1]["end"] = w["end"]
        else:
            merged.append(dict(w))

    result = []
    i = 0
    group_idx = 0
    while i < len(merged):
        group = merged[i:i+n]
        g_start, g_end = group[0]["start"], group[-1]["end"]
        for j, gw in enumerate(group):
            wc = dict(gw)
            wc["group_start"] = g_start
            wc["group_end"] = g_end
            wc["group_words"] = group
            wc["group_idx"] = group_idx
            wc["word_idx_in_group"] = j
            result.append(wc)
        i += n
        group_idx += 1
    return result


# ══════════════════════════════════════════════════════════════
# TEXT RENDERING (with super‑sampling & perfect baseline alignment)
# ══════════════════════════════════════════════════════════════
def _ease_out_cubic(t): return 1-(1-t)**3
def _ease_out_back(t):
    c1, c3 = 1.70158, 2.70158
    return 1 + c3*(t-1)**3 + c1*(t-1)**2
def _ease_out_bounce(t):
    n1, d1 = 7.5625, 2.75
    if t < 1/d1:
        return n1*t*t
    elif t < 2/d1:
        t -= 1.5/d1
        return n1*t*t + 0.75
    elif t < 2.5/d1:
        t -= 2.25/d1
        return n1*t*t + 0.9375
    else:
        t -= 2.625/d1
        return n1*t*t + 0.984375

def _apply_anim(img, anim, t):
    if t >= 1.0 or anim == "none":
        return img
    w, h = img.size
    if anim == "fade":
        alpha = img.split()[3].point(lambda p: int(p*t))
        img.putalpha(alpha)
    elif anim == "pop":
        scale = 0.5 + 0.5*_ease_out_back(t)
        nw, nh = max(1, int(w*scale)), max(1, int(h*scale))
        img = img.resize((nw, nh), Image.LANCZOS)
        c = Image.new("RGBA", (w, h), (0,0,0,0))
        c.paste(img, ((w-nw)//2, (h-nh)//2), img)
        img = c
    elif anim == "slide_up":
        off = int(h*(1-_ease_out_cubic(t)))
        c = Image.new("RGBA", (w, h), (0,0,0,0))
        c.paste(img, (0, off), img)
        img = c
    elif anim == "slide_down":
        off = int(h*(1-_ease_out_cubic(t)))
        c = Image.new("RGBA", (w, h), (0,0,0,0))
        c.paste(img, (0, -off), img)
        img = c
    elif anim == "bounce":
        scale = _ease_out_bounce(t)
        nw, nh = max(1, int(w*scale)), max(1, int(h*scale))
        img = img.resize((nw, nh), Image.LANCZOS)
        c = Image.new("RGBA", (w, h), (0,0,0,0))
        c.paste(img, ((w-nw)//2, (h-nh)//2), img)
        img = c
    return img

def _render_group(group_words, current_word_idx, style, base_color, canvas_w, canvas_h, anim_t=1.0, supersample=1):
    """Render a group of words with perfect vertical alignment and optional supersampling."""
    s = style
    # Supersampling: scale up font & everything
    scale = supersample
    font_size_scaled = int(s.font_size * scale)
    font = _load_font(s.font_path, font_size_scaled)
    space_w_scaled = 14 * scale
    outline_scaled = s.outline_width * scale
    shadow_offset_x_scaled = s.shadow_offset_x * scale
    shadow_offset_y_scaled = s.shadow_offset_y * scale
    shadow_blur_scaled = s.shadow_blur * scale
    word_bg_padding_scaled = s.word_bg_padding * scale
    word_bg_radius_scaled = s.word_bg_radius * scale
    # Get font metrics (ascent/descent) for baseline alignment
    try:
        ascent, descent = font.getmetrics()
        # Some fonts don't have getmetrics, fallback
    except:
        ascent = int(font_size_scaled * 0.75)
        descent = int(font_size_scaled * 0.25)

    dummy = Image.new("RGBA", (1,1))
    d = ImageDraw.Draw(dummy)

    # Pre‑compute word boxes and max ascender/descender for this group
    word_data = []
    max_ascent = 0
    max_descent = 0
    for wd in group_words:
        txt = wd["word"].upper() if s.uppercase else wd["word"]
        bbox = d.textbbox((0,0), txt, font=font)
        ww = bbox[2] - bbox[0]
        wh = bbox[3] - bbox[1]
        # bounding box relative to baseline: baseline = 0, top = -ascent, bottom = descent
        # textbbox gives top, left, bottom, right relative to origin (0,0) where origin is baseline-left?
        # Actually origin is baseline-left, so bbox[1] is top (negative), bbox[3] is bottom (positive)
        # Compute actual ascent/descent for this word
        word_ascent = -bbox[1]  # positive value
        word_descent = bbox[3]   # positive value
        max_ascent = max(max_ascent, word_ascent)
        max_descent = max(max_descent, word_descent)
        word_data.append((txt, ww, wh, bbox[0], bbox[1], bbox[2], bbox[3], word_ascent, word_descent))

    # Total dimensions of the whole group
    total_w = sum(wd[1] for wd in word_data) + space_w_scaled * max(0, len(word_data)-1)
    max_h = max_ascent + max_descent
    # Add padding, outline, shadow margins
    pad = outline_scaled + word_bg_padding_scaled + 8
    shex = (abs(shadow_offset_x_scaled) + shadow_blur_scaled + 4) if s.shadow else 0
    img_w = total_w + pad*2 + shex
    img_h = max_h + pad*2 + shex
    # Create image and draw
    img = Image.new("RGBA", (img_w, img_h), (0,0,0,0))
    draw = ImageDraw.Draw(img)

    # Baseline Y inside the image (from top)
    baseline_y = pad + shex//2 + max_ascent

    cursor_x = pad + shex//2

    for i, (txt, ww, wh, left_off, top_off, right_off, bottom_off, w_ascent, w_descent) in enumerate(word_data):
        # Text baseline relative to its own top: w_ascent from top to baseline
        # We want to draw such that baseline aligns with baseline_y
        # The text origin (left, baseline) should be at (cursor_x, baseline_y)
        tx = cursor_x
        ty = baseline_y

        # Determine colors
        if i == current_word_idx and s.highlight:
            tcol = _hex_to_rgb(s.highlight_color)
            ocol = _hex_to_rgb(s.highlight_outline)
        elif current_word_idx >= 0 and i < current_word_idx and s.words_per_display > 1:
            tcol = _hex_to_rgb(s.highlight_done_color)
            ocol = _hex_to_rgb(s.outline_color)
        else:
            tcol = _hex_to_rgb(base_color)
            ocol = _hex_to_rgb(s.outline_color)

        # Word background
        if s.word_bg:
            bg = _hex_to_rgb(s.word_bg_color)
            bbox = [tx + left_off - word_bg_padding_scaled,
                    baseline_y - w_ascent - word_bg_padding_scaled,
                    tx + right_off + word_bg_padding_scaled,
                    baseline_y + w_descent + word_bg_padding_scaled]
            draw.rounded_rectangle(bbox,
                                   radius=word_bg_radius_scaled,
                                   fill=(*bg, s.word_bg_opacity))

        # Shadow
        if s.shadow:
            sh = _hex_to_rgb(s.shadow_color)
            ow = outline_scaled
            ox, oy = shadow_offset_x_scaled, shadow_offset_y_scaled
            for dx in range(-ow, ow+1):
                for dy in range(-ow, ow+1):
                    draw.text((tx+ox+dx, ty+oy+dy), txt, font=font, fill=(*sh, s.shadow_opacity))
            draw.text((tx+ox, ty+oy), txt, font=font, fill=(*sh, s.shadow_opacity))

        # Outline
        ow = outline_scaled
        if ow > 0:
            for dx in range(-ow, ow+1):
                for dy in range(-ow, ow+1):
                    if dx == 0 and dy == 0:
                        continue
                    draw.text((tx+dx, ty+dy), txt, font=font, fill=(*ocol, 255))

        # Main text
        draw.text((tx, ty), txt, font=font, fill=(*tcol, 255))

        # Glow effect for highlighted current word
        if i == current_word_idx and s.highlight and s.words_per_display > 1:
            glow = Image.new("RGBA", img.size, (0,0,0,0))
            gd = ImageDraw.Draw(glow)
            gd.text((tx, ty), txt, font=font, fill=(*_hex_to_rgb(s.highlight_color), 80))
            glow = glow.filter(ImageFilter.GaussianBlur(4*scale))
            img = Image.alpha_composite(img, glow)
            draw = ImageDraw.Draw(img)

        cursor_x += ww + space_w_scaled

    # Animation
    img = _apply_anim(img, s.animation_in, anim_t)

    # Downsample if supersampled
    if supersample > 1:
        new_w = img_w // supersample
        new_h = img_h // supersample
        img = img.resize((new_w, new_h), Image.LANCZOS)

    # Paste on canvas
    canvas = Image.new("RGBA", (canvas_w, canvas_h), (0,0,0,0))
    if s.align == "center":
        x_px = int(canvas_w * s.x_position) - img.width // 2
    elif s.align == "left":
        x_px = int(canvas_w * s.x_position)
    else:
        x_px = int(canvas_w * s.x_position) - img.width
    x_px = max(0, min(canvas_w - img.width, x_px))
    y_px = int(canvas_h * s.y_position) - img.height // 2
    y_px = max(0, min(canvas_h - img.height, y_px))
    canvas.paste(img, (x_px, y_px), img)
    return np.array(canvas)

def _get_overlay(t, enriched, style, base_color, cw, ch, supersample=1):
    current = None
    for ew in enriched:
        if ew["group_start"] <= t <= ew["group_end"]:
            current = ew
            break
    if current is None:
        return None
    gw = current["group_words"]
    cur_wi = -1
    if style.words_per_display > 1 and style.highlight:
        for i, w in enumerate(gw):
            if w["start"] <= t:
                cur_wi = i
    anim_t = min((t - current["group_start"]) / max(style.animation_duration, 0.01), 1.0)
    return _render_group(gw, cur_wi, style, base_color, cw, ch, anim_t, supersample)


# ══════════════════════════════════════════════════════════════
# PREVIEW FRAME (optimized for speed)
# ══════════════════════════════════════════════════════════════
def render_preview_frame(video_path, t, word_timestamps, style, target_w=800, cap=None):
    close_cap = False
    if cap is None:
        cap = cv2.VideoCapture(video_path)
        close_cap = True
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ret, frame = cap.read()
    if close_cap:
        cap.release()
    if not ret:
        return None
    vh, vw = frame.shape[:2]
    # target_w is max width, but we keep aspect ratio
    scale = min(target_w / vw, 1.0)
    target_w = int(vw * scale)
    target_h = int(vh * scale)
    fr = cv2.resize(frame, (target_w, target_h))
    bg = style.export_bg
    if bg == "green":
        base = Image.new("RGBA", (target_w, target_h), (0, 255, 0, 255))
    elif bg == "black":
        base = Image.new("RGBA", (target_w, target_h), (0, 0, 0, 255))
    else:
        base = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).convert("RGBA")
    enriched = build_display_groups(word_timestamps, style.words_per_display)
    overlay = _get_overlay(t, enriched, style, style.text_color, target_w, target_h, supersample=1)
    if overlay is not None:
        base = Image.alpha_composite(base, Image.fromarray(overlay.astype(np.uint8)))
    return cv2.cvtColor(np.array(base.convert("RGB")), cv2.COLOR_RGB2BGR)


# ══════════════════════════════════════════════════════════════
# VIDEO COMPOSER (with high-quality text)
# ══════════════════════════════════════════════════════════════
import shutil

class VideoComposer:
    def __init__(self, video_path, style):
        self.video_path = video_path
        self.style = style
        cap = cv2.VideoCapture(video_path)
        self.vid_w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        self.vid_h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
        self.total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()

    def _out_size(self):
        res = self.style.export_resolution
        ratio = self.vid_w / self.vid_h
        if res == "1080p":
            return (1920, int(1920/ratio)) if ratio >= 1 else (int(1080*ratio), 1080)
        if res == "4k":
            return (3840, int(3840/ratio)) if ratio >= 1 else (int(2160*ratio), 2160)
        return (self.vid_w, self.vid_h)

    def _word_color(self, t):
        s = self.style
        if s.effect_mode == "negative":
            return _negative_color(self.video_path, t, s.y_position, self.vid_w, self.vid_h)
        if s.effect_mode == "gradient":
            return _lerp_color(s.gradient_color1, s.gradient_color2, (t % 3.0) / 3.0)
        return s.text_color

    def compose(self, word_timestamps, output_path, mode="export", progress_callback=None):
        def _prog(v, msg):
            if progress_callback:
                progress_callback(v, msg)

        ow, oh = self._out_size()
        ow = ow if ow % 2 == 0 else ow + 1   # dimensions paires pour le codec
        oh = oh if oh % 2 == 0 else oh + 1

        s = self.style
        words = [w for w in word_timestamps if w["start"] < 45] if mode == "preview" else word_timestamps
        for w in words:
            if not w["word"].strip():
                w["word"] = "[……]"
        enriched = build_display_groups(words, s.words_per_display)
        _prog(0.10, "Preparing video writer...")

        temp_video = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        writer = cv2.VideoWriter(temp_video, fourcc, self.fps, (ow, oh))

        cap = cv2.VideoCapture(self.video_path)
        frame_idx = 0
        total = self.total_frames or 1
        supersample = 2 if (s.export_resolution == "4k" or s.font_size >= 80) else 1

        _prog(0.20, "Rendering frames...")
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                t = frame_idx / self.fps
                bg = s.export_bg

                if bg == "green":
                    base = Image.new("RGB", (ow, oh), (0, 255, 0))
                elif bg == "black":
                    base = Image.new("RGB", (ow, oh), (0, 0, 0))
                else:
                    fr = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    img = Image.fromarray(fr)
                    if (ow, oh) != (self.vid_w, self.vid_h):
                        scale = min(ow / self.vid_w, oh / self.vid_h)
                        new_w = int(self.vid_w * scale)
                        new_h = int(self.vid_h * scale)
                        img = img.resize((new_w, new_h), Image.LANCZOS)
                        base = Image.new("RGB", (ow, oh), (0, 0, 0))
                        x_off = (ow - new_w) // 2
                        y_off = (oh - new_h) // 2
                        base.paste(img, (x_off, y_off))
                    else:
                        base = img

                ov = _get_overlay(t, enriched, s, self._word_color(t), ow, oh, supersample)
                if ov is not None:
                    overlay_img = Image.fromarray(ov, "RGBA")
                    base_rgba = base.convert("RGBA")
                    composited = Image.alpha_composite(base_rgba, overlay_img)
                    base = composited.convert("RGB")

                frame_out = cv2.cvtColor(np.array(base), cv2.COLOR_RGB2BGR)
                writer.write(frame_out)

                frame_idx += 1
                if frame_idx % 30 == 0:
                    _prog(0.20 + 0.70 * (frame_idx / total), f"Frame {frame_idx}/{total}")
        finally:
            cap.release()
            writer.release()

        _prog(0.90, "Adding audio...")
        import shutil
        try:
            # Fusion audio sans pipe
            cmd = [
                "ffmpeg", "-y",
                "-i", temp_video,
                "-i", self.video_path,
                "-c:v", "copy",
                "-c:a", "aac",
                "-map", "0:v:0",
                "-map", "1:a:0",
                "-shortest",
                output_path
            ]
            subprocess.run(cmd, capture_output=True, check=True, text=True)
        except Exception:
            shutil.copy(temp_video, output_path)   # vidéo muette
        finally:
            if os.path.exists(temp_video):
                os.unlink(temp_video)

        _prog(1.0, "Export finished ✓")

# ══════════════════════════════════════════════════════════════
# TRANSCRIBER (WhisperX)
# ══════════════════════════════════════════════════════════════
class Transcriber:
    def __init__(self, model_size="small", language=None):
        if not HAS_WHISPER:
            raise RuntimeError("whisperX not installed. Run: pip install whisperx torch")
        self.model_size = model_size
        self.language = language
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.compute_type = "float16" if self.device == "cuda" else "float32"

    def transcribe(self, video_path, progress_callback=None, strip_punct=False):
        def _p(v, msg):
            if progress_callback:
                progress_callback(v, msg)
        _p(0.10, "Extracting audio…")
        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp.close()
        try:
            clip = VideoFileClip(video_path)
            if not clip.audio:
                raise ValueError("No audio track.")
            clip.audio.write_audiofile(tmp.name, logger=None)
            clip.close()
        except Exception as e:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)
            raise RuntimeError(f"Audio extraction failed: {e}")

        _p(0.25, f"Loading Whisper model ({self.model_size})…")
        try:
            model = whisperx.load_model(self.model_size, self.device,
                                        compute_type=self.compute_type, language=self.language)
            audio = whisperx.load_audio(tmp.name)
            _p(0.40, "Transcribing…")
            result = model.transcribe(audio, batch_size=16)
            _p(0.65, "Forced alignment…")
            model_a, meta = whisperx.load_align_model(language_code=result["language"], device=self.device)
            aligned = whisperx.align(result["segments"], model_a, meta, audio, self.device, return_char_alignments=False)
        except Exception as e:
            raise
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

        _p(0.85, "Extracting timestamps…")
        words = []
        for seg in aligned.get("segments", []):
            for w in seg.get("words", []):
                if "start" not in w or "end" not in w:
                    continue
                words.append({"word": w["word"].strip(), "start": float(w["start"]), "end": float(w["end"])})
        if not words:
            raise RuntimeError("No words detected.")
        if strip_punct:
            words = strip_punctuation_from_words(words)
        _p(0.95, f"{len(words)} words aligned.")
        return words


# ══════════════════════════════════════════════════════════════
# SRT EXPORT
# ══════════════════════════════════════════════════════════════
def _fmt_time(sec):
    h, m, s = int(sec//3600), int((sec%3600)//60), int(sec%60)
    ms = int((sec - int(sec)) * 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"

def export_srt(words, path, words_per_block=5):
    lines = []
    for i in range(0, len(words), words_per_block):
        chunk = words[i:i+words_per_block]
        lines.append(str(i//words_per_block + 1))
        lines.append(f"{_fmt_time(chunk[0]['start'])} --> {_fmt_time(chunk[-1]['end'])}")
        lines.append(" ".join(w["word"] for w in chunk))
        lines.append("")
    open(path, "w", encoding="utf-8").write("\n".join(lines))

def export_word_srt(words, path):
    lines = []
    for i, w in enumerate(words, 1):
        lines.append(str(i))
        lines.append(f"{_fmt_time(w['start'])} --> {_fmt_time(w['end'])}")
        lines.append(w["word"])
        lines.append("")
    open(path, "w", encoding="utf-8").write("\n".join(lines))


# ══════════════════════════════════════════════════════════════
# AUDIO PLAYER (preview)
# ══════════════════════════════════════════════════════════════
class AudioPlayer:
    def __init__(self):
        self._audio_path = None

    def load(self, video_path):
        self._audio_path = None
        if not (HAS_PYGAME and HAS_MOVIEPY):
            return
        try:
            tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
            tmp.close()
            clip = VideoFileClip(video_path)
            if clip.audio:
                clip.audio.write_audiofile(tmp.name, logger=None)
                self._audio_path = tmp.name
            clip.close()
        except Exception:
            pass

    def play(self, t):
        if not (HAS_PYGAME and self._audio_path):
            return
        try:
            pygame.mixer.music.load(self._audio_path)
            pygame.mixer.music.play(start=t)
        except Exception:
            pass

    def stop(self):
        if HAS_PYGAME:
            try:
                pygame.mixer.music.stop()
            except Exception:
                pass


# ══════════════════════════════════════════════════════════════
# UI WIDGETS
# ══════════════════════════════════════════════════════════════
class ColorBtn(ctk.CTkButton):
    def __init__(self, parent, color, on_change, **kw):
        super().__init__(parent, width=36, height=28, text="", corner_radius=6,
                         fg_color=color, hover=False, **kw)
        self._color = color
        self._on_change = on_change
        self.configure(command=self._pick)

    def _pick(self):
        r = colorchooser.askcolor(color=self._color, title="Couleur")
        if r and r[1]:
            self._color = r[1]
            self.configure(fg_color=self._color)
            self._on_change(self._color)

    def set_color(self, c):
        self._color = c
        self.configure(fg_color=c)


class PreviewPlayer(ctk.CTkFrame):
    def __init__(self, parent, **kw):
        super().__init__(parent, fg_color=BG_CARD, corner_radius=12, **kw)
        self._video_path = None
        self._words = []
        self._style = None
        self._playing = False
        self._t = 0.0
        self._duration = 0.0
        self._fps = 30.0
        self._cap = None
        self._cap_lock = threading.Lock()
        self._audio = AudioPlayer()
        self._after_id = None
        self._pending_refresh = False  # flag pour refresh thread-safe

        self.canvas = tk.Canvas(self, bg="#000000", highlightthickness=0)
        self.canvas.pack(fill="both", expand=True, padx=6, pady=(6, 0))
        self._img_ref = None

        ctrl = ctk.CTkFrame(self, fg_color=BG_CARD2, corner_radius=8)
        ctrl.pack(fill="x", padx=8, pady=6)
        self.btn_play = ctk.CTkButton(ctrl, text="▶", width=44, height=34,
                                      fg_color=ACCENT, hover_color="#5A52D5",
                                      font=("", 14), command=self._toggle_play)
        self.btn_play.pack(side="left", padx=(8, 6), pady=5)
        self.slider = ctk.CTkSlider(ctrl, from_=0, to=100, command=self._seek,
                                    button_color=ACCENT, button_hover_color="#5A52D5",
                                    progress_color=ACCENT)
        self.slider.pack(side="left", fill="x", expand=True, padx=4)
        self.lbl_time = ctk.CTkLabel(ctrl, text="0:00 / 0:00", width=95,
                                     font=("", 11), text_color=TEXT_DIM)
        self.lbl_time.pack(side="right", padx=(4, 10))
        self._placeholder()

    def _placeholder(self):
        self.canvas.delete("all")
        self.canvas.create_text(400, 200,
            text="🎬  Load a video & transcribe\nto see the preview",
            fill="#444", font=("", 13), justify="center")

    def load(self, video_path, words, style):
        self._video_path = video_path
        self._words = words
        self._style = style
        with self._cap_lock:
            if self._cap:
                self._cap.release()
            self._cap = cv2.VideoCapture(video_path)
            self._fps = self._cap.get(cv2.CAP_PROP_FPS) or 30.0
            self._duration = self._cap.get(cv2.CAP_PROP_FRAME_COUNT) / self._fps
        self._t = 0.0
        self.slider.configure(to=self._duration)
        self._render(0.0)
        threading.Thread(target=self._audio.load, args=(video_path,), daemon=True).start()

    def _render(self, t):
        if not self._video_path or self._cap is None:
            return
        cw = self.canvas.winfo_width() or 760
        ch = self.canvas.winfo_height() or 430
        with self._cap_lock:
            self._cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
            ret, frame = self._cap.read()
        if not ret:
            return
        vh, vw = frame.shape[:2]
        scale = min(cw / vw, ch / vh)
        dw = int(vw * scale)
        dh = int(vh * scale)
        fr = cv2.resize(frame, (dw, dh))

        # Déterminer le fond selon export_bg
        bg_mode = self._style.export_bg if self._style else "video"

        # En green/black : la preview doit avoir le même ratio que la vidéo (dw x dh)
        # On crée l'image aux dimensions dw x dh puis on la centre dans le canvas
        if bg_mode == "green":
            canvas_img = Image.new("RGBA", (dw, dh), (0, 255, 0, 255))
        elif bg_mode == "black":
            canvas_img = Image.new("RGBA", (dw, dh), (0, 0, 0, 255))
        else:  # video
            canvas_img = Image.new("RGBA", (cw, ch), (0, 0, 0, 255))
            img = Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB)).convert("RGBA")
            x_offset = (cw - dw) // 2
            y_offset = (ch - dh) // 2
            canvas_img.paste(img, (x_offset, y_offset))

        # Appliquer les sous-titres sur la zone aux bonnes dimensions
        render_w = dw if bg_mode in ("green", "black") else cw
        render_h = dh if bg_mode in ("green", "black") else ch
        enriched = build_display_groups(self._words, self._style.words_per_display)
        overlay = _get_overlay(t, enriched, self._style, self._style.text_color, render_w, render_h, supersample=1)
        if overlay is not None:
            overlay_img = Image.fromarray(overlay.astype(np.uint8))
            canvas_img = Image.alpha_composite(canvas_img, overlay_img)

        # Centrer l'image dans le canvas (letterbox)
        final = Image.new("RGBA", (cw, ch), (0, 0, 0, 255))
        x_off = (cw - canvas_img.width) // 2
        y_off = (ch - canvas_img.height) // 2
        final.paste(canvas_img, (x_off, y_off))

        self._img_ref = ImageTk.PhotoImage(final)
        self.canvas.delete("all")
        self.canvas.create_image(cw//2, ch//2, image=self._img_ref, anchor="center")
        m, s = int(t)//60, int(t)%60
        dm, ds = int(self._duration)//60, int(self._duration)%60
        self.lbl_time.configure(text=f"{m}:{s:02d} / {dm}:{ds:02d}")

    def _toggle_play(self):
        if self._playing:
            self._playing = False
            self._audio.stop()
            self.btn_play.configure(text="▶")
            if self._after_id:
                self.after_cancel(self._after_id)
                self._after_id = None
        else:
            self._playing = True
            self._audio.play(self._t)
            self.btn_play.configure(text="⏸")
            self._play_loop()

    def _play_loop(self):
        if not self._playing or self._t >= self._duration:
            if self._t >= self._duration:
                self._playing = False
                self.btn_play.configure(text="▶")
                self._audio.stop()
            return
        self._render(self._t)
        self.slider.set(self._t)
        self._t += 1.0 / self._fps
        self._after_id = self.after(int(1000/self._fps), self._play_loop)

    def _seek(self, val):
        self._t = float(val)
        if self._playing:
            self._audio.stop()
            self._audio.play(self._t)
        self._render(self._t)

    def refresh_style(self, style):
        self._style = style
        if not self._playing:
            # Planifier le rendu dans le thread principal (tkinter/OpenCV safe)
            if not self._pending_refresh:
                self._pending_refresh = True
                self.after(30, self._do_pending_refresh)

    def _do_pending_refresh(self):
        self._pending_refresh = False
        if not self._playing:
            self._render(self._t)

    def destroy(self):
        if self._cap:
            self._cap.release()
        super().destroy()


class SubtitleEditor(ctk.CTkFrame):
    def __init__(self, parent, on_change, **kw):
        super().__init__(parent, fg_color=BG_CARD, corner_radius=12, **kw)
        self._on_change = on_change
        self._words = []
        hdr = ctk.CTkFrame(self, fg_color="transparent")
        hdr.pack(fill="x", padx=12, pady=(10, 4))
        ctk.CTkLabel(hdr, text="✏️  Edit subtitles",
                     font=("", 13, "bold"), text_color=TEXT_BRIGHT).pack(side="left")
        ctk.CTkButton(hdr, text="Apply ✓", width=90, height=28,
                      fg_color=ACCENT, hover_color="#5A52D5", font=("", 11, "bold"),
                      command=self._apply).pack(side="right")
        self.txt = ctk.CTkTextbox(self, font=("JetBrains Mono", 11), wrap="word",
                                  fg_color=BG_CARD2, text_color="#C9D1D9")
        self.txt.pack(fill="both", expand=True, padx=10, pady=(0, 10))
        self.txt.insert("1.0", "Subtitles will appear here after transcription.")

    def load_words(self, words):
        self._words = [dict(w) for w in words]
        self.txt.delete("1.0", "end")
        for w in self._words:
            self.txt.insert("end", f"{w['start']:.2f}\t{w['end']:.2f}\t{w['word']}\n")

    def _apply(self):
        new = []
        for line in self.txt.get("1.0", "end").strip().splitlines():
            p = line.split("\t")
            if len(p) < 3:
                continue
            try:
                new.append({"start": float(p[0]), "end": float(p[1]), "word": p[2].strip() or "[……]"})
            except ValueError:
                continue
        if new:
            self._words = new
            self._on_change(new)
            messagebox.showinfo("✅", f"{len(new)} words updated.")

    def get_words(self):
        return self._words


# ══════════════════════════════════════════════════════════════
# MAIN APP
# ══════════════════════════════════════════════════════════════
class SubtitorApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("✦ Subtitor-Local")
        self.geometry("1440x920")
        self.minsize(1100, 750)
        self.configure(fg_color=BG_ROOT)
        self.video_path = None
        self.word_timestamps = []
        self.style = StyleConfig()
        self.model_size = ctk.StringVar(value="small")
        self.strip_punct = tk.BooleanVar(value=False)
        self._build_ui()

    def _build_ui(self):
        # Top bar
        tb = ctk.CTkFrame(self, fg_color=BG_PANEL, corner_radius=0, height=52)
        tb.pack(fill="x")
        tb.pack_propagate(False)
        ctk.CTkLabel(tb, text="✦  SUBTITOR  LOCAL", font=("", 17, "bold"),
                     text_color=ACCENT).pack(side="left", padx=20)

        # Warning labels
        if not HAS_PYGAME:
            ctk.CTkLabel(tb, text="⚠ Audio preview: pip install pygame",
                         font=("", 10), text_color=WARNING).pack(side="right", padx=16)
        if not HAS_WHISPER:
            ctk.CTkLabel(tb, text="⚠ whisperX missing",
                         font=("", 10), text_color=DANGER).pack(side="right", padx=16)

        # Main grid
        c = ctk.CTkFrame(self, fg_color="transparent")
        c.pack(fill="both", expand=True)
        c.grid_columnconfigure(0, weight=0, minsize=290)
        c.grid_columnconfigure(1, weight=1)
        c.grid_columnconfigure(2, weight=0, minsize=350)
        c.grid_rowconfigure(0, weight=1)

        # LEFT PANEL (source & export)
        left = ctk.CTkScrollableFrame(c, width=290, fg_color=BG_PANEL, corner_radius=0,
                                      scrollbar_button_color=BG_CARD2)
        left.grid(row=0, column=0, sticky="nsew")
        self._build_left(left)

        # CENTER (preview + editor)
        center = ctk.CTkFrame(c, fg_color="#0A0A10", corner_radius=0)
        center.grid(row=0, column=1, sticky="nsew")
        center.grid_rowconfigure(0, weight=3)
        center.grid_rowconfigure(1, weight=2)
        center.grid_columnconfigure(0, weight=1)
        self.player = PreviewPlayer(center)
        self.player.grid(row=0, column=0, sticky="nsew", padx=12, pady=(12, 6))
        self.editor = SubtitleEditor(center, on_change=self._on_edit)
        self.editor.grid(row=1, column=0, sticky="nsew", padx=12, pady=(6, 12))

        # RIGHT PANEL (style)
        right = ctk.CTkScrollableFrame(c, width=350, fg_color=BG_PANEL, corner_radius=0,
                                       scrollbar_button_color=BG_CARD2)
        right.grid(row=0, column=2, sticky="nsew")
        self._build_style_panel(right)

    def _build_left(self, p):
        self._sec(p, "① Source Video")
        ctk.CTkButton(p, text="📂  Load Video", command=self._load_video, height=40,
                      fg_color=BG_CARD2, hover_color=BG_CARD, border_width=1, border_color=ACCENT,
                      font=("", 12, "bold"), text_color=ACCENT).pack(fill="x", padx=12, pady=(4, 2))
        self.lbl_video = ctk.CTkLabel(p, text="No video selected",
                                      text_color=TEXT_DIM, wraplength=250, font=("", 10))
        self.lbl_video.pack(padx=12, pady=(0, 8))

        self._sec(p, "② Whisper Model")
        mf = ctk.CTkFrame(p, fg_color=BG_CARD, corner_radius=8)
        mf.pack(fill="x", padx=12, pady=(4, 8))
        for i, sz in enumerate(["tiny", "small", "medium", "large"]):
            ctk.CTkRadioButton(mf, text=sz, variable=self.model_size, value=sz,
                               font=("", 11), fg_color=ACCENT, hover_color="#5A52D5"
                               ).grid(row=i//2, column=i%2, padx=10, pady=5, sticky="w")

        # Punctuation removal checkbox
        chk = ctk.CTkCheckBox(p, text="Remove punctuation after transcription",
                              variable=self.strip_punct, font=("", 11),
                              fg_color=ACCENT, hover_color="#5A52D5")
        chk.pack(anchor="w", padx=20, pady=(0, 6))

        self.btn_transcribe = ctk.CTkButton(p, text="🎙  Transcribe", command=self._transcribe,
                                            state="disabled", height=44, font=("", 13, "bold"),
                                            fg_color=BLUE_BTN, hover_color=BLUE_HOV)
        self.btn_transcribe.pack(fill="x", padx=12, pady=(0, 4))
        self.progress = ctk.CTkProgressBar(p, progress_color=ACCENT, fg_color=BG_CARD2)
        self.progress.pack(fill="x", padx=12, pady=(4, 2))
        self.progress.set(0)
        self.lbl_prog = ctk.CTkLabel(p, text="", text_color=TEXT_DIM, font=("", 10), wraplength=250)
        self.lbl_prog.pack(padx=12, pady=(0, 8))

        self._sec(p, "③ Export")
        rf = ctk.CTkFrame(p, fg_color=BG_CARD, corner_radius=8)
        rf.pack(fill="x", padx=12, pady=(4, 4))
        rf.columnconfigure(1, weight=1)
        ctk.CTkLabel(rf, text="Resolution", font=("", 11)).grid(row=0, column=0, padx=10, pady=7, sticky="w")
        ctk.CTkOptionMenu(rf, values=["source", "1080p", "4k"],
                          command=lambda v: setattr(self.style, "export_resolution", v),
                          width=110, fg_color=BG_CARD2, button_color=ACCENT,
                          button_hover_color="#5A52D5").grid(row=0, column=1, padx=8, pady=7)
        ctk.CTkLabel(rf, text="Background", font=("", 11)).grid(row=1, column=0, padx=10, pady=7, sticky="w")
        self.bg_menu = ctk.CTkOptionMenu(rf, values=["video", "green screen", "black screen"],
                                         command=self._on_bg_change,
                                         width=130, fg_color=BG_CARD2, button_color=ACCENT,
                                         button_hover_color="#5A52D5")
        self.bg_menu.grid(row=1, column=1, padx=8, pady=7)
        # Highlight green/black option
        self.bg_menu.configure(fg_color=BG_CARD2, button_color=GREEN_BTN)

        self.btn_export = ctk.CTkButton(p, text="💾  Export MP4", command=self._export_mp4,
                                        state="disabled", height=42, font=("", 12, "bold"),
                                        fg_color=GREEN_BTN, hover_color=GREEN_HOV)
        self.btn_export.pack(fill="x", padx=12, pady=(10, 4))
        self.btn_srt = ctk.CTkButton(p, text="📄  Export SRT", command=self._export_srt,
                                     state="disabled", height=34, font=("", 11),
                                     fg_color=BG_CARD, hover_color=BG_CARD2,
                                     border_width=1, border_color="#374151")
        self.btn_srt.pack(fill="x", padx=12, pady=(0, 4))
        self.btn_preview = ctk.CTkButton(p, text="👁  Quick Preview (file)", command=self._preview_file,
                                         state="disabled", height=34, font=("", 11),
                                         fg_color=BG_CARD, hover_color=BG_CARD2,
                                         border_width=1, border_color="#374151")
        self.btn_preview.pack(fill="x", padx=12, pady=(0, 16))

    def _build_style_panel(self, p):
        # PRESETS
        self._sec(p, "🎨 Style Presets")
        preset_frame = ctk.CTkFrame(p, fg_color=BG_CARD, corner_radius=10)
        preset_frame.pack(fill="x", padx=12, pady=(4, 8))
        ctk.CTkLabel(preset_frame, text="Quick presets:", font=("", 11)).pack(anchor="w", padx=10, pady=(6, 0))
        self.preset_menu = ctk.CTkOptionMenu(preset_frame, values=list(PRESETS.keys()),
                                             command=self._apply_preset,
                                             fg_color=BG_CARD2, button_color=ACCENT)
        self.preset_menu.pack(fill="x", padx=10, pady=(4, 8))

        # Then all the style sections as before
        self._sec(p, "🔢  Display")
        wf = self._card(p)
        ctk.CTkLabel(wf, text="Words per block", font=("", 11)).grid(row=0, column=0, padx=10, pady=6, sticky="w")
        self._wpd_lbl = ctk.CTkLabel(wf, text="1", font=("", 11, "bold"), text_color=ACCENT, width=24)
        self._wpd_lbl.grid(row=0, column=2, padx=4)
        s = ctk.CTkSlider(wf, from_=1, to=8, number_of_steps=7, command=self._on_wpd,
                          button_color=ACCENT, button_hover_color="#5A52D5", progress_color=ACCENT)
        s.set(1)
        s.grid(row=0, column=1, padx=8, pady=6, sticky="ew")
        wf.columnconfigure(1, weight=1)

        self._sec(p, "🎨  Text"); tf = self._card(p)
        self._slider(tf, "Size", 20, 150, 60, 0, lambda v: self._u("font_size", int(v)))
        self._color(tf, "Color", "#FFFFFF", 1, lambda c: self._u("text_color", c))
        self._toggle(tf, "Bold", True, 2, lambda v: self._u("bold", v))
        self._toggle(tf, "Italic", False, 3, lambda v: self._u("italic", v))
        self._toggle(tf, "UPPERCASE", False, 4, lambda v: self._u("uppercase", v))

        self._sec(p, "✏️  Outline"); of = self._card(p)
        self._slider(of, "Width", 0, 12, 2, 0, lambda v: self._u("outline_width", int(v)))
        self._color(of, "Color", "#000000", 1, lambda c: self._u("outline_color", c))

        self._sec(p, "🌑  Shadow"); shf = self._card(p)
        self._toggle(shf, "Enable", False, 0, lambda v: self._u("shadow", v))
        self._color(shf, "Color", "#000000", 1, lambda c: self._u("shadow_color", c))
        self._slider(shf, "Opacity", 0, 255, 180, 2, lambda v: self._u("shadow_opacity", int(v)))
        self._slider(shf, "Offset X", -20, 20, 3, 3, lambda v: self._u("shadow_offset_x", int(v)))
        self._slider(shf, "Offset Y", -20, 20, 3, 4, lambda v: self._u("shadow_offset_y", int(v)))
        self._slider(shf, "Blur", 0, 15, 4, 5, lambda v: self._u("shadow_blur", int(v)))

        self._sec(p, "🔲  Word background"); bf = self._card(p)
        self._toggle(bf, "Enable", False, 0, lambda v: self._u("word_bg", v))
        self._color(bf, "Color", "#000000", 1, lambda c: self._u("word_bg_color", c))
        self._slider(bf, "Opacity", 0, 255, 160, 2, lambda v: self._u("word_bg_opacity", int(v)))
        self._slider(bf, "Padding", 0, 30, 10, 3, lambda v: self._u("word_bg_padding", int(v)))
        self._slider(bf, "Radius", 0, 30, 8, 4, lambda v: self._u("word_bg_radius", int(v)))

        self._sec(p, "✨  Karaoke"); hlf = self._card(p)
        self._toggle(hlf, "Enable", True, 0, lambda v: self._u("highlight", v))
        self._color(hlf, "Active color", "#FFD700", 1, lambda c: self._u("highlight_color", c))
        self._color(hlf, "Active outline", "#000000", 2, lambda c: self._u("highlight_outline", c))
        self._color(hlf, "Past words", "#AAAAAA", 3, lambda c: self._u("highlight_done_color", c))

        self._sec(p, "📍  Position"); pf = self._card(p)
        self._slider(pf, "Y position", 0.05, 0.98, 0.82, 0, lambda v: self._u("y_position", round(float(v), 2)))
        self._slider(pf, "X position", 0.0, 1.0, 0.5, 1, lambda v: self._u("x_position", round(float(v), 2)))
        ctk.CTkLabel(pf, text="Alignment", font=("", 11)).grid(row=2, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkOptionMenu(pf, values=["left", "center", "right"],
                          command=lambda v: self._u("align", v), width=100,
                          fg_color=BG_CARD2, button_color=ACCENT).grid(row=2, column=1, padx=8, pady=5)

        self._sec(p, "🎬  Animation"); af = self._card(p)
        ctk.CTkLabel(af, text="Effect", font=("", 11)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkOptionMenu(af, values=["none", "pop", "fade", "slide_up", "slide_down", "bounce"],
                          command=lambda v: self._u("animation_in", v), width=120,
                          fg_color=BG_CARD2, button_color=ACCENT).grid(row=0, column=1, padx=8, pady=5)
        self._slider(af, "Duration", 0.05, 0.5, 0.12, 1, lambda v: self._u("animation_duration", round(float(v), 3)))

        self._sec(p, "🌈  Color effect"); ef = self._card(p)
        ctk.CTkLabel(ef, text="Mode", font=("", 11)).grid(row=0, column=0, padx=10, pady=5, sticky="w")
        ctk.CTkOptionMenu(ef, values=["fixed", "negative", "gradient"],
                          command=lambda v: self._u("effect_mode", v), width=120,
                          fg_color=BG_CARD2, button_color=ACCENT).grid(row=0, column=1, padx=8, pady=5)
        self._color(ef, "Gradient 1", "#FF6B6B", 1, lambda c: self._u("gradient_color1", c))
        self._color(ef, "Gradient 2", "#4ECDC4", 2, lambda c: self._u("gradient_color2", c))

        self._sec(p, "🔤  Font"); ff = self._card(p)
        ff.columnconfigure(1, weight=1)
        ctk.CTkButton(ff, text="📂  Import .ttf / .otf", command=self._import_font, height=32,
                      font=("", 11), fg_color=BG_CARD2, hover_color=BG_CARD,
                      border_width=1, border_color="#374151").grid(row=0, column=0, columnspan=2, padx=10, pady=8, sticky="ew")
        self.lbl_font = ctk.CTkLabel(ff, text="System default font", text_color=TEXT_DIM, font=("", 10))
        self.lbl_font.grid(row=1, column=0, columnspan=2, padx=10, pady=(0, 6))

    # UI helpers
    def _sec(self, p, t):
        f = ctk.CTkFrame(p, fg_color="transparent")
        f.pack(fill="x", padx=12, pady=(14, 2))
        ctk.CTkLabel(f, text=t, font=("", 12, "bold"), text_color=TEXT_BRIGHT).pack(side="left")
        ctk.CTkFrame(f, fg_color="#2A2A3A", height=1).pack(side="left", fill="x", expand=True, padx=(8, 0))

    def _card(self, p):
        f = ctk.CTkFrame(p, fg_color=BG_CARD, corner_radius=10)
        f.pack(fill="x", padx=12, pady=(2, 4))
        f.columnconfigure(1, weight=1)
        return f

    def _slider(self, p, lbl, mn, mx, default, row, cmd):
        ctk.CTkLabel(p, text=lbl, font=("", 11), text_color=TEXT_BRIGHT).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        s = ctk.CTkSlider(p, from_=mn, to=mx, command=cmd, button_color=ACCENT,
                          button_hover_color="#5A52D5", progress_color=ACCENT)
        s.set(default)
        s.grid(row=row, column=1, padx=8, pady=5, sticky="ew")

    def _color(self, p, lbl, default, row, cmd):
        ctk.CTkLabel(p, text=lbl, font=("", 11), text_color=TEXT_BRIGHT).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        ColorBtn(p, default, cmd).grid(row=row, column=1, padx=8, pady=5, sticky="w")

    def _toggle(self, p, lbl, default, row, cmd):
        ctk.CTkLabel(p, text=lbl, font=("", 11), text_color=TEXT_BRIGHT).grid(row=row, column=0, padx=10, pady=5, sticky="w")
        var = tk.BooleanVar(value=default)
        ctk.CTkSwitch(p, text="", variable=var, command=lambda: cmd(var.get()),
                      progress_color=ACCENT, button_color="#FFFFFF").grid(row=row, column=1, padx=8, pady=5, sticky="w")

    def _apply_preset(self, preset_name):
        preset = PRESETS[preset_name]
        for key, val in preset.items():
            if hasattr(self.style, key):
                setattr(self.style, key, val)
        # Also refresh the UI elements? Not necessary, the preview will update
        if self.word_timestamps:
            self.player.refresh_style(self.style)

    def _on_wpd(self, val):
        n = max(1, int(round(float(val))))
        self._wpd_lbl.configure(text=str(n))
        self._u("words_per_display", n)

    def _on_bg_change(self, v):
        self.style.export_bg = {"video": "video", "green screen": "green", "black screen": "black"}.get(v, "video")
        if self.word_timestamps:
            self.player.refresh_style(self.style)

    def _u(self, attr, val):
        setattr(self.style, attr, val)
        if self.word_timestamps:
            self.player.refresh_style(self.style)

    # Actions
    def _load_video(self):
        p = filedialog.askopenfilename(title="Video", filetypes=[("Video", "*.mp4 *.avi *.mov *.mkv *.webm")])
        if p:
            self.video_path = p
            self.lbl_video.configure(text=f"✅  {os.path.basename(p)}", text_color="#10B981")
            self.btn_transcribe.configure(state="normal")
            self._prog(0, "Video loaded.")

    def _import_font(self):
        p = filedialog.askopenfilename(title="Font", filetypes=[("Fonts", "*.ttf *.otf")])
        if p:
            self.style.font_path = p
            self.lbl_font.configure(text=os.path.basename(p), text_color=TEXT_BRIGHT)

    def _on_edit(self, words):
        self.word_timestamps = words
        self.player.load(self.video_path, words, self.style)

    def _transcribe(self):
        if not self.video_path:
            return
        self.btn_transcribe.configure(state="disabled", text="⏳  Transcribing…")
        self._prog(0.05, "Starting…")
        threading.Thread(target=self._run_transcribe, daemon=True).start()

    def _run_transcribe(self):
        try:
            strip = self.strip_punct.get()
            words = Transcriber(model_size=self.model_size.get()).transcribe(
                self.video_path, self._prog, strip_punct=strip
            )
            self.word_timestamps = words
            self.editor.load_words(words)
            self.player.load(self.video_path, words, self.style)
            self.btn_transcribe.configure(state="normal", text="🎙  Transcribe")
            self.btn_export.configure(state="normal")
            self.btn_srt.configure(state="normal")
            self.btn_preview.configure(state="normal")
            self._prog(1.0, f"✅  {len(words)} words transcribed.")
            messagebox.showinfo("✅", "Transcription complete!")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.btn_transcribe.configure(state="normal", text="🎙  Transcribe")
            self._prog(0, str(e)[:60])

    def _preview_file(self):
        if not self.video_path or not self.word_timestamps:
            return
        out = tempfile.NamedTemporaryFile(suffix=".mp4", delete=False).name
        self.btn_preview.configure(state="disabled", text="⏳ Generating…")
        threading.Thread(target=self._run_export, args=(out, "preview"), daemon=True).start()

    def _export_mp4(self):
        if not self.video_path or not self.word_timestamps:
            return
        p = filedialog.asksaveasfilename(defaultextension=".mp4", filetypes=[("MP4", "*.mp4")])
        if not p:
            return
        self.btn_export.configure(state="disabled", text="⏳ Exporting…")
        threading.Thread(target=self._run_export, args=(p, "export"), daemon=True).start()

    def _run_export(self, path, mode):
        try:
            VideoComposer(self.video_path, self.style).compose(
                self.word_timestamps, path, mode=mode, progress_callback=self._prog)
            self._prog(1.0, f"✅  {os.path.basename(path)}")
            if mode == "preview":
                if sys.platform == "darwin":
                    os.system(f"open '{path}'")
                elif sys.platform == "win32":
                    os.startfile(path)
                else:
                    os.system(f"xdg-open '{path}'")
                self.btn_preview.configure(state="normal", text="👁  Quick Preview (file)")
            else:
                self.btn_export.configure(state="normal", text="💾  Export MP4")
                messagebox.showinfo("✅", f"Exported to: {path}")
        except Exception as e:
            messagebox.showerror("Error", str(e))
            self.btn_export.configure(state="normal", text="💾  Export MP4")
            self.btn_preview.configure(state="normal", text="👁  Quick Preview (file)")
            self._prog(0, str(e)[:60])

    def _export_srt(self):
        p = filedialog.asksaveasfilename(defaultextension=".srt", filetypes=[("SRT", "*.srt")])
        if not p:
            return
        try:
            export_word_srt(self.word_timestamps, p)
            messagebox.showinfo("✅", f"SRT saved: {p}")
        except Exception as e:
            messagebox.showerror("Error", str(e))

    def _prog(self, v, msg=""):
        self.progress.set(v)
        if msg:
            self.lbl_prog.configure(text=msg)


if __name__ == "__main__":
    SubtitorApp().mainloop()
