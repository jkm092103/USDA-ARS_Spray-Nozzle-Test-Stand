
class PIDController:
    def __init__(self, kp, ki, kd, out_min=5.0, out_max=75.0):
        self.kp = kp
        self.ki = ki
        self.kd = kd

        self.out_min = out_min
        self.out_max = out_max

        self.integral = 0.0
        self.prev_error = 0.0

    def reset(self):
        self.integral = 0.0
        self.prev_error = 0.0

    def update(self, setpoint, process_value, dt):

        error = setpoint - process_value #NOTE: This produces a positive error from the initial bounds, since we should be starting from 100% PWM.
        derivative = (error - self.prev_error) / dt
        self.integral += error * dt
        
        output = self.kp * error + self.ki * self.integral + self.kd * derivative
        output = max(self.out_min, min(self.out_max, output))

            
        print(f"Current Pressure: {process_value:.2f}, Current Error: {error:.2f}, Current Output: {output:.2f}")

        self.prev_error = error
        return output