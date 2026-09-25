import os
import nidaqmx
import numpy
from nidaqmx.system import System
from PyQt6.QtWidgets import QWidget, QLabel, QLineEdit, QPushButton, QVBoxLayout, QFormLayout, QStackedWidget, QMessageBox, QFileDialog, QGraphicsOpacityEffect
from PyQt6.QtCore import Qt, QPropertyAnimation, QSequentialAnimationGroup, QPauseAnimation, QThread
from PyQt6.QtGui import QFont, QPixmap
from daqWorker import DAQWorker
from gui.liveTestPage import LiveTestPage
from gui.TestResultsPage import TestResultsPage

class userInputApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Flow Rate Test App")
        self.setStyleSheet("background-color: white;")
        self.liveTestPage = LiveTestPage()
        self.resultsPage = TestResultsPage()
        self.resultsPage.newTestRequested.connect(self.returnToInputPage)
        
        self.initUI()
        
    def initUI(self):
        self.resize(600, 400)
        self.raise_()
        self.activateWindow()
        self.centerOnScreen()
        
        self.stack = QStackedWidget()
        
        self.createSplashPage()
        self.createInputPage()
        self.stack.addWidget(self.liveTestPage)
        self.stack.addWidget(self.resultsPage)
        
        mainLayout = QVBoxLayout()
        mainLayout.addWidget(self.stack)
        
        self.setLayout(mainLayout)
        self.startSplashAnimation()
        
    def centerOnScreen(self):
        windowFrame = self.frameGeometry()
        screenCenter = self.screen().availableGeometry().center()
        windowFrame.moveCenter(screenCenter)
        self.move(windowFrame.topLeft())
        
    def createSplashPage(self):
        
        self.splashPage = QWidget()
        
        layout = QVBoxLayout()
        layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.logos = QLabel()

        pixmap = QPixmap("flowTechUSDAlogos.png")
        pixmap = pixmap.scaled(300, 150,Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        
        self.logos.setPixmap(pixmap)
        self.logos.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        self.intro = QLabel("Flow Rate Test Stand Application")
        self.intro.setFont(QFont("Yu Gothic", 18, QFont.Weight.Bold))
        
        layout.addWidget(self.logos)
        layout.addWidget(self.intro)
        
        self.splashPage.setLayout(layout)
        
        self.stack.addWidget(self.splashPage)
        
    def startSplashAnimation(self):
        opacity = QGraphicsOpacityEffect()
        self.logos.setGraphicsEffect(opacity)
        
        self.fadeIn = QPropertyAnimation(opacity, b"opacity")
        
        self.fadeIn.setDuration(2000)
        self.fadeIn.setStartValue(0.0)
        self.fadeIn.setEndValue(1.0)
        
        self.pause = QPauseAnimation(1000)
        
        self.fadeOut = QPropertyAnimation(opacity, b"opacity")
        
        self.fadeOut.setDuration(2000)
        self.fadeOut.setStartValue(1.0)
        self.fadeOut.setEndValue(0.0)
        
        self.sequence = QSequentialAnimationGroup()
        
        self.sequence.addAnimation(self.fadeIn)
        self.sequence.addAnimation(self.pause)
        self.sequence.addAnimation(self.fadeOut)
        
        self.sequence.finished.connect(self.showInputScreen)
        
        self.sequence.start()
        
    def showInputScreen(self):
        self.stack.setCurrentWidget(self.inputPage)
        
        
    def createInputPage(self):
        self.inputPage = QWidget()
        
        formLayout = QFormLayout()
        
        self.lowPressInput = QLineEdit()
        self.lowPressInput.setPlaceholderText("Enter lowest pressure setpoint (psig)")
        self.highPressInput = QLineEdit()
        self.highPressInput.setPlaceholderText("Enter highest pressure setpoint (psig)")
        self.incrementInput = QLineEdit()
        self.incrementInput.setPlaceholderText("Enter pressure setpoint increment (psig)")
        
        self.pressureSteps = []

        self.pressureInput = QLineEdit()
        self.pressureInput.setPlaceholderText("Enter pressure setpoint (psi)")
        
        self.filenameInput = QLineEdit()
        self.filenameInput.setPlaceholderText("test01.csv")
        
        self.directoryLabel = QLabel("No folder selected")
        
        self.browseButton = QPushButton("Select Save Location")
        self.browseButton.clicked.connect(self.selectDirectory)
        
        labelFont = QFont()
        labelFont.setPointSize(14)
        labelFont.setWeight(QFont.Weight.DemiBold)
        labelFont.setFamily("Yu Gothic")
        
        lowLabel = QLabel("Lowest Pressure Setpoint: ")
        highLabel = QLabel("Highest Pressure Setpoint: ")
        incLabel = QLabel("Pressure Setpoint Increment: ")
        fileLabel = QLabel("Output Filename: ")
        saveLabel = QLabel("Save Folder: ")
        
        for label in [lowLabel, highLabel, incLabel, fileLabel, saveLabel]:
            label.setFont(labelFont)
        
        formLayout.addRow(lowLabel, self.lowPressInput)
        formLayout.addRow(highLabel, self.highPressInput)
        formLayout.addRow(incLabel, self.incrementInput)
        formLayout.addRow(fileLabel , self.filenameInput)
        formLayout.addRow(saveLabel , self.directoryLabel)
        
        layout = QVBoxLayout()
        layout.addLayout(formLayout)
        
        layout.addWidget(self.browseButton)
        
        self.startButton = QPushButton("Begin Test")
        
        self.startButton.clicked.connect(self.validateInput)
        
        layout.addWidget(self.startButton)
        
        self.inputPage.setLayout(layout)
        
        self.stack.addWidget(self.inputPage)
        
    def selectDirectory(self):

        folder = QFileDialog.getExistingDirectory(self, "Select Output Folder")
    
        if folder:
            self.outputDirectory = folder
            self.directoryLabel.setText(folder)
            
    def validateInput(self):
        try:
            self.lowPress = float(self.lowPressInput.text())
            self.highPress = float(self.highPressInput.text())
            self.increment = float(self.incrementInput.text())
            
        except ValueError:
            QMessageBox.critical(self, "Input Error", "Pressure(s) must be numeric!")
            return
        
        filename = self.filenameInput.text().strip()
        if filename == "":
            QMessageBox.critical(self, "Input Error", "Please enter a filename.")
            return
        
        if not hasattr(self, "outputDirectory"):
            QMessageBox().critical(self, "Input Error", "Please select a save location on your PC.")
            return
        
        if self.lowPress > self.highPress:
            QMessageBox().critical(self, "Pressure Input Error", "Lowest pressure setpoint must be greater than highest pressure setpoint.")
            return
        
        for press in [self.lowPress, self.highPress, self.increment]:
            if press < 0 or press > 100:
                QMessageBox().critical(self, "Pressure Setpoint Error", "Pressure(s) must be between 0 and 100 psi.")
                return
        
        if self.increment > (self.highPress - self.lowPress):
            reply = QMessageBox.warning(self, "Large Increment Warning", "Set increment is greater than the difference between low and high pressures. Would you only like to test the high and low setpoints?")
            if reply == QMessageBox.StandardButton.No:
                return
            if reply == QMessageBox.StandardButton.Yes:
                self.increment = self.lowPress - self.highPress
        
        if self.lowPress < 15:
            reply = QMessageBox.warning(self, "Low Pressure Warning", "The setpoint(s) you would like to test at are below 15 psi.\n\nContinue?", QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.No:
                return
        
        elif self.highPress > 80:
            reply = QMessageBox.warning(self, "High Pressure Warning", "The setpoint(s) you would like to test at are above 80 psi.\n\nContinue?", QMessageBox.StandardButton.No | QMessageBox.StandardButton.Yes)
            if reply == QMessageBox.StandardButton.No:
                return
        
        self.beginTest()
        
    def showFault(self, message):

        faultBox = QMessageBox(self)
        
        faultBox.setIcon(QMessageBox.Icon.Critical)

        faultBox.setWindowTitle("Emergency Shutdown")

        faultBox.setText("Test aborted.")

        faultBox.setInformativeText(message)

        faultBox.exec()
    
    def checkDAQConnected(self):
        try:
            system = System.local()
            
            devices = list(system.devices)
            if len(devices) == 0:
                return False
            
            print("Detected NI Devices:")
            for device in devices:
                print(device.name)
                
            return True
        
        except Exception as e:
            print(f"DAQ detection error: {e}")
            return False
    
    def updateStatus(self, message):
        self.statusLabel.setText(message)
    
    def beginTest(self):
        #if not self.checkDAQConnected():
           # QMessageBox.critical(self, "DAQ Not Found", "No NI-DAQmx hardware was detected.\n\nPlease plug in the test stand and try again.")
           # return
        
        filename = self.filenameInput.text()
        if not filename.endswith(".csv"):
            filename += ".csv"
            
        self.savePath = os.path.join(self.outputDirectory, filename)
        
        print("Saving to:")
        print(self.savePath)
        
        print("Pressure Steps: [", end="")
        for i in numpy.arange(self.lowPress, self.highPress, self.increment):
            self.pressureSteps.append(i)
            print(str(i) + ", ", end="")
        self.pressureSteps.append(self.highPress)
        print(str(self.highPress) + "]")

        
        self.thread = QThread()
        self.worker = DAQWorker(self.pressureSteps, self.savePath)
        self.worker.moveToThread(self.thread)
        
        self.thread.started.connect(self.worker.run)
        
        self.worker.finished.connect(self.thread.quit)
        self.worker.finished.connect(self.thread.deleteLater)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker.finished.connect(self.testFinished)
        self.worker.finished.connect(lambda: print("FINISHED SIGNAL RECIEVED"))
        
        self.worker.status.connect(self.liveTestPage.updateStatus)
        self.worker.currentTargetChanged.connect(self.liveTestPage.updateCurrentTarget)
        
        self.worker.fault.connect(self.showFault)
        
        self.liveTestPage.stopRequested.connect(self.stopTest)
        self.worker.dataUpdated.connect(self.liveTestPage.updateLiveData)
        
        #self.liveTestPage.pressureSetpointLine.setPos(self.pressureSP)
        self.liveTestPage.setPressureSteps(self.pressureSteps)
        
        self.stack.setCurrentWidget(self.liveTestPage)
        
        self.resize(1200, 900)
        self.raise_()
        self.activateWindow()
        self.centerOnScreen()
        
        self.thread.start()
        
    def stopTest(self):
        if hasattr(self, "worker"):
            print("Stopping worker.")
            self.worker.stop()
            self.thread.quit()
            self.thread.wait(5000)
            print("Thread wait complete")
    
    def testFinished(self):
        if hasattr(self, "worker"):
            print("Stopping worker.")
            self.worker.stop()
            self.thread.quit()
            self.thread.wait(5000)
            print("Thread wait complete")
            
        results = {
            "time": list(self.liveTestPage.timeData),
            "pressure": list(self.liveTestPage.pressureData),
            "flow": list(self.liveTestPage.flowData),
            "pressureSteps": self.pressureSteps
        }
        
        print("testFinished() called.")
        print("Connecting resultsPage and returnToInputPage.")
        print("Calling loadResults")
        self.resultsPage.loadResults(results, self.savePath)
        print("Setting resultsPage as current widget.")
        self.stack.setCurrentWidget(self.resultsPage)
        self.resize(600, 400)
        self.raise_()
        self.activateWindow()
        self.centerOnScreen()
        
    def returnToInputPage(self):
        if hasattr(self, "lowPressInput"):
            self.lowPressInput.clear()
        if hasattr(self, "highPressInput"):
            self.highPressInput.clear()
        if hasattr(self, "incrementInput"):
            self.incrementInput.clear()
        if hasattr(self, "filenameInput"):
            self.filenameInput.clear()
        if hasattr(self, "pressureSteps"):
            self.pressureSteps.clear()
        
        self.liveTestPage.resetData()
        
        self.stack.setCurrentWidget(self.inputPage)
        self.resize(600, 400)
        self.raise_()
        self.activateWindow()
        self.centerOnScreen()
        
        
        

