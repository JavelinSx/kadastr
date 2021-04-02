import configparser
import os
import sys

from PyQt5 import QtWidgets, QtGui, QtCore
import sqlite3

from PyQt5.QtCore import QDate, QDateTime, QRegExp
from PyQt5.QtGui import  QColor, QBrush, QTextCharFormat, QRegExpValidator
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMessageBox, QDesktopWidget, QCompleter

import ui.newForm
import ctypes


class startWindow(QtWidgets.QMainWindow, ui.newForm.Ui_MainWindow):
    def __init__(self):
        super().__init__()
        self.error_dialog = QtWidgets.QErrorMessage()
        self.setupUi(self)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.regExpPhone = QRegExp('^\d\d\d\d\d\d\d\d\d\d\d$')
        self.regExpPrice = QRegExp('^\d\d\d\d\d$')
        self.intValidatorPhone = QRegExpValidator(self.regExpPhone, self.lineEditTelefone)
        self.intValidatorPrice = QRegExpValidator(self.regExpPrice, self.lineEditPrice)
        self.lineEditTelefone.setValidator(self.intValidatorPhone)
        self.lineEditPrice.setValidator(self.intValidatorPrice)
        self.city = []
        self.address = []
        self.search = []
        self.move(qr.topLeft())
        self.createConfig()
        self.conn = sqlite3.connect(self.createConfig()[0])
        self.cursor = self.conn.cursor()

        self.pushButtonUpdateGui.clicked.connect(self.updateGui)
        self.pushButtonChangePath.clicked.connect(self.changePath)
        self.pushButton.clicked.connect(self.insertInfo)
        self.pushButtonOpenFolder.clicked.connect(self.openFolder)
        self.pushButtonEdit.clicked.connect(self.updateInfo)

        self.calendarWork()
        self.tableWidget.itemDoubleClicked.connect(self.openFullInfo)
        self.pushButtonDelete.clicked.connect(self.deleteRecord)
        self.pushButtonSearch.clicked.connect(self.searchInfo)
        self.pushButtonUpdate.clicked.connect(lambda: self.fillRecord(self.getAllRecord()))
        self.calendarWidget.clicked.connect(self.calendarWork)
        self.massUpdate = ()
        self.completerSearchList = QCompleter(self.search,self.lineEditSearch)
        self.completerAddressList = QCompleter(self.address, self.lineEditAddress)
        self.completerCityList = QCompleter(self.city, self.lineEditCity)
        self.lineEditSearch.setCompleter(self.completerSearchList)
        self.lineEditCity.setCompleter(self.completerCityList)
        self.lineEditAddress.setCompleter(self.completerAddressList)
        self.updateGui()

    def changePath(self):
        pathFolder = QFileDialog.getExistingDirectory(self, "Выбрите директорию", self.lineEditPath.text(),
                                                      QFileDialog.ShowDirsOnly)
        if pathFolder != "":
            self.lineEditPath.clear()
            self.lineEditPath.setText(os.path.abspath(pathFolder))

    def searchInfo(self):
        textForCOmpleter = self.lineEditSearch.text().title()
        text = '%' + self.lineEditSearch.text() + '%'
        text = text.title()
        self.cursor.execute("select id from statement where address || surname || telefone || services || city like ?",
                            (text,))
        result = self.cursor.fetchall()
        mass = []
        try:
            self.cursor.execute("insert into completer_data_search values(?)", (textForCOmpleter,))
            self.conn.commit()
            if len(result) != 0:
                for res in result:
                    self.cursor.execute("select * from statement where id = ?", res)
                    records = self.cursor.fetchall()
                    mass = mass + records
                self.fillRecord(mass)

            else:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Информация")
                msg.setText("Данные не найдены")
                msg.addButton('Ok', QMessageBox.AcceptRole)
                msg.exec()
        except sqlite3.IntegrityError:
            pass

    def deleteRecord(self):
        currentRowSelect = self.tableWidget.currentRow()
        getNumber = self.tableWidget.item(currentRowSelect, 9).text()
        buttonReply = QMessageBox.question(self, 'Подтверждение действия', "Удалить выбранную запись?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM statement WHERE id=?", (getNumber,))
            self.conn.commit()
            self.fillRecord(self.getAllRecord())

    def colorItem(self, item, text):
        if text == "Готова":
            item.setBackground(QtGui.QColor(240, 128, 0))
        if text == "Ожидание":
            item.setBackground(QtGui.QColor(240, 128, 0))
        if text == "Разработка":
            item.setBackground(QtGui.QColor(236, 240, 0))
        if text == "Ожидает выезд":
            item.setBackground(QtGui.QColor(240, 128, 0))
        if text == "В обработке":
            item.setBackground(QtGui.QColor(236, 240, 0))
        if text == "Готова":
            item.setBackground(QtGui.QColor(134, 250, 45))

    def getFolder(self):  # получение полного пути до созданной директории
        provide = self.comboBoxProvideServices.itemText(self.comboBoxProvideServices.currentIndex())
        city = self.lineEditCity.text()
        address = self.lineEditAddress.text()
        fullPathToDir = os.path.join(self.createConfig()[1], provide, city, address)
        return os.path.abspath(fullPathToDir)

    def allClear(self):
        self.lineEditCity.clear()
        self.lineEditAddress.clear()
        self.lineEditSurname.clear()
        self.lineEditName.clear()
        self.lineEditMiddleName.clear()
        self.lineEditTelefone.clear()
        self.lineEditPrice.clear()
        self.textEditInfo.clear()
        self.lineEditPath.clear()

    def insertInfo(self):  # добавление информации в БД
        try:

            buttonReply = QMessageBox.question(self, 'Подтверждение действия', "Добавить запись?",
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                city = self.lineEditCity.text().title()
                address = self.lineEditAddress.text().title()

                mass = [(self.comboBoxProvideServices.itemText(self.comboBoxProvideServices.currentIndex()),
                         self.lineEditCity.text().title(),
                         self.lineEditAddress.text().title(),
                         self.lineEditSurname.text().title(),
                         self.lineEditName.text().title(),
                         self.lineEditMiddleName.text().title(),
                         self.lineEditTelefone.text(),
                         self.lineEditPrice.text(),
                         self.textEditInfo.toPlainText(),
                         self.comboBoxStatus.itemText(self.comboBoxStatus.currentIndex()),
                         self.comboBoxWork.itemText(self.comboBoxWork.currentIndex()),
                         self.dateEditDataWork.text(),
                         os.path.abspath(self.getFolder()),
                         self.dateTimeEdit.date().toString("dd.MM.yyyy"),
                         self.dateTimeEdit.time().toString("HH:mm"))]

                self.conn.executemany("INSERT INTO statement VALUES (null,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", mass)

                os.makedirs(self.getFolder())  # создание директории по заданному пути

                os.startfile(self.getFolder())  # открытие созданной директории

                if self.conn.commit():
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowTitle("Информация")
                    msg.setText("Данные успешно добавлены")
                    msg.addButton('Ok', QMessageBox.AcceptRole)
                    msg.exec()
                    self.allClear()  # очистка всех полей
                self.cursor.execute("insert into completer_data_city values(?)", (city,))
                self.cursor.execute("insert into completer_data_address values(?)", (address,))
                self.conn.commit()
        except FileExistsError as text:
            QMessageBox.critical(self, "Ошибка ", str(text), QMessageBox.Ok)
            self.conn.rollback()
        except sqlite3.IntegrityError as text:
            print(text)

    def openFolder(self):  # открыть директорию, указанную в БД
        try:
            os.startfile(os.path.abspath(self.lineEditPath.text()))
        except FileNotFoundError as text:
            QMessageBox.critical(self, "Ошибка ", str(text), QMessageBox.Ok)

    def createConfig(self):
        try:
            section = configparser.DEFAULTSECT
            optionDb = 'pathDb'
            optionFolder = 'pathFolder'
            config = configparser.ConfigParser()
            config.read('data/settings.ini')
            pathDb = config.get(section, optionDb)
            pathFolder = config.get(section, optionFolder)
        except:
            section = configparser.DEFAULTSECT
            optionDb = 'pathDb'
            optionFolder = 'pathFolder'
            config = configparser.ConfigParser()
            config.read('data/settings.ini')
            pathDb = QFileDialog.getOpenFileName(self,
                                                 "Выбрать файл базы данных",
                                                 ".",
                                                 "Data Base(*.db);;")
            pathFolder = QFileDialog.getExistingDirectory(self, "Выбрите директорию")
            config.set(section, optionDb, pathDb[0])
            config.set(section, optionFolder, pathFolder)
            with open('data/settings.ini', 'w') as config_file:
                config.write(config_file)
        return pathDb, pathFolder

    def fillRecord(self, records):
        self.tableWidget.setRowCount(len(records))
        self.tableWidget.hideColumn(9)
        for i in range(len(records)):
            item = QTableWidgetItem()
            self.colorItem(item, records[i][10])
            item.setText(str(records[i][10]))  # статус
            self.tableWidget.setItem(i, 0, item)
            item = QTableWidgetItem()
            self.colorItem(item, records[i][11])
            item.setText(str(records[i][11]))  # съёмка
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
            item.setText(str(records[i][1]))  # услуга
            self.tableWidget.setItem(i, 8, item)
            item = QTableWidgetItem()
            item.setText(str(records[i][0]))  # id
            self.tableWidget.setItem(i, 9, item)

    def calendarWork(self):
        dateSelect = self.calendarWidget.selectedDate().toString("dd.MM.yyyy")
        self.cursor.execute("select dateReception from statement")
        dateReception = self.cursor.fetchall()
        dateBuild = QDate()
        color = QColor()
        brush = QBrush()
        form = QTextCharFormat()
        counter = 0
        fillmass = []
        for date in dateReception:
            if str(date[0])[3:10] == dateSelect[3:10]:
                self.cursor.execute("select * from statement where dateReception = ?", date)
                result = self.cursor.fetchall()
                counter = counter + 1
                if result[0][11] != "Готова":
                    color.setRgb(220, 255, 170)
                year = str(date[0])[6:10]
                mnt = str(date[0])[3:5]
                day = str(date[0])[0:2]
                dateBuild.setDate(int(year), int(mnt), int(day))
                brush.setColor(color)
                form.setBackground(brush)
                self.calendarWidget.setDateTextFormat(dateBuild, form)

        self.cursor.execute("select * from statement")
        allInfo = self.cursor.fetchall()
        for i in range(len(dateReception)):
            if str(allInfo[i][14])[0:10] == dateSelect[0:10]:
                fillmass.append(allInfo[i])
        self.fillRecord(fillmass)

    def getInfoForCompleter(self):
        self.cursor.execute("select completerAddress from completer_data_address")
        completerAddress = self.cursor.fetchall()
        for item in completerAddress:
            self.address.append(item[0])

        self.cursor.execute("select completerCity from completer_data_city")
        completerCity = self.cursor.fetchall()
        for item in completerCity:
            self.city.append(item[0])

        self.cursor.execute("select completerSearch from completer_data_search")
        completerSearch = self.cursor.fetchall()
        for item in completerSearch:
            self.search.append(item[0])

    def getAllRecord(self):

        self.cursor.execute("SELECT * from statement")
        records = self.cursor.fetchall()
        return records

    def openFullInfo(self):
        self.labelService.hide()
        self.labelCity.hide()
        self.labelAddress.hide()
        self.comboBoxProvideServices.hide()
        self.lineEditCity.hide()
        self.lineEditAddress.hide()
        self.pushButton.hide()
        self.label.show()
        self.pushButtonChangePath.show()
        self.pushButtonOpenFolder.show()
        self.lineEditPath.show()
        self.pushButtonEdit.show()
        currentRowSelect = self.tableWidget.currentRow()
        getNumber = self.tableWidget.item(currentRowSelect, 9).text()
        self.cursor.execute("SELECT * from statement where id = ?", (getNumber,))
        mass = self.cursor.fetchall()
        self.tabWidget.setCurrentIndex(1)
        self.fillInfo(mass)

    def fillInfo(self, mass):  # копирование и воод информации о выделенной заявке
        dayW = int(mass[0][12][0:2])
        mouthW = int(mass[0][12][3:5])
        yearW = int(mass[0][12][6:10])
        dayR = int(mass[0][14][0:2])
        mouthR = int(mass[0][14][3:5])
        yearR = int(mass[0][14][6:10])
        timeHour = int(mass[0][15][0:len(mass[0][15]) - 3])
        timeMinutes = int(mass[0][15][len(mass[0][15]) - 2:len(mass[0][15])])
        dateFillWork = QDate(yearW, mouthW, dayW)
        dateFillReception = QDateTime(yearR, mouthR, dayR, timeHour, timeMinutes)

        self.massUpdate = mass
        self.lineEditSurname.setText(mass[0][4])
        self.lineEditName.setText(mass[0][5])
        self.lineEditMiddleName.setText(mass[0][6])
        self.lineEditTelefone.setText(mass[0][7])
        self.lineEditPrice.setText(mass[0][8])
        self.textEditInfo.setText(mass[0][9])
        self.comboBoxStatus.setCurrentIndex(self.comboBoxStatus.findText(mass[0][10]))
        self.comboBoxWork.setCurrentIndex(self.comboBoxWork.findText(mass[0][11]))
        self.dateEditDataWork.setDate(dateFillWork)
        self.lineEditPath.setText(mass[0][13])
        self.dateTimeEdit.setDateTime(dateFillReception)

    def updateInfo(self):
        try:
            buttonReply = QMessageBox.question(self, 'Подтверждение действия', "Обновить данную запись?",
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            id = self.massUpdate[0][0]
            name = self.lineEditName.text().title()
            surName = self.lineEditSurname.text().title()
            middleName = self.lineEditMiddleName.text().title()
            telefone = self.lineEditTelefone.text()
            price = self.lineEditPrice.text()
            info = self.textEditInfo.toPlainText()
            status = self.comboBoxStatus.itemText(self.comboBoxStatus.currentIndex())
            work = self.comboBoxWork.itemText(self.comboBoxWork.currentIndex())
            dateWork = self.dateEditDataWork.text()
            dateReception = self.dateTimeEdit.text()
            pathToDir = self.lineEditPath.text()
            if buttonReply == QMessageBox.Yes:
                self.cursor.execute("UPDATE statement SET name=?,surName=?,middleName=?,telefone=?,"
                                    "price=?,info=?,status=?,work=?,dateWork=?,dateReception=?, pathToDir=? WHERE id=?",
                                    (name, surName, middleName, telefone, price, info, status,
                                     work, dateWork, dateReception, pathToDir, id,))
                self.allClear()
                self.updateGui()
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Информация")
                msg.setText("Данные успешно изменены")
                msg.addButton('Ok', QMessageBox.AcceptRole)
                msg.exec()
        except IndexError:
            QMessageBox.critical(self, "Ошибка ", str("Для изменения информации, выберите клиента из базы данных"),
                                 QMessageBox.Ok)

    def updateGui(self):
        self.allClear()
        self.labelService.show()
        self.labelCity.show()
        self.labelAddress.show()
        self.comboBoxProvideServices.show()
        self.lineEditCity.show()
        self.lineEditAddress.show()
        self.pushButton.show()
        self.label.hide()
        self.pushButtonChangePath.hide()
        self.pushButtonOpenFolder.hide()
        self.lineEditPath.hide()
        self.pushButtonEdit.hide()


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = startWindow()
    myappid = 'mycompany.myproduct.subproduct.version'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app_icon = QtGui.QIcon()
    app_icon.addFile('img/main.ico', QtCore.QSize(16, 16))
    app_icon.addFile('img/main.ico', QtCore.QSize(24, 24))
    app_icon.addFile('img/main.ico', QtCore.QSize(32, 32))
    app_icon.addFile('img/main.ico', QtCore.QSize(48, 48))
    app_icon.addFile('img/main.ico', QtCore.QSize(256, 256))
    app.setWindowIcon(app_icon)
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
