import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFileDialog
)

class VideoCompilationGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Сведение видео")
        self.resize(500, 400)

        layout = QVBoxLayout()

        # Текст конспекта
        self.consp_label = QLabel("Текст конспекта:")
        self.consp_button = QPushButton("Открыть текст")
        self.consp_path = QLabel("Файл не выбран")
        self.consp_button.clicked.connect(self.select_consp_file)

        # Презентация
        self.pres_label = QLabel("Презентация:")
        self.pres_button = QPushButton("Открыть презентацию")
        self.pres_path = QLabel("Файл не выбран")
        self.pres_button.clicked.connect(self.select_pres_file)

        # Файл аудио
        self.audio_label = QLabel("Файл аудио:")
        self.audio_button = QPushButton("Открыть аудио")
        self.audio_path = QLabel("Файл не выбран")
        self.audio_button.clicked.connect(self.select_audio_file)

        # Сохранение видео
        self.save_label = QLabel("Путь сохранения итогового видео:")
        self.save_button = QPushButton("Сохранить видео")
        self.save_path = QLabel("Путь не выбран")
        self.save_button.clicked.connect(self.select_save_path)

        # Ход работы
        self.status_label = QLabel("Ход работы:\nЗагрузка материалов: -\nОбработка данных: -\nСведение видео: -")

        # Запуск сведения
        self.start_button = QPushButton("Запустить сведение")
        self.start_button.clicked.connect(self.start_compilation)

        # Размещение виджетов
        layout.addWidget(self.consp_label)
        layout.addWidget(self.consp_button)
        layout.addWidget(self.consp_path)

        layout.addWidget(self.pres_label)
        layout.addWidget(self.pres_button)
        layout.addWidget(self.pres_path)

        layout.addWidget(self.audio_label)
        layout.addWidget(self.audio_button)
        layout.addWidget(self.audio_path)

        layout.addWidget(self.save_label)
        layout.addWidget(self.save_button)
        layout.addWidget(self.save_path)

        layout.addWidget(self.status_label)
        layout.addWidget(self.start_button)

        self.setLayout(layout)

    def select_consp_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Выбрать текстовый файл", "", "Text Files (*.txt)")
        if file:
            self.consp_path.setText(file)

    def select_pres_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Выбрать презентацию", "", "PowerPoint Files (*.pptx)")
        if file:
            self.pres_path.setText(file)

    def select_audio_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Выбрать аудиофайл", "", "Audio Files (*.mp3 *.wav)")
        if file:
            self.audio_path.setText(file)

    def select_save_path(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить видео как", "", "Video Files (*.mp4)")
        if path:
            self.save_path.setText(path)

    def start_compilation(self):
        self.status_label.setText(
            "Ход работы:\nЗагрузка материалов: [OK]\nОбработка данных: [50%]\nСведение видео: [Ожидает]"
        )

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = VideoCompilationGUI()
    window.show()
    sys.exit(app.exec_())
