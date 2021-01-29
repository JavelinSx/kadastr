import configparser
import os
import sys

from PyQt5 import QtWidgets, QtGui
import sqlite3

from PyQt5.QtCore import QDate, QRectF
from PyQt5.QtGui import QIcon, QPainter, QColor, QBrush, QTextCharFormat
from PyQt5.QtWidgets import QFileDialog, QTableWidgetItem, QMessageBox, QDesktopWidget

import viewAllFormUi
import startWindowUi
import addFormUi
import viewSelectFormUi


class startWindow(QtWidgets.QMainWindow, startWindowUi.Ui_startWindow):
    def __init__(self, parent=None):
        super(startWindow, self).__init__(parent)
        self.parent = parent
        self.error_dialog = QtWidgets.QErrorMessage()
        self.setupUiStart(self)
        self.initUi()
        self.pushButtonAdd.clicked.connect(self.openWinAddServices)
        self.pushButtonView.clicked.connect(self.openWinView)
        self.createConfig()
        self.conn = sqlite3.connect(self.createConfig()[0])
        self.cursor = self.conn.cursor()

    def initUi(self):
        self.setWindowIcon(QIcon('main.png'))

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

        self.addForm = addForm(self.conn, self.cursor, self.createConfig()[1], self.createConfig()[0], self)
        self.addForm.show()

    def openWinView(self):

        self.viewAllForm = viewAllForm(self.createConfig()[0], self.createConfig()[1], self.conn, self.cursor, self)
        self.viewAllForm.show()


