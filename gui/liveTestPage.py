from collections import deque
import pyqtgraph

from PyQt6.QtGui import QFont
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QGridLayout, QGroupBox, QStackedLayout

class LiveTestPage(QWidget):
    stopRequested = pyqtSignal()
    currentMaxFlow = 0.0
    def __init__(self):
        super().__init__()
        self.initUI()
        
    def initUI(self):
        self.pageStack = QStackedLayout()
        
        startupWidget = QWidget()
        startupLayout = QVBoxLayout(startupWidget)

        self.statusLabel = QLabel("Initializing Test Stand...")
        self.statusLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.statusLabel.setStyleSheet("""
            QLabel {
                font-size: 24px;
                font-weight: bold;
            }
        """)
        
        axisFont = QFont()
        axisFont.setPointSize(12)
        axisFont.setBold(True)

        startupLayout.addStretch()
        startupLayout.addWidget(self.statusLabel)
        startupLayout.addStretch()
        
        testWidget = QWidget()
        testLayout = QVBoxLayout(testWidget)
        
        self.currentTargetTitle = QLabel("CURRENT TARGET")
        self.currentTargetTitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.currentTargetTitle.setStyleSheet("font-size: 23px; font-weight: bold;")
        
        self.currentTargetLabel = QLabel("-- psi")
        self.currentTargetLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.currentTargetLabel.setStyleSheet("font-size: 20px; font-weight: bold; color: darkgreen;")
        
        self.stepLabel = QLabel("Step -- of --")
        self.stepLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.stepLabel.setStyleSheet("font-size: 15px; font-weight: bold; color: lightgray;")
        
        targetLayout = QVBoxLayout()

        targetLayout.addWidget(self.currentTargetTitle)
        targetLayout.addWidget(self.currentTargetLabel)
        targetLayout.addWidget(self.stepLabel)
        
        testLayout.addLayout(targetLayout)
        
        self.pressureLabel = QLabel("Pressure: -- PSI")
        self.pressureLabel.setStyleSheet("font-size: 21px; font-weight: bold;")
        self.flowLabel = QLabel("Flow: -- GPM")
        self.flowLabel.setStyleSheet("font-size: 21px; font-weight: bold;")
        self.tempLabel = QLabel("Temperature: -- °C")
        self.tempLabel.setStyleSheet("font-size: 18px; font-weight: bold;")
        self.elapsedLabel = QLabel("Elapsed Time: -- s")
        
        statusGroup = QGroupBox("Live Test Data")
        
        statusLayout = QGridLayout()
        
        statusLayout.addWidget(self.pressureLabel, 0, 0)
        statusLayout.addWidget(self.flowLabel, 0, 1)
        statusLayout.addWidget(self.tempLabel, 1, 0)
        statusLayout.addWidget(self.elapsedLabel, 2, 0)
        statusGroup.setLayout(statusLayout)
        testLayout.addWidget(statusGroup)
        
        self.pressurePlot = pyqtgraph.PlotWidget()
        self.pressurePlot.setYRange(0, 75)
        self.pressurePlot.setTitle("<span style='font-size:20pt; font-weight:bold;'>Pressure</span>")
        self.pressurePlot.setLabel("left", "Pressure", "PSI")
        self.pressurePlot.setLabel("bottom", "Time", "s")
        self.pressureCurve = (self.pressurePlot.plot(pen=pyqtgraph.mkPen("r", width = 3)))
        
        #self.pressureSetpointLine = (pyqtgraph.InfiniteLine(angle = 0, movable = False))
        self.pressureSP_Lines = []
        
        self.flowPlot = pyqtgraph.PlotWidget()
        self.flowPlot.setYRange(0, 0.5)
        self.flowPlot.setTitle("<span style='font-size:20pt; font-weight:bold;'>Flow</span>")
        self.flowPlot.setLabel("left", "Flow Rate", "GPM")
        self.flowPlot.setLabel("bottom", "Time", "s")
        self.flowCurve = (self.flowPlot.plot(pen=pyqtgraph.mkPen("b", width = 3)))
        
        for plot in [self.pressurePlot, self.flowPlot]:
            plot.getAxis("left").setTickFont(axisFont)
            plot.getAxis("bottom").setTickFont(axisFont)
        
        testLayout.setSpacing(15)
        
        testLayout.addWidget(self.pressurePlot)
        testLayout.addWidget(self.flowPlot)
        
        for plot in [self.pressurePlot, self.flowPlot]:
            plot.setBackground('w')
        
        self.stopButton = QPushButton("STOP TEST")
        self.stopButton.setStyleSheet("background-color: rgb(255, 0, 0); color: white;")
        self.stopButton.clicked.connect(self.stopRequested.emit)
        testLayout.addWidget(self.stopButton)
        
        self.pageStack.addWidget(startupWidget)
        self.pageStack.addWidget(testWidget)
        
        self.setLayout(self.pageStack)
        
        self.pageStack.setCurrentIndex(0)
        
        self.timeData = deque(maxlen=1000)
        self.pressureData = deque(maxlen=1000)
        self.flowData = deque(maxlen=1000)
    
    def setPressureSteps(self, pressureSteps):
        for pressure in pressureSteps:
            line = pyqtgraph.InfiniteLine(pos=pressure, angle=0, pen=pyqtgraph.mkPen("orange", width = 2, style=Qt.PenStyle.DashLine))
            self.pressurePlot.addItem(line)
            self.pressureSP_Lines.append(line)

    def updateStatus(self, message):
        print(f"Status Recieved: {message}")
        if message == "TEST_READY":
            self.pageStack.setCurrentIndex(1)
            return
    
        self.statusLabel.setText(message)
    
    def highlightStep(self, index):
        for i, line in enumerate(self.pressureSP_Lines):
            if i == index:
                line.setPen(pyqtgraph.mkPen('#FFA437', width=3))
            elif i < index:
                line.setPen(pyqtgraph.mkPen("green", width=2))
            else:
                line.setPen(pyqtgraph.mkPen((150,150,150), width=1, style=Qt.PenStyle.DashLine))
    
    def updateCurrentTarget(self, targetPressure, stepNumber, totalSteps):
        self.currentTargetLabel.setText(f"{targetPressure:.1f} psi")
        self.stepLabel.setText(
            f"Step {stepNumber} of {totalSteps}"
        )
        self.highlightStep(stepNumber - 1)
    
    def updateLiveData(self, pressure, flow, temperature, elapsed):
        self.timeData.append(elapsed)
        self.pressureData.append(pressure)
        self.flowData.append(flow)
        
        if flow > self.currentMaxFlow:
            self.currentMaxFlow = flow
            self.flowPlot.setYRange(0, self.currentMaxFlow + 0.5)
        
        
        self.pressureLabel.setText(f"Pressure: {pressure:.1f} PSI")
        self.flowLabel.setText(f"Flow: {flow:.2f} GPM")
        self.tempLabel.setText(f"Temperature: {temperature:.1f} °C")
        self.elapsedLabel.setText(f"Elapsed Time: {elapsed:.1f} s")
        
        self.pressureCurve.setData(list(self.timeData), list(self.pressureData))

        self.flowCurve.setData(list(self.timeData), list(self.flowData))
        
    def resetData(self):
        self.timeData.clear()
        self.pressureData.clear()
        self.flowData.clear()
        
        for line in self.pressureSP_Lines:
            self.pressurePlot.removeItem(line) 
        self.pressureSP_Lines.clear()
    
        self.pressureCurve.clear()
        self.flowCurve.clear()
        
        self.flowPlot.setYRange(0, 0.5)
        self.pressurePlot.setYRange(0, 50)
        
        self.pageStack.setCurrentIndex(0)
        
    