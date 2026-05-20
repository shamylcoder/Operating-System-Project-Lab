# =============================================================================
#  CPU SCHEDULING SIMULATOR
#  Bahria University — CSL-320 Operating Systems
#  Language: Python 3  |  GUI: tkinter (comes built-in with Python!)
#
#  HOW TO RUN:
#    Open a terminal and type:  python cpu_scheduler.py
#    No extra installs needed — tkinter is already part of Python.
# =============================================================================
#
#  WHAT IS CPU SCHEDULING? (Simple Explanation)
#  ─────────────────────────────────────────────
#  Your computer has ONE processor (CPU) that can only do ONE thing at a time.
#  But you might have many programs open: a browser, music player, file copy…
#  The Operating System (OS) must decide: which program gets the CPU next?
#  That decision system is called the CPU Scheduler.
#
#  This simulator makes those decisions VISIBLE — you can watch the OS work!
#
#  IMPORTANT WORDS YOU WILL SEE:
#  ──────────────────────────────
#  Process       → A program that wants to use the CPU (like "P1", "P2")
#  Arrival Time  → The clock tick when the process first shows up in line
#  Burst Time    → How many time-units of CPU the process needs to finish
#  Priority      → How urgent it is — number 1 = MOST urgent (highest priority)
#  Waiting Time  → Total time spent sitting in line, doing nothing
#  Turnaround    → Time from arrival until it fully finishes (finish - arrival)
#  Response Time → Time until the process FIRST touches the CPU
#  Preemptive    → The OS CAN kick a process off the CPU mid-run and switch
#  Non-Preemptive→ Once a process starts, it runs until it is completely done
#  Starvation    → A process NEVER gets the CPU because others keep cutting in
#  Aging         → The fix for starvation: waiting processes slowly get more urgent
#  Gantt Chart   → A coloured bar chart showing who used the CPU at each moment
#
# =============================================================================


# ─── IMPORTS ──────────────────────────────────────────────────────────────────
# We only use libraries that are BUILT INTO Python — nothing to install.
#
# tkinter    → the library for building windows, buttons, labels, etc.
# ttk        → nicer-looking widgets (tables, dropdowns) from the same library
# messagebox → pop-up dialog boxes for errors, warnings, and info
# copy       → lets us make a full independent copy of a list (deep copy)
# ─────────────────────────────────────────────────────────────────────────────

import tkinter as tk           # Main GUI toolkit
from tkinter import ttk        # Themed (nicer-looking) widgets
from tkinter import messagebox # Pop-up dialogs
import copy                    # For duplicating process lists safely


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
# You chose to keep the Time Quantum field visible so the user can change it.
# The MLFQ quanta are fixed here (2, 4, 8) since they are advanced.
DEFAULT_QUANTUM     = 2         # Default time quantum for Round Robin
MLFQ_QUANTA_DEFAULT = [2, 4, 8] # Queue 0=2 units, Queue 1=4, Queue 2=8


# =============================================================================
#  CLASS: Process
#
#  A "class" is a Python blueprint for creating objects.
#  Think of it like a paper form with named fields.
#  Every process we add gets its own Process object with its own field values.
#
#  We split fields into two groups:
#    INPUT  fields → filled in by the user (PID, arrival, burst, priority)
#    OUTPUT fields → calculated by the simulator after it runs
# =============================================================================

class Process:

    def __init__(self, pid, arrival_time, burst_time, priority=1):
        # __init__ is the "constructor" — it runs automatically when you do:
        #   p = Process("P1", 0, 6, 2)
        # "self" means "this specific object being created right now".

        # ── INPUT FIELDS ──────────────────────────────────────────────────────
        self.pid          = pid           # e.g. "P1", "P2"
        self.arrival_time = arrival_time  # When it joins the ready queue
        self.burst_time   = burst_time    # Total CPU time needed
        self.priority     = priority      # 1 = most urgent; larger = less urgent

        # ── WORKING FIELDS (change during simulation) ─────────────────────────
        # remaining_time starts equal to burst_time and counts DOWN to 0.
        # Preemptive algorithms (SRTF, Round Robin, MLFQ) use this field.
        self.remaining_time = burst_time

        # queue_level is only used by MLFQ.
        # It tracks which priority queue (0, 1 or 2) this process is currently in.
        self.queue_level = 0

        # ── OUTPUT FIELDS (filled in after simulation finishes) ───────────────
        self.start_time      = -1  # First tick when it got the CPU (-1 = not yet)
        self.finish_time     = -1  # Tick when it fully completed
        self.waiting_time    = 0   # Total idle wait time (calculated later)
        self.turnaround_time = 0   # finish_time - arrival_time (calculated later)
        self.response_time   = -1  # First CPU tick - arrival_time (calculated later)

    def reset(self):
        # Resets all output fields back to their starting values.
        # Called before re-running a simulation so results are clean.
        self.remaining_time  = self.burst_time
        self.queue_level     = 0
        self.start_time      = -1
        self.finish_time     = -1
        self.waiting_time    = 0
        self.turnaround_time = 0
        self.response_time   = -1


# =============================================================================
#  CLASS: Scheduler
#
#  This class contains ALL the scheduling logic.
#  It has absolutely NO GUI code — just pure Python logic.
#
#  The public method is:
#    run(algorithm, processes, time_quantum) → returns a timeline
#
#  A "timeline" is a list of tuples like:
#    [("P1", 0, 6), ("P2", 6, 10), ("P3", 10, 18), ...]
#    meaning: P1 ran from time 0→6, P2 ran 6→10, P3 ran 10→18, etc.
#
#  The timeline is used by:
#    → GanttChart  (draws the coloured blocks)
#    → calculate_metrics (computes waiting time, turnaround, etc.)
# =============================================================================