class addForm(QtWidgets.QMainWindow, addFormUi.Ui_addFormUi):
    def __init__(self, conn, cursor, pathFolder, pathDb, parent=None):
        super(addForm, self).__init__(parent)
        self.parent = parent
        self.conn = conn
        self.cursor = cursor
        self.pathFolder = pathFolder
        self.pathDb = pathDb
        self.setupUiAddForm(self)
        self.pushButton.clicked.connect(self.insertInfo)
        self.winStart = None
        self.initUi()

    def initUi(self):
        self.setWindowIcon(QIcon('new.png'))

    def getFolder(self):  # получение полного пути до созданной директории
        provide = self.comboBoxProvideServices.itemText(self.comboBoxProvideServices.currentIndex())
        city = self.comboBoxCity.itemText(self.comboBoxCity.currentIndex())
        address = self.lineEditAddress.text()
        fullPathToDir = os.path.join(self.pathFolder, provide, city, address)
        return os.path.abspath(fullPathToDir)

    def AllClear(self):
        self.lineEditAddress.clear()
        self.lineEditSurname.clear()
        self.lineEditName.clear()
        self.lineEditMiddleName.clear()
        self.lineEditTelefone.clear()
        self.lineEditSnils.clear()
        self.lineEditPrice.clear()
        self.textEditPassport.clear()
        self.textEditInfo.clear()

    def insertInfo(self):  # добавление информации в БД
        try:
            buttonReply = QMessageBox.question(self, 'Подтверждение действия', "Добавить запись?",
                                               QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if buttonReply == QMessageBox.Yes:
                mass = [(self.comboBoxProvideServices.itemText(self.comboBoxProvideServices.currentIndex()),
                         self.comboBoxCity.itemText(self.comboBoxCity.currentIndex()), self.lineEditAddress.text(),
                         self.lineEditSurname.text(), self.lineEditName.text(), self.lineEditMiddleName.text(),
                         self.lineEditTelefone.text(), self.lineEditSnils.text(), self.textEditPassport.toPlainText(),
                         self.dateEditDate.text(), self.lineEditPrice.text(), self.textEditInfo.toPlainText(),
                         self.comboBoxStatus.itemText(self.comboBoxStatus.currentIndex()),
                         self.comboBoxWork.itemText(self.comboBoxWork.currentIndex()),
                         self.dateEditDataWork.text(), os.path.abspath(self.getFolder()))]
                self.conn.executemany("INSERT INTO statement VALUES (null,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)", mass)
                os.makedirs(self.getFolder())  # создание директории по заданному пути
                self.openFolder()  # открытие созданной директории
                if self.conn.commit():
                    msg = QMessageBox()
                    msg.setIcon(QMessageBox.Information)
                    msg.setWindowTitle("Информация")
                    msg.setText("Данные успешно добавлены")
                    msg.addButton('Ok', QMessageBox.AcceptRole)
                    msg.exec()
                self.AllClear()  # очистка всех полей
        except FileExistsError as text:
            QMessageBox.critical(self, "Ошибка ", str(text), QMessageBox.Ok)
            self.conn.rollback()

    def openFolder(self):  # открыть директорию, указанную в БД
        try:
            os.startfile(self.getFolder())
        except FileNotFoundError as text:
            QMessageBox.critical(self, "Ошибка ", str(text), QMessageBox.Ok)


class viewSelectForm(QtWidgets.QMainWindow, viewSelectFormUi.Ui_viewSelectFormUi):
    def __init__(self, conn, cursor, pathFolder, pathDb, parent=None):
        super(viewSelectForm, self).__init__(parent)
        self.parent = parent
        self.setupUiSelectForm(self)
        self.conn = conn
        self.cursor = cursor
        self.pathFolder = pathFolder
        self.pathDb = pathDb
        self.pushButtonOpenFolder.clicked.connect(self.openFolder)
        self.pushButton.clicked.connect(self.updateInfo)
        self.massUpdate = ()
        self.comboBoxProvideServices.setEnabled(False)
        self.lineEditAddress.setEnabled(False)
        self.comboBoxCity.setEnabled(False)
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())
        self.initUi()

    def initUi(self):
        self.setWindowIcon(QIcon('edit.png'))

    def fillInfo(self, mass):  # копирование и воод информации о выделенной заявке
        self.massUpdate = mass
        fullDateD = mass[0][10]
        dayD = int(fullDateD[0:2])
        mouthD = int(fullDateD[3:5])
        yearD = int(fullDateD[6:10])

        fullDateDD = mass[0][15]
        dayDD = int(fullDateDD[0:2])
        mouthDD = int(fullDateDD[3:5])
        yearDD = int(fullDateDD[6:10])

        getIndexServices = self.comboBoxProvideServices.findText(mass[0][1])
        getIndexCity = self.comboBoxCity.findText(mass[0][2])
        getIndexStatus = self.comboBoxStatus.findText(mass[0][13])
        getIndexWork = self.comboBoxWork.findText(mass[0][14])

        date = QDate(yearD, dayD, mouthD)
        dateD = QDate(yearDD, dayDD, mouthDD)

        self.comboBoxProvideServices.setCurrentIndex(getIndexServices)
        self.comboBoxCity.setCurrentIndex(getIndexCity)
        self.lineEditAddress.setText(mass[0][3])
        self.lineEditSurname.setText(mass[0][4])
        self.lineEditName.setText(mass[0][5])
        self.lineEditMiddleName.setText(mass[0][6])
        self.lineEditTelefone.setText(mass[0][7])
        self.lineEditSnils.setText(mass[0][8])
        self.textEditPassport.setText(mass[0][9])
        self.dateEditDate.setDate(date)
        self.lineEditPrice.setText(mass[0][11])
        self.textEditInfo.setText(mass[0][12])
        self.comboBoxStatus.setCurrentIndex(getIndexStatus)
        self.comboBoxWork.setCurrentIndex(getIndexWork)
        self.dateEditDataWork.setDate(dateD)
        self.getPathFolder = mass[0][16]

        return mass

    def getFolder(self):  # получение полного пути до созданной директории
        provide = self.comboBoxProvideServices.itemText(self.comboBoxProvideServices.currentIndex())
        city = self.comboBoxCity.itemText(self.comboBoxCity.currentIndex())
        address = self.lineEditAddress.text()
        provide.strip(' ')
        city.strip(' ')
        address.strip(' ')
        fullPathToDir = os.path.join(self.pathFolder, provide, city, address)
        return os.path.abspath(fullPathToDir)

    def openFolder(self):  # открыть директорию, указанную в БД
        try:
            os.startfile(self.getFolder())
        except FileNotFoundError as text:
            QMessageBox.critical(self, "Ошибка ", str(text), QMessageBox.Ok)

    def closeEvent(self, event):
        self.close()
        self.viewAllForm = viewAllForm(self.pathDb, self.pathFolder, self.conn, self.cursor)
        self.viewAllForm.show()

    def updateInfo(self):
        buttonReply = QMessageBox.question(self, 'Подтверждение действия', "Обновить данную запись?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        id = self.massUpdate[0][0]
        name = self.lineEditName.text()
        surName = self.lineEditSurname.text()
        middleName = self.lineEditMiddleName.text()
        telefone = self.lineEditTelefone.text()
        snils = self.lineEditSnils.text()
        passport = self.textEditPassport.toPlainText()
        dataStart = self.dateEditDate.text()
        price = self.lineEditPrice.text()
        info = self.textEditInfo.toPlainText()
        status = self.comboBoxStatus.itemText(self.comboBoxStatus.currentIndex())
        work = self.comboBoxWork.itemText(self.comboBoxWork.currentIndex())
        dateWork = self.dateEditDataWork.text()

        if buttonReply == QMessageBox.Yes:
            self.cursor.execute("UPDATE statement SET name=?,surName=?,middleName=?,telefone=?,snils=?,passport=?,"
                                "dateStart=?,price=?,info=?,status=?,work=?,dateWork=? WHERE id=?",
                                (name, surName, middleName, telefone, snils, passport, dataStart, price, info, status,
                                 work, dateWork, id,))
            if self.conn.commit():
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Information)
                msg.setWindowTitle("Информация")
                msg.setText("Данные успешно изменены")
                msg.addButton('Ok', QMessageBox.AcceptRole)
                msg.exec()


