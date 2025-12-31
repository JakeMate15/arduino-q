class SweepTuner:
    def __init__(self, candidates):
        self.candidates = list(candidates)
        self.idx = 0
        self.params = self.candidates[0]
        self.finished = False
        self.results = []

        self._prev_e = None
        self._sum_abs_e = 0.0
        self._sum_abs_de = 0.0
        self._sat = 0
        self._n = 0
        self._bad = 0

    def start(self):
        self.idx = 0
        self.params = self.candidates[self.idx]
        self.finished = False
        self._reset_metrics()

    def _reset_metrics(self):
        self._prev_e = None
        self._sum_abs_e = 0.0
        self._sum_abs_de = 0.0
        self._sat = 0
        self._n = 0
        self._bad = 0

    def observe(self, mode, info, pwm_izq, pwm_der):
        if mode != "ok":
            self._bad += 1
            return

        dR_f, e, ajuste = info
        self._sum_abs_e += abs(e)
        if self._prev_e is not None:
            self._sum_abs_de += abs(e - self._prev_e)
        self._prev_e = e
        self._n += 1

        if pwm_izq <= 5 or pwm_izq >= 250 or pwm_der <= 5 or pwm_der >= 250:
            self._sat += 1

    def end_run(self):
        cost, mae, osc, sat, bad = self._score()
        self.results.append((self.params, cost, mae, osc, sat, bad))

        self.idx += 1
        if self.idx >= len(self.candidates):
            self.finished = True
            return

        self.params = self.candidates[self.idx]
        self._reset_metrics()

    def _score(self):
        if self._n == 0:
            return (1e9, 1e9, 1e9, 1.0, self._bad)
        mae = self._sum_abs_e / self._n
        osc = self._sum_abs_de / self._n
        sat = self._sat / self._n
        cost = mae + 0.6 * osc + 10.0 * sat + 50.0 * self._bad
        return (cost, mae, osc, sat, self._bad)

    def best(self):
        if not self.results:
            return None
        return min(self.results, key=lambda x: x[1])