class Scheduler:

    # ─────────────────────────────────────────────────────────────────────────
    def run(self, algorithm, processes, time_quantum=2, mlfq_quanta=None):
        # This is the ENTRY POINT — the only method the GUI needs to call.
        #
        # Parameters:
        #   algorithm    → the name string e.g. "FCFS", "Round Robin", "MLFQ"
        #   processes    → list of Process objects the user has added
        #   time_quantum → for Round Robin only — how long each process runs per turn
        #   mlfq_quanta  → for MLFQ only — list like [2, 4, 8] for the 3 queue levels
        #
        # Why do we use copy.deepcopy()?
        # Every algorithm modifies process objects (decrements remaining_time, etc.)
        # If we modified the originals, the user's input data would be destroyed.
        # deepcopy() creates a 100% independent duplicate so originals stay safe.
        procs = copy.deepcopy(processes)

        # If no MLFQ quanta were provided, fall back to the global default [2, 4, 8]
        quanta = mlfq_quanta if mlfq_quanta else list(MLFQ_QUANTA_DEFAULT)

        # Pick the right algorithm and run it.
        # Each one returns a timeline list.
        if   algorithm == "FCFS":
            return self.fcfs(procs)
        elif algorithm == "SJF (Non-Preemptive)":
            return self.sjf_non_preemptive(procs)
        elif algorithm == "SRTF (Preemptive SJF)":
            return self.srtf(procs)
        elif algorithm == "Priority (Non-Preemptive)":
            return self.priority_non_preemptive(procs)
        elif algorithm == "Priority (Preemptive)":
            return self.priority_preemptive(procs)
        elif algorithm == "Round Robin":
            return self.round_robin(procs, time_quantum)
        elif algorithm == "MLFQ":
            # Use the quanta the user entered in the MLFQ field (or the default)
            return self.mlfq(procs, quanta)
        return []  # Unknown algorithm — return empty list


    # =========================================================================
    #  ALGORITHM 1: FCFS — First Come, First Served
    # =========================================================================
    # The simplest algorithm. Processes run in the order they ARRIVE.
    # Like a queue at a shop — first in line gets served first.
    # No interruptions: once a process starts it runs to completion.
    #
    # PROBLEM: "Convoy effect" — if the first process is huge (long burst),
    # everyone behind it waits a very long time, even if their burst is tiny.
    # =========================================================================

    def fcfs(self, procs):
        procs.sort(key=lambda p: p.arrival_time)  # Sort by who arrived first
        timeline     = []  # We'll fill this with (pid, start, end) tuples
        current_time = 0   # Our simulation clock starts at 0

        for p in procs:
            # If the CPU is idle (nothing arrived yet), jump forward in time
            if current_time < p.arrival_time:
                current_time = p.arrival_time  # Skip idle gap

            start = current_time
            end   = current_time + p.burst_time  # Runs all the way to completion

            timeline.append((p.pid, start, end))  # Record this block
            current_time = end  # Advance clock to when this process finished

        return timeline


    # =========================================================================
    #  ALGORITHM 2: SJF — Shortest Job First (Non-Preemptive)
    # =========================================================================
    # At each scheduling point, look at ALL processes currently in the queue.
    # Pick the one with the SHORTEST burst time.
    # Once selected, it runs until it finishes (no interruptions).
    #
    # WHY IT'S GOOD: Proven to give the lowest average waiting time.
    # PROBLEM:  Long processes can starve if short ones keep arriving.
    # Also: in a real OS, you can't always know burst time in advance.
    # =========================================================================

    def sjf_non_preemptive(self, procs):
        procs.sort(key=lambda p: p.arrival_time)
        timeline     = []
        current_time = 0
        remaining    = procs[:]  # Copy — we remove processes as they're scheduled

        while remaining:
            # Find all processes that have ALREADY ARRIVED (arrival <= current time)
            available = [p for p in remaining if p.arrival_time <= current_time]

            if not available:
                # Nothing has arrived yet — jump to the next arrival time
                current_time = remaining[0].arrival_time
                continue

            # From available processes, pick the one with the shortest burst
            shortest = min(available, key=lambda p: p.burst_time)
            remaining.remove(shortest)  # It's now being scheduled

            start = current_time
            end   = current_time + shortest.burst_time
            timeline.append((shortest.pid, start, end))
            current_time = end

        return timeline


    # =========================================================================
    #  ALGORITHM 3: SRTF — Shortest Remaining Time First (Preemptive SJF)
    # =========================================================================
    # Like SJF, but we CAN interrupt the running process.
    # Every single time unit we ask: "Is there a process with LESS remaining
    # time than the current one?" If yes — switch to that shorter one.
    #
    # This runs TICK BY TICK (one unit at a time) which is why we track
    # last_pid and last_start — to know when the running process changes
    # so we can save the completed block to the timeline.
    # =========================================================================

    def srtf(self, procs):
        procs.sort(key=lambda p: p.arrival_time)
        timeline     = []
        current_time = 0
        completed    = 0
        n            = len(procs)
        last_pid     = None  # Which process ran in the previous tick
        last_start   = 0     # When the current continuous run started

        while completed < n:
            # Find all processes that have arrived AND still have work left
            available = [p for p in procs
                         if p.arrival_time <= current_time and p.remaining_time > 0]

            if not available:
                current_time += 1  # CPU idle — tick forward
                continue

            # Always pick whoever has the LEAST remaining time
            shortest = min(available, key=lambda p: p.remaining_time)

            # Detect a process SWITCH — if the running process changed,
            # save the OLD process's block before starting the new one
            if last_pid != shortest.pid:
                if last_pid is not None:
                    timeline.append((last_pid, last_start, current_time))
                last_pid   = shortest.pid  # Record new runner
                last_start = current_time  # Record when this run started

            shortest.remaining_time -= 1  # Run for exactly 1 time unit
            current_time            += 1  # Tick the clock

            if shortest.remaining_time == 0:
                # Process is fully done — save its final block
                timeline.append((shortest.pid, last_start, current_time))
                last_pid  = None  # CPU is free now
                completed += 1    # One more process done

        return timeline


    # =========================================================================
    #  ALGORITHM 4: Priority Scheduling (Non-Preemptive)
    # =========================================================================
    # Each process has a priority number. LOWER number = MORE urgent.
    # At each scheduling point, pick the highest-priority available process.
    # Once it starts, it runs until completion (no interruptions).
    #
    # REAL EXAMPLE: Like a hospital — critical patients (priority 1)
    # are seen before routine checkups (priority 5).
    # PROBLEM: Low-priority processes can starve without aging.
    # =========================================================================

    def priority_non_preemptive(self, procs):
        procs.sort(key=lambda p: p.arrival_time)
        timeline     = []
        current_time = 0
        remaining    = procs[:]

        while remaining:
            available = [p for p in remaining if p.arrival_time <= current_time]

            if not available:
                current_time = min(remaining, key=lambda p: p.arrival_time).arrival_time
                continue

            # Pick lowest priority NUMBER (= highest urgency)
            chosen = min(available, key=lambda p: p.priority)
            remaining.remove(chosen)

            start = current_time
            end   = current_time + chosen.burst_time
            timeline.append((chosen.pid, start, end))
            current_time = end

        return timeline


    # =========================================================================
    #  ALGORITHM 5: Priority Scheduling (Preemptive) + AGING
    # =========================================================================
    # Like Algorithm 4, but NOW we can interrupt the running process
    # if a higher-priority one arrives.
    #
    # AGING prevents starvation:
    #   Every 5 time-units a process spends waiting, its priority number
    #   decreases by 1 (making it more urgent). Eventually even the lowest-
    #   priority process will reach priority 1 and get the CPU.
    #
    # Extra variables:
    #   eff_priority  → tracks the CURRENT effective priority (changes with aging)
    #   time_in_queue → how many ticks each process has been waiting
    # =========================================================================

    def priority_preemptive(self, procs):
        procs.sort(key=lambda p: p.arrival_time)
        timeline      = []
        current_time  = 0
        completed     = 0
        n             = len(procs)
        last_pid      = None
        last_start    = 0

        # Start with original priorities; these will improve as processes wait
        eff_priority  = {p.pid: p.priority for p in procs}
        time_in_queue = {p.pid: 0 for p in procs}  # Wait counter for each process

        while completed < n:
            available = [p for p in procs
                         if p.arrival_time <= current_time and p.remaining_time > 0]

            if not available:
                current_time += 1
                continue

            # ── AGING: boost priority of waiting processes ─────────────────
            for p in available:
                time_in_queue[p.pid] += 1  # This process waited one more tick
                # Every 5 ticks of waiting → priority improves by 1
                if time_in_queue[p.pid] % 5 == 0:
                    # max(1,...) makes sure priority never goes below 1
                    eff_priority[p.pid] = max(1, eff_priority[p.pid] - 1)
            # ──────────────────────────────────────────────────────────────

            # Pick the process with the best (lowest) EFFECTIVE priority
            chosen = min(available, key=lambda p: eff_priority[p.pid])

            if last_pid != chosen.pid:
                if last_pid is not None:
                    timeline.append((last_pid, last_start, current_time))
                last_pid   = chosen.pid
                last_start = current_time
                time_in_queue[chosen.pid] = 0  # Reset wait counter — it's running now

            chosen.remaining_time -= 1
            current_time          += 1

            if chosen.remaining_time == 0:
                timeline.append((chosen.pid, last_start, current_time))
                last_pid  = None
                completed += 1

        return timeline


    # =========================================================================
    #  ALGORITHM 6: Round Robin
    # =========================================================================
    # Every process gets a fixed time slice called the "time quantum".
    # When the quantum expires, the current process goes to the BACK of the queue
    # and the NEXT process gets its turn.
    #
    # ANALOGY: Like taking turns in a board game — Player 1 goes, then Player 2,
    # then Player 3, then back to Player 1. No one hogs all the turns.
    #
    # The time quantum is set by the user via the "Time Quantum" spinner.
    # Smaller quantum → fairer but more switching overhead.
    # Larger quantum  → less switching but some processes wait longer.
    # If quantum >= largest burst time, Round Robin behaves like FCFS.
    #
    # WHY IT'S USED: This is what most desktop OS use!
    # Windows, Linux, and macOS all use Round Robin variants.
    # =========================================================================

    def round_robin(self, procs, time_quantum):
        procs.sort(key=lambda p: p.arrival_time)
        timeline     = []
        current_time = 0
        queue        = []   # The ready queue — processes waiting their turn
        remaining    = procs[:]
        completed    = 0
        n            = len(procs)
        i            = 0    # Index into 'remaining' to detect new arrivals

        # Load processes that are already here at time 0
        while i < len(remaining) and remaining[i].arrival_time <= current_time:
            queue.append(remaining[i])
            i += 1

        while completed < n:
            if not queue:
                # Queue is empty — jump clock to next arrival and add it
                if i < len(remaining):
                    current_time = remaining[i].arrival_time
                    queue.append(remaining[i])
                    i += 1
                continue

            p = queue.pop(0)  # Take the FIRST process from the front of the queue

            # Run for quantum OR remaining time, whichever is less
            # (If only 2 units left but quantum is 4, just run 2 units and finish)
            run_time = min(time_quantum, p.remaining_time)
            start    = current_time
            end      = current_time + run_time

            timeline.append((p.pid, start, end))
            p.remaining_time -= run_time
            current_time      = end

            # Add any new arrivals that showed up during this time slice
            while i < len(remaining) and remaining[i].arrival_time <= current_time:
                queue.append(remaining[i])  # New arrivals join the BACK of queue
                i += 1

            if p.remaining_time > 0:
                queue.append(p)  # Not done yet — goes to the BACK of the queue
            else:
                completed += 1   # Fully finished!

        return timeline


    # =========================================================================
    #  ALGORITHM 7: MLFQ — Multilevel Feedback Queue
    # =========================================================================
    # The most advanced algorithm. Used in real OS: Linux, Windows, macOS!
    #
    # There are 3 queues, each with a different priority and time quantum:
    #   Queue 0 (HIGHEST priority) — quantum = 2   ← All new processes start here
    #   Queue 1 (medium priority)  — quantum = 4
    #   Queue 2 (LOWEST priority)  — quantum = 8
    #
    # THE SMART RULE:
    # If a process uses its FULL quantum without finishing → it gets DEMOTED
    # to the next lower queue (longer quantum, lower priority).
    # If it finishes before the quantum → it stays in its current queue.
    #
    # WHY IT'S SMART:
    # Short, interactive jobs (finish quickly) stay in the high-priority queues.
    # Long, CPU-heavy jobs automatically sink to the low-priority queues.
    # The OS doesn't need to know burst time in advance — the process reveals
    # its own nature through its behaviour!
    #
    # Fixed quanta: [2, 4, 8] — defined at the top of this file.
    # =========================================================================

    def mlfq(self, procs, quanta):
        procs.sort(key=lambda p: p.arrival_time)

        num_levels = len(quanta)                      # Usually 3 queues
        queues     = [[] for _ in range(num_levels)]  # One empty list per queue
        timeline   = []
        current_time = 0
        completed    = 0
        n            = len(procs)
        proc_index   = 0  # Points to the next process that hasn't arrived yet

        while completed < n:
            # Add every process that has arrived by now to Queue 0 (top priority)
            while proc_index < n and procs[proc_index].arrival_time <= current_time:
                queues[0].append(procs[proc_index])  # All newcomers start in Q0
                proc_index += 1

            # Find the highest-priority queue that has at least one process in it
            chosen_level = -1  # -1 means "all queues are empty"
            for level in range(num_levels):
                if queues[level]:       # This queue is not empty
                    chosen_level = level
                    break              # Stop at the first (highest priority) one

            if chosen_level == -1:
                # All queues empty — jump time to the next process arrival
                if proc_index < n:
                    current_time = procs[proc_index].arrival_time
                continue

            # Take the first process from the chosen queue
            p        = queues[chosen_level].pop(0)
            quantum  = quanta[chosen_level]         # This queue's time quantum
            run_time = min(quantum, p.remaining_time)  # Don't run past finish

            start = current_time
            end   = current_time + run_time
            timeline.append((p.pid, start, end))
            p.remaining_time -= run_time
            current_time      = end

            # Add new arrivals that showed up during this slice
            while proc_index < n and procs[proc_index].arrival_time <= current_time:
                queues[0].append(procs[proc_index])  # Always join at the top
                proc_index += 1

            if p.remaining_time > 0:
                # Used the full quantum → DEMOTE to next lower queue
                next_level = min(chosen_level + 1, num_levels - 1)
                queues[next_level].append(p)
            else:
                completed += 1  # Process fully finished

        return timeline


    # =========================================================================
    #  CALCULATE METRICS
    #  After the simulation, compute performance numbers for each process.
    #  Returns a dictionary: { "P1": {waiting, turnaround, ...}, "__summary__": {...} }
    # =========================================================================

    def calculate_metrics(self, processes, timeline):
        if not timeline or not processes:
            return {}

        # Step 1: Find FIRST start and LAST end for each PID in the timeline
        first_run = {}  # { pid: first_start_time }
        last_end  = {}  # { pid: last_end_time }
        for (pid, start, end) in timeline:
            if pid not in first_run:
                first_run[pid] = start  # First time this process ever ran
            last_end[pid] = end         # Always update to get the LAST end time

        # Step 2: Calculate metrics for each process
        metrics          = {}
        total_wait       = 0
        total_turnaround = 0
        total_response   = 0
        count            = len(processes)

        for p in processes:
            if p.pid not in last_end:
                continue

            finish     = last_end[p.pid]
            turnaround = finish - p.arrival_time          # Total time: arrival→finish
            waiting    = max(0, turnaround - p.burst_time)# Time NOT on CPU
            response   = max(0, first_run.get(p.pid, p.arrival_time) - p.arrival_time)

            metrics[p.pid] = {
                "arrival":    p.arrival_time,
                "burst":      p.burst_time,
                "priority":   p.priority,
                "finish":     finish,
                "turnaround": turnaround,
                "waiting":    waiting,
                "response":   response,
            }
            total_wait       += waiting
            total_turnaround += turnaround
            total_response   += response

        # Step 3: Overall summary statistics
        total_time = max(last_end.values()) if last_end else 1
        busy_time  = sum(end - start for (_, start, end) in timeline)
        cpu_util   = round((busy_time / total_time) * 100, 1)
        throughput = round(count / total_time, 3)

        # Store summary under a special key so the GUI can find it separately
        metrics["__summary__"] = {
            "avg_waiting":     round(total_wait / count, 2)       if count else 0,
            "avg_turnaround":  round(total_turnaround / count, 2) if count else 0,
            "avg_response":    round(total_response / count, 2)   if count else 0,
            "cpu_utilization": cpu_util,
            "throughput":      throughput,
        }
        return metrics


    # =========================================================================
    #  GET RECOMMENDATION — the "smart" part
    #  Analyses the current process list and suggests the best algorithm.
    # =========================================================================

    def get_recommendation(self, processes):
        if not processes:
            return "?", "Add some processes first."

        bursts          = [p.burst_time for p in processes]
        priorities      = [p.priority   for p in processes]
        avg_burst       = sum(bursts) / len(bursts)
        burst_range     = max(bursts) - min(bursts)
        priorities_used = (max(priorities) != min(priorities))  # Are priorities different?

        reasons    = []
        suggestion = ""

        # Logic tree — most specific condition first
        if len(processes) <= 2:
            suggestion = "FCFS"
            reasons.append("Very few processes — FCFS is the simplest and works fine here.")

        elif priorities_used:
            suggestion = "Priority (Preemptive)"
            reasons.append("Your processes have DIFFERENT priority values set.")
            reasons.append("Priority (Preemptive) ensures the most urgent process always runs first.")
            reasons.append("Built-in Aging prevents low-priority processes from waiting forever.")

        elif burst_range <= 2:
            suggestion = "Round Robin"
            reasons.append("All burst times are very close to each other.")
            reasons.append("Round Robin gives every process equal CPU time — perfectly fair here.")

        elif burst_range > avg_burst:
            suggestion = "SRTF (Preemptive SJF)"
            reasons.append("Burst times vary a LOT — some very short, some very long.")
            reasons.append("SRTF always runs whoever finishes soonest, minimising average wait.")

        elif len(processes) >= 5:
            suggestion = "MLFQ"
            reasons.append("Many processes with varied characteristics.")
            reasons.append("MLFQ adapts: short jobs get fast response, long jobs still get CPU time.")

        else:
            suggestion = "SJF (Non-Preemptive)"
            reasons.append("Moderate workload — SJF gives the best average waiting time here.")

        # Starvation risk warning
        if max(bursts) > 3 * avg_burst:
            reasons.append("")
            reasons.append("WARNING: One process has a VERY long burst time!")
            reasons.append("  Shorter processes may starve waiting for it to finish.")
            reasons.append("  Use Priority (Preemptive) with Aging or MLFQ to be safe.")

        return suggestion, "\n".join(reasons)


