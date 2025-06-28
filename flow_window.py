import sys
import os
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QLabel, 
                            QPushButton, QVBoxLayout, QGridLayout, QHBoxLayout,
                            QFrame, QMessageBox, QProgressBar)
from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtGui import QFont, QIcon

# Импорты окон (если модули недоступны, будут показаны заглушки)
try:
    from content_gen_ui import ContentGenerationGUI
except ImportError:
    ContentGenerationGUI = None
    
try:
    from audio_gen_ui import AudioGenerationGUI
except ImportError:
    AudioGenerationGUI = None
    
try:
    from video_com_ui import VideoCompilationGUI
except ImportError:
    VideoCompilationGUI = None
    
try:
    from keyframes_viewer import KeyframeViewer
except ImportError:
    KeyframeViewer = None
    
try:
    from vector_base_upload import VectorBaseUploader
except ImportError:
    VectorBaseUploader = None
    
try:
    from recognition_cleaning import RecognitionCleaningGUI
except ImportError:
    RecognitionCleaningGUI = None


class FlowGridWindow(QMainWindow):
    """Окно управления ходом генерации контента для проекта."""
    
    # Сигнал для обновления статуса
    status_updated = pyqtSignal(str, str)  # stage_name, status
    
    def __init__(self, project_name=None, project_path=None, avtogen_data=None, materials_path=None):
        super().__init__()
        self.project_name = project_name or "Проект не выбран"
        self.project_path = project_path or ""
        self.avtogen_data = avtogen_data or {}
        self.materials_path = materials_path or ""
        
        # Словарь для отслеживания статусов этапов
        self.stage_statuses = self.load_project_status()
        
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса."""
        self.setWindowTitle(f"Управление ходом генерации - {self.project_name}")
        self.setMinimumSize(1200, 400)
        
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(15, 15, 15, 15)
        main_layout.setSpacing(15)
        
        # Заголовок с информацией о проекте
        self.create_project_header(main_layout)
        
        # Прогресс-бар общего выполнения
        self.create_progress_section(main_layout)
        
        # Основная сетка с этапами
        grid_frame = QFrame()
        grid_frame.setFrameStyle(QFrame.StyledPanel)
        grid_layout = QGridLayout(grid_frame)
        grid_layout.setSpacing(8)
        
        self.create_workflow_grid(grid_layout)
        
        main_layout.addWidget(grid_frame)
        
        # Нижняя панель с кнопками действий
        self.create_action_panel(main_layout)
        
    def create_project_header(self, layout):
        """Создание заголовка с информацией о проекте."""
        header_frame = QFrame()
        header_frame.setFrameStyle(QFrame.StyledPanel)
        header_frame.setStyleSheet("background-color: #f8f9fa; border: 1px solid #dee2e6;")
        
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(15, 10, 15, 10)
        
        # Название проекта
        project_label = QLabel(f"Проект: {self.project_name}")
        project_label.setFont(QFont("Arial", 14, QFont.Bold))
        header_layout.addWidget(project_label)
        
        header_layout.addStretch()
        
        # Путь к проекту
        if self.project_path:
            path_label = QLabel(f"Путь: {self.project_path}")
            path_label.setFont(QFont("Arial", 9))
            path_label.setStyleSheet("color: #6c757d;")
            header_layout.addWidget(path_label)
            
        layout.addWidget(header_frame)
        
    def create_progress_section(self, layout):
        """Создание секции с общим прогрессом."""
        progress_frame = QFrame()
        progress_layout = QVBoxLayout(progress_frame)
        progress_layout.setContentsMargins(0, 0, 0, 0)
        
        progress_label = QLabel("Общий прогресс выполнения:")
        progress_label.setFont(QFont("Arial", 10, QFont.Bold))
        progress_layout.addWidget(progress_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        progress_layout.addWidget(self.progress_bar)
        
        layout.addWidget(progress_frame)
        self.update_progress()
        
    def create_workflow_grid(self, grid_layout):
        """Создание основной сетки с этапами работы."""
        # Цвета статусов
        self.status_colors = {
            "not_started": "#FFA07A",    # Красный - не начато
            "in_progress": "#87CEFA",    # Голубой - в процессе  
            "completed": "#90EE90"       # Зеленый - завершено
        }
        
        # Определение этапов для прямого хода
        forward_stages = [
            ("materials", "Материалы", self.open_vector_base),
            ("conspect", "Конспект", self.open_content_gen),
            ("images", "Изображения", self.open_keyframes),
            ("final_conspect", "Конспект финальный", self.open_content_gen),
            ("presentation", "Презентация", self.open_content_gen),
            ("final_audio", "Аудио финальное", self.open_audio_gen),
            ("final_video", "Видео финальное", self.open_video_com)
        ]
        
        # Определение этапов для обратного хода
        reverse_stages = [
            ("source_video", "Видео исходное", self.open_video_processing),
            ("rev_images", "Изображения", self.open_keyframes),
            ("rev_audio", "Аудио финальное", self.open_audio_gen),
            ("rev_conspect", "Конспект", self.open_recognition_cleaning),
            ("rev_final_conspect", "Конспект финальный", self.open_content_gen),
            ("rev_presentation", "Презентация", self.open_content_gen),
            ("rev_materials", "Материалы", self.open_vector_base)
        ]
        
        # Заголовок "Прямой ход"
        forward_header = self.create_section_header("Прямой ход ➡️")
        grid_layout.addWidget(forward_header, 0, 0, 1, 7)
        
        # Кнопки прямого хода
        for col, (stage_id, stage_name, callback) in enumerate(forward_stages):
            button = self.create_stage_button(stage_id, stage_name, callback)
            grid_layout.addWidget(button, 1, col)
            
        # Заголовок "Обратный ход"
        reverse_header = self.create_section_header("Обратный ход ⬅️")
        grid_layout.addWidget(reverse_header, 2, 0, 1, 7)
        
        # Кнопки обратного хода
        for col, (stage_id, stage_name, callback) in enumerate(reverse_stages):
            button = self.create_stage_button(stage_id, stage_name, callback)
            grid_layout.addWidget(button, 3, col)
            
    def create_section_header(self, text):
        """Создание заголовка секции."""
        header = QLabel(text)
        header.setAlignment(Qt.AlignCenter)
        header.setFont(QFont("Arial", 12, QFont.Bold))
        header.setStyleSheet("""
            background-color: #e9ecef;
            border: 2px solid #dee2e6;
            border-radius: 5px;
            padding: 8px;
            color: #495057;
        """)
        header.setFixedHeight(40)
        return header
        
    def create_stage_button(self, stage_id, stage_name, callback):
        """Создание кнопки этапа."""
        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(2, 2, 2, 2)
        
        button = QPushButton(stage_name)
        button.setFixedHeight(35)
        button.setFont(QFont("Arial", 9, QFont.Bold))
        
        # Получаем статус этапа
        status = self.stage_statuses.get(stage_id, "not_started")
        color = self.status_colors[status]
        
        button.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                border: 2px solid #404040;
                border-radius: 5px;
                color: #000000;
                font-weight: bold;
            }}
            QPushButton:hover {{
                border-color: #007bff;
                transform: scale(1.02);
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color)};
            }}
        """)
        
        # Подключаем обработчик с передачей ID этапа
        button.clicked.connect(lambda checked, sid=stage_id, cb=callback: self.handle_stage_click(sid, cb))
        
        layout.addWidget(button)
        
        # Сохраняем ссылку на кнопку для обновления
        setattr(self, f"btn_{stage_id}", button)
        
        return container
        
    def create_action_panel(self, layout):
        """Создание панели с кнопками действий."""
        action_frame = QFrame()
        action_layout = QHBoxLayout(action_frame)
        action_layout.setContentsMargins(0, 10, 0, 0)
        
        # Кнопка сброса статусов
        reset_btn = QPushButton("Сбросить все статусы")
        reset_btn.setStyleSheet(self.get_action_button_style("#dc3545"))
        reset_btn.clicked.connect(self.reset_all_statuses)
        action_layout.addWidget(reset_btn)
        
        action_layout.addStretch()
        
        # Кнопка обновления статусов
        refresh_btn = QPushButton("Обновить из .avtogen")
        refresh_btn.setStyleSheet(self.get_action_button_style("#17a2b8"))
        refresh_btn.clicked.connect(self.load_avtogen_data)
        action_layout.addWidget(refresh_btn)
        
        # Кнопка сохранения
        save_btn = QPushButton("Сохранить в .avtogen")
        save_btn.setStyleSheet(self.get_action_button_style("#28a745"))
        save_btn.clicked.connect(self.save_project_status)
        action_layout.addWidget(save_btn)
        
        layout.addWidget(action_frame)
        
    def get_action_button_style(self, color):
        """Получение стиля для кнопок действий."""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 8px 16px;
                font-size: 12px;
                font-weight: bold;
                border-radius: 5px;
                min-width: 120px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
        """
        
    def darken_color(self, color, factor=0.2):
        """Затемнение цвета."""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * (1 - factor)) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        
    def setup_connections(self):
        """Настройка соединений сигналов."""
        self.status_updated.connect(self.on_status_updated)
        
    def handle_stage_click(self, stage_id, callback):
        """Обработка клика по этапу."""
        # Циклическое изменение статуса: не начато -> в процессе -> завершено -> не начато
        current_status = self.stage_statuses.get(stage_id, "not_started")
        
        status_cycle = ["not_started", "in_progress", "completed"]
        current_index = status_cycle.index(current_status)
        new_status = status_cycle[(current_index + 1) % len(status_cycle)]
        
        self.stage_statuses[stage_id] = new_status
        self.update_stage_button(stage_id, new_status)
        self.update_progress()
        
        # Вызываем callback для открытия соответствующего окна
        if callback:
            callback()
            
    def update_stage_button(self, stage_id, status):
        """Обновление внешнего вида кнопки этапа."""
        button = getattr(self, f"btn_{stage_id}", None)
        if button:
            color = self.status_colors[status]
            button.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    border: 2px solid #404040;
                    border-radius: 5px;
                    color: #000000;
                    font-weight: bold;
                }}
                QPushButton:hover {{
                    border-color: #007bff;
                }}
                QPushButton:pressed {{
                    background-color: {self.darken_color(color)};
                }}
            """)
            
    def update_progress(self):
        """Обновление прогресс-бара."""
        total_stages = len(self.stage_statuses)
        completed_stages = sum(1 for status in self.stage_statuses.values() if status == "completed")
        
        if total_stages > 0:
            progress = int((completed_stages / total_stages) * 100)
            self.progress_bar.setValue(progress)
            self.progress_bar.setFormat(f"{completed_stages}/{total_stages} этапов завершено ({progress}%)")
        else:
            self.progress_bar.setValue(0)
            
    def load_project_status(self):
        """Загрузка статусов этапов проекта из .avtogen файла."""
        if self.avtogen_data and "Workflow_Status" in self.avtogen_data:
            return self.avtogen_data["Workflow_Status"].copy()
        
        # Если данных нет, возвращаем все этапы как "не начато" (красные)
        return {
            "materials": "not_started",
            "conspect": "not_started", 
            "images": "not_started",
            "final_conspect": "not_started",
            "presentation": "not_started",
            "final_audio": "not_started",
            "final_video": "not_started",
            "source_video": "not_started",
            "rev_images": "not_started",
            "rev_audio": "not_started",
            "rev_conspect": "not_started",
            "rev_final_conspect": "not_started",
            "rev_presentation": "not_started",
            "rev_materials": "not_started"
        }
        
    def save_project_status(self):
        """Сохранение статусов этапов проекта в .avtogen файл."""
        if not self.project_path or not self.project_name:
            self.show_warning("Информация о проекте недоступна!")
            return
            
        try:
            avtogen_file = os.path.join(self.project_path, f"{self.project_name}.avtogen")
            
            # Загружаем существующие данные или создаем новые
            if os.path.exists(avtogen_file):
                with open(avtogen_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "Project_Name": self.project_name,
                    "Offset": 0,
                    "Slide_Style": "По умолчанию",
                    "Timings": 5,
                    "Description": ""
                }
            
            # Обновляем статусы рабочего процесса
            data["Workflow_Status"] = self.stage_statuses.copy()
            
            # Сохраняем файл
            with open(avtogen_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            self.show_info("Прогресс проекта сохранен в .avtogen файл!")
            
        except Exception as e:
            self.show_error(f"Ошибка при сохранении: {e}")
            
    def load_avtogen_data(self):
        """Перезагрузка данных из .avtogen файла."""
        if not self.project_path or not self.project_name:
            return
            
        try:
            avtogen_file = os.path.join(self.project_path, f"{self.project_name}.avtogen")
            
            if os.path.exists(avtogen_file):
                with open(avtogen_file, 'r', encoding='utf-8') as f:
                    self.avtogen_data = json.load(f)
                    
                # Обновляем статусы
                if "Workflow_Status" in self.avtogen_data:
                    self.stage_statuses = self.avtogen_data["Workflow_Status"].copy()
                    
                    # Обновляем все кнопки
                    for stage_id, status in self.stage_statuses.items():
                        self.update_stage_button(stage_id, status)
                        
                    self.update_progress()
                    
        except Exception as e:
            self.show_error(f"Ошибка при загрузке .avtogen файла: {e}")
            
    def reset_all_statuses(self):
        """Сброс всех статусов к начальному состоянию."""
        reply = QMessageBox.question(
            self,
            "Подтверждение сброса",
            "Вы действительно хотите сбросить все статусы?\n"
            "Весь прогресс будет потерян!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            for stage_id in self.stage_statuses:
                self.stage_statuses[stage_id] = "not_started"
                self.update_stage_button(stage_id, "not_started")
            self.update_progress()
            
    def refresh_statuses(self):
        """Обновление статусов этапов."""
        self.load_avtogen_data()
        self.show_info("Статусы обновлены из .avtogen файла!")
        
    def on_status_updated(self, stage_name, status):
        """Обработка сигнала обновления статуса."""
        self.update_progress()
        
    # Методы для открытия различных окон
    def open_content_gen(self):
        """Открытие окна генерации контента."""
        if ContentGenerationGUI:
            self.content_window = ContentGenerationGUI()
            self.content_window.show()
        else:
            self.show_module_not_found("content_gen_ui")
            
    def open_audio_gen(self):
        """Открытие окна генерации аудио."""
        if AudioGenerationGUI:
            self.audio_window = AudioGenerationGUI()
            self.audio_window.show()
        else:
            self.show_module_not_found("audio_gen_ui")
            
    def open_video_com(self):
        """Открытие окна компиляции видео."""
        if VideoCompilationGUI:
            self.video_window = VideoCompilationGUI()
            self.video_window.show()
        else:
            self.show_module_not_found("video_com_ui")
            
    def open_keyframes(self):
        """Открытие просмотрщика ключевых кадров."""
        if KeyframeViewer:
            self.keyframes_window = KeyframeViewer()
            self.keyframes_window.show()
        else:
            self.show_module_not_found("keyframes_viewer")
            
    def open_vector_base(self):
        """Открытие загрузчика векторной базы."""
        if VectorBaseUploader:
            self.vector_window = VectorBaseUploader(materials_path=self.materials_path)
            self.vector_window.show()
        else:
            self.show_module_not_found("vector_base_upload")
            
    def open_recognition_cleaning(self):
        """Открытие модуля распознавания и очистки текста."""
        if RecognitionCleaningGUI:
            self.recognition_window = RecognitionCleaningGUI()
            self.recognition_window.show()
        else:
            self.show_module_not_found("recognition_cleaning")
            
    def open_video_processing(self):
        """Открытие модуля обработки исходного видео (комбинированный)."""
        # Для исходного видео нужны и ключевые кадры, и распознавание аудио
        keyframes_opened = False
        recognition_opened = False
        
        if KeyframeViewer:
            self.keyframes_window = KeyframeViewer()
            self.keyframes_window.show()
            keyframes_opened = True
        
        if RecognitionCleaningGUI:
            self.recognition_window = RecognitionCleaningGUI()
            self.recognition_window.show()
            recognition_opened = True
            
        if not keyframes_opened and not recognition_opened:
            self.show_module_not_found("keyframes_viewer и recognition_cleaning")
        elif not keyframes_opened:
            self.show_module_not_found("keyframes_viewer")
        elif not recognition_opened:
            self.show_module_not_found("recognition_cleaning")
            
    def show_module_not_found(self, module_name):
        """Показ сообщения о недоступном модуле."""
        self.show_warning(f"Модуль {module_name} не найден!\n"
                         f"Убедитесь, что файл {module_name}.py доступен.")
        
    def show_error(self, message):
        """Показ сообщения об ошибке."""
        QMessageBox.critical(self, "Ошибка", message)
        
    def show_warning(self, message):
        """Показ предупреждения."""
        QMessageBox.warning(self, "Предупреждение", message)
        
    def show_info(self, message):
        """Показ информационного сообщения."""
        QMessageBox.information(self, "Информация", message)


def main():
    """Главная функция для тестирования."""
    app = QApplication(sys.argv)
    
    # Тестовый запуск с параметрами
    test_avtogen_data = {
        "Project_Name": "Тестовый проект",
        "Offset": 0,
        "Slide_Style": "По умолчанию", 
        "Timings": 5,
        "Description": "Тестовое описание проекта",
        "Workflow_Status": {
            "materials": "completed",
            "conspect": "in_progress", 
            "images": "not_started"
        }
    }
    
    window = FlowGridWindow(
        project_name="Тестовый проект",
        project_path="C:\\Avtogen\\test_project",
        avtogen_data=test_avtogen_data,
        materials_path="C:\\Avtogen\\test_project\\materials"
    )
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()