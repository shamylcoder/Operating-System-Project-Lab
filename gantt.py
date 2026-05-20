# =============================================================================
#  MODULE: gantt.py
#
#  Contains the GanttChart widget and the make_btn helper function.
#
#  GanttChart is a self-contained custom widget that extends tk.Canvas.

#  CONTENTS:
#    make_btn(...)   → factory function for consistently styled flat buttons
#    GanttChart      → tk.Canvas subclass that draws and animates the chart
# =============================================================================

import tkinter as tk  # Core GUI toolkit

from constants import (  # Visual settings shared across modules
    BG_GANTT, FG_GREY, FONT_NORMAL, FONT_BTN,
    GANTT_COLORS, FG_WHITE
)


# =============================================================================
#  HELPER FUNCTION: make_btn
#
#  Creates a styled flat button with a consistent look and feel.
#  Defined once here so we don't repeat the same 8 styling options
#  every time we need a button in the main App window.
#
#  Usage:
#    btn = make_btn(parent, "+ Add", callback, BG_BTN_ADD)
#    btn.pack(...)
# =============================================================================

def make_btn(parent, text, command, bg, fg=FG_WHITE, font=FONT_BTN, padx=12, pady=6):
    return tk.Button(
        parent, text=text, command=command,
        bg=bg, fg=fg, font=font,
        relief="flat",         # No raised/sunken border — clean flat look
        cursor="hand2",        # Mouse cursor changes to a hand when hovering
        padx=padx, pady=pady,
        activebackground=bg,   # Same colour when clicked (no colour flash)
        activeforeground=fg,
        bd=0                   # Border width = 0
    )


# =============================================================================
#  CLASS: GanttChart
#
#  A CUSTOM WIDGET that draws the coloured Gantt chart.
#  Extends tk.Canvas — a blank drawing surface — and adds domain-specific
#  drawing logic on top of it.
#
#  We draw using three canvas primitives:
#    create_rectangle(x1, y1, x2, y2, ...) → coloured process blocks
#    create_text(x, y, ...)                → process labels inside blocks
#    create_line(x1, y1, x2, y2, ...)      → tick marks on the time axis
#
#  HOW ANIMATION WORKS:
#  The main App adds blocks ONE AT A TIME to self.timeline, then calls
#  redraw(). Each call redraws the entire chart from scratch — this
#  produces a step-by-step "live" animation effect as the simulation runs.
# =============================================================================

class GanttChart(tk.Canvas):

    def __init__(self, parent, **kwargs):
        # Call the parent Canvas constructor, passing all extra options through.
        # bg=BG_GANTT sets the chart's background to off-white.
        super().__init__(parent, bg=BG_GANTT, **kwargs)

        self.timeline   = []  # List of (pid, start, end) tuples to draw
        self.colors     = {}  # Maps each PID → its assigned hex colour string
        self.total_time = 0   # The maximum end-time value — sets the chart's width

    def set_data(self, timeline, process_list):
        # Load a FULL timeline at once.
        # Used by the "Show Instantly" path (no animation, show everything at once).
        self.timeline   = list(timeline)
        self.total_time = max((end for (_, _, end) in timeline), default=0)

        # Assign a unique colour to each process (preserving insertion order)
        # dict.fromkeys() removes duplicates while keeping order (unlike set())
        pids = list(dict.fromkeys(p.pid for p in process_list))
        self.colors = {}
        for i, pid in enumerate(pids):
            self.colors[pid] = GANTT_COLORS[i % len(GANTT_COLORS)]

        self.redraw()

    def redraw(self):
        # Wipe everything on the canvas and redraw the entire chart from scratch.
        # Called after each animation step AND on window resize events.
        self.delete("all")  # Remove all previously drawn shapes and text

        if not self.timeline:
            # Nothing to draw yet — show a helpful placeholder message
            w = self.winfo_width() or 800
            self.create_text(w // 2, 50,
                             text="Run a simulation to see the Gantt chart here",
                             font=FONT_NORMAL, fill=FG_GREY)
            return

        w          = self.winfo_width() or 800  # Actual canvas pixel width
        bar_top    = 28    # Y coordinate where bars start (pixels from top)
        bar_height = 52    # Height of each bar block in pixels
        label_y    = bar_top + bar_height + 18  # Y position for time axis labels
        padding    = 40    # Left/right gap so bars don't touch the window edges

        # Scale: how many pixels correspond to one time unit?
        # Example: total_time=20, usable_width=800px → scale = 40px per unit
        scale = (w - padding * 2) / self.total_time if self.total_time > 0 else 1

        # ── Draw each process block ───────────────────────────────────────────
        for (pid, start, end) in self.timeline:
            x1    = padding + start * scale   # Left edge pixel coordinate
            x2    = padding + end   * scale   # Right edge pixel coordinate
            color = self.colors.get(pid, "#95A5A6")  # Default grey if no colour assigned

            # Filled rectangle for the block; white border separates adjacent blocks
            self.create_rectangle(x1, bar_top, x2, bar_top + bar_height,
                                  fill=color, outline="white", width=2)

            # Draw the process name label inside the block
            # Skip label if the block is too narrow to display text readably
            if (x2 - x1) > 22:
                self.create_text((x1 + x2) / 2, bar_top + bar_height / 2,
                                 text=pid, font=("Arial", 9, "bold"), fill="white")

        # ── Draw time axis labels ─────────────────────────────────────────────
        # Labels show clock values: 0, 1, 2, 3, ... up to total_time.
        # We skip some numbers if the chart is too narrow to fit them all,
        # automatically choosing a step size that keeps labels readable.
        min_gap = 18   # Minimum pixels between labels before they start overlapping
        step    = 1
        while scale * step < min_gap and step < self.total_time:
            step += 1

        for t in range(0, self.total_time + 1, step):
            x = padding + t * scale
            # Short vertical tick mark below each bar
            self.create_line(x, bar_top + bar_height,
                             x, bar_top + bar_height + 6,
                             fill=FG_GREY)
            # Numeric time label below the tick
            self.create_text(x, label_y, text=str(t),
                             font=("Arial", 8), fill=FG_GREY)