# =============================================================================
#  CLASS: GanttChart
#
#  This is a CUSTOM WIDGET that draws the coloured Gantt chart.
#  It extends tk.Canvas — a blank drawing surface.
#
#  We draw on it using:
#    create_rectangle(x1, y1, x2, y2, ...)  → coloured blocks
#    create_text(x, y, ...)                  → process labels inside blocks
#    create_line(x1, y1, x2, y2, ...)        → tick marks on the time axis
#
#  HOW ANIMATION WORKS:
#  The main app adds blocks ONE AT A TIME to self.timeline, then calls redraw().
#  Each call draws the chart up to the current block — creating a live effect.
# =============================================================================

class GanttChart(tk.Canvas):

    def __init__(self, parent, **kwargs):
        # Call the parent Canvas constructor, passing all extra options through
        super().__init__(parent, bg=BG_GANTT, **kwargs)

        self.timeline   = []  # List of (pid, start, end) to draw
        self.colors     = {}  # Maps each PID to its hex colour string
        self.total_time = 0   # The maximum time value — sets the chart's width

    def set_data(self, timeline, process_list):
        # Load a FULL timeline at once (used by "Show Instantly").
        self.timeline   = list(timeline)
        self.total_time = max((end for (_, _, end) in timeline), default=0)

        # Assign a unique colour to each process
        pids = list(dict.fromkeys(p.pid for p in process_list))  # Preserve order, no duplicates
        self.colors = {}
        for i, pid in enumerate(pids):
            self.colors[pid] = GANTT_COLORS[i % len(GANTT_COLORS)]

        self.redraw()

    def redraw(self):
        # Wipe everything on the canvas and redraw from scratch.
        # Called after each animation step and on window resize.
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
        label_y    = bar_top + bar_height + 18  # Y position for time labels
        padding    = 40    # Left/right gap so bars don't touch the edges

        # Scale: how many pixels per time unit?
        # If total_time=20 and usable width=800px → scale = 40px per unit
        scale = (w - padding * 2) / self.total_time if self.total_time > 0 else 1

        # Draw each block
        for (pid, start, end) in self.timeline:
            x1    = padding + start * scale   # Left edge pixel
            x2    = padding + end   * scale   # Right edge pixel
            color = self.colors.get(pid, "#95A5A6")  # Default grey if no colour assigned

            # Draw the filled rectangle
            self.create_rectangle(x1, bar_top, x2, bar_top + bar_height,
                                  fill=color, outline="white", width=2)

            # Draw the process name inside the block (only if wide enough to read)
            if (x2 - x1) > 22:
                self.create_text((x1 + x2) / 2, bar_top + bar_height / 2,
                                 text=pid, font=("Arial", 9, "bold"), fill="white")

