import sys
from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QListWidget
from PyQt5.QtCore import Qt

class FileDropWidget(QListWidget):
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.addItem("Перетащите файлы сюда для загрузки")

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event):
        self.clear()
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            self.addItem(file_path)

class VectorBaseUploader(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Загрузка материалов для векторной базы")
        self.resize(400, 300)
        layout = QVBoxLayout()

        instruction_label = QLabel("Загрузите текстовые материалы (PDF, DOCX, TXT):")
        instruction_label.setAlignment(Qt.AlignCenter)

        self.file_drop_widget = FileDropWidget()

        layout.addWidget(instruction_label)
        layout.addWidget(self.file_drop_widget)

        self.setLayout(layout)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = VectorBaseUploader()
    window.show()
    sys.exit(app.exec_())
