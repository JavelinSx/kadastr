import configparser
import ctypes
import os
import sqlite3
import sys

from PyQt5 import QtWidgets, QtGui, QtCore
from PyQt5.QtCore import QDate, QDateTime, QRegExp
from PyQt5.QtGui import QColor, QBrush, QTextCharFormat, QRegExpValidator, QIcon
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMessageBox, QDesktopWidget, QCompleter

import ui.newForm


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

        self.setWindowIcon(QIcon('img/main.png'))

        self.intValidatorPhone = QRegExpValidator(self.regExpPhone, self.lineEditTelefone)
        self.intValidatorPrice = QRegExpValidator(self.regExpPrice, self.lineEditPrice)
        self.lineEditTelefone.setValidator(self.intValidatorPhone)
        self.lineEditPrice.setValidator(self.intValidatorPrice)

        self.city = []
        self.address = []
        self.search = []
        self.massForCalendar = []
        self.move(qr.topLeft())
        self.checkFolder()
        self.conn = sqlite3.connect('//lena/c/Users/LenaPC/Documents/GitHub/DataBase dont delete/kadastr.db')
        self.cursor = self.conn.cursor()

        self.getInfoForCompleter()

        self.tableWidget.setSortingEnabled(True)
        self.currentDate = QDate.currentDate().toString("dd.MM.yyyy")


        self.currentDateForCombo = QDate.currentDate()
        self.dateTimeEdit.setDate(self.currentDateForCombo)
        self.dateEditDataWork.setDate(self.currentDateForCombo)
        self.dateEditNew.setDate(self.currentDateForCombo)
        self.pushButtonUpdateGui.clicked.connect(self.updateGui)
        self.pushButtonChangePath.clicked.connect(self.changePath)
        self.pushButton.clicked.connect(self.insertInfo)
        self.pushButtonOpenFolder.clicked.connect(self.openFolder)
        self.pushButtonEdit.clicked.connect(self.updateInfo)

        self.tableWidget.itemDoubleClicked.connect(self.openFullInfo)
        self.pushButtonDelete.clicked.connect(self.deleteRecord)
        self.pushButtonSearch.clicked.connect(self.searchInfo)
        self.pushButtonUpdate.clicked.connect(lambda: self.fillRecord(self.getAllRecord()))

        self.calendarWidget.clicked.connect(self.calendarWork)
        self.massUpdate = ()
        self.completerSearchList = QCompleter(self.search, self.lineEditSearch)
        self.completerAddressList = QCompleter(self.address, self.lineEditAddress)
        self.completerCityList = QCompleter(self.city, self.lineEditCity)
        self.lineEditSearch.setCompleter(self.completerSearchList)
        self.lineEditCity.setCompleter(self.completerCityList)
        self.lineEditAddress.setCompleter(self.completerAddressList)

        self.pushButtonDebts.clicked.connect(self.getInfoDebts)

        self.updateGui()

        self.tableWidget.itemClicked.connect(self.setCurrentDateCalendar)



    def setCurrentDateCalendar(self):
        dateBuild = QDate()
        row = self.tableWidget.currentRow()
        id = int(self.tableWidget.item(row, 9).text())
        date = ""

        for item in self.massForCalendar:
            if item[0] == id:
                date = item[12]

        year = int(date[6:10])
        mnt = int(date[3:5])
        day = int(date[0:2])
        dateBuild.setDate(year, mnt, day)


        self.calendarWidget.setCurrentPage(year, mnt)
        self.calendarWidget.setSelectedDate(dateBuild)

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
            self.cursor.execute("select pathToDir from statement where id=?", (getNumber,))
            result = self.cursor.fetchone()
            os.rmdir(result[0])
            self.cursor.execute("DELETE FROM statement WHERE id=?", (getNumber,))
            self.conn.commit()
            self.fillRecord(self.getAllRecord())

    def colorItem(self, item, text):
        if text == "Готова":
            item.setBackground(QtGui.QColor(240, 128, 0))
        if text == "Разработка":
            item.setBackground(QtGui.QColor(240, 128, 0))
        if text == "Ожидает выезд":
            item.setBackground(QtGui.QColor(240, 128, 0))
        if text == "В обработке":
            item.setBackground(QtGui.QColor(236, 240, 0))
        if text == "Готова":
            item.setBackground(QtGui.QColor(134, 250, 45))

    def checkFolder(self):

        pathFolder = "//lena/межевание/МЕЖЕВАНИЕ"

        if os.path.isdir(pathFolder):
            os.chdir(pathFolder)
        else:
            self.directory = QtWidgets.QFileDialog.getExistingDirectory(self, "Выберите дерикторию")
            if self.directory:  # не продолжать выполнение, если пользователь не выбрал директорию
                QMessageBox.critical(self, "Ошибка ", "ВЫберите основную деректорию", QMessageBox.Ok)
        for item in range(self.comboBoxProvideServices.count()):
            if not os.path.isdir(os.path.join(pathFolder, self.comboBoxProvideServices.itemText(item))):
                os.makedirs(os.path.join(pathFolder, self.comboBoxProvideServices.itemText(item)))

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
            path = os.path.join(os.getcwd(),
                                self.comboBoxProvideServices.itemText(self.comboBoxProvideServices.currentIndex()),
                                self.lineEditCity.text(),
                                self.lineEditAddress.text() + " " + self.lineEditSurname.text())
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
                         path,
                         self.dateTimeEdit.date().toString("dd.MM.yyyy"),
                         self.dateTimeEdit.time().toString("HH:mm"),
                         self.dateEditNew.text())]
                self.allClear()
                self.conn.executemany("INSERT INTO statement VALUES (null,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", mass)

                os.makedirs(path)  # создание директории по заданному пути

                os.startfile(path)  # открытие созданной директории

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
            pass

    def openFolder(self):  # открыть директорию, указанную в БД
        try:
            os.startfile(os.path.abspath(self.lineEditPath.text()))
        except FileNotFoundError as text:
            QMessageBox.critical(self, "Ошибка ", str(text), QMessageBox.Ok)

    def fillRecord(self, records):
        self.tableWidget.setSortingEnabled(False)
        self.tableWidget.clearContents()
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

        self.tableWidget.setSortingEnabled(True)

    def calendarWork(self):
        dateSelect = self.calendarWidget.selectedDate().toString("dd.MM.yyyy")
        self.cursor.execute("select dateNew from statement")
        dateNew = self.cursor.fetchall()
        dateBuild = QDate()
        color = QColor()
        brush = QBrush()
        form = QTextCharFormat()
        fillmass = []
        for date in dateNew:
                self.cursor.execute("select * from statement where dateNew = ?", date)
                result = self.cursor.fetchall()
                if result[0][11] == "В обработке":
                    color.setRgb(236, 240, 0)
                elif result[0][11] == "Ожидает выезд":
                    color.setRgb(219, 94, 26)
                elif result[0][11] == "Готова" and (result[0][10] == "Разработка"):
                    color.setRgb(236, 240, 0)
                elif result[0][11] == "Готова" and result[0][10] == "Готова":
                    color.setRgb(134, 250, 45)
                else:
                    color.setRgb(74, 81, 87)
                year = int(str(date[0])[6:10])
                mnt = int(str(date[0])[3:5])
                day = int(str(date[0])[0:2])
                dateBuild.setDate(year, mnt, day)
                brush.setColor(color)
                form.setBackground(brush)
                self.calendarWidget.setDateTextFormat(dateBuild, form)

        self.cursor.execute("select * from statement")
        allInfo = self.cursor.fetchall()

        for i in range(len(dateNew)):
            if str(allInfo[i][16]) == dateSelect:
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
        self.massForCalendar = records
        records.sort()
        return records

    def openFullInfo(self):
        self.labelService.hide()
        self.labelCity.hide()
        self.labelAddress.hide()
        self.comboBoxProvideServices.hide()
        self.lineEditCity.hide()
        self.lineEditAddress.hide()
        self.pushButton.hide()
        self.labelDateNew.show()
        self.label.show()
        self.dateEditNew.show()
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
        dayN = int(mass[0][16][0:2])
        mouthN = int(mass[0][16][3:5])
        yearN = int(mass[0][16][6:10])
        dayR = int(mass[0][14][0:2])
        mouthR = int(mass[0][14][3:5])
        yearR = int(mass[0][14][6:10])
        timeHour = int(mass[0][15][0:len(mass[0][15]) - 3])
        timeMinutes = int(mass[0][15][len(mass[0][15]) - 2:len(mass[0][15])])
        dateFillWork = QDate(yearW, mouthW, dayW)
        dateFillReception = QDateTime(yearR, mouthR, dayR, timeHour, timeMinutes)
        dateFillNew = QDate(yearN,mouthN,dayN)
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
        self.dateEditNew.setDate(dateFillNew)

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
            dateNew = self.dateEditNew.text()
            pathToDir = self.lineEditPath.text()

            if buttonReply == QMessageBox.Yes:
                self.cursor.execute("UPDATE statement SET name=?,surName=?,middleName=?,telefone=?,"
                                    "price=?,info=?,status=?,work=?,dateWork=?,dateReception=?, pathToDir=?, dateNew=? WHERE id=?",
                                    (name, surName, middleName, telefone, price, info, status,
                                     work, dateWork, dateReception, pathToDir, dateNew, id,))
                self.conn.commit()
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
        self.labelDateNew.show()
        self.dateEditNew.show()
        self.pushButtonChangePath.hide()
        self.pushButtonOpenFolder.hide()
        self.lineEditPath.hide()
        self.pushButtonEdit.hide()

    def getInfoDebts(self):
        self.cursor.execute("select id,dateReception,work from statement")
        dateReceprionMass = self.cursor.fetchall()

        year = int(self.currentDate[6:10])
        mounth = int(self.currentDate[3:5])
        day = int(self.currentDate[0:2])
        datePass = QDate(year, mounth, day)

        dateMass = []
        countMass = []

        for item in dateReceprionMass:

            dateReception = QDate(int(item[1][6:10]), int(item[1][3:5]), int(item[1][0:2]))
            dateReception.toString("dd.MM.yyyy")

            countDays = dateReception.daysTo(datePass)
            if countDays > 20 and item[2]=="Ожидает выезд":
                    dateMass.append(item[0])
                    countMass.append(countDays)

        self.cursor.execute("select * from statement where id in ({0})".format(', '.join('?' for _ in dateMass)), dateMass)
        result = self.cursor.fetchall()

        self.fillRecord(result)

def main():
    app = QtWidgets.QApplication(sys.argv)
    window = startWindow()
    myappid = 'mycompany.myproduct.subproduct.version'  # arbitrary string
    ctypes.windll.shell32.SetCurrentProcessExplicitAppUserModelID(myappid)
    app_icon = QIcon()

    app_icon.addFile('img/main.png', QtCore.QSize(32, 32))

    app.setWindowIcon(app_icon)
    window.show()
    app.exec_()

if __name__ == "__main__":
    main()
