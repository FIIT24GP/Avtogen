import sys
import os
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QGridLayout, QLabel, QVBoxLayout, QPushButton, QListWidget, QTextEdit
from PyQt5.QtGui import QColor
from PyQt5.QtCore import Qt, QRandomGenerator

class ColorGridWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Random Color Grid")
        self.setMinimumSize(800, 400)

        # Create central widget and grid layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        grid_layout = QGridLayout(central_widget)
        grid_layout.setSpacing(2)  # Add small spacing between cells

        # Explicitly define each cell (8 columns x 7 rows)
        # Row 0
        cell_0_0 = QWidget()
        #cell_0_0.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_0_0.setFixedHeight(30)
        label_0_0 = QLabel("Доступные проекты")
        label_0_0.setAlignment(Qt.AlignCenter)
        cell_0_0.setLayout(QVBoxLayout())
        cell_0_0.layout().setContentsMargins(0, 0, 0, 0)
        cell_0_0.layout().addWidget(label_0_0)
        grid_layout.addWidget(cell_0_0, 0, 0, 1, 3)

        cell_0_3 = QWidget()
        #cell_0_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_0_3.setFixedHeight(30)
        cell_0_3.setFixedWidth(10)
        grid_layout.addWidget(cell_0_3, 0, 3)

        cell_0_4 = QWidget()
        #cell_0_4.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_0_4.setFixedHeight(30)
        label_0_4 = QLabel("Описание проекта")
        label_0_4.setAlignment(Qt.AlignCenter)
        cell_0_4.setLayout(QVBoxLayout())
        cell_0_4.layout().setContentsMargins(0, 0, 0, 0)
        cell_0_4.layout().addWidget(label_0_4)
        grid_layout.addWidget(cell_0_4, 0, 4, 1, 4)

        # Объединенная ячейка для Row 1-7 (столбцы 0-2)
   # Объединенная ячейка для Row 1-7 (столбцы 0-2)
        combined_1_7 = QWidget()
        #combined_1_7.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        layout_1_7 = QVBoxLayout()
        layout_1_7.setContentsMargins(0, 0, 0, 0)
        self.project_list = QListWidget()
        self.project_list.setStyleSheet("QListWidget { border: none; font-size: 16px; }")
        self.project_path = "C:\\Avtogen"
        if not os.path.exists(self.project_path):
            os.makedirs(self.project_path)
        for folder in os.listdir(self.project_path):
            if os.path.isdir(os.path.join(self.project_path, folder)):
                self.project_list.addItem(folder)
        self.project_list.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.project_list.itemClicked.connect(self.on_project_selected)  # Connect the signal
        layout_1_7.addWidget(self.project_list)
        combined_1_7.setLayout(layout_1_7)
        grid_layout.addWidget(combined_1_7, 1, 0, 7, 3)

        cell_1_3 = QWidget()
        #cell_1_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_1_3.setFixedHeight(30)
        cell_1_3.setFixedWidth(10)
        grid_layout.addWidget(cell_1_3, 1, 3)

        # Исправление для ячейки cell_1_4 (объединенная ячейка, строки 1-2, столбцы 4-7)
        cell_1_4 = QWidget()
        #cell_1_4.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_1_4.setMinimumWidth(200)
        cell_1_4.setLayout(QVBoxLayout())
        cell_1_4.layout().setContentsMargins(0, 0, 0, 0)
        text_area_1_4 = QTextEdit()
        #text_area_1_4.setStyleSheet("background-color: #FFFFFF; border: 1px solid #CCCCCC;")
        text_area_1_4.setPlaceholderText("Введите описание проекта")
        cell_1_4.layout().addWidget(text_area_1_4)
        grid_layout.addWidget(cell_1_4, 1, 4, 2, 4)

        # Row 2 (оставляем пустой, так как объединено)
        cell_2_3 = QWidget()
        #cell_2_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_2_3.setFixedHeight(30)
        cell_2_3.setFixedWidth(10)
        grid_layout.addWidget(cell_2_3, 2, 3)

        # Row 3
        cell_3_3 = QWidget()
        #cell_3_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_3_3.setFixedHeight(30)
        cell_3_3.setFixedWidth(10)
        grid_layout.addWidget(cell_3_3, 3, 3)

        cell_3_4 = QWidget()
        #cell_3_4.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_3_4.setFixedHeight(30)
        cell_3_4.setMinimumWidth(200)
        label_3_4 = QLabel("Ход работы")
        label_3_4.setAlignment(Qt.AlignCenter)
        cell_3_4.setLayout(QVBoxLayout())
        cell_3_4.layout().setContentsMargins(0, 0, 0, 0)
        cell_3_4.layout().addWidget(label_3_4)
        grid_layout.addWidget(cell_3_4, 3, 4, 1, 4)

        # Row 4
        cell_4_3 = QWidget()
        #cell_4_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_4_3.setFixedHeight(30)
        cell_4_3.setFixedWidth(10)
        grid_layout.addWidget(cell_4_3, 4, 3)

        cell_4_4 = QWidget()
        #cell_4_4.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_4_4.setStyleSheet("background-color: #90EE90; border: 1px solid #404040;")
        cell_4_4.setFixedHeight(30)
        cell_4_4.setMinimumWidth(200)        
        label_4_4 = QLabel("Материалы для базы")
        label_4_4.setAlignment(Qt.AlignCenter)
        cell_4_4.setLayout(QVBoxLayout())
        cell_4_4.layout().setContentsMargins(0, 0, 0, 0)
        cell_4_4.layout().addWidget(label_4_4)
        grid_layout.addWidget(cell_4_4, 4, 4, 1, 4)

        # Row 5
        cell_5_3 = QWidget()
        #cell_5_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_5_3.setFixedHeight(30)
        cell_5_3.setFixedWidth(10)
        grid_layout.addWidget(cell_5_3, 5, 3)

        cell_5_4 = QWidget()
        #cell_5_4.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_5_4.setFixedHeight(30)
        cell_5_4.setMinimumWidth(200)
        label_5_4 = QLabel("Видео исходное")
        cell_5_4.setStyleSheet("background-color: #FFA07A; border: 1px solid #404040;")
        label_5_4.setAlignment(Qt.AlignCenter)
        cell_5_4.setLayout(QVBoxLayout())
        cell_5_4.layout().setContentsMargins(0, 0, 0, 0)
        cell_5_4.layout().addWidget(label_5_4)
        grid_layout.addWidget(cell_5_4, 5, 4, 1, 4)

        # Row 6
        cell_6_3 = QWidget()
        #cell_6_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_6_3.setFixedHeight(30)
        cell_6_3.setFixedWidth(10)
        grid_layout.addWidget(cell_6_3, 6, 3)

        cell_6_4 = QWidget()
        #cell_6_4.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_6_4.setFixedHeight(30)
        cell_6_4.setMinimumWidth(200)
        cell_6_4.setStyleSheet("background-color: #90EE90; border: 1px solid #404040;")
        label_6_4 = QLabel("Конспект исходный")
        label_6_4.setAlignment(Qt.AlignCenter)
        cell_6_4.setLayout(QVBoxLayout())
        cell_6_4.layout().setContentsMargins(0, 0, 0, 0)
        cell_6_4.layout().addWidget(label_6_4)
        grid_layout.addWidget(cell_6_4, 6, 4, 1, 4)

        # Row 7
        cell_7_3 = QWidget()
        #cell_7_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_7_3.setFixedHeight(30)
        cell_7_3.setFixedWidth(10)
        grid_layout.addWidget(cell_7_3, 7, 3)

        cell_7_4 = QWidget()
        #cell_7_4.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
       
        cell_7_4.setFixedHeight(30)
        cell_7_4.setMinimumWidth(200)
        cell_7_4.setStyleSheet("background-color: #FFA07A; border: 1px solid #404040;")
        label_7_4 = QLabel("Изображения исходные")
        label_7_4.setAlignment(Qt.AlignCenter)
        cell_7_4.setLayout(QVBoxLayout())
        cell_7_4.layout().setContentsMargins(0, 0, 0, 0)
        cell_7_4.layout().addWidget(label_7_4)
        grid_layout.addWidget(cell_7_4, 7, 4, 1, 4)

        # Row 8
        cell_8_0 = QWidget()
        #cell_8_0.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_8_0.setFixedHeight(30)
        cell_8_0.setMinimumWidth(50)
        label_8_0 = QLabel("Папка проекта")
        label_8_0.setAlignment(Qt.AlignCenter)
        cell_8_0.setLayout(QVBoxLayout())
        cell_8_0.layout().setContentsMargins(0, 0, 0, 0)
        cell_8_0.layout().addWidget(label_8_0)
        grid_layout.addWidget(cell_8_0, 8, 0)

        cell_8_1 = QWidget()
        #cell_8_1.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_8_1.setFixedHeight(30)
        cell_8_1.setMinimumWidth(100)  # Общая ширина для объединения 1-2
        self.project_path_label = QLabel("")  # Store reference to the label
        self.project_path_label.setAlignment(Qt.AlignCenter)
        cell_8_1.setLayout(QVBoxLayout())
        cell_8_1.layout().setContentsMargins(0, 0, 0, 0)
        cell_8_1.layout().addWidget(self.project_path_label)
        grid_layout.addWidget(cell_8_1, 8, 1, 1, 2)  # Объединяет столбцы 1-2

        cell_8_3 = QWidget()
        #cell_8_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_8_3.setFixedHeight(30)
        cell_8_3.setFixedWidth(10)
        grid_layout.addWidget(cell_8_3, 8, 3)

        cell_8_4 = QWidget()
        #cell_8_4.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")

        cell_8_4.setFixedHeight(30)
        cell_8_4.setMinimumWidth(200)
        cell_8_4.setStyleSheet("background-color: #87CEFA; border: 1px solid #404040;")
        label_8_4 = QLabel("Видео финальное")
        label_8_4.setAlignment(Qt.AlignCenter)
        cell_8_4.setLayout(QVBoxLayout())
        cell_8_4.layout().setContentsMargins(0, 0, 0, 0)
        cell_8_4.layout().addWidget(label_8_4)
        grid_layout.addWidget(cell_8_4, 8, 4, 1, 4)


        # Row 9
        cell_9_0 = QWidget()
        #cell_9_0.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_9_0.setFixedHeight(30)
        cell_9_0.setMinimumWidth(150)
        layout_9_0 = QVBoxLayout()
        layout_9_0.setContentsMargins(0, 0, 0, 0)
        btn_9_0 = QPushButton("Создать")
        btn_9_0.setFixedWidth(int(250 * 0.8))  # 80% ширины одной ячейки (50 пикселей)
        btn_9_0.setFixedHeight(20)
        layout_9_0.addWidget(btn_9_0, alignment=Qt.AlignHCenter)
        cell_9_0.setLayout(layout_9_0)
        grid_layout.addWidget(cell_9_0, 9, 0, 1, 3)

        cell_9_3 = QWidget()
        #cell_9_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_9_3.setFixedHeight(30)
        cell_9_3.setFixedWidth(10)
        grid_layout.addWidget(cell_9_3, 9, 3)

        cell_9_4 = QWidget()
        #cell_9_4.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
       
        cell_9_4.setFixedHeight(30)
        cell_9_4.setMinimumWidth(200)
        cell_9_4.setStyleSheet("background-color: #87CEFA; border: 1px solid #404040;")
        label_9_4 = QLabel("Аудио финальное")
        label_9_4.setAlignment(Qt.AlignCenter)
        cell_9_4.setLayout(QVBoxLayout())
        cell_9_4.layout().setContentsMargins(0, 0, 0, 0)
        cell_9_4.layout().addWidget(label_9_4)
        grid_layout.addWidget(cell_9_4, 9, 4, 1, 4)

        # Row 10
        cell_10_0 = QWidget()
        cell_10_0 = QWidget()
        #cell_10_0.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_10_0.setFixedHeight(30)
        cell_10_0.setMinimumWidth(150)
        layout_10_0 = QVBoxLayout()
        layout_10_0.setContentsMargins(0, 0, 0, 0)
        btn_10_0 = QPushButton("Перенести в папку")
        btn_10_0.setFixedWidth(int(250 * 0.8))  # 80% ширины одной ячейки (50 пикселей)
        btn_10_0.setFixedHeight(20)
        layout_10_0.addWidget(btn_10_0, alignment=Qt.AlignHCenter)
        cell_10_0.setLayout(layout_10_0)
        grid_layout.addWidget(cell_10_0, 10, 0, 1, 3)

        cell_10_3 = QWidget()
        #cell_10_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_10_3.setFixedHeight(30)
        cell_10_3.setFixedWidth(10)
        grid_layout.addWidget(cell_10_3, 10, 3)

        cell_10_4 = QWidget()
        #cell_10_4.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        
        cell_10_4.setFixedHeight(30)
        cell_10_4.setMinimumWidth(200)
        cell_10_4.setStyleSheet("background-color: #FFA07A; border: 1px solid #404040;")
        label_10_4 = QLabel("Конспект финальный")
        label_10_4.setAlignment(Qt.AlignCenter)
        cell_10_4.setLayout(QVBoxLayout())
        cell_10_4.layout().setContentsMargins(0, 0, 0, 0)
        cell_10_4.layout().addWidget(label_10_4)
        grid_layout.addWidget(cell_10_4, 10, 4, 1, 4)

        # Row 11
        cell_11_0 = QWidget()
        #cell_11_0.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_11_0.setFixedHeight(30)
        cell_11_0.setMinimumWidth(150)
        layout_11_0 = QVBoxLayout()
        layout_11_0.setContentsMargins(0, 0, 0, 0)
        btn_11_0 = QPushButton("Удалить")
        btn_11_0.setFixedWidth(int(250 * 0.8))
        btn_11_0.setFixedHeight(20)
        btn_11_0.clicked.connect(lambda: self.delete_project(self.project_list.currentItem()))
        layout_11_0.addWidget(btn_11_0, alignment=Qt.AlignHCenter)
        cell_11_0.setLayout(layout_11_0)
        grid_layout.addWidget(cell_11_0, 11, 0, 1, 3)

        cell_11_3 = QWidget()
        #cell_11_3.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")
        cell_11_3.setFixedHeight(30)
        cell_11_3.setFixedWidth(10)
        grid_layout.addWidget(cell_11_3, 11, 3)

        cell_11_4 = QWidget()
        #cell_11_4.setStyleSheet(f"background-color: {QColor(QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256), QRandomGenerator.global_().bounded(256)).name()};")

        cell_11_4.setFixedHeight(30)
        cell_11_4.setMinimumWidth(200)
        cell_11_4.setStyleSheet("background-color: #FFA07A; border: 1px solid #404040;")
        label_11_4 = QLabel("Презентация финальная")
        label_11_4.setAlignment(Qt.AlignCenter)
        cell_11_4.setLayout(QVBoxLayout())
        cell_11_4.layout().setContentsMargins(0, 0, 0, 0)
        cell_11_4.layout().addWidget(label_11_4)
        grid_layout.addWidget(cell_11_4, 11, 4, 1, 4)

    def on_project_selected(self, item):
        """Handle project selection from the list box."""
        selected_project = item.text()
        full_path = os.path.join(self.project_path, selected_project)
        self.project_path_label.setText(full_path)

    def delete_project(self, item):
        if item:
            project_name = item.text()
            project_path = os.path.join(self.project_path, project_name)
            try:
                import shutil
                shutil.rmtree(project_path)
                self.project_list.takeItem(self.project_list.row(item))
            except Exception as e:
                print(f"Ошибка при удалении: {e}")


def main():
    app = QApplication(sys.argv)
    window = ColorGridWindow()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()