# =============================================================================
#  MODULE: scheduler.py
#
#  Contains the Scheduler class — ALL scheduling logic in one place.
#  This module has absolutely NO GUI code: pure Python logic only.

#  PUBLIC INTERFACE — what the GUI needs to call:
#    scheduler.run(algorithm, processes, time_quantum, mlfq_quanta)
#        → Returns a timeline: [(pid, start, end), ...]
#
#    scheduler.calculate_metrics(processes, timeline)
#        → Returns per-process stats plus averages
#
#    scheduler.get_recommendation(processes)
#        → Returns (suggested_algorithm, reason_text)
#
#  TIMELINE FORMAT:
#    A list of tuples like [("P1", 0, 6), ("P2", 6, 10), ...]
#    meaning P1 ran from time 0→6, P2 from 6→10, etc.
#    Used by GanttChart (drawing) and calculate_metrics (stats).
# =============================================================================

import copy  # For duplicating process lists safely (deepcopy)

from constants import MLFQ_QUANTA_DEFAULT  # Default MLFQ queue quanta [2, 4, 8]


# =============================================================================
#  CLASS: Scheduler
# =============================================================================

class Scheduler:

    # ─────────────────────────────────────────────────────────────────────────
    def run(self, algorithm, processes, time_quantum=2, mlfq_quanta=None):
        # This is the ENTRY POINT — the only method the GUI needs to call
        # to start a scheduling simulation.
        #
        # Parameters:
        #   algorithm    → the name string e.g. "FCFS", "Round Robin", "MLFQ"
        #   processes    → list of Process objects the user has added
        #   time_quantum → for Round Robin only — how long each process runs per turn
        #   mlfq_quanta  → for MLFQ only — list like [2, 4, 8] for the 3 queue levels
        #
# copy.deepcopy()?
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
    # Fixed quanta: [2, 4, 8] — defined in constants.py.
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
            quantum  = quanta[chosen_level]            # This queue's time quantum
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
            turnaround = finish - p.arrival_time           # Total time: arrival→finish
            waiting    = max(0, turnaround - p.burst_time) # Time NOT on CPU
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
