import sys
import os
import shutil
import json
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QGridLayout, 
                            QLabel, QVBoxLayout, QPushButton, QListWidget, 
                            QTextEdit, QMessageBox, QInputDialog, QHBoxLayout,
                            QFrame, QSplitter)
from PyQt5.QtGui import QColor, QFont
from PyQt5.QtCore import Qt, pyqtSignal


class ProjectManager(QMainWindow):
    """Менеджер проектов с улучшенным интерфейсом и функциональностью."""
    
    # Сигналы для взаимодействия между компонентами
    project_selected = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.project_path = "C:\\Avtogen"
        self.current_project = None
        self.setup_ui()
        self.setup_connections()
        self.load_projects()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса."""
        self.setWindowTitle("Менеджер проектов")
        self.setMinimumSize(1000, 700)
        
        # Создание центрального виджета с разделителем
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        # Основной макет
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)
        
        # Создание разделителя
        splitter = QSplitter(Qt.Horizontal)
        main_layout.addWidget(splitter)
        
        # Левая панель - список проектов
        left_panel = self.create_project_panel()
        splitter.addWidget(left_panel)
        
        # Правая панель - детали проекта
        right_panel = self.create_details_panel()
        splitter.addWidget(right_panel)
        
        # Установка пропорций разделителя
        splitter.setSizes([300, 700])
        
    def create_project_panel(self):
        """Создание панели со списком проектов."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Заголовок
        title = QLabel("Доступные проекты")
        title.setFont(QFont("Arial", 12, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(title)
        
        # Список проектов
        self.project_list = QListWidget()
        self.project_list.setStyleSheet("""
            QListWidget {
                border: 1px solid #ccc;
                font-size: 14px;
                selection-background-color: #4CAF50;
                selection-color: white;
            }
            QListWidget::item {
                padding: 8px;
                border-bottom: 1px solid #eee;
                color: black;
            }
            QListWidget::item:hover {
                background-color: #f5f5f5;
            }
            QListWidget::item:selected {
                background-color: #4CAF50;
                color: white;
            }
        """)
        layout.addWidget(self.project_list)
        
        # Кнопки управления проектами
        buttons_layout = QVBoxLayout()
        
        self.create_btn = QPushButton("Создать проект")
        self.create_btn.setStyleSheet(self.get_button_style("#4CAF50"))
        buttons_layout.addWidget(self.create_btn)
        
        self.delete_btn = QPushButton("Удалить проект")
        self.delete_btn.setStyleSheet(self.get_button_style("#f44336"))
        self.delete_btn.setEnabled(False)
        buttons_layout.addWidget(self.delete_btn)
        
        self.flow_btn = QPushButton("Перейти к ходу работы")
        self.flow_btn.setStyleSheet(self.get_button_style("#2196F3"))
        self.flow_btn.setEnabled(False)
        buttons_layout.addWidget(self.flow_btn)
        
        layout.addLayout(buttons_layout)
        
        # Информация о текущем проекте
        self.project_info = QLabel("Выберите проект")
        self.project_info.setWordWrap(True)
        self.project_info.setStyleSheet("padding: 10px; background-color: #f9f9f9; border: 1px solid #ddd;")
        layout.addWidget(self.project_info)
        
        return panel
        
    def create_details_panel(self):
        """Создание панели с деталями проекта."""
        panel = QFrame()
        panel.setFrameStyle(QFrame.StyledPanel)
        layout = QVBoxLayout(panel)
        
        # Описание проекта
        desc_title = QLabel("Описание проекта")
        desc_title.setFont(QFont("Arial", 12, QFont.Bold))
        desc_title.setAlignment(Qt.AlignCenter)
        desc_title.setStyleSheet("padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc;")
        layout.addWidget(desc_title)
        
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Введите описание проекта...")
        self.description_edit.setMaximumHeight(150)
        self.description_edit.setStyleSheet("border: 1px solid #ccc; font-size: 14px;")
        layout.addWidget(self.description_edit)
        
        # Панель хода работы
        workflow_title = QLabel("Ход работы")
        workflow_title.setFont(QFont("Arial", 12, QFont.Bold))
        workflow_title.setAlignment(Qt.AlignCenter)
        workflow_title.setStyleSheet("padding: 10px; background-color: #f0f0f0; border: 1px solid #ccc; margin-top: 10px;")
        layout.addWidget(workflow_title)
        
        # Создание этапов работы
        workflow_widget = self.create_workflow_widget()
        layout.addWidget(workflow_widget)
        
        return panel
        
    def create_workflow_widget(self):
        """Создание виджета с этапами работы."""
        widget = QWidget()
        layout = QGridLayout(widget)
        layout.setSpacing(5)
        
        # Определение этапов работы с их статусами
        self.workflow_stages = [
            ("Материалы для базы", "completed"),
            ("Видео исходное", "in_progress"), 
            ("Конспект исходный", "completed"),
            ("Изображения исходные", "in_progress"),
            ("Видео финальное", "pending"),
            ("Аудио финальное", "pending"),
            ("Конспект финальный", "in_progress"),
            ("Презентация финальная", "in_progress")
        ]
        
        # Создание карточек для каждого этапа
        for i, (stage_name, status) in enumerate(self.workflow_stages):
            row = i // 2
            col = i % 2
            
            stage_card = self.create_stage_card(stage_name, status)
            layout.addWidget(stage_card, row, col)
            
        return widget
        
    def create_stage_card(self, name, status):
        """Создание карточки этапа работы."""
        card = QFrame()
        card.setFrameStyle(QFrame.StyledPanel)
        card.setFixedHeight(60)
        
        layout = QVBoxLayout(card)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Заголовок этапа
        title_label = QLabel(name)
        title_label.setAlignment(Qt.AlignCenter)
        title_label.setFont(QFont("Arial", 10, QFont.Bold))
        layout.addWidget(title_label)
        
        # Установка цвета в зависимости от статуса
        colors = {
            "completed": "#90EE90",  # Зеленый - завершено
            "in_progress": "#FFA07A",  # Оранжевый - в процессе
            "pending": "#87CEFA"  # Голубой - ожидание
        }
        
        card.setStyleSheet(f"""
            QFrame {{
                background-color: {colors.get(status, '#f0f0f0')};
                border: 2px solid #404040;
                border-radius: 5px;
            }}
        """)
        
        return card
        
    def get_button_style(self, color):
        """Получение стиля для кнопок."""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px;
                font-size: 14px;
                font-weight: bold;
                border-radius: 5px;
            }}
            QPushButton:hover {{
                background-color: {self.darken_color(color)};
            }}
            QPushButton:pressed {{
                background-color: {self.darken_color(color, 0.3)};
            }}
            QPushButton:disabled {{
                background-color: #cccccc;
                color: #666666;
            }}
        """
        
    def darken_color(self, color, factor=0.1):
        """Затемнение цвета для эффектов hover."""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * (1 - factor)) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        
    def setup_connections(self):
        """Настройка соединений сигналов и слотов."""
        self.project_list.itemClicked.connect(self.on_project_selected)
        self.create_btn.clicked.connect(self.create_project)
        self.delete_btn.clicked.connect(self.delete_project)
        self.flow_btn.clicked.connect(self.open_flow_window)
        self.description_edit.textChanged.connect(self.save_description)
        
    def ensure_project_directory(self):
        """Обеспечение существования директории проектов."""
        if not os.path.exists(self.project_path):
            try:
                os.makedirs(self.project_path)
            except OSError as e:
                self.show_error(f"Не удалось создать директорию проектов: {e}")
                return False
        return True
        
    def load_projects(self):
        """Загрузка списка проектов."""
        if not self.ensure_project_directory():
            return
            
        self.project_list.clear()
        
        try:
            for folder in os.listdir(self.project_path):
                folder_path = os.path.join(self.project_path, folder)
                if os.path.isdir(folder_path):
                    self.project_list.addItem(folder)
        except OSError as e:
            self.show_error(f"Ошибка при загрузке проектов: {e}")
            
    def create_project(self):
        """Создание нового проекта."""
        project_name, ok = QInputDialog.getText(
            self, 
            "Новый проект", 
            "Введите название проекта:"
        )
        
        if ok and project_name.strip():
            project_name = project_name.strip()
            project_full_path = os.path.join(self.project_path, project_name)
            
            if os.path.exists(project_full_path):
                self.show_warning("Проект с таким названием уже существует!")
                return
                
            try:
                os.makedirs(project_full_path)
                
                # Создание стандартных подпапок
                subfolders = [
                    "materials", "source_video", "source_notes", 
                    "source_images", "final_video", "final_audio",
                    "final_notes", "final_presentation"
                ]
                
                for subfolder in subfolders:
                    os.makedirs(os.path.join(project_full_path, subfolder), exist_ok=True)
                
                # Создание .avtogen файла с начальными данными
                self.create_avtogen_file(project_full_path, project_name)
                
                self.load_projects()
                self.select_project(project_name)
                self.show_info(f"Проект '{project_name}' успешно создан!")
                
            except OSError as e:
                self.show_error(f"Ошибка при создании проекта: {e}")
                
    def create_avtogen_file(self, project_path, project_name):
        """Создание .avtogen файла для проекта."""
        avtogen_file = os.path.join(project_path, f"{project_name}.avtogen")
        
        # Начальные данные проекта
        initial_data = {
            "Project_Name": project_name,
            "Offset": 0,
            "Slide_Style": "По умолчанию", 
            "Timings": 5,
            "Description": "",
            "Workflow_Status": {
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
        }
        
        try:
            with open(avtogen_file, 'w', encoding='utf-8') as f:
                json.dump(initial_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            self.show_error(f"Ошибка при создании .avtogen файла: {e}")
                
    def delete_project(self):
        """Удаление выбранного проекта."""
        current_item = self.project_list.currentItem()
        if not current_item:
            return
            
        project_name = current_item.text()
        
        reply = QMessageBox.question(
            self,
            "Подтверждение удаления",
            f"Вы действительно хотите удалить проект '{project_name}'?\n"
            "Все файлы проекта будут безвозвратно удалены!",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            project_path = os.path.join(self.project_path, project_name)
            try:
                shutil.rmtree(project_path)
                self.load_projects()
                self.current_project = None
                self.update_project_info()
                self.description_edit.clear()
                self.delete_btn.setEnabled(False)
                self.flow_btn.setEnabled(False)
                # Очищаем выделение
                self.project_list.clearSelection()
                self.show_info(f"Проект '{project_name}' успешно удален!")
                
            except OSError as e:
                self.show_error(f"Ошибка при удалении проекта: {e}")
                
    def on_project_selected(self, item):
        """Обработка выбора проекта."""
        if item is None:
            return
            
        project_name = item.text()
        self.current_project = project_name
        self.update_project_info()
        self.load_description()
        self.delete_btn.setEnabled(True)
        self.flow_btn.setEnabled(True)
        
        # Убеждаемся, что элемент остается выделенным
        self.project_list.setCurrentItem(item)
        
    def select_project(self, project_name):
        """Программный выбор проекта."""
        for i in range(self.project_list.count()):
            item = self.project_list.item(i)
            if item.text() == project_name:
                self.project_list.setCurrentItem(item)
                self.on_project_selected(item)
                break
                
    def update_project_info(self):
        """Обновление информации о проекте."""
        if self.current_project:
            full_path = os.path.join(self.project_path, self.current_project)
            self.project_info.setText(f"Проект: {self.current_project}\nПуть: {full_path}")
        else:
            self.project_info.setText("Выберите проект")
            
    def load_description(self):
        """Загрузка описания проекта из .avtogen файла."""
        if not self.current_project:
            return
            
        avtogen_file = os.path.join(
            self.project_path, 
            self.current_project, 
            f"{self.current_project}.avtogen"
        )
        
        try:
            if os.path.exists(avtogen_file):
                with open(avtogen_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    description = data.get("Description", "")
                    self.description_edit.setPlainText(description)
            else:
                # Если .avtogen файл не существует, создаем его
                self.create_avtogen_file(
                    os.path.join(self.project_path, self.current_project),
                    self.current_project
                )
                self.description_edit.clear()
        except Exception as e:
            self.show_error(f"Ошибка при загрузке описания: {e}")
            
    def save_description(self):
        """Сохранение описания проекта в .avtogen файл."""
        if not self.current_project:
            return
            
        avtogen_file = os.path.join(
            self.project_path, 
            self.current_project, 
            f"{self.current_project}.avtogen"
        )
        
        try:
            # Загружаем существующие данные или создаем новые
            if os.path.exists(avtogen_file):
                with open(avtogen_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "Project_Name": self.current_project,
                    "Offset": 0,
                    "Slide_Style": "По умолчанию",
                    "Timings": 5,
                    "Workflow_Status": {}
                }
            
            # Обновляем описание
            data["Description"] = self.description_edit.toPlainText()
            
            # Сохраняем файл
            with open(avtogen_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            self.show_error(f"Ошибка при сохранении описания: {e}")
            
    def get_project_avtogen_data(self, project_name):
        """Получение данных из .avtogen файла проекта."""
        avtogen_file = os.path.join(
            self.project_path, 
            project_name, 
            f"{project_name}.avtogen"
        )
        
        try:
            if os.path.exists(avtogen_file):
                with open(avtogen_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            self.show_error(f"Ошибка при чтении .avtogen файла: {e}")
            
        return None
        
    def open_flow_window(self):
        """Открытие окна управления ходом генерации."""
        if not self.current_project:
            self.show_warning("Сначала выберите проект!")
            return
            
        try:
            # Импортируем модуль с окном управления генерацией
            from flow_window import FlowGridWindow
            
            # Создаем и показываем окно, передавая информацию о проекте
            avtogen_data = self.get_project_avtogen_data(self.current_project)
            project_materials_path = os.path.join(self.project_path, self.current_project, "materials")
            
            self.flow_window = FlowGridWindow(
                project_name=self.current_project,
                project_path=os.path.join(self.project_path, self.current_project),
                avtogen_data=avtogen_data,
                materials_path=project_materials_path
            )
            self.flow_window.show()
            
        except ImportError:
            self.show_error("Модуль flow_window не найден!\nУбедитесь, что файл flow_window.py находится в той же папке.")
        except Exception as e:
            self.show_error(f"Ошибка при открытии окна управления: {e}")
            
    def show_error(self, message):
        """Показ сообщения об ошибке."""
        QMessageBox.critical(self, "Ошибка", message)
        
    def show_warning(self, message):
        """Показ предупреждения."""
        QMessageBox.warning(self, "Предупреждение", message)
        
    def show_info(self, message):
        """Показ информационного сообщения."""
        QMessageBox.information(self, "Информация", message)
            
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
    """Главная функция приложения."""
    app = QApplication(sys.argv)
    
    # Установка стиля приложения
    app.setStyle('Fusion')
    
    window = ProjectManager()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()