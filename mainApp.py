import configparser
import os
import sys

from PyQt5 import QtWidgets
import sqlite3

from PyQt5.QtWidgets import QFileDialog, QPlainTextEdit, QTableWidgetItem

import addServices
import startWindow
import viewAllServices


class winStart(QtWidgets.QMainWindow, startWindow.Ui_startWindow):
    def __init__(self):
        super().__init__()
        self.error_dialog = QtWidgets.QErrorMessage()
        self.setupUiStart(self)
        self.pushButtonAdd.clicked.connect(self.openWinAddServices)
        self.pushButtonView.clicked.connect(self.openWinView)
        self.createConfig()

    def checkDb(self):
        conn = sqlite3.connect(self.createConfig()[0])
        cursor = conn.cursor()
        return conn, cursor

    def createConfig(self):
        try:
            section = configparser.DEFAULTSECT
            optionDb = 'pathDb'
            optionFolder = 'pathFolder'
            config = configparser.ConfigParser()
            config.read('settings.ini')
            pathDb = config.get(section, optionDb)
            pathFolder = config.get(section, optionFolder)
        except:
            section = configparser.DEFAULTSECT
            optionDb = 'pathDb'
            optionFolder = 'pathFolder'
            config = configparser.ConfigParser()
            config.read('settings.ini')
            pathDb = QFileDialog.getOpenFileName(self,
                                                 "Выбрать файл базы данных",
                                                 ".",
                                                 "Data Base(*.db);;")
            pathFolder = QFileDialog.getExistingDirectory(self,
                                                          "Выбрите директорию")

            config.set(section, optionDb, pathDb[0])
            config.set(section, optionFolder, pathFolder)
            with open('settings.ini', 'w') as config_file:
                config.write(config_file)

        return pathDb, pathFolder

    def openWinAddServices(self):
        self.hide()
        self.winAdd = winAdd(self.createConfig()[0], self.createConfig()[1], self.checkDb()[0], self.checkDb()[1])
        self.winAdd.show()

    def openWinView(self):
        self.hide()
        self.winView = winView(self.createConfig()[0], self.createConfig()[1], self.checkDb()[0], self.checkDb()[1])
        self.winView.show()


class winAdd(QtWidgets.QMainWindow, addServices.Ui_addServices):
    def __init__(self, pathDb, pathFolder, conn, cursor):
        super().__init__()
        self.pathDb = pathDb
        self.pathFolder = pathFolder
        self.conn = conn
        self.cursor = cursor
        self.setupUiAddServices(self)
        self.pushButton.clicked.connect(self.getAddInfo)
        self.pushButtonOpenFolder.clicked.connect(self.openFolder)
        self.getFolder()

    def getFolder(self):
        provide = self.comboBoxProvideServices.itemText(self.comboBoxProvideServices.currentIndex())
        city = self.comboBoxCity.itemText(self.comboBoxCity.currentIndex())
        address = self.lineEditAddress.text()
        fullPathToDir = os.path.join(self.pathFolder, provide, city, address)

        self.pushButtonOpenFolder.setEnabled(True)
        return fullPathToDir

    def getAddInfo(self):
        mass = [(self.comboBoxProvideServices.itemText(self.comboBoxProvideServices.currentIndex()),
                 self.comboBoxCity.itemText(self.comboBoxCity.currentIndex()), self.lineEditAddress.text(),
                 self.lineEditSurname.text(), self.lineEditName.text(), self.lineEditMiddleName.text(),
                 self.lineEditTelefone.text(), self.lineEditSnils.text(), self.textEditPassportText(),
                 self.dateEditDate.text(), self.lineEditPrice.text(), self.textEditInfoText(),
                 self.comboBoxStatus.itemText(self.comboBoxStatus.currentIndex()),
                 self.comboBoxWork.itemText(self.comboBoxWork.currentIndex()),
                 self.dateEditDataWork.text(), os.path.abspath(self.getFolder()))]
        self.conn.executemany("INSERT INTO statement VALUES (null,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", mass)
        self.conn.commit()
        os.makedirs(self.getFolder())

        return mass

    def openFolder(self):
        os.startfile(os.path.abspath(self.getFolder()))

    def textEditPassportText(self):
        text = self.textEditPassport.toPlainText()
        return text

    def textEditInfoText(self):
        text = self.textEditInfo.toPlainText()
        return text

    def fillFullInfo(self,provide,city,address,surname,name,middlename,telefone,snils,passport,date,price,info,status,work,datework,path):
        self.comboBoxProvideServices.itemText(provide)


    def closeEvent(self, event):
        self.hide()
        self.winStart = winStart()
        self.winStart.show()


class winView(QtWidgets.QMainWindow, viewAllServices.Ui_viewAllServices):
    def __init__(self, pathDb, pathFolder, conn, cursor):
        super().__init__()
        self.pathDb = pathDb
        self.pathFolder = pathFolder
        self.conn = conn
        self.cursor = cursor
        self.setupUiView(self)
        self.getAllRecord()
        self.tableWidget.itemDoubleClicked.connect(self.openFullInfo)

    def getAllRecord(self):

        self.cursor.execute("SELECT * from statement")
        records = self.cursor.fetchall()
        self.tableWidget.setRowCount(len(records))
        for i in range(len(records)):
            for j in range(6):
                item = QTableWidgetItem()
                item.setText(str(records[i][13]))  # статус
                self.tableWidget.setItem(i, 0, item)
                item = QTableWidgetItem()
                item.setText(str(records[i][14]))  # съёмка
                self.tableWidget.setItem(i, 1, item)
                item = QTableWidgetItem()
                item.setText(str(records[i][2]))  # нас.пункт
                self.tableWidget.setItem(i, 2, item)
                item = QTableWidgetItem()
                item.setText(str(records[i][3]))  # адрес
                self.tableWidget.setItem(i, 3, item)
                item = QTableWidgetItem()
                item.setText(str(records[i][4]))  # фамилия
                self.tableWidget.setItem(i, 4, item)
                item = QTableWidgetItem()
                item.setText(str(records[i][5]))  # имя
                self.tableWidget.setItem(i, 5, item)
                item = QTableWidgetItem()
                item.setText(str(records[i][6]))  # отчество
                self.tableWidget.setItem(i, 6, item)
                item = QTableWidgetItem()
                item.setText(str(records[i][7]))  # ном.телефона
                self.tableWidget.setItem(i, 7, item)
                item = QTableWidgetItem()
                item.setText(str(records[i][10]))  # дата записи
                self.tableWidget.setItem(i, 8, item)
                item = QTableWidgetItem()
                item.setText(str(records[i][1]))  # услуга
                self.tableWidget.setItem(i, 9, item)
                item = QTableWidgetItem()
                item.setText(str(records[i][0]))  # услуга
                self.tableWidget.setItem(i, 10, item)

    def openFullInfo(self):
        currentRowSelect = self.tableWidget.currentRow()
        getNumber = self.tableWidget.item(currentRowSelect, 10).text()
        self.cursor.execute("SELECT * from statement where id = ?", (getNumber,))
        result = self.cursor.fetchall()
        self.winAdd = winAdd(self.pathDb, self.pathFolder, self.conn, self.cursor)

        print(result)

    def closeEvent(self, event):
        self.hide()
        self.winStart = winStart()
        self.winStart.show()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = winStart()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
