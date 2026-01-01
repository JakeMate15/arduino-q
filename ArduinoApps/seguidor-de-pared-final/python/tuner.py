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
        bad = self._bad
        cost = mae + 1.5 * osc + 10.0 * sat + 50.0 * bad
        return (cost, mae, osc, sat, bad)

    def best(self):
        if not self.results:
            return None
        return min(self.results, key=lambda x: x[1])

class TwiddleTuner:
    def __init__(self, base_params, keys=("kp", "corr_max"), deltas=(0.5, 10.0), tol=0.05, reps=2, bounds=None):
        self.params = dict(base_params)
        self.best_params = dict(self.params)
        self.base_params = dict(base_params)

        self.last_avg_cost = None

        self.keys = list(keys)
        self.deltas = [float(d) for d in deltas]
        self.tol = float(tol)
        self.reps = int(reps)
        self.bounds = bounds or {}

        self.best_cost = float("inf")

        self.i = 0
        self.phase = 0
        self.sign = +1

        self._rep_count = 0
        self._rep_cost_sum = 0.0

        self.finished = False
        self.history = []

        self._prev_e = None
        self._sum_abs_e = 0.0
        self._sum_abs_de = 0.0
        self._sat = 0
        self._n = 0
        self._bad = 0

    def start(self):
        self.params = dict(self.base_params)
        self.best_params = dict(self.params)
        self.last_avg_cost = None

        self.finished = False
        self.i = 0
        self.phase = 0
        self.sign = +1
        self.best_cost = float("inf")
        self._rep_count = 0
        self._rep_cost_sum = 0.0
        self.history.clear()
        self._reset_metrics()

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

    def _score(self):
        if self._n == 0:
            mae = 1e9
            osc = 1e9
            sat = 1.0
            bad = self._bad
            cost = 1e9 + 50.0 * bad
            return (cost, mae, osc, sat, bad)

        mae = self._sum_abs_e / self._n
        osc = self._sum_abs_de / self._n
        sat = self._sat / self._n
        bad = self._bad
        cost = mae + 0.6 * osc + 10.0 * sat + 50.0 * bad
        return (cost, mae, osc, sat, bad)

    def _apply_bounds(self, k):
        if k in self.bounds:
            lo, hi = self.bounds[k]
            v = float(self.params[k])
            if v < lo: v = lo
            if v > hi: v = hi
            self.params[k] = v

    def _tweak(self, k, amount):
        self.params[k] = float(self.params[k]) + float(amount)
        self._apply_bounds(k)

    def _sum_deltas(self):
        return sum(self.deltas)

    def end_run(self):
        cost, mae, osc, sat, bad = self._score()

        # repetir (promediar) para que no dependa de una sola corrida
        self._rep_cost_sum += cost
        self._rep_count += 1

        # guardar por si quieres ver el run a run
        self.history.append((dict(self.params), cost, mae, osc, sat, bad))

        # reinicia métricas para el siguiente RUN (misma config o siguiente)
        self._reset_metrics()

        if self._rep_count < self.reps:
            return "repeat"  # repetir mismo params otra vez

        avg_cost = self._rep_cost_sum / self.reps
        self.last_avg_cost = avg_cost
        self._rep_cost_sum = 0.0
        self._rep_count = 0

        # criterio de parada
        if self._sum_deltas() < self.tol:
            self.finished = True
            return "done"

        k = self.keys[self.i]
        d = self.deltas[self.i]

        if self.best_cost == float("inf"):
            # primera evaluación: define best y luego intenta +d
            self.best_cost = avg_cost
            self.best_params = dict(self.params)
            self.sign = +1
            self._tweak(k, +d)
            self.phase = 0
            return "next"

        if self.phase == 0:
            # acabamos de evaluar params con +d
            if avg_cost < self.best_cost:
                self.best_cost = avg_cost
                self.best_params = dict(self.params)
                self.deltas[self.i] *= 1.1
                self._advance_key()
            else:
                # probar -2d (desde +d bajar 2d)
                self._tweak(k, -2 * d)
                self.phase = 1
            return "next"

        if self.phase == 1:
            # acabamos de evaluar params con -d
            if avg_cost < self.best_cost:
                self.best_cost = avg_cost
                self.best_params = dict(self.params)
                self.deltas[self.i] *= 1.1
            else:
                # volver al valor original (sumar d) y reducir delta
                self._tweak(k, +d)
                self.deltas[self.i] *= 0.9
            self._advance_key()
            return "next"

        return "next"

    def _advance_key(self):
        self.phase = 0
        self.i = (self.i + 1) % len(self.keys)
        k = self.keys[self.i]
        d = self.deltas[self.i]
        self._tweak(k, +d)

    def best(self):
        return dict(self.best_params), self.best_cost

