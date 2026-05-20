# =============================================================================
#  MODULE: constants.py
#
#  Central configuration file for the CPU Scheduling Simulator.
#  All colours, fonts, and algorithm default values live here.
#
#  WHY A SEPARATE FILE?
#  Having all constants in one place means:
#    → Change a colour once and it updates across the whole app.
#    → Easy to theme or customise without hunting through code.
#    → No "magic numbers" scattered through the codebase.
# =============================================================================


# ─── COLOUR CONSTANTS ─────────────────────────────────────────────────────────
# All colours are defined here in one place.
# Change any of these and the whole theme updates automatically!
# Format: "#RRGGBB" — two hex digits each for Red, Green, Blue.
# ─────────────────────────────────────────────────────────────────────────────

BG_MAIN    = "#F0F4F8"  # Light grey-blue background of the whole window
BG_PANEL   = "#FFFFFF"  # White — background of each panel/section
BG_HEADER  = "#2C3E7A"  # Dark navy — the top header bar
BG_BTN_ADD = "#27AE60"  # Green  — "Add Process" button
BG_BTN_RUN = "#2980B9"  # Blue   — "Run Simulation" button
BG_BTN_DEL = "#E74C3C"  # Red    — "Remove" and "Reset" buttons
BG_BTN_EX  = "#8E44AD"  # Purple — "Load Example" preset buttons
BG_BTN_INS = "#F39C12"  # Orange — "Show Instantly" button
BG_GANTT   = "#FAFAFA"  # Off-white — Gantt chart drawing area

FG_WHITE   = "#FFFFFF"  # White text (used on dark-coloured buttons)
FG_DARK    = "#1A1A2E"  # Very dark navy — main body text
FG_BLUE    = "#2C3E7A"  # Navy — section headings and titles
FG_GREEN   = "#1E8449"  # Dark green — status messages (success)
FG_GREY    = "#7F8C8D"  # Medium grey — hint text and minor labels

# Colours for the Gantt chart blocks.
# Each process automatically gets a different colour from this list.
# If there are more than 10 processes the colours cycle/repeat.
GANTT_COLORS = [
    "#3498DB",  # Blue
    "#E74C3C",  # Red
    "#2ECC71",  # Green
    "#F39C12",  # Orange
    "#9B59B6",  # Purple
    "#1ABC9C",  # Teal
    "#E91E63",  # Pink
    "#FF5722",  # Deep Orange
    "#00BCD4",  # Cyan
    "#8BC34A",  # Light Green
]

# ─── FONT CONSTANTS ───────────────────────────────────────────────────────────
# tkinter fonts are tuples: ("font name", size)  or  ("name", size, "bold")
FONT_HEADING = ("Arial", 12, "bold")  # Section titles
FONT_NORMAL  = ("Arial", 11)          # Regular labels and input fields
FONT_SMALL   = ("Arial", 10)          # Hints, table content, status text
FONT_BTN     = ("Arial", 11, "bold")  # Main buttons
FONT_BTN_SM  = ("Arial", 10, "bold")  # Smaller buttons (Remove, Clear)

# ─── ALGORITHM SETTINGS ───────────────────────────────────────────────────────
# These are the default values used by each algorithm.
# Round Robin needs a "time quantum" — how long each process runs before switching.
# MLFQ uses three queues; each queue has its own time quantum.
DEFAULT_QUANTUM     = 2         # Default time quantum for Round Robin
MLFQ_QUANTA_DEFAULT = [2, 4, 8] # Queue 0=2 units, Queue 1=4, Queue 2=8
