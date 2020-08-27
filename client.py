import socket
import threading
import sys
import contextlib
import json
import webbrowser

from PyQt5.QtWidgets import QLineEdit, QGridLayout, QFrame, QTextEdit, QListWidget, QListWidgetItem, QFormLayout, QMainWindow, QProgressBar, QWidget, QApplication, QGroupBox, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QPushButton, QDialog
from PyQt5.QtGui import QIcon, QFont, QCursor, QBrush, QColor
from PyQt5.QtCore import QRect, QSize, QTimer, QTime, QThread, pyqtSignal, Qt


lock = threading.Lock()

@contextlib.contextmanager
def wait_until_send(widget):
    try:
        lock.acquire()
        yield
    finally:
        lock.release()


class MWindow(QWidget, threading.Thread):
    def __init__(self):
        QWidget.__init__(self)
        threading.Thread.__init__(self)

        with open("config.json", "r") as file:
            config = json.load(file)

        HOST = config["HOST_CLIENT"]
        PORT = config["PORT"]
        self.BUFSIZ = config["BUFSIZ"]

        self.client_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client_sock.connect((HOST, PORT))

        self.color_message = {
            "&b":"blue",
            "&g":"green",
            "&o":"orange",
            "&p":"purple",
            "&r":"red",
            "&y":"yellow"
        }

        self.color_message_prefix = {
            self.color_message[key] : key for key in self.color_message.keys()
        }

        self.prefix_color = ""

        self.setWindowTitle("Chatter")
        self.setGeometry(0, 0, 300, 500)
        self.setWindowIcon(QIcon("serv_disc.png"))
        self.setStyleSheet("background-color:#dddddd")

        self.lastrow = -1

        self.main_layout = QGridLayout()

        self.initUi()
        self.set_all_layout()

        self.show()

    def set_all_layout(self):
        
        self.main_layout.addWidget(self.listwidget)

        self.bar = QHBoxLayout()
        self.main_layout.addWidget(self.count_label)
        self.main_layout.addWidget(self.entry_message)
        self.bar.addWidget(self.send_button)
        self.bar.addWidget(self.delete_button)
        self.bar.addWidget(self.label_player_number)

        self.main_layout.addLayout(self.bar, 3, 0, 3, 0)

    def initUi(self):

        self.listwidget = QListWidget()
        self.listwidget.resize(300,120)
        self.listwidget.setStyleSheet("width:200px")

        self.entry_message = QLineEdit()
        self.entry_message.setGeometry(0, 0, 10, 10)
        #self.entry_message.setMaxLength(100)
        self.entry_message.setFont(QFont("Arial",20))
        self.entry_message.setStyleSheet('''
            background-color:white;
            border-radius:10px;
            border:1px solid black;
            width:200px;
        ''')
    
    

        self.send_button = QPushButton("Send", self)
        self.send_button.setFont(QFont("Comic sans ms", 15))
        self.send_button.clicked.connect(self.send_socket_message)

        self.delete_button = QPushButton("Delete", self)
        self.delete_button.setFont(QFont("Comic sans ms", 15))
        self.delete_button.clicked.connect(self.delete_no_socket_message)

        def setStyle(bg, fg="white"):
            return f"background-color:{bg};color:{fg};border-radius:10px;border:3px solid white;"

        self.send_button.setStyleSheet(setStyle("blue"))
        self.delete_button.setStyleSheet(setStyle("orange"))

        self.send_button.setCursor(QCursor(Qt.PointingHandCursor))
        self.delete_button.setCursor(QCursor(Qt.PointingHandCursor))

        def addtime():
            self.count = self.count.addSecs(1)
            self.count_label.setText(f"Tu es connecté depuis : {self.count.toString('hh:mm:ss')}")


        self.count = QTime(00,00,00)

        self.count_label = QLabel(f"Tu es connecté depuis : {self.count.toString('hh:mm:ss')}", self)
        self.count_label.setGeometry(QRect(500, 500, 100, 50))

        self.timer = QTimer()
        self.timer.timeout.connect(addtime)
        self.timer.start(1000)

        

        self.label_player_number = QLabel("", self)
        self.label_player_number.setStyleSheet("font-size:20px")
        self.label_player_number.hide()

        


        self.setLayout(self.main_layout)

    def openLink(self, link):
        webbrowser.open_new(link)

    def addListItem(self, item):
        self.listwidget.addItem(item)
        self.lastrow += 1

                
        if ":" not in item:
            return

        islink = item[item.index(":")+1:].strip() # in future add a QWidgetItem.signal if selected().startswith("https://") : open_new("...")


        if islink.startswith("http://") or islink.startswith("https://"):
            listitem = self.listwidget.item(self.lastrow)
            listitem.setForeground(QBrush(QColor("blue")))
            #listitem.clicked.connect(lambda:self.openLink(islink))

    def removeListItem(self, item):
        self.listwidget.takeItem(self.listwidget.row(item))
        self.lastrow -= 1

    def run(self):
        " Thread run on new message send to this current client "
        while True:
            try:
                msg = self.client_sock.recv(self.BUFSIZ).decode("utf8")
                msg_split = msg.split(":")
                author = msg_split[0]
                message = "".join(msg_split[1:]).strip()
                

                if msg.startswith("<YOTfb3po7lBNv19in6yC>"):
                    self.label_player_number.show()
                    self.label_player_number.setText(msg.split("/")[1] + "/5") # 5 : connection max to server
                else:
                    case = ["&b", "&g", "&o", "&p", "&r", "&y"]
                    color = message[:2]


                    if not color in case:
                        self.addListItem(msg)
                        continue

                    self.addListItem(f"{author}: {message[2:]}")
                    listitem = self.listwidget.item(self.lastrow)

                    
                    listitem.setForeground(QBrush(QColor(self.color_message[color])))
                    

            except OSError:
                break

    def send_socket_message(self, msg=None):
        msg = msg or self.entry_message.text()

        if not msg:
            return

        self.entry_message.clear()

        if msg.startswith("/color"):
            color = msg.split()[1]
            if color not in self.color_message.values():
                self.addListItem(f"-> Color not enable. {''.join(self.color_message.values())}")
            else:
                self.prefix_color = self.color_message_prefix[color]
                self.addListItem(f"-> Your messages color is now {color} !")
            return

        # check (if not self.prefix_color)
        if msg[:2] in self.color_message.keys():
            to_send = msg
        else:
            to_send = self.prefix_color + msg

        self.client_sock.send(to_send.encode("utf8"))
        
        if msg == "/quit":
            self.client_sock.close()
            app.quit()


    def delete_no_socket_message(self): # delete only in this user interface
        messages_to_delete = self.listwidget.selectedItems()
        if not messages_to_delete:
            return
        for message in messages_to_delete:
           self.removeListItem(message)




if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MWindow()
    win.start()

    app.aboutToQuit.connect(lambda : win.send_socket_message("/quit"))
    sys.exit(app.exec_())