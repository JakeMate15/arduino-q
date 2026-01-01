class WallFollowerP:
    def __init__(self, setpoint_derecha=15.0, distancia_obstaculo=20.0, sin_pared_umbral=300.0, filtro_alpha=0.7):
        self.setpoint = float(setpoint_derecha)
        self.obst = float(distancia_obstaculo)
        self.sin_pared = float(sin_pared_umbral)
        self.alpha = float(filtro_alpha)
        self.dR_f = None
        self.prev_error = None

    @staticmethod
    def clip(x, lo, hi):
        return max(lo, min(hi, x))

    def reset(self):
        self.dR_f = None
        self.prev_error = None

    def step(self, dC, dR, params):
        base = int(params["base"])
        kp = float(params["kp"])
        kd = float(params.get("kd", 0.0))
        corr_max = int(params["corr_max"])
        zona = float(params["zona_muerta"])

        obst_izq = int(params.get("obst_izq", -80))
        obst_der = int(params.get("obst_der", 80))
        busc_izq = int(params.get("busc_izq", 140))
        busc_der = int(params.get("busc_der", 80))

        if dC <= self.obst:
            return obst_izq, obst_der, "obst", None

        if dR >= self.sin_pared:
            self.prev_error = None 
            return busc_izq, busc_der, "buscar", None

        if self.dR_f is None:
            self.dR_f = dR
        self.dR_f = self.alpha * self.dR_f + (1.0 - self.alpha) * dR

        error = self.dR_f - self.setpoint
        
        if self.prev_error is None:
            self.prev_error = error
        
        derivative = error - self.prev_error
        self.prev_error = error

        if abs(error) <= zona:
            ajuste = 0
        else:
            ajuste = int(kp * error + kd * derivative)
            ajuste = self.clip(ajuste, -corr_max, corr_max)

        pwm_izq = int(self.clip(base + ajuste, 0, 255))
        pwm_der = int(self.clip(base - ajuste, 0, 255))

        return pwm_izq, pwm_der, "ok", (self.dR_f, error, derivative, ajuste)