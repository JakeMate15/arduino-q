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
        if mode != "ok" or info is None: # Añadimos protección contra None
            self._bad += 1
            return

        # CAMBIO: Ahora desempacamos 4 valores (añadimos _ para ignorar la derivada aquí)
        dR_f, e, derivative, ajuste = info 
        
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
        
        mae = self._sum_abs_e / self._n      # Error promedio (Precisión)
        osc = self._sum_abs_de / self._n     # Cambio de error (Estabilidad)
        sat = self._sat / self._n            # % de tiempo en motores al máximo
        bad = self._bad                      # Veces que perdió la pared o chocó
        
        cost = mae + 2.0 * osc + 10.0 * sat + 50.0 * bad
        return (cost, mae, osc, sat, bad)

    def best(self):
        if not self.results:
            return None
        return min(self.results, key=lambda x: x[1])

class TwiddleTuner:
    def __init__(self, base_params, keys=("kp", "kd", "corr_max"), deltas=(0.5, 2.0, 10.0), tol=0.05, reps=2, bounds=None):
        self.params = dict(base_params)
        self.best_params = dict(self.params)
        self.base_params = dict(base_params)
        self.keys = list(keys)
        self.deltas = [float(d) for d in deltas]
        self.tol = float(tol)
        self.reps = int(reps)
        self.bounds = bounds or {}
        self.best_cost = float("inf")
        self.i, self.phase, self.sign = 0, 0, +1
        self._rep_count, self._rep_cost_sum = 0, 0.0
        self.finished = False
        self.history = []
        self._reset_metrics()

    def _reset_metrics(self):
        self._prev_e = None
        self._sum_abs_e = 0.0
        self._sum_abs_de = 0.0
        self._sat, self._n, self._bad = 0, 0, 0

    def start(self):
        self.best_cost = float("inf")
        self.finished = False
        self._reset_metrics()

    def observe(self, mode, info, pwm_izq, pwm_der):
        if mode != "ok" or info is None:
            self._bad += 1
            return

        dR_f, e, derivative, ajuste = info
        
        self._sum_abs_e += abs(e)
        if self._prev_e is not None:
            self._sum_abs_de += abs(e - self._prev_e)
        self._prev_e = e
        self._n += 1

        if pwm_izq <= 5 or pwm_izq >= 250 or pwm_der <= 5 or pwm_der >= 250:
            self._sat += 1

    def _score(self):
        if self._n == 0: return (1e9, 1e9, 1e9, 1.0, self._bad)
        mae = self._sum_abs_e / self._n
        osc = self._sum_abs_de / self._n
        sat = self._sat / self._n
        bad = self._bad
        cost = mae + 3.0 * osc + 10.0 * sat + 100.0 * bad
        return (cost, mae, osc, sat, bad)

    def _apply_bounds(self, k):
        if k in self.bounds:
            lo, hi = self.bounds[k]
            self.params[k] = max(lo, min(hi, float(self.params[k])))

    def _tweak(self, k, amount):
        self.params[k] = float(self.params[k]) + float(amount)
        self._apply_bounds(k)

    def _sum_deltas(self):
        return sum(self.deltas)

    def end_run(self):
        cost, mae, osc, sat, bad = self._score()
        self._rep_cost_sum += cost
        self._rep_count += 1
        self.history.append((dict(self.params), cost, mae, osc, sat, bad))
        self._reset_metrics()

        if self._rep_count < self.reps: return "repeat"

        avg_cost = self._rep_cost_sum / self.reps
        self._rep_cost_sum, self._rep_count = 0.0, 0

        if self._sum_deltas() < self.tol:
            self.finished = True
            return "done"

        k, d = self.keys[self.i], self.deltas[self.i]

        if self.best_cost == float("inf"):
            self.best_cost, self.best_params = avg_cost, dict(self.params)
            self._tweak(k, +d)
            return "next"

        if self.phase == 0:
            if avg_cost < self.best_cost:
                self.best_cost, self.best_params = avg_cost, dict(self.params)
                self.deltas[self.i] *= 1.1
                self._advance_key()
            else:
                self._tweak(k, -2 * d)
                self.phase = 1
            return "next"

        if self.phase == 1:
            if avg_cost < self.best_cost:
                self.best_cost, self.best_params = avg_cost, dict(self.params)
                self.deltas[self.i] *= 1.1
            else:
                self._tweak(k, +d)
                self.deltas[self.i] *= 0.9
            self._advance_key()
            return "next"

    def _advance_key(self):
        self.phase = 0
        self.i = (self.i + 1) % len(self.keys)
        self._tweak(self.keys[self.i], self.deltas[self.i])

    def best(self):
        return dict(self.best_params), self.best_cost

