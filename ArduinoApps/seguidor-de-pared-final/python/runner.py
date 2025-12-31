import time

class RunPause:
    def __init__(self, run_seconds=3.0, pause_seconds=4.0):
        self.run_s = float(run_seconds)
        self.pause_s = float(pause_seconds)
        self._phase = "pause"
        self._t0 = time.time()

    def start(self):
        self._phase = "pause"
        self._t0 = time.time()

    def update(self):
        now = time.time()
        dt = now - self._t0

        if self._phase == "run" and dt >= self.run_s:
            self._phase = "pause"
            self._t0 = now
            return "to_pause"

        if self._phase == "pause" and dt >= self.pause_s:
            self._phase = "run"
            self._t0 = now
            return "to_run"

        return None

    @property
    def phase(self):
        return self._phase

    @property
    def time_left(self):
        now = time.time()
        dt = now - self._t0
        if self._phase == "run":
            return max(0.0, self.run_s - dt)
        return max(0.0, self.pause_s - dt)
