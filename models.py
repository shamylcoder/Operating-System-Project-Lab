# =============================================================================
#  MODULE: models.py
#
#  Defines the Process data class used throughout the simulator.
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