# Draw time axis labels — every number from 0, 1, 2, 3 ...
        # Only skip numbers if the window is too narrow to fit them all
        min_gap = 18   # minimum pixels between labels before they overlap
        step = 1
        while scale * step < min_gap and step < self.total_time:
            step += 1

        for t in range(0, self.total_time + 1, step):
            x = padding + t * scale
            self.create_line(x, bar_top + bar_height,
                             x, bar_top + bar_height + 6,
                             fill=FG_GREY)
            self.create_text(x, label_y, text=str(t),
                             font=("Arial", 8), fill=FG_GREY)


# =============================================================================
#  HELPER FUNCTION: make_btn
#
#  Creates a styled flat button with consistent look.
#  Defined once so we don't repeat the same styling options 15 times.
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
#  CLASS: App  (the Main Application Window)
#
#  Inherits from tk.Tk — the root window of the entire application.
#  __init__ sets up all data and builds the GUI.
#
#  GUI layout (top → bottom):
#    ┌─────────────────────────────────────────────┐
#    │  HEADER BAR (title + university name)       │
#    ├────────────────────────┬────────────────────┤
#    │  Process Management    │  Simulation        │
#    │  (add/remove/table)    │  Controls          │
#    ├────────────────────────┴────────────────────┤
#    │  Gantt Chart (animated bar chart)           │
#    ├────────────────────────┬────────────────────┤
#    │  Performance Metrics   │  Adaptive Feedback │
#    │  (results table)       │  (recommendations) │
#    └────────────────────────┴────────────────────┘
# =============================================================================

