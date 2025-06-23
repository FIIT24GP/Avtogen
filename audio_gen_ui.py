import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QRadioButton, QFileDialog, QButtonGroup
)

class AudioGenerationGUI(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Генерация аудио")
        self.resize(500, 300)

        layout = QVBoxLayout()

        voice_layout = QHBoxLayout()
        self.voice_label = QLabel("Озвучивание:")
        self.voice_ksenia = QRadioButton("Ксения")
        self.voice_user = QRadioButton("Пользователь")
        self.voice_ksenia.setChecked(True)
        voice_group = QButtonGroup(self)
        voice_group.addButton(self.voice_ksenia)
        voice_group.addButton(self.voice_user)

        voice_layout.addWidget(self.voice_label)
        voice_layout.addWidget(self.voice_ksenia)
        voice_layout.addWidget(self.voice_user)

        file_layout = QHBoxLayout()
        self.file_label = QLabel("Файл с текстом:")
        self.file_button = QPushButton("Выбрать файл")
        self.file_path_label = QLabel("Файл не выбран")

        file_layout.addWidget(self.file_label)
        file_layout.addWidget(self.file_button)

        self.file_button.clicked.connect(self.select_file)

        self.status_label = QLabel("Ход работы:\nЗагружено: -\nОбрабатывается: -\nЗавершено: -")

        output_layout = QHBoxLayout()
        self.output_label = QLabel("Путь к папке выгрузки:")
        self.output_button = QPushButton("Выбрать папку")
        self.output_path_label = QLabel("Папка не выбрана")

        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_button)

        self.output_button.clicked.connect(self.select_folder)

        self.generate_button = QPushButton("Запустить генерацию")
        self.generate_button.clicked.connect(self.start_generation)

        layout.addLayout(voice_layout)
        layout.addLayout(file_layout)
        layout.addWidget(self.file_path_label)
        layout.addWidget(self.status_label)
        layout.addLayout(output_layout)
        layout.addWidget(self.output_path_label)
        layout.addWidget(self.generate_button)

        self.setLayout(layout)

    def select_file(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Выбрать файл с текстом", "", "Text Files (*.txt)")
        if file_path:
            self.file_path_label.setText(file_path)

    def select_folder(self):
        folder_path = QFileDialog.getExistingDirectory(self, "Выбрать папку для выгрузки")
        if folder_path:
            self.output_path_label.setText(folder_path)

    def start_generation(self):
        self.status_label.setText("Ход работы:\nЗагружено: [OK]\nОбрабатывается: [50%]\nЗавершено: [Ожидает]")

if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = AudioGenerationGUI()
    window.show()
    sys.exit(app.exec_())
