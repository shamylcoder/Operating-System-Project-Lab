# =============================================================================
#  MODULE: app.py
#
#  The main application window — the GUI layer of the CPU Scheduling Simulator.
#
#  WHY A SEPARATE MODULE#  The App class only handles presentation and user interaction.
#  It calls into Scheduler (logic) and GanttChart (drawing) but never
#  implements any scheduling itself. This keeps each layer independent.
#
#  CLASS: App  (inherits from tk.Tk — the root window)
#
# =============================================================================

import tkinter as tk           # Main GUI toolkit
from tkinter import ttk        # Themed (nicer-looking) widgets: Treeview, Combobox
from tkinter import messagebox # Pop-up dialog boxes for errors and warnings

from constants import (
    BG_MAIN, BG_PANEL, BG_HEADER,
    BG_BTN_ADD, BG_BTN_RUN, BG_BTN_DEL, BG_BTN_EX,
    FG_WHITE, FG_DARK, FG_BLUE, FG_GREY,
    FONT_HEADING, FONT_NORMAL, FONT_SMALL, FONT_BTN, FONT_BTN_SM,
    DEFAULT_QUANTUM, MLFQ_QUANTA_DEFAULT, GANTT_COLORS
)
from models    import Process       # Process data class
from scheduler import Scheduler     # All scheduling algorithms + metrics
from gantt     import GanttChart, make_btn  # Chart widget + button factory


# =============================================================================
#  CLASS: App
# =============================================================================

