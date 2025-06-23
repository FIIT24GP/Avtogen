from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QLabel, QPushButton, QVBoxLayout, QGridLayout
from PyQt5.QtCore import Qt
import sys
from content_gen_ui import ContentGenerationGUI
from audio_gen_ui import AudioGenerationGUI
from video_com_ui import VideoCompilationGUI
from keyframes_viewer import KeyframeViewer
from vector_base_upload import VectorBaseUploader

class FlowGridWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Управление ходом генерации")
        self.setMinimumSize(1000, 250)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        grid = QGridLayout(central_widget)
        grid.setSpacing(2)

        # Цвета
        color_red = "#FFA07A"    # не начато
        color_blue = "#87CEFA"   # в процессе
        color_green = "#90EE90"  # завершено

        # ---------- Прямой ход ----------
        grid.addWidget(self._make_heading("Прямой ход"), 0, 0, 1, 7)

        materials_btn = self._make_button("Материалы", color_green)
        materials_btn.layout().itemAt(0).widget().clicked.connect(self.open_vector_base)
        grid.addWidget(materials_btn, 1, 0)

        conspect_btn = self._make_button("Конспект", color_green)
        conspect_btn.layout().itemAt(0).widget().clicked.connect(self.open_content_gen)
        grid.addWidget(conspect_btn, 1, 1)

        images_btn = self._make_button("Изображения", color_blue)
        images_btn.layout().itemAt(0).widget().clicked.connect(self.open_keyframes)
        grid.addWidget(images_btn, 1, 2)

        final_conspect_btn = self._make_button("Конспект финальный", color_blue)
        final_conspect_btn.layout().itemAt(0).widget().clicked.connect(self.open_content_gen)
        grid.addWidget(final_conspect_btn, 1, 3)

        presentation_btn = self._make_button("Презентация", color_red)
        presentation_btn.layout().itemAt(0).widget().clicked.connect(self.open_content_gen)
        grid.addWidget(presentation_btn, 1, 4)

        audio_btn = self._make_button("Аудио финальное", color_red)
        audio_btn.layout().itemAt(0).widget().clicked.connect(self.open_audio_gen)
        grid.addWidget(audio_btn, 1, 5)

        video_btn = self._make_button("Видео финальное", color_red)
        video_btn.layout().itemAt(0).widget().clicked.connect(self.open_video_com)
        grid.addWidget(video_btn, 1, 6)

        # ---------- Обратный ход ----------
        grid.addWidget(self._make_heading("Обратный ход"), 2, 0, 1, 7)

        source_video_btn = self._make_button("Видео исходное", color_red)
        source_video_btn.layout().itemAt(0).widget().clicked.connect(self.open_video_com)
        grid.addWidget(source_video_btn, 3, 0)

        rev_images_btn = self._make_button("Изображения", color_red)
        rev_images_btn.layout().itemAt(0).widget().clicked.connect(self.open_keyframes)
        grid.addWidget(rev_images_btn, 3, 1)

        rev_audio_btn = self._make_button("Аудио финальное", color_red)
        rev_audio_btn.layout().itemAt(0).widget().clicked.connect(self.open_audio_gen)
        grid.addWidget(rev_audio_btn, 3, 2)

        rev_conspect_btn = self._make_button("Конспект", color_red)
        rev_conspect_btn.layout().itemAt(0).widget().clicked.connect(self.open_content_gen)
        grid.addWidget(rev_conspect_btn, 3, 3)

        rev_final_conspect_btn = self._make_button("Конспект финальный", color_red)
        rev_final_conspect_btn.layout().itemAt(0).widget().clicked.connect(self.open_content_gen)
        grid.addWidget(rev_final_conspect_btn, 3, 4)

        rev_presentation_btn = self._make_button("Презентация", color_red)
        rev_presentation_btn.layout().itemAt(0).widget().clicked.connect(self.open_content_gen)
        grid.addWidget(rev_presentation_btn, 3, 5)

        rev_materials_btn = self._make_button("Материалы", color_red)
        rev_materials_btn.layout().itemAt(0).widget().clicked.connect(self.open_vector_base)
        grid.addWidget(rev_materials_btn, 3, 6)

    def _make_heading(self, text):
        label = QLabel(text)
        label.setAlignment(Qt.AlignCenter)
        label.setStyleSheet("background-color: #E0E0E0; font-weight: bold; font-size: 14px;")
        label.setFixedHeight(40)
        container = QWidget()
        container.setLayout(QVBoxLayout())
        container.layout().addWidget(label)
        container.layout().setContentsMargins(0, 0, 0, 0)
        return container

    def _make_button(self, text, color):
        button = QPushButton(text)
        button.setStyleSheet(f"background-color: {color}; font-weight: normal;")
        button.setFixedHeight(30)
        container = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(button)
        layout.setContentsMargins(0, 0, 0, 0)
        container.setLayout(layout)
        return container

    def open_content_gen(self):
        self.content_window = ContentGenerationGUI()
        self.content_window.show()

    def open_audio_gen(self):
        self.audio_window = AudioGenerationGUI()
        self.audio_window.show()

    def open_video_com(self):
        self.video_window = VideoCompilationGUI()
        self.video_window.show()

    def open_keyframes(self):
        self.keyframes_window = KeyframeViewer()
        self.keyframes_window.show()

    def open_vector_base(self):
        self.vector_window = VectorBaseUploader()
        self.vector_window.show()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = FlowGridWindow()
    win.show()
    sys.exit(app.exec_())
