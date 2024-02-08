import socket
import threading
import sys
import contextlib
import yaml
import webbrowser

from PyQt6.QtWidgets import QStyledItemDelegate, QSpacerItem, QSizePolicy, QMessageBox, QInputDialog, QLineEdit, QGridLayout, QFrame, QTextEdit, QListWidget, QListWidgetItem, QFormLayout, QMainWindow, QProgressBar, QWidget, QApplication, QGroupBox, QHBoxLayout, QVBoxLayout, QLabel, QCheckBox, QPushButton, QDialog
from PyQt6.QtGui import QIcon, QFont,QFontDatabase, QCursor, QBrush, QColor
from PyQt6.QtCore import QRect, QSize, QTimer, QTime, QThread, pyqtSignal, Qt

import buttons


lock = threading.Lock()

@contextlib.contextmanager
def wait_until_send(widget): # not used.
    try:
        lock.acquire()
        yield
    finally:
        lock.release()

listAuthorMessage = []
limitPerLine = 20

class CustomItemDelegate(QStyledItemDelegate):
    def paint(self, painter, option, index):
        super().paint(painter, option, index)
        message_size = min(len(index.data(Qt.ItemDataRole.DisplayRole)), limitPerLine) # mod TAILLE MAX SUR UNE LIGNE
        if index.row() in listAuthorMessage:
            painter.setPen(QColor("white"))  
            painter.setBrush(QBrush(QColor("#f0f0f0")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(option.rect)
            painter.setPen(Qt.PenStyle.SolidLine)

            list_width = option.widget.viewport().width()  
            margin = 5  
            half_list_width = list_width // 2 + 100
            adjusted_rect = option.rect.adjusted(half_list_width-7*message_size, margin, -margin, -margin)

            painter.setPen(QColor("#f0f0f0"))
            painter.setBrush(QBrush(QColor("#17a2b8")))
            painter.drawRoundedRect(adjusted_rect, 5, 5)
            
            text_rect = adjusted_rect.adjusted(5, 0, 0, 0)  # Décalage de 5 pixels à gauche
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, index.data(Qt.ItemDataRole.DisplayRole))
        else:
            painter.setPen(QColor("white"))  
            painter.setBrush(QBrush(QColor("#f0f0f0")))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRect(option.rect)
            painter.setPen(Qt.PenStyle.SolidLine)

            list_width = option.widget.viewport().width()  
            margin = 5  
            half_list_width = list_width // 2 + 100
            adjusted_rect = option.rect.adjusted(1, margin, -half_list_width+7*message_size, -margin)

            painter.setPen(QColor("#17a2b8"))
            painter.setBrush(QBrush(QColor("white")))
            painter.drawRoundedRect(adjusted_rect, 5, 5)
            
            text_rect = adjusted_rect.adjusted(5, 0, 0, 0)  # Décalage de 5 pixels à gauche
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignVCenter, index.data(Qt.ItemDataRole.DisplayRole))


