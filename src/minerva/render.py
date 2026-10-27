"""Pictures for the dossier and the dashboard.

Two rules govern everything here.

**Comparability over prettiness.** Two dates rendered for a legal annex must be
rendered identically — same stretch, same gain, same colour assignment. Nothing
in this module auto-scales to the scene.

**Colour carries state, and never carries it alone.** The overlay uses the
reserved status palette (inside authorised area / outside it / inside the
boundary tolerance), and every rendering that uses it ships with a legend and
with the same numbers written out, so that a reader with any colour vision, or
a black-and-white print in a case file, loses nothing.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Dict, List, Optional, Sequence, Tuple

import numpy as np

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt          # noqa: E402
from matplotlib.lines import Line2D      # noqa: E402
from PIL import Image, ImageDraw         # noqa: E402

from .detectors.base import Observation  # noqa: E402
from .geom import Grid                   # noqa: E402
from .scene import Scene                 # noqa: E402

# --- the validated palette (see references/palette.md; validator run 2026-08-19)
LIGHT = {
    "surface": "#fcfcfb",
    "page": "#f9f9f7",
    "ink": "#0b0b0b",
    "ink2": "#52514e",
    "muted": "#898781",
    "grid": "#e1e0d9",
    "axis": "#c3c2b7",
    "s1": "#2a78d6",
    "s2": "#eb6834",
    "s3": "#1baf7a",
}
DARK = {
    "surface": "#1a1a19",
    "page": "#0d0d0d",
    "ink": "#ffffff",
    "ink2": "#c3c2b7",
    "muted": "#898781",
    "grid": "#2c2c2a",
    "axis": "#383835",
    "s1": "#3987e5",
    "s2": "#d95926",
    "s3": "#199e70",
}
STATUS = {           # reserved; never used for a data series
    "good": "#0ca30c",
    "warning": "#fab219",
    "serious": "#ec835a",
    "critical": "#d03b3b",
}

FONT = ["DejaVu Sans", "sans-serif"]   # matplotlib cannot resolve system-ui


def _style(ax, theme: Dict[str, str]) -> None:
    ax.set_facecolor(theme["surface"])
    ax.figure.set_facecolor(theme["surface"])
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(theme["axis"])
        ax.spines[side].set_linewidth(1.0)
    ax.tick_params(colors=theme["muted"], labelsize=9, length=0)
    ax.grid(True, axis="y", color=theme["grid"], linewidth=1.0, linestyle="-")
    ax.set_axisbelow(True)
    for lbl in ax.get_xticklabels() + ax.get_yticklabels():
        lbl.set_color(theme["muted"])


# --------------------------------------------------------------------------
# Imagery
# --------------------------------------------------------------------------

def true_colour_png(scene: Scene, path: Path, gain: float = 3.2,
                    annotate: bool = True) -> Path:
    img = Image.fromarray(scene.true_colour(gain=gain))
    if annotate:
        img = _add_chrome(img, scene, caption=scene.acquired.strftime("%B %Y"))
    img.save(path)
    return path


# The three attribution classes, with the alpha each deserves. 'Inside' is the
# unremarkable case and is painted lightly; 'outside' is the claim and is
# painted heavily. Alpha carries emphasis so that hue is not doing it alone.
PAINT_ALPHA = {"inside": 0.30, "indeterminate": 0.45, "outside": 0.65}
PAINT_LABEL = {
    "inside": "inside the titled polygon",
    "indeterminate": "within the boundary tolerance (not counted)",
    "outside": "outside the titled polygon",
}


def overlay_png(
    scene: Scene,
    path: Path,
    masks: Dict[str, np.ndarray],
    rings: Sequence[Tuple[Sequence[Tuple[float, float]], str, str]] = (),
    gain: float = 3.2,
    areas_ha: Optional[Dict[str, float]] = None,
) -> Path:
    """True colour with the classified footprint painted over it.

    ``masks`` keys are 'inside', 'outside', 'indeterminate'.
    ``rings`` is a sequence of (ring, hex colour, label) drawn as outlines.

    The output carries its own legend, scale bar and date. An evidence image
    that has to be read alongside a caption in a different file is an evidence
    image that will eventually be read without it.
    """
    base = scene.true_colour(gain=gain).astype(float)
    paint = {
        "inside": _hex(STATUS["good"]),
        "outside": _hex(STATUS["critical"]),
        "indeterminate": _hex(STATUS["warning"]),
    }
    for key, colour in paint.items():
        m = masks.get(key)
        if m is None or not m.any():
            continue
        a = PAINT_ALPHA[key]
        for c in range(3):
            base[..., c][m] = (1 - a) * base[..., c][m] + a * colour[c]

    img = Image.fromarray(np.clip(base, 0, 255).astype(np.uint8))
    draw = ImageDraw.Draw(img)
    for ring, colour, _label in rings:
        pts = [_to_px(scene.grid, lon, lat) for lon, lat in ring]
        draw.line(pts + [pts[0]], fill=colour, width=2)

    legend = []
    for key in ("outside", "indeterminate", "inside"):
        if masks.get(key) is not None and masks[key].any():
            label = PAINT_LABEL[key]
            if areas_ha and key in areas_ha:
                label = f"{areas_ha[key]:,.1f} ha {label}"
            legend.append((paint[key], label))
    for ring, colour, label in rings:
        legend.append((_hex(colour), label))

    img = _add_chrome(img, scene, caption=scene.acquired.strftime("%B %Y"),
                      legend=legend)
    img.save(path)
    return path


def _add_chrome(img: Image.Image, scene: Scene, caption: str = "",
                legend: Sequence[Tuple[Tuple[int, int, int], str]] = ()) -> Image.Image:
    """Scale bar, north arrow, date, provider and legend, on a footer band."""
    from PIL import ImageFont
    try:
        font = ImageFont.load_default(13)
        small = ImageFont.load_default(11)
    except TypeError:                      # Pillow < 10
        font = small = ImageFont.load_default()

    band = 26 + 18 * max(len(legend), 1)
    out = Image.new("RGB", (img.width, img.height + band), (252, 252, 251))
    out.paste(img, (0, 0))
    d = ImageDraw.Draw(out)

    # scale bar, drawn on the image itself
    target_m = _nice_length(scene.grid.pixel_m * img.width * 0.25)
    bar_px = int(target_m / scene.grid.pixel_m)
    label = f"{target_m:,.0f} m" if target_m < 1000 else f"{target_m / 1000:,.0f} km"
    x0, y0 = 14, img.height - 16
    d.rectangle([x0 - 8, y0 - 20, x0 + bar_px + 8, y0 + 7], fill=(20, 20, 20))
    d.line([(x0, y0), (x0 + bar_px, y0)], fill=(255, 255, 255), width=3)
    for tick in (x0, x0 + bar_px):
        d.line([(tick, y0 - 4), (tick, y0 + 4)], fill=(255, 255, 255), width=3)
    d.text((x0, y0 - 18), label, fill=(255, 255, 255), font=small)

    # north arrow
    nx, ny = img.width - 22, 26
    d.polygon([(nx, ny - 16), (nx - 6, ny + 4), (nx, ny - 2), (nx + 6, ny + 4)],
              fill=(255, 255, 255), outline=(0, 0, 0))
    d.text((nx - 4, ny + 6), "N", fill=(255, 255, 255), font=small)

    # footer
    head = f"{scene.site_id} · {caption} · {scene.provider}"
    if scene.cloud_fraction is not None:
        head += f" · {scene.valid_fraction * 100:.0f}% observable"
    d.text((10, img.height + 6), head, fill=(11, 11, 11), font=font)
    for i, (colour, text) in enumerate(legend):
        y = img.height + 26 + 18 * i
        d.rectangle([10, y + 3, 26, y + 15], fill=tuple(int(c) for c in colour),
                    outline=(120, 120, 120))
        d.text((32, y + 2), text, fill=(82, 81, 78), font=small)
    return out


def _nice_length(x: float) -> float:
    """Largest tidy distance that fits inside the target width."""
    best = 100.0
    for candidate in (100, 200, 250, 500, 1000, 2000, 2500, 5000, 10000):
        if candidate <= x:
            best = float(candidate)
    return best


def _to_px(grid: Grid, lon: float, lat: float) -> Tuple[int, int]:
    col = (lon - grid.origin_lon) / grid.deg_per_pixel_lon
    row = (grid.origin_lat - lat) / grid.deg_per_pixel_lat
    return int(round(col)), int(round(row))


def _hex(h: str) -> Tuple[float, float, float]:
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


# --------------------------------------------------------------------------
# Charts
# --------------------------------------------------------------------------

def footprint_chart(
    path: Path,
    dates: List[date],
    total_ha: List[float],
    outside_ha: Optional[List[float]] = None,
    degraded: Optional[Tuple[List[date], List[float]]] = None,
    breakpoint: Optional[date] = None,
    theme: str = "light",
    title: str = "Disturbed surface",
) -> Path:
    t = LIGHT if theme == "light" else DARK
    fig, ax = plt.subplots(figsize=(9.2, 4.0), dpi=160)
    _style(ax, t)

    x = [d.toordinal() for d in dates]
    ax.plot(x, total_ha, color=t["s1"], linewidth=2.0, zorder=3,
            solid_capstyle="round")
    if outside_ha is not None:
        ax.plot(x, outside_ha, color=t["s2"], linewidth=2.0, zorder=3,
                solid_capstyle="round")

    # Partially observed dates are lower bounds, not measurements of the same
    # quantity, so they are plotted as unconnected open markers. Joining them to
    # the line would draw a fall in the footprint that never happened.
    if degraded and degraded[0]:
        ax.scatter([d.toordinal() for d in degraded[0]], degraded[1], s=30,
                   facecolors="none", edgecolors=t["muted"], linewidths=1.4,
                   zorder=4)

    if breakpoint is not None:
        bx = breakpoint.toordinal()
        ax.axvline(bx, color=t["muted"], linewidth=1.0, zorder=2)
        ax.annotate(f"rate change\n{breakpoint.strftime('%b %Y')}",
                    xy=(bx, max(total_ha) * 0.97), xytext=(6, 0),
                    textcoords="offset points", ha="left", va="top",
                    fontsize=9, color=t["ink2"], fontfamily=FONT)

    # direct labels at the endpoint rather than a number on every point
    ax.annotate(f"{total_ha[-1]:,.0f} ha total",
                xy=(x[-1], total_ha[-1]), xytext=(8, 0), textcoords="offset points",
                va="center", fontsize=10, color=t["ink"], fontfamily=FONT)
    if outside_ha is not None:
        ax.annotate(f"{outside_ha[-1]:,.0f} ha outside title",
                    xy=(x[-1], outside_ha[-1]), xytext=(8, 0),
                    textcoords="offset points", va="center", fontsize=10,
                    color=t["ink"], fontfamily=FONT)

    handles = [Line2D([], [], color=t["s1"], linewidth=2.0, label="Total disturbed")]
    if outside_ha is not None:
        handles.append(Line2D([], [], color=t["s2"], linewidth=2.0,
                              label="Outside licensed polygon"))
    if degraded and degraded[0]:
        handles.append(Line2D([], [], marker="o", linestyle="none",
                              markerfacecolor="none", markeredgecolor=t["muted"],
                              markeredgewidth=1.4, markersize=6,
                              label="Cloud-limited date (lower bound)"))
    leg = ax.legend(handles=handles, loc="upper left", frameon=False, fontsize=9)
    for txt in leg.get_texts():
        txt.set_color(t["ink2"])
        txt.set_fontfamily(FONT)

    _date_axis(ax, dates, t)
    ax.set_ylabel("hectares", color=t["muted"], fontsize=9, fontfamily=FONT)
    ax.set_title(title, color=t["ink"], fontsize=12, loc="left", pad=12,
                 fontfamily=FONT)
    ax.margins(x=0.10)
    fig.tight_layout()
    fig.savefig(path, facecolor=t["surface"])
    plt.close(fig)
    return path


def water_chart(path: Path, dates: List[date], pond_ha: List[float],
                theme: str = "light",
                title: str = "Impounded water surface") -> Path:
    t = LIGHT if theme == "light" else DARK
    fig, ax = plt.subplots(figsize=(9.2, 3.2), dpi=160)
    _style(ax, t)
    x = [d.toordinal() for d in dates]
    ax.plot(x, pond_ha, color=t["s1"], linewidth=2.0, solid_capstyle="round")
    ax.annotate(f"{pond_ha[-1]:,.1f} ha", xy=(x[-1], pond_ha[-1]), xytext=(8, 0),
                textcoords="offset points", va="center", fontsize=10,
                color=t["ink"], fontfamily=FONT)
    _date_axis(ax, dates, t)
    ax.set_ylabel("hectares", color=t["muted"], fontsize=9, fontfamily=FONT)
    ax.set_title(title, color=t["ink"], fontsize=12, loc="left", pad=12,
                 fontfamily=FONT)
    ax.margins(x=0.10)
    fig.tight_layout()
    fig.savefig(path, facecolor=t["surface"])
    plt.close(fig)
    return path


def deformation_chart(path: Path, dates: List[str], series: List[List[float]],
                      theme: str = "light",
                      title: str = "Tailings dam crest — cumulative displacement") -> Path:
    """One story, one colour: the median, with the population behind it in grey."""
    t = LIGHT if theme == "light" else DARK
    fig, ax = plt.subplots(figsize=(9.2, 3.6), dpi=160)
    _style(ax, t)
    x = list(range(len(dates)))
    arr = np.array(series, dtype=float)
    for row in arr:
        ax.plot(x, row, color=t["muted"], linewidth=0.8, alpha=0.35, zorder=2)
    med = np.median(arr, axis=0)
    ax.plot(x, med, color=t["s1"], linewidth=2.2, zorder=3, solid_capstyle="round")
    ax.axhline(0.0, color=t["axis"], linewidth=1.0, zorder=1)
    ax.annotate(f"{med[-1]:,.0f} mm median", xy=(x[-1], med[-1]), xytext=(8, 0),
                textcoords="offset points", va="center", fontsize=10,
                color=t["ink"], fontfamily=FONT)

    handles = [
        Line2D([], [], color=t["s1"], linewidth=2.2, label="Median of coherent points"),
        Line2D([], [], color=t["muted"], linewidth=0.8, alpha=0.6,
               label=f"Individual scatterers (n={len(series)})"),
    ]
    leg = ax.legend(handles=handles, loc="lower left", frameon=False, fontsize=9)
    for txt in leg.get_texts():
        txt.set_color(t["ink2"])
        txt.set_fontfamily(FONT)

    step = max(len(dates) // 8, 1)
    ax.set_xticks(x[::step])
    ax.set_xticklabels([dates[i][:7] for i in x[::step]], fontfamily=FONT)
    ax.set_ylabel("mm (line of sight)", color=t["muted"], fontsize=9, fontfamily=FONT)
    ax.set_title(title, color=t["ink"], fontsize=12, loc="left", pad=12,
                 fontfamily=FONT)
    fig.tight_layout()
    fig.savefig(path, facecolor=t["surface"])
    plt.close(fig)
    return path


def _date_axis(ax, dates: List[date], t: Dict[str, str]) -> None:
    """Ticks on the calendar, not on the observations.

    Observations are unevenly spaced because cloud is unevenly spaced. Ticking
    every n-th observation puts labels wherever the weather happened to be
    good, and they collide.
    """
    if not dates:
        return
    first, last = min(dates), max(dates)
    span_months = (last.year - first.year) * 12 + (last.month - first.month)
    every = 3 if span_months <= 18 else (6 if span_months <= 60 else 12)
    ticks, labels = [], []
    y, m = first.year, ((first.month - 1) // every) * every + 1
    while date(y, m, 1) <= last:
        d = date(y, m, 1)
        if d >= first:
            ticks.append(d.toordinal())
            labels.append(d.strftime("%b %Y") if every >= 6 else d.strftime("%b %y"))
        m += every
        while m > 12:
            m -= 12
            y += 1
    ax.set_xticks(ticks)
    ax.set_xticklabels(labels, fontfamily=FONT)


def observations_to_series(obs: Sequence[Observation]) -> Tuple[List[date], List[float], List[str]]:
    """Only fully observed dates form the line.

    A measurement taken through a hole in the cloud is a *lower bound*, not an
    estimate of the same quantity, and joining the two with a line would draw a
    decrease that never happened. Partially observed dates are returned
    separately by ``degraded_points`` and drawn as unconnected open markers.
    """
    keep = [o for o in obs if o.reliability == "ok"]
    keep.sort(key=lambda o: o.acquired)
    return ([o.acquired for o in keep],
            [o.value for o in keep],
            [o.reliability for o in keep])


def degraded_points(obs: Sequence[Observation]) -> Tuple[List[date], List[float]]:
    keep = sorted([o for o in obs if o.reliability == "degraded"],
                  key=lambda o: o.acquired)
    return [o.acquired for o in keep], [o.value for o in keep]
