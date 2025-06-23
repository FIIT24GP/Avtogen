import sys
from PyQt5.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton, QListWidget, QFileDialog,
    QHBoxLayout, QVBoxLayout, QListWidgetItem, QSpinBox
)
from PyQt5.QtGui import QPixmap
from PyQt5.QtCore import Qt

class KeyframeViewer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Извлечение и просмотр ключевых кадров")
        self.resize(800, 500)

        layout_main = QVBoxLayout()

        self.open_btn = QPushButton("Открыть видеофайл")
        self.file_path_label = QLabel("Путь: файл не выбран")
        layout_main.addWidget(self.open_btn)
        layout_main.addWidget(self.file_path_label)

        layout_center = QHBoxLayout()

        self.keyframes_list = QListWidget()
        self.keyframes_list.addItems(["Кадр 1", "Кадр 2", "Кадр 3"])
        
        layout_preview = QVBoxLayout()
        self.preview_label = QLabel("Превью выбранного кадра:")
        self.preview_area = QLabel()
        self.preview_area.setFixedSize(300, 200)
        self.preview_area.setStyleSheet("border: 1px solid black;")
        self.preview_area.setAlignment(Qt.AlignCenter)

        layout_preview.addWidget(self.preview_label)
        layout_preview.addWidget(self.preview_area)

        layout_center.addWidget(self.keyframes_list)
        layout_center.addLayout(layout_preview)

        layout_main.addLayout(layout_center)

        layout_buttons = QHBoxLayout()
        self.play_btn = QPushButton("Просмотреть выбранный кадр")
        self.offset_btn = QPushButton("Просмотреть на ХХ секунд >>")
        self.offset_spin = QSpinBox()
        self.offset_spin.setValue(20)
        self.offset_spin.setSuffix(" сек")

        layout_buttons.addWidget(self.play_btn)
        layout_buttons.addWidget(self.offset_btn)
        layout_buttons.addWidget(self.offset_spin)

        layout_main.addLayout(layout_buttons)

        self.status_label = QLabel("Статус просмотра:\nТекущий кадр: -\nСмещение вправо: -\nСтатус: ожидание")
        layout_main.addWidget(self.status_label)

        self.setLayout(layout_main)

        # Подключение событий
        self.open_btn.clicked.connect(self.open_file)
        self.keyframes_list.currentItemChanged.connect(self.update_preview)
        self.play_btn.clicked.connect(self.play_frame)
        self.offset_btn.clicked.connect(self.play_offset_frame)

    def open_file(self):
        file, _ = QFileDialog.getOpenFileName(self, "Открыть видеофайл", "", "Видео (*.mp4 *.avi)")
        if file:
            self.file_path_label.setText(f"Путь: {file}")
            # Здесь будет логика извлечения кадров из видеофайла

    def update_preview(self):
        current_item = self.keyframes_list.currentItem()
        if current_item:
            # Здесь будет логика обновления изображения превью
            pixmap = QPixmap(300, 200)
            pixmap.fill(Qt.gray)
            self.preview_area.setPixmap(pixmap)
            self.status_label.setText(f"Статус просмотра:\nТекущий кадр: {current_item.text()}\nСмещение вправо: -\nСтатус: ожидание")

    def play_frame(self):
        current_item = self.keyframes_list.currentItem()
        if current_item:
            self.status_label.setText(f"Статус просмотра:\nТекущий кадр: {current_item.text()}\nСмещение вправо: 0 сек\nСтатус: кадр просмотрен")

    def play_offset_frame(self):
        current_item = self.keyframes_list.currentItem()
        offset = self.offset_spin.value()
        if current_item:
            self.status_label.setText(f"Статус просмотра:\nТекущий кадр: {current_item.text()}\nСмещение вправо: {offset} сек\nСтатус: фрагмент просмотрен")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    viewer = KeyframeViewer()
    viewer.show()
    sys.exit(app.exec_())
