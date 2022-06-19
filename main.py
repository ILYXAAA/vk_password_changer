from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtWidgets import QApplication, QFileDialog, QMessageBox, QProgressBar, QPushButton
from PyQt5.QtCore import Qt
import sys
import datetime
import time
from pykeepass import PyKeePass
import vk_api
import random

from prog import *
from lockscreen import *
from settings import *
from auth_dialog import *

class MyWin(QtWidgets.QMainWindow):
    def __init__(self, parent=None):
        QtWidgets.QWidget.__init__(self, parent)
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.pushButton_exit.clicked.connect(self.exit)
        self.ui.pushButton_settings.clicked.connect(self.show_settings)
        self.ui.pushButton_update_password.clicked.connect(self.update_password)

        global Dialog_lockscreen
        Dialog_lockscreen = QtWidgets.QMainWindow()
        self.lo = Ui_lockscreen_window()
        self.lo.setupUi(Dialog_lockscreen)
        self.lo.pushButton_exit.clicked.connect(self.exit)
        self.lo.pushButton_enter.clicked.connect(self.enter_pin)

        global Dialog_auth_code
        Dialog_auth_code = QtWidgets.QDialog()
        self.ac = Ui_Dialog_auth_code()
        self.ac.setupUi(Dialog_auth_code)
        self.ac.pushButton_accept.clicked.connect(self.auth_ok_button)
        self.ac.pushButton_cancel.clicked.connect(self.auth_ok_button)


        global Dialog_settings
        Dialog_settings = QtWidgets.QMainWindow()
        self.se = Ui_settings_window()
        self.se.setupUi(Dialog_settings)
        self.se.pushButton_back.clicked.connect(self.cancel_settings)
        self.se.pushButton_yes.clicked.connect(self.auth_yes)
        self.se.pushButton_no.clicked.connect(self.auth_no)
        self.se.pushButton_show_password.clicked.connect(self.view_password)
        self.se.pushButton_clear_password.clicked.connect(self.clear_password)
        self.se.pushButton_set_password.clicked.connect(self.set_password)


        with open('auth.txt', 'r') as file:
            global is_a_auth
            is_a_auth = file.readline()

    def closeEvent(self, event):
        reply = QtWidgets.QMessageBox.question \
            (self, 'Информация',
             "Вы уверены, что хотите выйти?",
             QtWidgets.QMessageBox.Yes,
             QtWidgets.QMessageBox.No)
        if reply == QtWidgets.QMessageBox.Yes:
            event.accept()
            Dialog_settings.close()
            Dialog_auth_code.close()
            Dialog_lockscreen.close()
        else:
            event.ignore()

    def set_password(self):
        if len(self.se.lineEdit_set_vk_password.text()) != 0:
            with open('psswd.txt', 'w') as file:
                file.write(self.se.lineEdit_set_vk_password.text()[3:len(self.se.lineEdit_set_vk_password.text())])
                file.close()
            self.msg_info("Новый пароль был установлен!")
        else:
            self.msg_warn("Вы не ввели никаких данных для изменения пароля!")

    def clear_password(self):
        with open('psswd.txt', 'w') as file:
            file.write('')
        with open('login.txt', 'w') as file:
            file.write('')
        self.msg_info("Пароль и логин были стёрты из приложения!")

    def view_password(self):
        with open('psswd.txt', 'r') as file:
            passwoord = file.readline()
        self.se.lineEdit_vk_password.setText(str(app_password) + str(passwoord))

    def auth_ok_button(self):
        if len(self.ac.lineEdit_auth_code.text()) == 6:
            Dialog_auth_code.close()
        else:
            self.msg_warn("Вы неправильно ввели код. Проверьте пожалуйста.")

    def auth_yes(self):
        with open('auth.txt', 'w') as file:
            file.write('yes')
        self.msg_info('Настройки изменены!')

    def auth_no(self):
        with open('auth.txt', 'w') as file:
            file.write('no')
        self.msg_info('Настройки изменены!')

    def cancel_settings(self):
        Dialog_settings.close()

    def enter_pin(self):
        global app_password
        app_password = self.lo.lineEdit_pin.text()
        Dialog_lockscreen.close()

    def show_settings(self):
        Dialog_settings.show()
        Dialog_settings.activateWindow()

    def write_password(self, new_password):
        with open('psswd.txt', 'w') as file:
            file.write(new_password[3:len(new_password)])

    def auth_handler(self):
        """ При двухфакторной аутентификации вызывается эта функция.
        """
        self.msg_warn('У вас включена двухфакторная авторизация.' + '\n' + 'Сейчас вам придёт код, введите его в поле ниже')
        Dialog_auth_code.exec_()
        Dialog_auth_code.activateWindow()

        key = self.ac.lineEdit_auth_code.text()
        remember_device = False
        return key, remember_device

    def update_password(self):
        try:
            with open('login.txt', 'r') as file1:
                login = file1.readline()
            with open('psswd.txt', 'r') as file2:
                password = file2.readline()

            password = str(app_password) + str(password)
            print(password)
            old_password = app_password + password
            new_password = self.generate_password()

        except Exception as error_msg:
            self.msg_crit('Отсутствуют данные для авторизации')
            self.msg_crit(str(error_msg))
            return

        if is_a_auth.lower() == 'yes':
            try:
                vk_session = vk_api.VkApi(login, password,  # функция для обработки двухфакторной аутентификации
                                          auth_handler=self.auth_handler)
                time.sleep(5)

                vk_session.auth()
                time.sleep(5)
                vk = vk_session.get_api()
                print(new_password)
                time.sleep(5)

                vk.account.changePassword(old_password=old_password, new_password=new_password)
                print(new_password)
                self.msg_info('Успешно изменён')
                self.ui.lineEdit_new_password.setText(new_password)

                self.write_password(new_password)

                self.msg_info("Запомните первые 3 символа пароля. Это будет код для входа в приложение")


            except Exception as error_msg:
                self.msg_crit(str(error_msg))

        else:
            try:
                vk_session = vk_api.VkApi(login, password)
                vk_session.auth()
                vk = vk_session.get_api()

                vk.account.changePassword(old_password=old_password, new_password=new_password)
                self.msg_info('Успешно изменён')
                self.ui.lineEdit_new_password.setText(new_password)

                new_password = self.crypt(new_password)
                with open('password.txt', 'w') as file:
                    file.write(new_password)

            except Exception as error_msg:
                self.msg_crit(str(error_msg))

    def msg_warn(self, text):
        QMessageBox.warning(self, "Предупреждение ",
                            text, QMessageBox.Ok)
    def msg_crit(self, text):
        QMessageBox.critical(self, "Ошибка ",
                            text, QMessageBox.Ok)
    def msg_info(self, text):
        QMessageBox.information(self, "Информация ",
                            text, QMessageBox.Ok)


    def generate_password(self):
        chars = "abcdefghijklnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ1234567890#&!@%"
        number = 1
        length = 20
        for n in range(number):
            new_password =''
            for i in range(length):
                new_password += random.choice(chars)

        return new_password


    def exit(self):
        myapp.close()







if __name__=="__main__":
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    myapp = MyWin()
    myapp.show()
    Dialog_lockscreen.show()
    sys.exit(app.exec_())
