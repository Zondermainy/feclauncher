import shutil

from PyQt5.QtCore import QThread, pyqtSignal, QSize, Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QSpacerItem, QSizePolicy, \
    QProgressBar, QPushButton, QMainWindow, QApplication, QErrorMessage, QMessageBox
from PyQt5.QtGui import QPixmap, QIcon

from minecraft_launcher_lib.utils import get_minecraft_directory, get_version_list
from minecraft_launcher_lib.install import install_minecraft_version
from minecraft_launcher_lib.command import get_minecraft_command

from random_username.generate import generate_username
from uuid import uuid1

from subprocess import call
from sys import argv, exit

minecraft_directory = get_minecraft_directory().replace('minecraft', 'feclauncher')


class LaunchThread(QThread):
    launch_setup_signal = pyqtSignal(str, str)
    progress_update_signal = pyqtSignal(int, int, str)
    state_update_signal = pyqtSignal(bool)

    version_id = ''
    username = ''

    progress = 0
    progress_max = 0
    progress_label = ''

    def __init__(self):
        super().__init__()
        self.launch_setup_signal.connect(self.launch_setup)

    def launch_setup(self, version_id, username):
        self.version_id = version_id
        self.username = username


        if username == '':
            self.username = generate_username()[0]

        for symbol in [' ', '!', '@', '#', '$', '%', '^', '&', '*', '(', ')', '-', '+', '=', '{', '}', '[', ']',
                           '/', '|', ';', ':', "'", '<', '>', ',', '.', '/', '?']:

            if symbol in username:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Critical)
                msg.setText("Неверный ник!")
                msg.setInformativeText('Никнейм должен содержать только символы A-Z, Нижнее подчеркивание, цифры 0-9')
                msg.setWindowTitle("Обнаружены недопустимые символы в никнейме")
                msg.exec_()
                return


    def update_progress_label(self, value):
        self.progress_label = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def update_progress(self, value):
        self.progress = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def update_progress_max(self, value):
        self.progress_max = value
        self.progress_update_signal.emit(self.progress, self.progress_max, self.progress_label)

    def run(self):
        self.state_update_signal.emit(True)

        install_minecraft_version(versionid=self.version_id, minecraft_directory=minecraft_directory,
                                  callback={'setStatus': self.update_progress_label,
                                            'setProgress': self.update_progress, 'setMax': self.update_progress_max})

        options = {
            'username': self.username,
            'uuid': str(uuid1()),
            'token': ''
        }

        source_path = "_internal/servers.dat"
        destination_path = "C:/users/user/appdata/roaming/.feclauncher/servers.dat"

        shutil.copyfile(source_path, destination_path)

        call(get_minecraft_command(version=self.version_id, minecraft_directory=minecraft_directory, options=options))
        self.state_update_signal.emit(False)


class MainWindow(QMainWindow):

    def __init__(self):
        super().__init__()
        self.setWindowTitle('FEC Launcher v0.1')
        self.setWindowIcon(QIcon('_internal/minilogo.ico'))

        self.resize(400, 450)
        self.centralwidget = QWidget(self)

        self.logo = QLabel(self.centralwidget)
        self.logo.setMaximumSize(QSize(293, 171))
        self.logo.setText('')
        self.logo.setPixmap(QPixmap('_internal/FECL_Logo.png'))
        self.logo.setScaledContents(True)

        self.titlespacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.username = QLineEdit(self.centralwidget)
        self.username.setPlaceholderText('Никнейм')

        self.version_select = QComboBox(self.centralwidget)

        for version in get_version_list():
            if version['id'] not in ['1.16.5', '1.20.1']:
                continue
            else:
                self.version_select.addItem(version['id'])

        self.progress_spacer = QSpacerItem(20, 80, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Minimum)

        self.start_progress_label = QLabel(self.centralwidget)
        self.start_progress_label.setText('')
        self.start_progress_label.setVisible(False)

        self.start_progress = QProgressBar(self.centralwidget)
        self.start_progress.setProperty('value', 0)
        self.start_progress.setVisible(False)

        self.start_button = QPushButton(self.centralwidget)
        self.start_button.setText('Играть')
        self.start_button.clicked.connect(self.launch_game)

        self.vertical_layout = QVBoxLayout(self.centralwidget)
        self.vertical_layout.setContentsMargins(15, 15, 15, 15)
        self.vertical_layout.addWidget(self.logo, 0, Qt.AlignmentFlag.AlignHCenter)
        self.vertical_layout.addItem(self.titlespacer)
        self.vertical_layout.addWidget(self.username)
        self.vertical_layout.addWidget(self.version_select)
        self.vertical_layout.addItem(self.progress_spacer)
        self.vertical_layout.addWidget(
            self.start_progress_label)
        self.vertical_layout.addWidget(self.start_progress)
        self.vertical_layout.addWidget(self.start_button)

        self.launch_thread = LaunchThread()
        self.launch_thread.state_update_signal.connect(self.state_update)
        self.launch_thread.progress_update_signal.connect(self.update_progress)

        self.setCentralWidget(self.centralwidget)

    def state_update(self, value):
        self.start_button.setDisabled(value)
        self.start_progress_label.setVisible(value)
        self.start_progress.setVisible(value)

    def update_progress(self, progress, max_progress, label):
        self.start_progress.setValue(progress)
        self.start_progress.setMaximum(max_progress)
        self.start_progress_label.setText(label)

    def launch_game(self):
        self.launch_thread.launch_setup_signal.emit(self.version_select.currentText(), self.username.text())
        self.launch_thread.start()



if __name__ == '__main__':
    QApplication.setAttribute(Qt.ApplicationAttribute.AA_EnableHighDpiScaling, True)

    app = QApplication(argv)
    window = MainWindow()
    window.show()

    exit(app.exec_())