class MWindow(QWidget, threading.Thread):
    def __init__(self):
        QWidget.__init__(self)
        threading.Thread.__init__(self)

        with open("config.yaml", "r") as file:
            config = yaml.load(file, Loader=yaml.Loader)

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

        font_id = QFontDatabase.addApplicationFont("PoorStory-Regular.ttf")
        font_family = QFontDatabase.applicationFontFamilies(font_id)[0]

        self.custom_font = QFont(font_family, 12)
        self.custom_title_font = QFont(font_family, 16)

        self.setFont(self.custom_font)

        self.setWindowTitle("Proxichat")
        self.setGeometry(100, 100, 300, 500)
        self.setWindowIcon(QIcon("chat.png"))
        self.setStyleSheet("background-color:#dddddd")


        self.lastrow = -1

        self.main_layout = QGridLayout()

        self.initUi()
        self.set_all_layout()

        self.show()

    def set_all_layout(self):
        
        self.main_layout.addLayout(self.layoutLogo, 0, 0, 1, 0)

        layout = QGridLayout()

        layout.addWidget(self.entry_message, 0, 0, 1, 1)  # Ligne 0, Colonne 0, 2 lignes, 1 colonne

        layoutLabelPlayerNumber = QHBoxLayout()
        layoutLabelPlayerNumber.addWidget(self.label_player_number)  # Ligne 0, Colonne 0, 2 lignes, 1 colonne
        layoutLabelPlayerNumber.addStretch()
        layoutLabelPlayerNumber.addWidget(self.delete_button)  # Ligne 1, Colonne 1, 1 ligne, 1 colonne
        layout.addLayout(layoutLabelPlayerNumber, 1, 0, 1, 1)

        layout.addWidget(self.send_button, 0, 1, 1, 1)  # Ligne 0, Colonne 1, 1 ligne, 1 colonne
        layout.addWidget(self.edit_name_button, 1, 1, 1, 1)  # Ligne 1, Colonne 1, 1 ligne, 1 colonne

        chat_layout = QVBoxLayout()
        chat_layout.addWidget(self.listwidget)


        self.main_layout.addLayout(chat_layout, 1, 0, 1, 0)
        self.listwidget.setMinimumHeight(300)  # Ajustez cette valeur selon vos besoins
        self.listwidget.setMaximumHeight(1677215)

        self.main_layout.addWidget(self.count_label)
        self.main_layout.addLayout(layout, 3, 0, 1, 0)
        self.entry_message.setFocus()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key.Key_Return:
            self.send_socket_message()

    def initUi(self):
        self.logo = buttons.AppButton("chat2.png", (60, 60), (60, 60), "#dddddd")
        self.textLogo = QLabel("Proxichat")
        self.textLogo.setStyleSheet("color:#17a2b8;")

        self.textLogo.setFont(self.custom_title_font)

        self.logo.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)
        self.textLogo.setSizePolicy(QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Fixed)

        self.layoutLogo = QHBoxLayout()
        self.layoutLogo.addStretch()
        self.layoutLogo.addWidget(self.logo)
        self.layoutLogo.addWidget(self.textLogo)
        self.layoutLogo.addStretch()

        self.listwidget = QListWidget()
        self.listwidget.setStyleSheet("""
            QListWidget {
                background-color: #f0f0f0;
                border: 2px solid #17a2b8;
                border-radius: 10px;
                padding: 5px;
                font-size: 13px;
            }
            QListWidget::item {
                padding: 10px;
            }
            """)
        self.listwidget.setItemDelegate(CustomItemDelegate())
        

        self.listwidget.setFont(self.custom_font)

        # self.listwidget.resize(400,120)
        self.listwidget.setFixedHeight(300)
        #self.listwidget.setStyleSheet("""QListWidget {margin-top:1px}QListWidget::item { padding: 3px; }""")

        self.entry_message = QLineEdit()

        self.entry_message.setPlaceholderText("Enter your message here...")
        self.entry_message.setGeometry(0, 0, 10, 10)
        self.entry_message.setMaxLength(100)
        self.entry_message.setFont(self.custom_font)
        self.entry_message.setStyleSheet('''
            QLineEdit {
            color:white;
            background-color:#17a2b8;
            border-radius:7px;
            border:2px solid black;
            width:150px;
            padding:5px;
        }
        ''')
        self.entry_message.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        self.send_button = buttons.AppButton("send.png", (37, 37), (37, 37), "#17a2b8", "black")
        self.send_button.clicked.connect(self.send_socket_message)

        self.edit_name_button = buttons.AppButton("edit.png", (37, 37), (37, 37), "#fd7e14", "black")
        self.edit_name_button.clicked.connect(self.show_dialog)
        self.edit_name_button.setEnabled(False)

        self.delete_button = buttons.AppButton("chat.png", (37, 37), (37, 37), "#dc3545", "black")
        self.delete_button.clicked.connect(self.delete_no_socket_message)

        def addtime():
            self.count = self.count.addSecs(1)
            self.count_label.setText(f"Tu es en ligne depuis : {self.count.toString('hh:mm:ss')}")

        self.count = QTime(00, 00, 00)

        self.count_label = QLabel(f"Tu es en ligne depuis : {self.count.toString('hh:mm:ss')}", self)

        self.timer = QTimer()
        self.timer.timeout.connect(addtime)
        self.timer.start(1000)

        self.label_player_number = QLabel("", self)
        self.label_player_number.setStyleSheet("font-size:20px")
        self.label_player_number.hide()

        self.setLayout(self.main_layout)

    def openLink(self, link):
        webbrowser.open_new(link)

    def paginate_message(self, content):
        lst = [content[i:i+limitPerLine].strip() for i in range(0, len(content), limitPerLine)]
        return "\n".join(lst)


    def addListItem(self, item):
        print(item)
        self.listwidget.addItem(self.paginate_message(item))

        self.lastrow += 1
        listitem = self.listwidget.item(self.lastrow)
        self.listwidget.scrollToItem(self.listwidget.item(self.lastrow))

        if ":" not in item:
            return

        islink = item[item.index(":")+1:].strip() # in future add a QWidgetItem.signal if selected().startswith("https://") : open_new("...")

        if islink.startswith("http://") or islink.startswith("https://"):
            listitem = self.listwidget.item(self.lastrow)
            listitem.setForeground(QBrush(QColor("#17a2b8")))
            #listitem.clicked.connect(lambda:self.openLink(islink))

    def removeListItem(self, item):
        self.listwidget.takeItem(self.listwidget.row(item))
        self.lastrow -= 1

    def run(self):
        " Thread run on new message send to this current client "
        editNameBtnEnabledCounter = 0
        while True:
            try:
                msg = self.client_sock.recv(self.BUFSIZ).decode("utf8")
                msg_split = msg.split(":")
                author = msg_split[0]
                message = "".join(msg_split[1:]).strip()
                

                if msg.startswith("<YOTfb3po7lBNv19in6yC>"):
                    self.label_player_number.show()
                    self.label_player_number.setText(msg.split("/")[1] + "/5 en ligne") # 5 : connection max to server
                else:
                    editNameBtnEnabledCounter += 1;
                    if editNameBtnEnabledCounter == 2:
                        self.edit_name_button.setEnabled(True)

                    case = ["&b", "&g", "&o", "&p", "&r", "&y"]

                    if message == "":
                        color = msg[:2]
                        if not color in case:
                            self.addListItem(msg)
                        else:
                            self.addListItem(msg[2:])
                            listitem = self.listwidget.item(self.lastrow)                        
                            listitem.setForeground(QBrush(QColor(self.color_message[color])))
                    else:
                        color = message[:2]

                        if not color in case:
                            self.addListItem(msg)
                        else:
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


        if msg[:2] in ["&b", "&g", "&o", "&p", "&r", "&y"]:
            msgWithoutColors = msg[2:]
        else:
            msgWithoutColors = msg

        if msgWithoutColors == "/quit":
            app.aboutToQuit.disconnect()
            self.client_sock.send(msg.encode("utf8")) # msg ou msgWithoutColors ou meme to_send il capte que c'est un /quit
            self.client_sock.close() # crash window (2 client.close (one here and one in server.py))
            self.close()
            return

        # check (if not self.prefix_color)
        if msg[:2] in self.color_message.keys():
            to_send = msg
        else:
            to_send = self.prefix_color + msg

        self.addListItem(to_send)
        listAuthorMessage.append(self.lastrow)

        self.client_sock.send(to_send.encode("utf8"))
        

    def delete_no_socket_message(self): # delete only in this user interface
        messages_to_delete = self.listwidget.selectedItems()
        if not messages_to_delete:
            return
        for message in messages_to_delete:
           self.removeListItem(message)


    def show_dialog(self):
        text, ok_or_cancel = QInputDialog.getText(self, "Name modification", "New name:")

        if ok_or_cancel:
            if not text:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Critical)
                msg.setText("ERROR ON NAME")
                msg.setInformativeText("The name you enter has a bad format (it cannot be empty).")
                msg.setWindowTitle("Error")
                #msg.setWindowIcon(QMessageBox.Icon.Critical)
                msg.exec()
                return
            self.send_socket_message(f"/rename {text}")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = MWindow()
    win.start()

    app.aboutToQuit.connect(lambda : win.send_socket_message("/quit"))
    sys.exit(app.exec())