class viewAllForm(QtWidgets.QMainWindow, viewAllFormUi.Ui_viewAllFormUi):
    def __init__(self, pathDb, pathFolder, conn, cursor, parent=None):
        super(viewAllForm, self).__init__(parent)
        self.parent = parent
        self.pathDb = pathDb
        self.pathFolder = pathFolder
        self.conn = conn
        self.cursor = cursor
        self.setupUiAllForm(self)
        self.getAllRecord()
        self.tableWidget.itemDoubleClicked.connect(self.openFullInfo)
        self.pushButtonDelete.clicked.connect(self.deleteRecord)
        self.initUi()
        self.pushButtonSearch.clicked.connect(self.searchInfo)
        self.pushButtonUpdate.clicked.connect(self.getAllRecord)
        self.calendarWidget.clicked.connect(self.calendarWork)
    def searchInfo(self):
        text = '%'+self.lineEditSearch.text()+'%'
        self.cursor.execute("select id from statement where address || surname || telefone || services || city like ?", (text,))
        result = self.cursor.fetchall()
        self.cursor.execute("select * from statement where id = ?", result[0])
        records = self.cursor.fetchall()
        self.fillRecord(records)

    def initUi(self):
        self.setWindowIcon(QIcon('BD.png'))
        self.tableWidget.setSortingEnabled(True)
        self.tableWidget.verticalHeader().hide()

    def deleteRecord(self):
        currentRowSelect = self.tableWidget.currentRow()
        getNumber = self.tableWidget.item(currentRowSelect, 10).text()
        buttonReply = QMessageBox.question(self, 'Подтверждение действия', "Удалить выбранную запись?",
                                           QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
        if buttonReply == QMessageBox.Yes:
            self.cursor.execute("DELETE FROM statement WHERE id=?", (getNumber,))
            self.conn.commit()
            self.getAllRecord()

    def colorItem(self, item, text):
        if text == "Срочно":
            item.setBackground(QtGui.QColor(240, 128, 0))
        if text == "Обычно":
            item.setBackground(QtGui.QColor(134, 250, 45))
        if text == "В ожидании":
            item.setBackground(QtGui.QColor(236, 240, 0))
        if text == "Ожидает выезд":
            item.setBackground(QtGui.QColor(240, 128, 0))
        if text == "В обработке":
            item.setBackground(QtGui.QColor(236, 240, 0))
        if text == "Готова":
            item.setBackground(QtGui.QColor(134, 250, 45))

    def fillRecord(self, records):
        self.tableWidget.setRowCount(len(records))
        self.tableWidget.hideColumn(10)
        for i in range(len(records)):
            for j in range(6):
                item = QTableWidgetItem()
                self.colorItem(item, records[i][13])
                item.setText(str(records[i][13]))  # статус
                self.tableWidget.setItem(i, 0, item)
                item = QTableWidgetItem()
                self.colorItem(item, records[i][14])
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
                item.setText(str(records[i][0]))  # id
                self.tableWidget.setItem(i, 10, item)

    def getAllRecord(self):
        self.cursor.execute("SELECT * from statement")
        records = self.cursor.fetchall()
        self.fillRecord(records)

    def openFullInfo(self):

        currentRowSelect = self.tableWidget.currentRow()
        getNumber = self.tableWidget.item(currentRowSelect, 10).text()

        self.cursor.execute("SELECT * from statement where id = ?", (getNumber,))
        mass = self.cursor.fetchall()
        self.viewSelectForm = viewSelectForm(self.conn, self.cursor, self.pathFolder, self.pathDb, self)
        self.viewSelectForm.fillInfo(mass)
        self.viewSelectForm.show()
        self.hide()

    def calendarWork(self):
        dateSelect = self.calendarWidget.selectedDate().toString("dd.MM.yyyy")
        self.cursor.execute("select dateStart from statement")
        dateStart = self.cursor.fetchall()
        date = QDate()
        color = QColor()
        brush = QBrush()
        form = QTextCharFormat()

        for month in dateStart:
            if str(month[0])[3:10] == dateSelect[3:10]:
                self.cursor.execute("select * from statement where dateStart = ?", month)
                result = self.cursor.fetchall()
                for status in result:
                    if status[14] == 'Готова':
                        color.setRgb(134, 250, 45)
                        break
                    elif status[14] == 'В обработке':
                        color.setRgb(236, 240, 0)
                        break
                    elif status[14] == 'Ожидает выезд':
                        color.setRgb(240, 128, 0)
                        break
                year = str(month[0])[6:10]
                mnt = str(month[0])[3:5]
                day = str(month[0])[0:2]
                date.setDate(int(year),int(mnt),int(day))
                brush.setColor(color)
                form.setBackground(brush)
                self.calendarWidget.setDateTextFormat(date,form)

class checkAndUpdate():
    #проверка файлов по размеру(то что имеется, относительно того что есть в репозитории)
    #батники для каждого окна
    #батник для сборки
    #возможность скачивания через НЕ основной аккаунт

    pass


def main():
    app = QtWidgets.QApplication(sys.argv)
    window = startWindow()
    window.show()
    app.exec_()


if __name__ == "__main__":
    main()
