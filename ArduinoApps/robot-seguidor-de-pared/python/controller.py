class WallFollowerP:
    def __init__(
        self,
        setpoint_derecha=15.0,
        kp=1.5,
        velocidad_base=100,
        distancia_obstaculo=15.0,
        corr_max=40,
        sin_pared_umbral=300.0,
        zona_muerta=1.0,
        filtro_alpha=0.7,
    ):
        self.setpoint = float(setpoint_derecha)
        self.kp = float(kp)
        self.base = int(velocidad_base)
        self.obst = float(distancia_obstaculo)
        self.corr_max = int(corr_max)
        self.sin_pared = float(sin_pared_umbral)
        self.zona = float(zona_muerta)
        self.alpha = float(filtro_alpha)

        self.dR_f = None

    @staticmethod
    def clip(x, lo, hi):
        return max(lo, min(hi, x))

    def step(self, dC, dR):
        if dC <= self.obst:
            return -80, 80, "obst"

        if dR >= self.sin_pared:
            return 140, 80, "buscar"

        if self.dR_f is None:
            self.dR_f = dR
        self.dR_f = self.alpha * self.dR_f + (1.0 - self.alpha) * dR

        error = self.dR_f - self.setpoint

        if abs(error) <= self.zona:
            ajuste = 0
        else:
            ajuste = int(self.kp * error)
            ajuste = self.clip(ajuste, -self.corr_max, self.corr_max)

        pwm_izq = int(self.clip(self.base + ajuste, 0, 255))
        pwm_der = int(self.clip(self.base - ajuste, 0, 255))

        return pwm_izq, pwm_der, (self.dR_f, error, ajuste)
