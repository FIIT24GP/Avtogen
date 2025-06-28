import sys
import os
import shutil
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
    QListWidget, QPushButton, QProgressBar, QMessageBox,
    QFileDialog, QFrame
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont, QDragEnterEvent, QDropEvent


class FileCopyWorker(QThread):
    """Поток для копирования файлов без блокировки UI"""
    progress = pyqtSignal(int)
    finished = pyqtSignal(bool, str)  # success, message
    file_copied = pyqtSignal(str)  # filename
    
    def __init__(self, files_to_copy, destination_path):
        super().__init__()
        self.files_to_copy = files_to_copy
        self.destination_path = destination_path
        
    def run(self):
        try:
            total_files = len(self.files_to_copy)
            copied_files = []
            
            for i, file_path in enumerate(self.files_to_copy):
                if not os.path.exists(file_path):
                    continue
                    
                filename = os.path.basename(file_path)
                destination_file = os.path.join(self.destination_path, filename)
                
                # Проверяем, не существует ли уже файл с таким именем
                counter = 1
                original_destination = destination_file
                while os.path.exists(destination_file):
                    name, ext = os.path.splitext(original_destination)
                    destination_file = f"{name}_{counter}{ext}"
                    counter += 1
                
                # Копируем файл
                shutil.copy2(file_path, destination_file)
                copied_files.append(os.path.basename(destination_file))
                
                # Обновляем прогресс
                progress_percent = int((i + 1) / total_files * 100)
                self.progress.emit(progress_percent)
                self.file_copied.emit(os.path.basename(destination_file))
                
            success_msg = f"Успешно скопировано {len(copied_files)} файлов"
            self.finished.emit(True, success_msg)
            
        except Exception as e:
            self.finished.emit(False, f"Ошибка при копировании: {str(e)}")