class App(tk.Tk):

    def __init__(self):
        super().__init__()  # Create the actual OS-level window

        # ── Window setup ──────────────────────────────────────────────────────
        self.title("CPU Scheduling Simulator — Bahria University OS Project")
        self.configure(bg=BG_MAIN)
        self.geometry("1200x900")   # Taller window so bottom panels have more space
        self.minsize(1000, 820)     # User cannot shrink the window below this size

        # ── Application data ──────────────────────────────────────────────────
        self.processes   = []           # List of all Process objects the user added
        self.timeline    = []           # Simulation output: [(pid, start, end), ...]
        self.scheduler   = Scheduler()  # One Scheduler object, reused for every run

        self.pid_counter = 1            # Auto-increments for generated PIDs (P1, P2, ...)
        self.sim_index   = 0            # Which animation step are we currently on?
        self.sim_running = False        # True while animation is actively playing
        self.sim_paused  = False        # True when the user has hit Pause

        # Animation speed: time in milliseconds between each Gantt block appearing.
        # Lower = faster animation; higher = slower (easier to follow).
        # This is fixed at 600 ms (roughly "5x speed") — no slider in the GUI.
        self.sim_speed   = 600

        # ── Build the GUI ─────────────────────────────────────────────────────
        self._build_header()
        self._build_body()

    # =========================================================================
    #  GUI BUILDER METHODS
    #  Each _build_* method constructs one visual section of the window.
    #  They are called once during __init__ and never again.
    # =========================================================================

    # ─── HEADER ───────────────────────────────────────────────────────────────

    def _build_header(self):
        # The dark navy bar that stretches across the very top of the window.
        bar = tk.Frame(self, bg=BG_HEADER, pady=10)
        bar.pack(fill="x")  # fill="x" stretches it to the full window width

        tk.Label(bar, text="CPU Scheduling Simulator",
                 bg=BG_HEADER, fg=FG_WHITE,
                 font=("Arial", 18, "bold")).pack(side="left", padx=20)

        tk.Label(bar, text="Operating System Project",
                 bg=BG_HEADER, fg="#A9C4E8",
                 font=("Arial", 11)).pack(side="right", padx=20)

    # ─── BODY ─────────────────────────────────────────────────────────────────

    def _build_body(self):
        # The main content area below the header.
        # Structured in three horizontal rows: top controls, Gantt chart, bottom stats.
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(fill="both", expand=True, padx=12, pady=10)

        # TOP ROW: Process Management (left) and Simulation Controls (right)
        top = tk.Frame(body, bg=BG_MAIN)
        top.pack(fill="x", pady=(0, 8))
        self._build_process_panel(top)   # Left panel
        self._build_controls_panel(top)  # Right panel

        # MIDDLE ROW: Full-width animated Gantt chart
        self._build_gantt_panel(body)

        # BOTTOM ROW: Performance Metrics (left) and Adaptive Feedback (right)
        bottom = tk.Frame(body, bg=BG_MAIN)
        bottom.pack(fill="both", expand=True, pady=(8, 0))
        self._build_metrics_panel(bottom)   # Left panel
        self._build_feedback_panel(bottom)  # Right panel

    # ─── PROCESS MANAGEMENT PANEL (top left) ──────────────────────────────────

    def _build_process_panel(self, parent):
        # LabelFrame = a Frame with a visible border and an embedded title text
        frame = tk.LabelFrame(parent, text="  Process Management  ",
                              bg=BG_PANEL, fg=FG_BLUE, font=FONT_HEADING,
                              relief="solid", bd=1, padx=10, pady=8)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # ── Input row: PID, Arrival, Burst, Priority + action buttons ─────────
        # grid() places widgets in a table-like (row, column) layout
        inp = tk.Frame(frame, bg=BG_PANEL)
        inp.pack(fill="x", pady=(0, 6))

        # PID text field — linked to self.pid_var (a StringVar)
        # StringVar is a special tkinter object: when it changes the widget updates automatically
        tk.Label(inp, text="PID:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).grid(row=0, column=0, padx=(0,3))
        self.pid_var = tk.StringVar()
        tk.Entry(inp, textvariable=self.pid_var, font=FONT_NORMAL,
                 width=6, relief="solid", bd=1).grid(row=0, column=1, padx=(0,8))

        # Arrival Time — Spinbox lets users click up/down arrows to change the value
        tk.Label(inp, text="Arrival:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).grid(row=0, column=2, padx=(0,3))
        self.arrival_var = tk.IntVar(value=0)  # Default arrival = 0
        tk.Spinbox(inp, from_=0, to=999, textvariable=self.arrival_var,
                   font=FONT_NORMAL, width=5, relief="solid", bd=1).grid(row=0, column=3, padx=(0,8))

        # Burst Time
        tk.Label(inp, text="Burst:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).grid(row=0, column=4, padx=(0,3))
        self.burst_var = tk.IntVar(value=4)  # Default burst = 4
        tk.Spinbox(inp, from_=1, to=999, textvariable=self.burst_var,
                   font=FONT_NORMAL, width=5, relief="solid", bd=1).grid(row=0, column=5, padx=(0,8))

        # Priority (1 = most urgent)
        tk.Label(inp, text="Priority:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).grid(row=0, column=6, padx=(0,3))
        self.priority_var = tk.IntVar(value=1)  # Default priority = 1 (highest)
        tk.Spinbox(inp, from_=1, to=99, textvariable=self.priority_var,
                   font=FONT_NORMAL, width=4, relief="solid", bd=1).grid(row=0, column=7, padx=(0,8))

        # Action buttons — colours defined in constants.py
        make_btn(inp, "+ Add",    self._add_process,    BG_BTN_ADD).grid(row=0, column=8, padx=3)
        make_btn(inp, "Remove",   self._remove_process, BG_BTN_DEL, font=FONT_BTN_SM).grid(row=0, column=9,  padx=3)
        make_btn(inp, "Clear All",self._clear_all,      BG_BTN_DEL, font=FONT_BTN_SM).grid(row=0, column=10, padx=3)

        # Hint text — explains the fields in plain language
        tk.Label(frame,
                 text="Arrival = when it joins the queue   |   Burst = CPU time needed   |   Priority: 1 is highest",
                 bg=BG_PANEL, fg=FG_GREY, font=FONT_SMALL).pack(anchor="w", pady=(0, 4))

        # ── Process table (Treeview) ───────────────────────────────────────────
        tbl_frame = tk.Frame(frame, bg=BG_PANEL)
        tbl_frame.pack(fill="both", expand=True)

        # Apply ttk styling — "clam" theme allows more colour customisation
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background=BG_PANEL, foreground=FG_DARK,
                        font=FONT_NORMAL, rowheight=26, fieldbackground=BG_PANEL)
        style.configure("Treeview.Heading", background=BG_HEADER, foreground=FG_WHITE,
                        font=FONT_HEADING, relief="flat")
        # Fix: prevent headings from turning white/invisible on hover
        style.map("Treeview.Heading",
                  background=[("active", BG_HEADER)],   # Stay navy on mouse-over
                  foreground=[("active", FG_WHITE)])     # Keep white text on hover
        style.map("Treeview", background=[("selected", "#D6E4FF")],
                  foreground=[("selected", FG_DARK)])

        cols = ("PID", "Arrival", "Burst", "Priority")
        self.proc_table = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=5)
        for col in cols:
            self.proc_table.heading(col, text=col)
            self.proc_table.column(col, width=90, anchor="center")

        # Alternating row stripe colours via tags
        self.proc_table.tag_configure("odd",  background="#EBF5FB")  # Light blue
        self.proc_table.tag_configure("even", background=BG_PANEL)   # White

        # Vertical scrollbar attached to the table
        sb = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.proc_table.yview)
        self.proc_table.configure(yscrollcommand=sb.set)
        self.proc_table.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # ── Load Example buttons ──────────────────────────────────────────────
        # Pre-built process sets for quick testing without manual data entry
        ex_frame = tk.Frame(frame, bg=BG_PANEL)
        ex_frame.pack(fill="x", pady=(6, 0))
        tk.Label(ex_frame, text="Load Example:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).pack(side="left")
        for name in ["Classic 4-Process", "Starvation Demo", "Mixed Workload"]:
            # lambda n=name captures the current loop value — without this trick,
            # all buttons would share the LAST value of 'name' (a Python gotcha)
            make_btn(ex_frame, name, lambda n=name: self._load_example(n),
                     BG_BTN_EX, font=FONT_BTN_SM, padx=10, pady=5).pack(side="left", padx=4)

    # ─── SIMULATION CONTROLS PANEL (top right) ────────────────────────────────

    def _build_controls_panel(self, parent):
        frame = tk.LabelFrame(parent, text="  Simulation Controls  ",
                              bg=BG_PANEL, fg=FG_BLUE, font=FONT_HEADING,
                              relief="solid", bd=1, padx=12, pady=8)
        frame.pack(side="right", fill="y", padx=(6, 0))

        # Algorithm selection dropdown
        # StringVar links the selected item to self.algo_var — read it with .get()
        tk.Label(frame, text="Algorithm:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).grid(
            row=0, column=0, sticky="w", pady=4)
        self.algo_var = tk.StringVar(value="FCFS")
        algo_cb = ttk.Combobox(frame, textvariable=self.algo_var, font=FONT_NORMAL,
                               width=23, state="readonly",  # readonly = user can only pick, not type
                               values=["FCFS", "SJF (Non-Preemptive)", "SRTF (Preemptive SJF)",
                                       "Priority (Non-Preemptive)", "Priority (Preemptive)",
                                       "Round Robin", "MLFQ"])
        algo_cb.grid(row=0, column=1, sticky="ew", pady=4, padx=(6, 0))
        # <<ComboboxSelected>> is a virtual event that fires when the user picks a new item
        algo_cb.bind("<<ComboboxSelected>>", self._on_algo_change)

        # ── Time Quantum — only active when Round Robin is selected ───────────
        # How long each process runs before being swapped out.
        # Greyed out (disabled) for all other algorithms.
        tk.Label(frame, text="Time Quantum (Round Robin):", bg=BG_PANEL, fg=FG_DARK,
                 font=FONT_NORMAL).grid(row=1, column=0, sticky="w", pady=4)

        self.quantum_var  = tk.IntVar(value=DEFAULT_QUANTUM)  # Default = 2
        self.quantum_spin = tk.Spinbox(frame, from_=1, to=20,
                                       textvariable=self.quantum_var,
                                       font=FONT_NORMAL, width=6,
                                       relief="solid", bd=1,
                                       state="disabled")  # Greyed out until RR is chosen
        self.quantum_spin.grid(row=1, column=1, sticky="w", pady=4, padx=(6, 0))

        # Hint explaining what this field does
        tk.Label(frame,
                 text="← Time units each process gets before switching (RR only)",
                 bg=BG_PANEL, fg=FG_GREY, font=("Arial", 9)).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))

        # ── MLFQ Quanta — only active when MLFQ is selected ──────────────────
        # Three comma-separated values for the three MLFQ priority queues.
        # Example: "2,4,8" means Q0=2 units, Q1=4 units, Q2=8 units.
        tk.Label(frame, text="MLFQ Queue Quanta (Q0, Q1, Q2):", bg=BG_PANEL, fg=FG_DARK,
                 font=FONT_NORMAL).grid(row=3, column=0, sticky="w", pady=4)

        self.mlfq_var   = tk.StringVar(value="2,4,8")  # Default three-level quanta
        self.mlfq_entry = tk.Entry(frame, textvariable=self.mlfq_var,
                                   font=FONT_NORMAL, width=10,
                                   relief="solid", bd=1,
                                   state="disabled")  # Greyed out until MLFQ is chosen
        self.mlfq_entry.grid(row=3, column=1, sticky="w", pady=4, padx=(6, 0))

        # Hint for the MLFQ quanta field
        tk.Label(frame,
                 text="← Three comma-separated quanta for each MLFQ queue (MLFQ only)",
                 bg=BG_PANEL, fg=FG_GREY, font=("Arial", 9)).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(0, 4))

        # ── Thin separator line ───────────────────────────────────────────────
        tk.Frame(frame, bg="#DEE2E6", height=1).grid(row=5, columnspan=2,
                                                      sticky="ew", pady=8)

        # ── Simulation action buttons ─────────────────────────────────────────
        # Row 1: Run and Pause/Resume side by side
        r1 = tk.Frame(frame, bg=BG_PANEL)
        r1.grid(row=6, columnspan=2, pady=3)

        self.run_btn = make_btn(r1, "Run Simulation", self._run_simulation, BG_BTN_RUN, padx=14)
        self.run_btn.pack(side="left", padx=4)

        self.pause_btn = make_btn(r1, "Pause", self._pause_resume, "#7F8C8D", padx=12)
        self.pause_btn.pack(side="left", padx=4)
        self.pause_btn.config(state="disabled")  # Cannot pause before simulation starts

        # Row 2: Reset button
        r2 = tk.Frame(frame, bg=BG_PANEL)
        r2.grid(row=7, columnspan=2, pady=3)
        make_btn(r2, "Reset", self._reset, BG_BTN_DEL, padx=14).pack(side="left", padx=4)

        # Analyze & Recommend — triggers the intelligent algorithm suggestion engine
        make_btn(frame, "Analyze & Recommend", self._analyze_and_recommend,
                 "#16A085", padx=10, pady=8).grid(row=8, columnspan=2,
                                                   pady=(8, 0), sticky="ew")

        # status_var exists so that _add_process, _reset, etc. can call .set(...)
        # without crashing. No visible label is shown in the GUI for this.
        self.status_var = tk.StringVar(value="")

    # ─── GANTT CHART PANEL (middle) ───────────────────────────────────────────

    def _build_gantt_panel(self, parent):
        frame = tk.LabelFrame(parent, text="  Gantt Chart  ",
                              bg=BG_PANEL, fg=FG_BLUE, font=FONT_HEADING,
                              relief="solid", bd=1, padx=6, pady=6)
        frame.pack(fill="x")

        # GanttChart is our custom canvas widget (defined in gantt.py)
        self.gantt = GanttChart(frame, height=90)
        self.gantt.pack(fill="x", expand=True)

        # Redraw the chart whenever the user resizes the window,
        # so bars stay correctly scaled to the new pixel width
        self.gantt.bind("<Configure>", lambda e: self.gantt.redraw())

    # ─── PERFORMANCE METRICS PANEL (bottom left) ──────────────────────────────

    def _build_metrics_panel(self, parent):
        frame = tk.LabelFrame(parent, text="  Performance Metrics  ",
                              bg=BG_PANEL, fg=FG_BLUE, font=FONT_HEADING,
                              relief="solid", bd=1, padx=8, pady=8)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # Metrics table — one row per process, showing all calculated values
        cols = ("PID", "Arrival", "Burst", "Finish", "Turnaround", "Waiting", "Response")
        self.met_table = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        widths = [60, 70, 60, 65, 100, 75, 80]
        for col, w in zip(cols, widths):
            self.met_table.heading(col, text=col)
            self.met_table.column(col, width=w, anchor="center")

        # Fix heading hover colour bug (same fix as the process table)
        style = ttk.Style()
        style.map("Treeview.Heading",
                  background=[("active", BG_HEADER)],
                  foreground=[("active", FG_WHITE)])

        self.met_table.tag_configure("odd",  background="#EBF5FB")
        self.met_table.tag_configure("even", background=BG_PANEL)

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.met_table.yview)
        self.met_table.configure(yscrollcommand=sb.set)
        self.met_table.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Summary line below the table — shows averages and CPU utilisation
        self.summary_var = tk.StringVar(value="Run a simulation to see metrics here.")
        tk.Label(frame, textvariable=self.summary_var, bg=BG_PANEL, fg="#1A5276",
                 font=FONT_SMALL, justify="left", wraplength=600).pack(anchor="w", pady=(6, 0))

    # ─── ADAPTIVE FEEDBACK PANEL (bottom right) ───────────────────────────────

    def _build_feedback_panel(self, parent):
        frame = tk.LabelFrame(parent, text="  Adaptive Feedback  ",
                              bg=BG_PANEL, fg=FG_BLUE, font=FONT_HEADING,
                              relief="solid", bd=1, padx=8, pady=8)
        frame.pack(side="right", fill="both", padx=(6, 0))

        # tk.Text is a multi-line text box.
        # state="disabled" makes it read-only — users can't type in it.
        # To insert text programmatically: set state="normal", insert, then "disabled".
        self.feedback_text = tk.Text(frame, font=FONT_SMALL, bg="#F8F9FA", fg=FG_DARK,
                                     relief="solid", bd=1, wrap="word",
                                     state="disabled", width=34)
        self.feedback_text.pack(fill="both", expand=True)

        # Tags in a Text widget work like CSS classes — style specific ranges of text
        self.feedback_text.tag_configure("title",   font=("Arial",11,"bold"), foreground=FG_BLUE)
        self.feedback_text.tag_configure("suggest", font=("Arial",11,"bold"), foreground="#1E8449")
        self.feedback_text.tag_configure("warning", font=("Arial",10,"bold"), foreground="#E74C3C")
        self.feedback_text.tag_configure("normal",  font=("Arial",10),        foreground=FG_DARK)

        # Show a default placeholder message before any analysis is run
        self._set_feedback("Add processes and click\nAnalyze & Recommend\nto get suggestions here.", "normal")

    #  ACTION METHODS — called when the user clicks buttons


    def _add_process(self):
        # Read the PID field — auto-generate "P1", "P2", ... if left blank
        pid = self.pid_var.get().strip()
        if not pid:
            pid = f"P{self.pid_counter}"  # f-string: embed variable value into string

        # Reject duplicate PIDs so each process stays uniquely identifiable
        if any(p.pid == pid for p in self.processes):
            messagebox.showwarning("Duplicate PID", f"A process named '{pid}' already exists!")
            return

        # Validate numeric input from spinboxes
        try:
            arrival  = int(self.arrival_var.get())
            burst    = int(self.burst_var.get())
            priority = int(self.priority_var.get())
        except (ValueError, tk.TclError):
            messagebox.showerror("Input Error", "Please enter valid numbers for Arrival, Burst, and Priority.")
            return

        # Create the Process object and add it to the internal list
        p = Process(pid, arrival, burst, priority)
        self.processes.append(p)
        self.pid_counter += 1

        # Insert a row into the visual table
        # odd/even tags apply alternating stripe background colours
        tag = "odd" if len(self.processes) % 2 == 1 else "even"
        self.proc_table.insert("", "end", values=(pid, arrival, burst, priority), tags=(tag,))

        self.pid_var.set("")  # Clear the PID field ready for the next entry
        self.status_var.set(f"Added {pid}. Total: {len(self.processes)} processes.")

    def _remove_process(self):
        # selection() returns the internal IDs of all selected rows
        sel = self.proc_table.selection()
        if not sel:
            return  # Nothing selected — do nothing
        pid = self.proc_table.item(sel[0], "values")[0]  # Read PID from column 0
        self.proc_table.delete(sel[0])                    # Remove from visual table
        # Filter out the matching process from the data list
        self.processes = [p for p in self.processes if p.pid != pid]
        self.status_var.set(f"Removed {pid}.")

    def _clear_all(self):
        # Remove all processes from data and visual table, then reset simulation state
        self.processes.clear()
        self.proc_table.delete(*self.proc_table.get_children())  # *args unpacks all IDs
        self._reset()
        self.pid_counter = 1
        self.status_var.set("All cleared.")

    def _load_example(self, name):
        # Replace the current process list with a pre-built example set.
        # Useful for quickly demonstrating different algorithm behaviours.
        self._clear_all()

        if name == "Classic 4-Process":
            # Good starting point for comparing FCFS, SJF, and Round Robin
            data = [("P1",0,6,2), ("P2",1,4,1), ("P3",2,8,3), ("P4",3,3,2)]

        elif name == "Starvation Demo":
            # P1 has a huge burst (20) and low priority (3).
            # With Priority Non-Preemptive, P1 blocks everyone.
            # Switch to Priority Preemptive to see Aging rescue P2 and P3.
            data = [("P1",0,20,3), ("P2",1,3,1), ("P3",2,4,1), ("P4",3,2,2), ("P5",4,5,3)]

        else:  # Mixed Workload
            # Variety of burst times and priorities — ideal for testing MLFQ
            data = [("P1",0,2,1), ("P2",0,10,3), ("P3",1,3,2),
                    ("P4",2,7,1), ("P5",3,4,2), ("P6",5,1,1)]

        # Insert each process into both the data list and the visual table
        for pid, at, bt, pr in data:
            p = Process(pid, at, bt, pr)
            self.processes.append(p)
            tag = "odd" if len(self.processes) % 2 == 1 else "even"
            self.proc_table.insert("", "end", values=(pid,at,bt,pr), tags=(tag,))

        self.pid_counter = len(self.processes) + 1
        self.status_var.set(f"Loaded '{name}' — {len(self.processes)} processes ready.")
        self._analyze_and_recommend()  # Automatically suggest the best algorithm

    def _on_algo_change(self, event=None):
        # Called every time the user picks a different algorithm from the dropdown.
        # Enable/disable the quantum and MLFQ quanta fields accordingly.
        # Fields that don't apply to the selected algorithm are greyed out.
        algo = self.algo_var.get()

        # The Time Quantum spinner is only relevant for Round Robin
        self.quantum_spin.config(state="normal" if algo == "Round Robin" else "disabled")

        # The MLFQ Quanta text entry is only relevant for MLFQ
        self.mlfq_entry.config(state="normal" if algo == "MLFQ" else "disabled")

    # =========================================================================
    #  SIMULATION FLOW METHODS
    #  These manage the animated step-by-step playback of results.
    # =========================================================================

    def _run_simulation(self):
        # Validate that at least one process exists before running
        if not self.processes:
            messagebox.showinfo("No Processes", "Please add at least one process first!")
            return
        if self.sim_running:
            return  # Already animating — ignore duplicate clicks

        # Run the selected algorithm and receive the complete timeline at once.
        # Animation then plays it back step-by-step via _sim_step().
        self.timeline = self.scheduler.run(
            self.algo_var.get(),
            self.processes,
            self.quantum_var.get(),   # Only used by Round Robin
            self._get_mlfq_quanta()   # Only used by MLFQ
        )

        if not self.timeline:
            messagebox.showwarning("No Output", "Simulation produced no output. Check your data.")
            return

        # Prepare the Gantt chart for animation — start with an empty timeline
        self.gantt.total_time = max(end for (_, _, end) in self.timeline)
        self.gantt.colors     = {p.pid: GANTT_COLORS[i % len(GANTT_COLORS)]
                                 for i, p in enumerate(self.processes)}
        self.gantt.timeline   = []  # Blocks will be added one at a time by _sim_step
        self.gantt.redraw()

        # Clear the metrics table to show fresh results after this run
        self.met_table.delete(*self.met_table.get_children())
        self.summary_var.set("Simulation running...")

        # Initialise animation state
        self.sim_index   = 0
        self.sim_running = True
        self.sim_paused  = False
        self.run_btn.config(state="disabled")    # Prevent re-running while animating
        self.pause_btn.config(state="normal", text="Pause")
        self.status_var.set(f"Running {self.algo_var.get()}...")

        self._sim_step()  # Kick off the animation loop

    def _sim_step(self):
        # Called repeatedly by tkinter's timer — adds ONE Gantt block per call.
        # self.after(ms, func) schedules the next call after 'ms' milliseconds,
        # creating a smooth animation loop without blocking the GUI.
        if self.sim_paused or not self.sim_running:
            return  # Do nothing if paused or already stopped

        if self.sim_index >= len(self.timeline):
            # All blocks have been displayed — simulation is complete
            self.sim_running = False
            self.run_btn.config(state="normal")
            self.pause_btn.config(state="disabled")
            self.status_var.set(f"Done!  {self.algo_var.get()} simulation complete.")
            self._show_metrics()  # Populate the metrics table now that we're done
            return

        # Append the next timeline block to the chart and redraw
        block = self.timeline[self.sim_index]
        self.gantt.timeline.append(block)
        self.gantt.redraw()
        self.status_var.set(
            f"Step {self.sim_index+1}/{len(self.timeline)} — "
            f"{block[0]}  runs from time {block[1]} to {block[2]}"
        )
        self.sim_index += 1

        # Schedule the next step — this is what creates the animation loop
        self.after(self.sim_speed, self._sim_step)

    def _pause_resume(self):
        # Toggle between paused and running states
        if self.sim_paused:
            self.sim_paused = False
            self.pause_btn.config(text="Pause")
            self.status_var.set("Resumed.")
            self._sim_step()  # Restart the animation loop from where it stopped
        else:
            self.sim_paused = True
            self.pause_btn.config(text="Resume")
            self.status_var.set("Paused. Click Resume to continue.")

    def _reset(self):
        # Stop any running simulation and clear all visual output.
        # The process table is intentionally NOT cleared — the user can re-run.
        self.sim_running = False
        self.sim_paused  = False
        self.sim_index   = 0
        self.timeline    = []
        self.gantt.timeline = []
        self.gantt.redraw()
        self.met_table.delete(*self.met_table.get_children())
        self.summary_var.set("Run a simulation to see metrics here.")
        self.run_btn.config(state="normal")
        self.pause_btn.config(state="disabled", text="Pause")
        self.status_var.set("Reset — ready to run again.")

    def _show_metrics(self):
        # Populate the metrics table after the simulation completes.
        # Calls into Scheduler.calculate_metrics() to get all the numbers.
        if not self.timeline:
            return

        # metrics is a dict: { "P1": {...}, "P2": {...}, "__summary__": {...} }
        metrics = self.scheduler.calculate_metrics(self.processes, self.timeline)
        summary = metrics.pop("__summary__", {})  # Extract the averages row separately

        self.met_table.delete(*self.met_table.get_children())

        # Insert one row per process into the table
        for i, (pid, m) in enumerate(metrics.items()):
            tag = "odd" if i % 2 == 0 else "even"
            self.met_table.insert("", "end", values=(
                pid, m["arrival"], m["burst"], m["finish"],
                m["turnaround"], m["waiting"], m["response"]
            ), tags=(tag,))

        # Update the summary label below the table with aggregate statistics
        if summary:
            self.summary_var.set(
                f"Avg Waiting: {summary['avg_waiting']}   |   "
                f"Avg Turnaround: {summary['avg_turnaround']}   |   "
                f"Avg Response: {summary['avg_response']}   |   "
                f"CPU Utilisation: {summary['cpu_utilization']}%   |   "
                f"Throughput: {summary['throughput']} proc/unit"
            )

    def _analyze_and_recommend(self):
        # Run the intelligent recommendation engine and display the results
        # in the Adaptive Feedback panel on the bottom right.
        if not self.processes:
            self._set_feedback("Add processes first, then click Analyze.", "normal")
            return

        suggestion, reasons = self.scheduler.get_recommendation(self.processes)
        bursts = [p.burst_time for p in self.processes]

        # Enable the text box, clear it, insert new content, then lock it again
        self.feedback_text.config(state="normal")
        self.feedback_text.delete("1.0", "end")  # "1.0" = line 1, character 0 (start of file)

        # Each insert call uses a different tag to apply different styling
        self.feedback_text.insert("end", "RECOMMENDED ALGORITHM\n", "title")
        self.feedback_text.insert("end", f"  {suggestion}\n\n", "suggest")
        self.feedback_text.insert("end", "REASONS:\n", "title")
        for line in reasons.split("\n"):
            # Lines containing "WARNING" or "STARVATION" get red bold styling
            tag = "warning" if "WARNING" in line or "STARVATION" in line else "normal"
            self.feedback_text.insert("end", line + "\n", tag)
        self.feedback_text.insert("end", "\nWORKLOAD SUMMARY:\n", "title")
        self.feedback_text.insert("end",
            f"  Processes: {len(self.processes)}\n"
            f"  Burst range: {min(bursts)} to {max(bursts)}\n"
            f"  Average burst: {sum(bursts)/len(bursts):.1f}\n"
            f"  Priorities in use: {sorted(set(p.priority for p in self.processes))}\n",
            "normal")
        self.feedback_text.config(state="disabled")

    # =========================================================================
    #  UTILITY HELPERS
    # =========================================================================

    def _get_mlfq_quanta(self):
        # Parse the MLFQ quanta text field — user types something like "2,4,8".
        # Converts that string into a Python list of integers: [2, 4, 8].
        # Falls back silently to the default [2, 4, 8] on any parsing error.
        try:
            return [int(x.strip()) for x in self.mlfq_var.get().split(",")]
        except (ValueError, AttributeError):
            return list(MLFQ_QUANTA_DEFAULT)  # Use the constant from constants.py

    def _set_feedback(self, text, tag="normal"):
        # Helper: replace all feedback panel text with a single uniformly styled message.
        # Avoids repeating the enable/delete/insert/disable pattern every time.
        self.feedback_text.config(state="normal")
        self.feedback_text.delete("1.0", "end")
        self.feedback_text.insert("end", text, tag)
        self.feedback_text.config(state="disabled")
