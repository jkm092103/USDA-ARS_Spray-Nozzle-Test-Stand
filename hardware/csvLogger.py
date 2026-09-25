import csv

class CSVLogger:

    def __init__(self, filepath):
        self.file = open(filepath, mode="w", newline="")

        self.writer = csv.writer(self.file)
        self.writer.writerow([ "ElapsedTime_s", "Pressure_psi", "Flow_gpm", "Temperature_C", "Target_psi", "Step"])

        self.file.flush()

    def log(self, elapsed, pressure, flow, temperature, target, step):
        self.writer.writerow([elapsed, pressure, flow, temperature, target, step])

        self.file.flush()

    def close(self):
        self.file.flush()
        self.file.close()