class FileDropWidget(QListWidget):
    """Виджет для drag-and-drop загрузки файлов"""
    files_dropped = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.setAcceptDrops(True)
        self.setMinimumHeight(200)
        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                font-size: 14px;
                padding: 20px;
            }
            QListWidget:hover {
                border-color: #007bff;
                background-color: #f0f8ff;
            }
        """)
        
        # Добавляем инструкцию
        self.addItem("📁 Перетащите файлы сюда или нажмите 'Выбрать файлы'")
        self.addItem("")
        self.addItem("Поддерживаемые форматы: PDF, DOCX, TXT")
        
    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            # Проверяем, что есть хотя бы один поддерживаемый файл
            valid_files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if self.is_supported_file(file_path):
                    valid_files.append(file_path)
            
            if valid_files:
                event.acceptProposedAction()
                self.setStyleSheet("""
                    QListWidget {
                        border: 2px solid #28a745;
                        border-radius: 10px;
                        background-color: #d4edda;
                        font-size: 14px;
                        padding: 20px;
                    }
                """)
        
    def dragLeaveEvent(self, event):
        self.setStyleSheet("""
            QListWidget {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                font-size: 14px;
                padding: 20px;
            }
            QListWidget:hover {
                border-color: #007bff;
                background-color: #f0f8ff;
            }
        """)
        
    def dropEvent(self, event: QDropEvent):
        files = []
        for url in event.mimeData().urls():
            file_path = url.toLocalFile()
            if self.is_supported_file(file_path):
                files.append(file_path)
        
        if files:
            self.files_dropped.emit(files)
            
        # Восстанавливаем стиль
        self.dragLeaveEvent(None)
        
    def is_supported_file(self, file_path):
        """Проверка поддерживаемых форматов"""
        supported_extensions = ['.pdf', '.docx', '.txt']
        return any(file_path.lower().endswith(ext) for ext in supported_extensions)


class VectorBaseUploader(QWidget):
    def __init__(self, materials_path=None):
        super().__init__()
        self.materials_path = materials_path or ""
        self.copy_worker = None
        self.setup_ui()
        self.setup_connections()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса"""
        self.setWindowTitle("Загрузка материалов для векторной базы")
        self.setMinimumSize(600, 500)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # Заголовок
        title = QLabel("Загрузка учебных материалов")
        title.setFont(QFont("Arial", 16, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        title.setStyleSheet("color: #333; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Информация о папке назначения
        if self.materials_path:
            path_frame = QFrame()
            path_frame.setFrameStyle(QFrame.StyledPanel)
            path_frame.setStyleSheet("background-color: #e8f4fd; border: 1px solid #bee5eb; border-radius: 5px; padding: 10px;")
            path_layout = QVBoxLayout(path_frame)
            
            path_label = QLabel("📂 Папка назначения:")
            path_label.setFont(QFont("Arial", 10, QFont.Bold))
            path_value = QLabel(self.materials_path)
            path_value.setStyleSheet("color: #0056b3; font-family: monospace;")
            path_value.setWordWrap(True)
            
            path_layout.addWidget(path_label)
            path_layout.addWidget(path_value)
            layout.addWidget(path_frame)
        
        # Инструкция
        instruction = QLabel("Добавьте текстовые материалы (PDF, DOCX, TXT) для создания базы знаний:")
        instruction.setFont(QFont("Arial", 12))
        instruction.setAlignment(Qt.AlignCenter)
        instruction.setStyleSheet("color: #666; margin: 10px 0;")
        layout.addWidget(instruction)
        
        # Область для drag-and-drop
        self.file_drop_widget = FileDropWidget()
        layout.addWidget(self.file_drop_widget)
        
        # Кнопки управления
        buttons_layout = QHBoxLayout()
        
        self.select_files_btn = QPushButton("📁 Выбрать файлы")
        self.select_files_btn.setStyleSheet(self.get_button_style("#007bff"))
        self.select_files_btn.setMinimumHeight(40)
        
        self.clear_btn = QPushButton("🗑️ Очистить список")
        self.clear_btn.setStyleSheet(self.get_button_style("#6c757d"))
        self.clear_btn.setMinimumHeight(40)
        
        buttons_layout.addWidget(self.select_files_btn)
        buttons_layout.addWidget(self.clear_btn)
        layout.addLayout(buttons_layout)
        
        # Прогресс-бар
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        self.progress_bar.setStyleSheet("""
            QProgressBar {
                border: 2px solid #dee2e6;
                border-radius: 5px;
                text-align: center;
                font-weight: bold;
                height: 25px;
            }
            QProgressBar::chunk {
                background-color: #28a745;
                border-radius: 3px;
            }
        """)
        layout.addWidget(self.progress_bar)
        
        # Статус
        self.status_label = QLabel("Готов к загрузке файлов")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setStyleSheet("color: #666; font-style: italic; margin-top: 10px;")
        layout.addWidget(self.status_label)
        
        # Список загруженных файлов
        self.files_list = QListWidget()
        self.files_list.setMaximumHeight(150)
        self.files_list.setVisible(False)
        layout.addWidget(self.files_list)
        
        self.setLayout(layout)
        
    def get_button_style(self, color):
        """Получение стиля для кнопок"""
        return f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                padding: 10px 20px;
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
        """
        
    def darken_color(self, color, factor=0.1):
        """Затемнение цвета для эффектов hover"""
        color = color.lstrip('#')
        rgb = tuple(int(color[i:i+2], 16) for i in (0, 2, 4))
        darkened = tuple(int(c * (1 - factor)) for c in rgb)
        return f"#{darkened[0]:02x}{darkened[1]:02x}{darkened[2]:02x}"
        
    def setup_connections(self):
        """Настройка соединений сигналов"""
        self.file_drop_widget.files_dropped.connect(self.handle_files)
        self.select_files_btn.clicked.connect(self.select_files)
        self.clear_btn.clicked.connect(self.clear_list)
        
    def select_files(self):
        """Выбор файлов через диалог"""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            "Выберите учебные материалы",
            "",
            "Учебные материалы (*.pdf *.docx *.txt);;PDF файлы (*.pdf);;Word документы (*.docx);;Текстовые файлы (*.txt)"
        )
        
        if files:
            self.handle_files(files)
            
    def handle_files(self, files):
        """Обработка выбранных файлов"""
        if not self.materials_path:
            self.show_error("Ошибка: не указана папка проекта для сохранения файлов!")
            return
            
        if not os.path.exists(self.materials_path):
            try:
                os.makedirs(self.materials_path, exist_ok=True)
            except Exception as e:
                self.show_error(f"Не удалось создать папку: {e}")
                return
        
        # Фильтруем поддерживаемые файлы
        valid_files = []
        for file_path in files:
            if os.path.exists(file_path) and self.file_drop_widget.is_supported_file(file_path):
                valid_files.append(file_path)
                
        if not valid_files:
            self.show_warning("Не найдено поддерживаемых файлов!")
            return
            
        # Показываем список файлов для копирования
        self.update_file_list(valid_files)
        
        # Запускаем копирование
        self.start_file_copy(valid_files)
        
    def update_file_list(self, files):
        """Обновление списка файлов"""
        self.file_drop_widget.clear()
        for file_path in files:
            filename = os.path.basename(file_path)
            size = self.get_file_size(file_path)
            self.file_drop_widget.addItem(f"📄 {filename} ({size})")
            
    def get_file_size(self, file_path):
        """Получение размера файла в читаемом формате"""
        try:
            size = os.path.getsize(file_path)
            for unit in ['Б', 'КБ', 'МБ', 'ГБ']:
                if size < 1024.0:
                    return f"{size:.1f} {unit}"
                size /= 1024.0
            return f"{size:.1f} ТБ"
        except:
            return "неизвестно"
            
    def start_file_copy(self, files):
        """Запуск копирования файлов"""
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.status_label.setText("Копирование файлов...")
        self.select_files_btn.setEnabled(False)
        self.clear_btn.setEnabled(False)
        
        # Создаем и запускаем рабочий поток
        self.copy_worker = FileCopyWorker(files, self.materials_path)
        self.copy_worker.progress.connect(self.update_progress)
        self.copy_worker.file_copied.connect(self.on_file_copied)
        self.copy_worker.finished.connect(self.on_copy_finished)
        self.copy_worker.start()
        
    def update_progress(self, value):
        """Обновление прогресс-бара"""
        self.progress_bar.setValue(value)
        
    def on_file_copied(self, filename):
        """Обработка события копирования файла"""
        self.status_label.setText(f"Скопирован: {filename}")
        
    def on_copy_finished(self, success, message):
        """Завершение копирования"""
        self.progress_bar.setVisible(False)
        self.select_files_btn.setEnabled(True)
        self.clear_btn.setEnabled(True)
        
        if success:
            self.status_label.setText(f"✅ {message}")
            self.show_success("Файлы успешно загружены в папку проекта!")
        else:
            self.status_label.setText(f"❌ {message}")
            self.show_error(message)
            
        # Очищаем ссылку на поток
        self.copy_worker = None
        
    def clear_list(self):
        """Очистка списка файлов"""
        self.file_drop_widget.clear()
        self.file_drop_widget.addItem("📁 Перетащите файлы сюда или нажмите 'Выбрать файлы'")
        self.file_drop_widget.addItem("")
        self.file_drop_widget.addItem("Поддерживаемые форматы: PDF, DOCX, TXT")
        self.status_label.setText("Готов к загрузке файлов")
        
    def closeEvent(self, event):
        """Обработка закрытия окна"""
        if self.copy_worker and self.copy_worker.isRunning():
            reply = QMessageBox.question(
                self,
                "Копирование в процессе",
                "Идёт копирование файлов. Закрыть окно?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.copy_worker.terminate()
                self.copy_worker.wait()
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()
            
    def show_error(self, message):
        """Показ сообщения об ошибке"""
        QMessageBox.critical(self, "Ошибка", message)
        
    def show_warning(self, message):
        """Показ предупреждения"""
        QMessageBox.warning(self, "Предупреждение", message)
        
    def show_success(self, message):
        """Показ сообщения об успехе"""
        QMessageBox.information(self, "Успех", message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    
    # Тестовый запуск
    test_path = "C:/test_materials"
    window = VectorBaseUploader(materials_path=test_path)
    window.show()
    
    sys.exit(app.exec_())