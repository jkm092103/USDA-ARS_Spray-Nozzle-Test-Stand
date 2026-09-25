
class SensorScaling:
    
    @staticmethod
    def clamp(value, minimum, maximum):
        return max(minimum, min(maximum, value))
    @staticmethod
    def linear_scale(voltage, v_min, v_max, eng_min, eng_max):
        voltage = SensorScaling.clamp(voltage, v_min, v_max)
        return ((voltage - v_min) * (eng_max - eng_min) / (v_max - v_min)) + eng_min
    
    @staticmethod
    def voltage_to_pressure(voltage):
        return SensorScaling.linear_scale(voltage, 1.0, 5.0, 0.0, 200.0)
    
    @staticmethod
    def voltage_to_flow(voltage):
        return SensorScaling.linear_scale(voltage, 1.0, 5.0, 0.0, 6.6)
    
    @staticmethod
    def voltage_to_temp(voltage):
        return SensorScaling.linear_scale(voltage, 1.0, 5.0, -20.0, 80.0)