# CoinSim.py
# purpose   : 변동성 돌파 전략  Simulate  화폐별, 기간별  UI 연동
# author    : simverse
# reference : 누구나 할수 있다. 비트코인 자동매매   유부장/조대협 저
# history   :
#       version date        author      description
#       1.0     2019.07.06  simverse    dev start
import sys
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
import pybithumb
import time
import numpy as np
import pandas as pd

form_class = uic.loadUiType("CoinSim.ui")[0]

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)

        # Widget Initialize
        self.pushButton_saveExcel.setEnabled(False)
        self.comboBox_coinName.addItems(pybithumb.get_tickers())

        #Event Handler Connect
        self.comboBox_coinName.currentIndexChanged.connect(self.loadCoinHistory)
        self.comboBox_periodType.currentIndexChanged.connect(self.loadCoinHistory)
        self.pushButton_simulate.clicked.connect(self.simulate)
        self.pushButton_saveExcel.clicked.connect(self.saveExcel)

        self.loadCoinHistory()

    def simulate(self):
        try:
#            coin = self.comboBox_coinName.currentText()
#            period = self.comboBox_periodType.currentText()

            tm_start = self.dateTimeEdit_start.dateTime().toPyDateTime()
            tm_end = self.dateTimeEdit_end.dateTime().toPyDateTime()

            print ("Row Cound #1 :", len(self.df.index))

#            self.df = self.df[(self.df.index >= tm_start)and (self.df.index <= tm_end )]
            self.df = self.df[self.df.index >= tm_start ]
            self.df = self.df[self.df.index <= tm_end ]


            print ("Row Cound #2 :", len(self.df.index))

            rateChange  = self.doubleSpinBox_rateChange.value()
            rateFee     = self.doubleSpinBox_rateFee.value()
            mvUnit      = self.spinBox_mvAvg.value()

            self.df['ma5']   = self.df['close'].rolling(window=mvUnit).mean().shift(1)
            self.df['range'] = (self.df['high'] - self.df['low']) * rateChange
            self.df['target']= self.df['open'] + self.df['range'].shift(1)
            self.df['bull']  = self.df['open'] > self.df['ma5']

            # sell / buy  -> double
            fee = rateFee /100. * 2
            self.df['ror']   = np.where((self.df['high'] > self.df['target']) & self.df['bull'],
                                          self.df['close']/self.df['target']- fee, 1)

            self.df['hpr']   = self.df['ror'].cumprod()
            self.df['dd']    = (self.df['hpr'].cummax() - self.df['hpr']) / self.df['hpr'].cummax() * 100

            print("MDD: ", self.df['dd'].max())
            print("HPR: ", self.df['hpr'][-2])

            #결과 저장
            self.label_HPR.setText(str(self.df['hpr'][-2]))
            self.label_MDD.setText(str(self.df['dd'].max()))

            self.displayResult(self.df)

            # Widget Initialize
            self.pushButton_saveExcel.setEnabled(True)

        except Exception as err:
            QMessageBox.information(self, "Error", str(err))


    def saveExcel(self):
        try:
            coin = self.comboBox_coinName.currentText()
            period = self.comboBox_periodType.currentText()
            filename =  coin+"_"+period +"_"+ time.strftime('%Y%m%d%H%M%S', time.localtime(time.time()))+".xlsx"

            self.df.to_excel(filename)
            
        except Exception as err:
            QMessageBox.information(self, "Error", str(err))

    def loadCoinHistory(self):
        try:
            coin = self.comboBox_coinName.currentText()
            period = self.comboBox_periodType.currentText()

            self.df = pybithumb.get_ohlcv(coin, period)

            self.dateTimeEdit_start.setDateTime(self.df.index[1])
            self.dateTimeEdit_end.setDateTime(self.df.index[len(self.df)-1])

        except Exception as err:
            QMessageBox.information(self, "Error", str(err))

    def displayResult(self, dataframe):

        try:
            self.tableWidget.setColumnCount(len(dataframe.columns)+1)
            self.tableWidget.setRowCount(len(dataframe.index))

            headers = list(dataframe.columns.values)
            headers.insert(0,"Date")

            self.tableWidget.setHorizontalHeaderLabels(headers)

            if self.checkBox_applyBullOnly.isChecked() == True :
                dataframe = dataframe[dataframe['bull'] == True]

            for i in range(0,len(dataframe.index)-1,1):
                self.tableWidget.setItem(i, 0, QTableWidgetItem(str(dataframe.index[i])))
                for j in range(1, len(headers) , 1):
                    self.tableWidget.setItem(i, j, QTableWidgetItem(str(dataframe[headers[j]][i])))

            self.tableWidget.resizeColumnsToContents()
            self.tableWidget.resizeRowsToContents()

        except Exception as err:
            QMessageBox.information(self, "Error", str(err))


app = QApplication(sys.argv)
win = MyWindow()
win.show()
app.exec_()