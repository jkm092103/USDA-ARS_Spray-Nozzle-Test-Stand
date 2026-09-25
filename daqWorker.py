import time
import nidaqmx
import numpy
from PyQt6.QtCore import QObject, pyqtSignal
from nidaqmx.constants import LineGrouping, AcquisitionType

from hardware.SensorScaling import SensorScaling
from hardware.csvLogger import CSVLogger

class DAQWorker(QObject):
    dataUpdated = pyqtSignal(
        float, #pressure
        float, #flow
        float, #temp
        float, #elapsedTime
        )
    
    finished = pyqtSignal()
    status = pyqtSignal(str)
    fault = pyqtSignal(str)
    currentTargetChanged = pyqtSignal(
        float, #target pressure
        int, #current step
        int, #total steps
    )
    
    def __init__(self, pressureSteps, save_path, holdTime = 5, tolerance = 2.25): 
        super().__init__()
        
        self.pressureSteps = pressureSteps
        self.save_path = save_path
        self.holdTime = holdTime
        self.tolerance = tolerance
        self.running = True
        
    def stop(self):
        self.running = False
        
    def run(self):
        self.status.emit("Initializing DAQ...")
        logger = CSVLogger(self.save_path)
        
        with nidaqmx.Task() as ai_task, nidaqmx.Task() as do_task:
            ai_task.ai_channels.add_ai_voltage_chan("Dev1/ai0") #Flow
            ai_task.ai_channels.add_ai_voltage_chan("Dev1/ai1") #Temperature
            ai_task.ai_channels.add_ai_voltage_chan("Dev1/ai2") #Pressure
            
            ai_task.timing.cfg_samp_clk_timing(rate = 100, sample_mode=AcquisitionType.CONTINUOUS, samps_per_chan=10)
            
            time.sleep(0.5) #Wait a bit before turning motor on...
            self.status.emit("Starting Motor...")
            
            do_task.do_channels.add_do_chan("Dev1/port0/line0", line_grouping=LineGrouping.CHAN_PER_LINE)
            do_task.write(True)
            
            time.sleep(2) #Wait a bit after motor is turned on to start recording data.
            self.status.emit("TEST_READY")
            print("Emitting 'TEST_READY'.")
            start_time = time.time()
            try:
                ai_task.start()
                for step, target in enumerate(self.pressureSteps):
                    print(f"\n=============\nBeginning Step {step+1}\nTarget = {target:.1f} psi.")
                    self.currentTargetChanged.emit(target, step + 1, len(self.pressureSteps))
                    self.status.emit(f"Adjust bleed valve to reach {target:.1f} psi")
                    
                    stableStart = time.time()
                    
                    collecting = False
                    stepComplete = False
                    FLOW_SETTLE_TIME = 2.5
                    PRESS_STABLE_TIME = 1.5
                    while self.running and (not stepComplete):
                        elapsed = time.time() - start_time
                        sensorVoltages = ai_task.read(number_of_samples_per_channel=10)
                        
                        flow = SensorScaling.voltage_to_flow(numpy.mean(sensorVoltages[0])) #Averaging those 10 samples, then converting to proper units using functions in SensorScaling.
                        temperature = SensorScaling.voltage_to_temp(numpy.mean(sensorVoltages[1]))
                        pressure = SensorScaling.voltage_to_pressure(numpy.mean(sensorVoltages[2]))
                        
                        if pressure > 150:
                            do_task.write(False)
                            self.fault.emit("Pressure exceeded 150 psi, program auto-quit.")
                            self.running = False
                            break
                        
                        self.dataUpdated.emit(
                                pressure,
                                flow,
                                temperature,
                                elapsed
                            )
                        
                        if abs(pressure-target) > self.tolerance:
                            stableStart = time.time()
                            
                        elif time.time() - stableStart >= PRESS_STABLE_TIME:
                            settleStart = time.time()
                            collecting = True
                            self.status.emit(f"Target reached. Stabilizing flow at {target:.1f} psi.")
                            loggingData = False
                            while self.running and collecting:
                                elapsed = time.time() - start_time
                                
                                sensorVoltages = ai_task.read(number_of_samples_per_channel=10)
                                
                                flow = SensorScaling.voltage_to_flow(numpy.mean(sensorVoltages[0])) #Averaging those 10 samples, then converting to proper units using functions in SensorScaling.
                                temperature = SensorScaling.voltage_to_temp(numpy.mean(sensorVoltages[1]))
                                pressure = SensorScaling.voltage_to_pressure(numpy.mean(sensorVoltages[2]))
                                
                                if abs(pressure - target) > self.tolerance:
                                    self.status.emit("Pressure drifted outside tolerance. Reacquiring target...")
                                    collecting = False
                                    stableStart = time.time()
                                    break
                                
                                if not loggingData:
                                    if time.time() - settleStart >= FLOW_SETTLE_TIME:
                                        loggingData = True
                                        holdStart = time.time()
                                
                                        self.status.emit(f"Flow stabilized. Collecting data at {target:.1f} psi.")
                                    else:
                                        continue
                                
                                if time.time() - holdStart >= self.holdTime:
                                    collecting = False
                                    stepComplete = True
                                    self.status.emit("Step Complete.")
                                    print(f"Finished Step {step+1}.")
                                    break
                    
                                logger.log(
                                    elapsed,
                                    pressure,
                                    flow,
                                    temperature,
                                    target,
                                    step + 1
                                )
                            
                                self.dataUpdated.emit(
                                    pressure,
                                    flow,
                                    temperature,
                                    elapsed
                                )
                        
            finally:
                ai_task.stop()
                do_task.write(False)
                    
                self.status.emit("Test complete.")
                logger.close()
                self.finished.emit()
                    