from PyQt6.QtWidgets import QTableWidget, QHeaderView, QTableWidgetItem, QWidget, QVBoxLayout, QLabel, QPushButton, QHBoxLayout, QApplication, QMessageBox
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
import pyqtgraph as pg
import os, pandas, numpy, csv

class TestResultsPage(QWidget):
    newTestRequested = pyqtSignal()
    
    def __init__(self):
        print("Initializing testResultsPage class.")
        super().__init__()
        self.initUI()
        
    def initUI(self):
        mainLayout = QVBoxLayout()
        print("testResultsPage initUI called.")
        
        self.titleLabel = QLabel("TEST RESULTS")

        self.titleLabel.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.titleLabel.setStyleSheet("""
            QLabel {font-size: 28px;
                    font-weight: bold;
                    color: #500000;
                    }
            """)
            
        mainLayout.addWidget(self.titleLabel)
        
        
        self.subtitleLabel = QLabel("Pressure Control Test Summary:")

        self.subtitleLabel.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.subtitleLabel.setStyleSheet("""
            QLabel {font-size: 17px;
                    color: #303030;
                    font-style: italic;
                    
                    }
            """)
        mainLayout.addWidget(self.subtitleLabel)
        
        self.resultsTable = QTableWidget()
        self.resultsTable.setColumnCount(6)
        self.resultsTable.setHorizontalHeaderLabels(["Nominal Pressure (psi)", "Avg. Pressure (psi)", "Estimated Flow (GPM)", "Flow Std. Dev.", "Samples", "Status"])
        
        mainLayout.addWidget(self.resultsTable)
        
        self.regressionPlot = pg.PlotWidget()
        mainLayout.addWidget(self.regressionPlot)
        
        self.modelLabel = QLabel()
        mainLayout.addWidget(self.modelLabel)
        
        buttonLayout = QHBoxLayout()
        self.openCSVButton = QPushButton("Open CSV")
        self.newTestButton = QPushButton("New Test")
        self.exitButton = QPushButton("Exit")
        
        buttonLayout.addWidget(self.openCSVButton)
        buttonLayout.addWidget(self.newTestButton)
        buttonLayout.addWidget(self.exitButton)
        
        self.openCSVButton.clicked.connect(self.openCSV)
        self.exitButton.clicked.connect(QApplication.quit)
        self.newTestButton.clicked.connect(self.newTestRequested.emit)
        print("Button and plot widgets added within testResultsPage.")
        
        mainLayout.addLayout(buttonLayout)
        self.setLayout(mainLayout)
        
    def loadResults(self, results, csv_path):
        self.csv_path = csv_path
        self.results = results
        
        self.regressionPlot.clear()
        self.regressionPlot.show()
        
        print("loadResults called.")
        
        MIN_SAMPLES = 25
        
        df = pandas.read_csv(csv_path)
        
        summary = (
            df.groupby("Target_psi")
              .agg(
                  PressureMean = ("Pressure_psi", "mean"),
                  FlowMean = ("Flow_gpm", "mean"),
                  PressureStd = ("Pressure_psi", "std"),
                  FlowStd = ("Flow_gpm", "std"),
                  SampleCount = ("Flow_gpm", "count")
              ).reset_index()
        )
        summary["Valid"] = summary["SampleCount"] >= MIN_SAMPLES
        summary.reset_index(inplace=True)
        
        validSummary = summary[summary["Valid"]]
        invalidSummary = summary[~summary["Valid"]]
        
        if len(validSummary) == 0:
            self.subtitleLabel.setText("Test ended before any pressure steps were completed.")
            self.resultsTable.hide()
            
        else:
            self.resultsTable.setRowCount(len(summary))
            for row, (_, data) in enumerate(summary.iterrows()):
                if data["Valid"]:
                    status = "Complete"
                else:
                    status = "Incomplete"
                
                self.resultsTable.setItem(row, 0, QTableWidgetItem(f"{data['Target_psi']:.0f}"))
                self.resultsTable.setItem(row, 1, QTableWidgetItem(f"{data['PressureMean']:.3f}"))
                self.resultsTable.setItem(row, 2, QTableWidgetItem(f"{data['FlowMean']:.3f}"))
                self.resultsTable.setItem(row, 3, QTableWidgetItem(f"{data['FlowStd']:.3f}"))
                self.resultsTable.setItem(row, 4, QTableWidgetItem(str(int(data["SampleCount"]))))
                self.resultsTable.setItem(row, 5, QTableWidgetItem(status))
                
                if not data["Valid"]:
                    for column in range(self.resultsTable.columnCount()):
                        self.resultsTable.item(row, column).setBackground(QColor(255, 240, 180))
            
            pressure = validSummary["PressureMean"].to_numpy()
            flow = validSummary["FlowMean"].to_numpy()
            logPress = numpy.log(pressure)
            logFlow = numpy.log(flow)
            
            if len(validSummary) >= 2:
                b, logA = numpy.polyfit(logPress, logFlow, 1)
                pressureFit = numpy.linspace(pressure.min(), pressure.max(), 100)
                a = numpy.exp(logA)
                flowFit = a * pressureFit**b
                predictedFlow = a * pressure**b
                ssResidual = numpy.sum((flow - predictedFlow)**2)
                ssTotal = numpy.sum((flow - numpy.mean(flow))**2)
                rSquared = 1 - ssResidual / ssTotal
                
                self.regressionPlot.plot(pressureFit, flowFit, pen=pg.mkPen("red", width = 3))
                
                self.modelLabel.setText(f"Flow = {a:.4f} × Pressure^({b:.3f})\n"
                                        f"R² = {rSquared:.4f}")
                
                with open(csv_path, "a", newline="") as file:
                    writer = csv.writer(file)
                    writer.writerow([])
                    writer.writerow(["===", "===", "Test Summary", "===", "==="])
                    writer.writerow([])
                    
                    writer.writerow([
                        "NominalPressure_psi",
                        "AveragePressure_psi",
                        "AverageFlow_gpm",
                        "FlowStdDev_gpm",
                        "SampleCount",
                        "Status"
                    ])
                    
                    for _, row in summary.iterrows():
                        status = "Complete" if row["Valid"] else "Incomplete"
                        writer.writerow([
                            round(row["Target_psi"]),
                            round(row["PressureMean"], 2),
                            round(row["FlowMean"], 3),
                            round(row["FlowStd"], 3),
                            int(row["SampleCount"]),
                            status
                        ])
                    
                    writer.writerow([])
                    writer.writerow(["===", "===", "Estimation Model", "===", "==="])
                    writer.writerow([])
                    
                    writer.writerow(["Model", "Power Law"])
                    writer.writerow(["Coefficient a", a])
                    writer.writerow(["Exponent b", b])
                    writer.writerow(["Equation", f"Q = {a:.4f} * P^{b:.4f}"])
                    writer.writerow(["R^2", rSquared])
            else:
                self.regressionPlot.hide()
                self.modelLabel.setText("Not enough completed steps to generate estimation model.")
        
        
        
        self.resultsTable.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.ResizeToContents)
            
        # tolerance = 0.8
        # required_samples = 20
        # start_index = None
        # for i in range(len(results["pressure"]) - required_samples):
        #     window = results["pressure"][i:i+required_samples]

        #     if all(abs(p - results["setpoint"]) <= tolerance for p in window):
        #         start_index = i
        #         break
            
        # if start_index == None:
        #     self.summaryLabel.setText(
        #         f"""
        #     Duration:
        #     {results["time"][-1]:.1f} s
            
        #     Steady output at pressure setpoint was never reached. 
        #     """)
        # else:
        #     steadyPressureList = results["pressure"][start_index:]
        #     steadyPressure = sum(steadyPressureList) / len(steadyPressureList)
        #     steadyFlowList = results["flow"][start_index:]
        #     steadyFlow = sum(steadyFlowList) / len(steadyFlowList)
        #     steadyTime = results["time"][start_index]
            
        #     print("Pressure and flow averages found.")
        #     self.summaryLabel.setText(
        #         f"""
        #     Duration:
        #     {results["time"][-1]:.1f} s
            
        #     Time taken to establish steady output:
        #     {steadyTime:.1f} s
            
        #     Pressure Setpoint:
        #     {results["setpoint"]:.1f} psi
            
        #     Average (Steady) Pressure:
        #     {steadyPressure:.2f} psi
            
        #     Average (Steady) Flow:
        #     {steadyFlow:.2f} GPM
        #     """)
        #     print("Completed loadResults.")
    def openCSV(self):
        if not self.csv_path:
            QMessageBox.warning(self, "CSV Not Available", "No CSV file has been associated with this test.")
            return
        os.startfile(self.csv_path)
        