class App(tk.Tk):

    def __init__(self):
        super().__init__()  # Create the actual window

        # ── Window setup ──────────────────────────────────────────────────────
        self.title("CPU Scheduling Simulator — Bahria University OS Project")
        self.configure(bg=BG_MAIN)
        self.geometry("1200x900")   # Taller window so bottom panels have more space
        self.minsize(1000, 820)     # User cannot shrink the window below this

        # ── Application data ──────────────────────────────────────────────────
        self.processes   = []         # List of all Process objects the user added
        self.timeline    = []         # Simulation output: [(pid, start, end), ...]
        self.scheduler   = Scheduler()# One Scheduler object, reused for every run

        self.pid_counter = 1          # Auto-increments for generated PIDs (P1, P2, ...)
        self.sim_index   = 0          # Which animation step are we on?
        self.sim_running = False      # True while animation is playing
        self.sim_paused  = False      # True when user has paused
        # Animation speed is fixed at 5x = 600 milliseconds between steps.
        # The speed slider has been removed — this constant controls the pace.
        # Lower number = faster, higher number = slower.
        self.sim_speed   = 600        # 600ms per animation step (5x speed)

        # ── Build the GUI ─────────────────────────────────────────────────────
        self._build_header()
        self._build_body()

    # ─── HEADER ───────────────────────────────────────────────────────────────

    def _build_header(self):
        # The dark navy bar across the very top of the window
        bar = tk.Frame(self, bg=BG_HEADER, pady=10)
        bar.pack(fill="x")  # Stretch horizontally to fill the full window width

        tk.Label(bar, text="CPU Scheduling Simulator",
                 bg=BG_HEADER, fg=FG_WHITE,
                 font=("Arial", 18, "bold")).pack(side="left", padx=20)

        tk.Label(bar, text="Operating System Project",
                 bg=BG_HEADER, fg="#A9C4E8",
                 font=("Arial", 11)).pack(side="right", padx=20)

    # ─── BODY ─────────────────────────────────────────────────────────────────

    def _build_body(self):
        # The main content area below the header
        body = tk.Frame(self, bg=BG_MAIN)
        body.pack(fill="both", expand=True, padx=12, pady=10)

        # TOP ROW: two panels side by side
        top = tk.Frame(body, bg=BG_MAIN)
        top.pack(fill="x", pady=(0, 8))
        self._build_process_panel(top)   # Left side
        self._build_controls_panel(top)  # Right side

        # MIDDLE: full-width Gantt chart
        self._build_gantt_panel(body)

        # BOTTOM ROW: two panels side by side
        bottom = tk.Frame(body, bg=BG_MAIN)
        bottom.pack(fill="both", expand=True, pady=(8, 0))
        self._build_metrics_panel(bottom)   # Left side
        self._build_feedback_panel(bottom)  # Right side

    # ─── PROCESS MANAGEMENT PANEL (top left) ──────────────────────────────────

    def _build_process_panel(self, parent):
        # LabelFrame = a Frame with a visible border and a title text
        frame = tk.LabelFrame(parent, text="  Process Management  ",
                              bg=BG_PANEL, fg=FG_BLUE, font=FONT_HEADING,
                              relief="solid", bd=1, padx=10, pady=8)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        # ── Input row: PID, Arrival, Burst, Priority, buttons ─────────────────
        # grid() places widgets in a table-like layout (row, column)
        inp = tk.Frame(frame, bg=BG_PANEL)
        inp.pack(fill="x", pady=(0, 6))

        # PID field — text entry linked to self.pid_var (a StringVar)
        # StringVar is a special tkinter variable; changing it updates the widget automatically
        tk.Label(inp, text="PID:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).grid(row=0, column=0, padx=(0,3))
        self.pid_var = tk.StringVar()
        tk.Entry(inp, textvariable=self.pid_var, font=FONT_NORMAL,
                 width=6, relief="solid", bd=1).grid(row=0, column=1, padx=(0,8))

        # Arrival Time — Spinbox allows up/down arrows to change the number
        tk.Label(inp, text="Arrival:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).grid(row=0, column=2, padx=(0,3))
        self.arrival_var = tk.IntVar(value=0)  # Default = 0
        tk.Spinbox(inp, from_=0, to=999, textvariable=self.arrival_var,
                   font=FONT_NORMAL, width=5, relief="solid", bd=1).grid(row=0, column=3, padx=(0,8))

        # Burst Time
        tk.Label(inp, text="Burst:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).grid(row=0, column=4, padx=(0,3))
        self.burst_var = tk.IntVar(value=4)  # Default = 4
        tk.Spinbox(inp, from_=1, to=999, textvariable=self.burst_var,
                   font=FONT_NORMAL, width=5, relief="solid", bd=1).grid(row=0, column=5, padx=(0,8))

        # Priority
        tk.Label(inp, text="Priority:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).grid(row=0, column=6, padx=(0,3))
        self.priority_var = tk.IntVar(value=1)  # Default = 1 (highest)
        tk.Spinbox(inp, from_=1, to=99, textvariable=self.priority_var,
                   font=FONT_NORMAL, width=4, relief="solid", bd=1).grid(row=0, column=7, padx=(0,8))

        # Action buttons
        make_btn(inp, "+ Add",   self._add_process,    BG_BTN_ADD).grid(row=0, column=8, padx=3)
        make_btn(inp, "Remove",  self._remove_process, BG_BTN_DEL, font=FONT_BTN_SM).grid(row=0, column=9,  padx=3)
        make_btn(inp, "Clear All", self._clear_all,    BG_BTN_DEL, font=FONT_BTN_SM).grid(row=0, column=10, padx=3)

        # Hint text below the input row
        tk.Label(frame,
                 text="Arrival = when it joins the queue   |   Burst = CPU time needed   |   Priority: 1 is highest",
                 bg=BG_PANEL, fg=FG_GREY, font=FONT_SMALL).pack(anchor="w", pady=(0, 4))

        # ── Process table ─────────────────────────────────────────────────────
        tbl_frame = tk.Frame(frame, bg=BG_PANEL)
        tbl_frame.pack(fill="both", expand=True)

        # Apply styling to the Treeview (table) widget
        style = ttk.Style()
        style.theme_use("clam")  # "clam" allows more colour customisation
        style.configure("Treeview", background=BG_PANEL, foreground=FG_DARK,
                        font=FONT_NORMAL, rowheight=26, fieldbackground=BG_PANEL)
        style.configure("Treeview.Heading", background=BG_HEADER, foreground=FG_WHITE,
                        font=FONT_HEADING, relief="flat")
        # The line below stops headings from turning white when the mouse hovers over them.
        # Without it, tkinter's default behaviour changes the heading background on hover.
        # We lock it to always stay navy (BG_HEADER) and white text no matter what.
        style.map("Treeview.Heading",
                  background=[("active", BG_HEADER)],   # stay navy when mouse is over it
                  foreground=[("active", FG_WHITE)])     # keep white text on hover
        style.map("Treeview", background=[("selected", "#D6E4FF")],
                  foreground=[("selected", FG_DARK)])

        cols = ("PID", "Arrival", "Burst", "Priority")
        self.proc_table = ttk.Treeview(tbl_frame, columns=cols, show="headings", height=5)
        for col in cols:
            self.proc_table.heading(col, text=col)
            self.proc_table.column(col, width=90, anchor="center")

        # Tags control the appearance of specific rows (alternating stripe colours)
        self.proc_table.tag_configure("odd",  background="#EBF5FB")  # Light blue
        self.proc_table.tag_configure("even", background=BG_PANEL)   # White

        sb = ttk.Scrollbar(tbl_frame, orient="vertical", command=self.proc_table.yview)
        self.proc_table.configure(yscrollcommand=sb.set)
        self.proc_table.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # ── Load Example buttons ──────────────────────────────────────────────
        ex_frame = tk.Frame(frame, bg=BG_PANEL)
        ex_frame.pack(fill="x", pady=(6, 0))
        tk.Label(ex_frame, text="Load Example:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).pack(side="left")
        for name in ["Classic 4-Process", "Starvation Demo", "Mixed Workload"]:
            # lambda n=name captures the current loop value — without this,
            # all buttons would use the LAST value of 'name'
            make_btn(ex_frame, name, lambda n=name: self._load_example(n),
                     BG_BTN_EX, font=FONT_BTN_SM, padx=10, pady=5).pack(side="left", padx=4)

    # ─── SIMULATION CONTROLS PANEL (top right) ────────────────────────────────

    def _build_controls_panel(self, parent):
        frame = tk.LabelFrame(parent, text="  Simulation Controls  ",
                              bg=BG_PANEL, fg=FG_BLUE, font=FONT_HEADING,
                              relief="solid", bd=1, padx=12, pady=8)
        frame.pack(side="right", fill="y", padx=(6, 0))

        # Algorithm dropdown
        # StringVar links the selected text to self.algo_var — read with .get()
        tk.Label(frame, text="Algorithm:", bg=BG_PANEL, fg=FG_DARK, font=FONT_NORMAL).grid(
            row=0, column=0, sticky="w", pady=4)
        self.algo_var = tk.StringVar(value="FCFS")
        algo_cb = ttk.Combobox(frame, textvariable=self.algo_var, font=FONT_NORMAL,
                               width=23, state="readonly",  # readonly = pick only, no typing
                               values=["FCFS", "SJF (Non-Preemptive)", "SRTF (Preemptive SJF)",
                                       "Priority (Non-Preemptive)", "Priority (Preemptive)",
                                       "Round Robin", "MLFQ"])
        algo_cb.grid(row=0, column=1, sticky="ew", pady=4, padx=(6, 0))
        # <<ComboboxSelected>> fires when the user picks a new item
        algo_cb.bind("<<ComboboxSelected>>", self._on_algo_change)

        # ── Time Quantum — only active for Round Robin ────────────────────────
        # This controls how many time units each process runs before being swapped out.
        # It is greyed out (disabled) for every algorithm except Round Robin.
        # Try different values to see how they affect the Gantt chart!
        tk.Label(frame, text="Time Quantum (Round Robin):", bg=BG_PANEL, fg=FG_DARK,
                 font=FONT_NORMAL).grid(row=1, column=0, sticky="w", pady=4)

        self.quantum_var  = tk.IntVar(value=DEFAULT_QUANTUM)  # Starts at 2
        self.quantum_spin = tk.Spinbox(frame, from_=1, to=20,
                                       textvariable=self.quantum_var,
                                       font=FONT_NORMAL, width=6,
                                       relief="solid", bd=1,
                                       state="disabled")  # Greyed out until RR is selected
        self.quantum_spin.grid(row=1, column=1, sticky="w", pady=4, padx=(6, 0))

        # Hint label explaining what the quantum does
        tk.Label(frame,
                 text="← Time units each process gets before switching (RR only)",
                 bg=BG_PANEL, fg=FG_GREY, font=("Arial", 9)).grid(
            row=2, column=0, columnspan=2, sticky="w", pady=(0, 4))

        # ── MLFQ Quanta — only active for MLFQ ───────────────────────────────
        # MLFQ has 3 priority queues. Each queue gives processes a different
        # amount of time before moving them to the next lower-priority queue.
        # Format: three numbers separated by commas, e.g.  2,4,8
        #   Queue 0 = 2 units  (highest priority — short burst, fast response)
        #   Queue 1 = 4 units  (medium priority)
        #   Queue 2 = 8 units  (lowest priority — for long CPU-heavy processes)
        tk.Label(frame, text="MLFQ Queue Quanta (Q0, Q1, Q2):", bg=BG_PANEL, fg=FG_DARK,
                 font=FONT_NORMAL).grid(row=3, column=0, sticky="w", pady=4)

        self.mlfq_var   = tk.StringVar(value="2,4,8")  # Default: 2, 4, 8
        self.mlfq_entry = tk.Entry(frame, textvariable=self.mlfq_var,
                                   font=FONT_NORMAL, width=10,
                                   relief="solid", bd=1,
                                   state="disabled")   # Greyed out until MLFQ is selected
        self.mlfq_entry.grid(row=3, column=1, sticky="w", pady=4, padx=(6, 0))

        # Hint label for MLFQ quanta
        tk.Label(frame,
                 text="← Three comma-separated quanta for each MLFQ queue (MLFQ only)",
                 bg=BG_PANEL, fg=FG_GREY, font=("Arial", 9)).grid(
            row=4, column=0, columnspan=2, sticky="w", pady=(0, 4))

        # ── NOTE: Animation speed is fixed at 5x (600ms per step) ────────────
        # The speed slider has been removed to keep the interface simple.
        # Speed is set here as a constant — 600 milliseconds between each step.
        # To change it, edit the number 600 in self.sim_speed below (in __init__).
        # (Lower number = faster animation, higher number = slower)

        # Thin horizontal separator line
        tk.Frame(frame, bg="#DEE2E6", height=1).grid(row=5, columnspan=2,
                                                      sticky="ew", pady=8)

        # ── Simulation action buttons ─────────────────────────────────────────
        # Row 1: Run + Pause
        r1 = tk.Frame(frame, bg=BG_PANEL)
        r1.grid(row=6, columnspan=2, pady=3)

        self.run_btn   = make_btn(r1, "Run Simulation", self._run_simulation, BG_BTN_RUN, padx=14)
        self.run_btn.pack(side="left", padx=4)

        self.pause_btn = make_btn(r1, "Pause", self._pause_resume, "#7F8C8D", padx=12)
        self.pause_btn.pack(side="left", padx=4)
        self.pause_btn.config(state="disabled")  # Can't pause before simulation starts

        # Row 2: Reset only  ("Show Instantly" has been removed)
        r2 = tk.Frame(frame, bg=BG_PANEL)
        r2.grid(row=7, columnspan=2, pady=3)
        make_btn(r2, "Reset", self._reset, BG_BTN_DEL, padx=14).pack(side="left", padx=4)

        # Analyze button — runs the intelligent recommendation engine
        make_btn(frame, "Analyze & Recommend", self._analyze_and_recommend,
                 "#16A085", padx=10, pady=8).grid(row=8, columnspan=2,
                                                   pady=(8, 0), sticky="ew")

        # Status variable still exists so other methods can call self.status_var.set(...)
        # without crashing, but no label is shown in the GUI — the green "Ready" text
        # has been removed as requested. Status updates still happen internally but
        # are not displayed visibly to the user.
        self.status_var = tk.StringVar(value="")

    # ─── GANTT CHART PANEL (middle) ───────────────────────────────────────────

    def _build_gantt_panel(self, parent):
        frame = tk.LabelFrame(parent, text="  Gantt Chart  ",
                              bg=BG_PANEL, fg=FG_BLUE, font=FONT_HEADING,
                              relief="solid", bd=1, padx=6, pady=6)
        frame.pack(fill="x")

        self.gantt = GanttChart(frame, height=90)  # Slightly shorter to give more room to bottom panels
        self.gantt.pack(fill="x", expand=True)
        # Redraw when the window is resized so the chart stays correctly scaled
        self.gantt.bind("<Configure>", lambda e: self.gantt.redraw())

    # ─── PERFORMANCE METRICS PANEL (bottom left) ──────────────────────────────

    def _build_metrics_panel(self, parent):
        frame = tk.LabelFrame(parent, text="  Performance Metrics  ",
                              bg=BG_PANEL, fg=FG_BLUE, font=FONT_HEADING,
                              relief="solid", bd=1, padx=8, pady=8)
        frame.pack(side="left", fill="both", expand=True, padx=(0, 6))

        cols = ("PID", "Arrival", "Burst", "Finish", "Turnaround", "Waiting", "Response")
        self.met_table = ttk.Treeview(frame, columns=cols, show="headings", height=10)
        widths = [60, 70, 60, 65, 100, 75, 80]
        for col, w in zip(cols, widths):
            self.met_table.heading(col, text=col)
            self.met_table.column(col, width=w, anchor="center")

        # This fixes the white hover bug on column headings in the metrics table.
        # tkinter's default makes headings turn white when you hover over them.
        # We lock heading colours to always stay navy + white text.
        style = ttk.Style()
        style.map("Treeview.Heading",
                  background=[("active", BG_HEADER)],  # Stay navy on hover
                  foreground=[("active", FG_WHITE)])    # Stay white text on hover

        self.met_table.tag_configure("odd",  background="#EBF5FB")
        self.met_table.tag_configure("even", background=BG_PANEL)

        sb = ttk.Scrollbar(frame, orient="vertical", command=self.met_table.yview)
        self.met_table.configure(yscrollcommand=sb.set)
        self.met_table.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        # Summary averages line shown below the table
        self.summary_var = tk.StringVar(value="Run a simulation to see metrics here.")
        tk.Label(frame, textvariable=self.summary_var, bg=BG_PANEL, fg="#1A5276",
                 font=FONT_SMALL, justify="left", wraplength=600).pack(anchor="w", pady=(6, 0))

    # ─── ADAPTIVE FEEDBACK PANEL (bottom right) ───────────────────────────────

    def _build_feedback_panel(self, parent):
        frame = tk.LabelFrame(parent, text="  Adaptive Feedback  ",
                              bg=BG_PANEL, fg=FG_BLUE, font=FONT_HEADING,
                              relief="solid", bd=1, padx=8, pady=8)
        frame.pack(side="right", fill="both", padx=(6, 0))

        # tk.Text is a multi-line text widget.
        # state="disabled" makes it read-only (user cannot type in it).
        # We must set state="normal" before inserting text, then "disabled" again.
        self.feedback_text = tk.Text(frame, font=FONT_SMALL, bg="#F8F9FA", fg=FG_DARK,
                                     relief="solid", bd=1, wrap="word",
                                     state="disabled", width=34)
        self.feedback_text.pack(fill="both", expand=True)

        # Tags in a Text widget work like CSS classes — style specific words/lines
        self.feedback_text.tag_configure("title",   font=("Arial",11,"bold"), foreground=FG_BLUE)
        self.feedback_text.tag_configure("suggest", font=("Arial",11,"bold"), foreground="#1E8449")
        self.feedback_text.tag_configure("warning", font=("Arial",10,"bold"), foreground="#E74C3C")
        self.feedback_text.tag_configure("normal",  font=("Arial",10),        foreground=FG_DARK)

        self._set_feedback("Add processes and click\nAnalyze & Recommend\nto get suggestions here.", "normal")

    # =========================================================================
    #  ACTION METHODS — called when buttons are clicked
    # =========================================================================

    def _add_process(self):
        # Get PID from the field, or auto-generate if blank
        pid = self.pid_var.get().strip()
        if not pid:
            pid = f"P{self.pid_counter}"  # f-string: embed variable in text

        # Reject duplicate PIDs
        if any(p.pid == pid for p in self.processes):
            messagebox.showwarning("Duplicate PID", f"A process named '{pid}' already exists!")
            return

        # Read numeric values from spinboxes
        try:
            arrival  = int(self.arrival_var.get())
            burst    = int(self.burst_var.get())
            priority = int(self.priority_var.get())
        except (ValueError, tk.TclError):
            messagebox.showerror("Input Error", "Please enter valid numbers for Arrival, Burst, and Priority.")
            return

        # Create the Process object and add it to our list
        p = Process(pid, arrival, burst, priority)
        self.processes.append(p)
        self.pid_counter += 1

        # Add a row to the visual table
        # Odd/even tags give alternating row stripe colours
        tag = "odd" if len(self.processes) % 2 == 1 else "even"
        self.proc_table.insert("", "end", values=(pid, arrival, burst, priority), tags=(tag,))

        self.pid_var.set("")  # Clear the PID field ready for next entry
        self.status_var.set(f"Added {pid}. Total: {len(self.processes)} processes.")

    def _remove_process(self):
        # selection() returns the IDs of selected rows in the table
        sel = self.proc_table.selection()
        if not sel:
            return
        pid = self.proc_table.item(sel[0], "values")[0]  # Get PID from first column
        self.proc_table.delete(sel[0])                    # Remove from visual table
        # Remove from data list using list comprehension filter
        self.processes = [p for p in self.processes if p.pid != pid]
        self.status_var.set(f"Removed {pid}.")

    def _clear_all(self):
        self.processes.clear()
        # delete(*...) deletes all children of the table widget
        self.proc_table.delete(*self.proc_table.get_children())
        self._reset()
        self.pid_counter = 1
        self.status_var.set("All cleared.")

    def _load_example(self, name):
        # Pre-built process sets for quick testing
        self._clear_all()

        if name == "Classic 4-Process":
            # Good for comparing FCFS vs SJF vs Round Robin
            data = [("P1",0,6,2), ("P2",1,4,1), ("P3",2,8,3), ("P4",3,3,2)]

        elif name == "Starvation Demo":
            # P1 has huge burst (20!) and low priority (3).
            # With Priority Non-Preemptive: P1 runs first (arrived first), blocks everyone.
            # Switch to Priority Preemptive to see aging kick in and rescue P2, P3.
            data = [("P1",0,20,3), ("P2",1,3,1), ("P3",2,4,1), ("P4",3,2,2), ("P5",4,5,3)]

        else:  # Mixed Workload
            # Great for testing MLFQ — varied burst times and priorities
            data = [("P1",0,2,1), ("P2",0,10,3), ("P3",1,3,2),
                    ("P4",2,7,1), ("P5",3,4,2), ("P6",5,1,1)]

        for pid, at, bt, pr in data:
            p = Process(pid, at, bt, pr)
            self.processes.append(p)
            tag = "odd" if len(self.processes) % 2 == 1 else "even"
            self.proc_table.insert("", "end", values=(pid,at,bt,pr), tags=(tag,))

        self.pid_counter = len(self.processes) + 1
        self.status_var.set(f"Loaded '{name}' — {len(self.processes)} processes ready.")
        self._analyze_and_recommend()  # Auto-suggest the best algorithm

    def _on_algo_change(self, event=None):
        # Called every time the user picks a different algorithm from the dropdown.
        # We enable or disable the quantum/MLFQ fields based on which algorithm is chosen.
        # Fields that don't apply to the selected algorithm are greyed out (state="disabled").
        algo = self.algo_var.get()

        # The Time Quantum spinner is ONLY relevant for Round Robin.
        # For FCFS, SJF, SRTF, Priority, and MLFQ it has no meaning, so we grey it out.
        self.quantum_spin.config(state="normal" if algo == "Round Robin" else "disabled")

        # The MLFQ Quanta entry is ONLY relevant for MLFQ.
        # For all other algorithms it is greyed out and cannot be edited.
        self.mlfq_entry.config(state="normal" if algo == "MLFQ" else "disabled")

    def _run_simulation(self):
        # Run the simulation with animation — Gantt blocks appear one by one.
        if not self.processes:
            messagebox.showinfo("No Processes", "Please add at least one process first!")
            return
        if self.sim_running:
            return  # Already running — ignore the click

        # Run the full algorithm and get the complete timeline at once.
        # We pass the quantum (for RR) and the MLFQ quanta (for MLFQ).
        # All other algorithms ignore these parameters.
        self.timeline = self.scheduler.run(
            self.algo_var.get(),
            self.processes,
            self.quantum_var.get(),   # Used by Round Robin only
            self._get_mlfq_quanta()   # Used by MLFQ only
        )

        if not self.timeline:
            messagebox.showwarning("No Output", "Simulation produced no output. Check your data.")
            return

        # Prepare the Gantt chart for animation (start empty)
        self.gantt.total_time = max(end for (_, _, end) in self.timeline)
        self.gantt.colors     = {p.pid: GANTT_COLORS[i % len(GANTT_COLORS)]
                                 for i, p in enumerate(self.processes)}
        self.gantt.timeline   = []  # Empty — blocks will be added step by step
        self.gantt.redraw()

        self.met_table.delete(*self.met_table.get_children())
        self.summary_var.set("Simulation running...")

        self.sim_index   = 0
        self.sim_running = True
        self.sim_paused  = False
        self.run_btn.config(state="disabled")
        self.pause_btn.config(state="normal", text="Pause")
        self.status_var.set(f"Running {self.algo_var.get()}...")

        self._sim_step()  # Start the animation loop

    def _sim_step(self):
        # Called repeatedly by tkinter's timer — adds ONE block per call.
        # self.after(ms, func) schedules the next call after 'ms' milliseconds.
        if self.sim_paused or not self.sim_running:
            return  # Do nothing if paused or stopped

        if self.sim_index >= len(self.timeline):
            # All blocks shown — simulation is complete
            self.sim_running = False
            self.run_btn.config(state="normal")
            self.pause_btn.config(state="disabled")
            self.status_var.set(f"Done!  {self.algo_var.get()} simulation complete.")
            self._show_metrics()
            return

        # Add the next block to the Gantt chart and redraw
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
        if self.sim_paused:
            self.sim_paused = False
            self.pause_btn.config(text="Pause")
            self.status_var.set("Resumed.")
            self._sim_step()  # Restart the animation loop from where it left off
        else:
            self.sim_paused = True
            self.pause_btn.config(text="Resume")
            self.status_var.set("Paused. Click Resume to continue.")

    def _reset(self):
        # Stop any running simulation and clear all visual outputs.
        # The process table is NOT cleared — processes stay for re-running.
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
        # Calculate all performance numbers from the timeline and fill the table
        if not self.timeline:
            return

        metrics = self.scheduler.calculate_metrics(self.processes, self.timeline)
        summary = metrics.pop("__summary__", {})  # Pull out the averages separately

        self.met_table.delete(*self.met_table.get_children())

        for i, (pid, m) in enumerate(metrics.items()):
            tag = "odd" if i % 2 == 0 else "even"
            self.met_table.insert("", "end", values=(
                pid, m["arrival"], m["burst"], m["finish"],
                m["turnaround"], m["waiting"], m["response"]
            ), tags=(tag,))

        if summary:
            self.summary_var.set(
                f"Avg Waiting: {summary['avg_waiting']}   |   "
                f"Avg Turnaround: {summary['avg_turnaround']}   |   "
                f"Avg Response: {summary['avg_response']}   |   "
                f"CPU Utilisation: {summary['cpu_utilization']}%   |   "
                f"Throughput: {summary['throughput']} proc/unit"
            )

    def _analyze_and_recommend(self):
        if not self.processes:
            self._set_feedback("Add processes first, then click Analyze.", "normal")
            return

        suggestion, reasons = self.scheduler.get_recommendation(self.processes)
        bursts = [p.burst_time for p in self.processes]

        # Enable the text widget, clear it, insert formatted text, then disable again
        self.feedback_text.config(state="normal")
        self.feedback_text.delete("1.0", "end")  # "1.0" = line 1, character 0

        # Insert sections with different tags for colour/bold styling
        self.feedback_text.insert("end", "RECOMMENDED ALGORITHM\n", "title")
        self.feedback_text.insert("end", f"  {suggestion}\n\n", "suggest")
        self.feedback_text.insert("end", "REASONS:\n", "title")
        for line in reasons.split("\n"):
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

    def _get_mlfq_quanta(self):
        # Parse the MLFQ quanta text field — the user types something like "2,4,8".
        # This converts that string into a Python list of integers: [2, 4, 8].
        # If the user typed something invalid (letters, wrong format, etc.),
        # we fall back silently to the safe default [2, 4, 8].
        try:
            return [int(x.strip()) for x in self.mlfq_var.get().split(",")]
        except (ValueError, AttributeError):
            return list(MLFQ_QUANTA_DEFAULT)  # Fall back to the global default

    def _set_feedback(self, text, tag="normal"):
        # Helper: quickly replace all feedback panel text with a single-style message
        self.feedback_text.config(state="normal")
        self.feedback_text.delete("1.0", "end")
        self.feedback_text.insert("end", text, tag)
        self.feedback_text.config(state="disabled")


# =============================================================================
#  ENTRY POINT
#
#  In Python, when you run a file directly, __name__ is set to "__main__".
#  When a file is imported by another file, __name__ is set to the module name.
#  This check ensures the app only starts when run directly, not when imported.
# =============================================================================

if __name__ == "__main__":
    app = App()      # Create the main window
    app.mainloop()   # Start the event loop — listens for clicks, keys, etc. forever