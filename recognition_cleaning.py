import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QTextEdit,
    QFileDialog, QVBoxLayout
)

class RecognitionCleaningGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Распознавание и очистка текста")
        self.resize(600, 500)

        layout = QVBoxLayout()

        self.select_audio_btn = QPushButton("Открыть аудиофайл")
        self.audio_path_label = QLabel("Файл не выбран")
        self.recognize_btn = QPushButton("Распознать")
        self.recognized_text_label = QLabel("Распознанный текст:")
        self.recognized_text_area = QTextEdit()
        self.recognized_text_area.setPlaceholderText("Здесь появится распознанный текст...")

        self.clean_btn = QPushButton("Очистить текст")
        self.cleaned_text_label = QLabel("Очищенный текст:")
        self.cleaned_text_area = QTextEdit()
        self.cleaned_text_area.setPlaceholderText("Здесь появится очищенный текст...")

        layout.addWidget(self.select_audio_btn)
        layout.addWidget(self.audio_path_label)
        layout.addWidget(self.recognize_btn)
        layout.addWidget(self.recognized_text_label)
        layout.addWidget(self.recognized_text_area)
        layout.addWidget(self.clean_btn)
        layout.addWidget(self.cleaned_text_label)
        layout.addWidget(self.cleaned_text_area)

        self.setLayout(layout)

        self.select_audio_btn.clicked.connect(self.select_audio)
        self.recognize_btn.clicked.connect(self.recognize_text)
        self.clean_btn.clicked.connect(self.clean_text)

    def select_audio(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать аудиофайл", "", "Аудио (*.mp3 *.wav)")
        if file_path:
            self.audio_path_label.setText(file_path)

    def recognize_text(self):
        # Заглушка для распознанного текста
        dummy_text = "Эмм... ну в общем, как бы, сегодня мы, типа, говорим про нейронные сети..."
        self.recognized_text_area.setText(dummy_text)

    def clean_text(self):
        raw = self.recognized_text_area.toPlainText()
        cleaned = raw.replace("Эмм", "").replace("как бы", "").replace("ну", "").replace("в общем", "").replace("типа", "").replace("...", ".")
        self.cleaned_text_area.setText(cleaned.strip())

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = RecognitionCleaningGUI()
    window.show()
    sys.exit(app.exec_())
