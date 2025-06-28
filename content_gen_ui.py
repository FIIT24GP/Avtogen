import sys
import os
from PyQt5.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QPushButton,
    QLineEdit, QListWidget, QLabel, QHBoxLayout,
    QComboBox, QProgressBar, QMessageBox, QSpinBox,
    QGroupBox, QTextEdit, QSplitter
)
from PyQt5.QtCore import QThread, pyqtSignal, Qt
from PyQt5.QtGui import QFont

# Импорт сервиса
from content_generation_service import ContentGenerationService


class ContentGenerationThread(QThread):
    """Поток для асинхронной генерации контента"""
    result_ready = pyqtSignal(str)
    error_occurred = pyqtSignal(str)
    chunk_ready = pyqtSignal(str)  # Для потокового вывода
    
    def __init__(self, service, content, level, model_name, temperature, max_tokens, top_p, rerank_method):
        super().__init__()
        self.service = service
        self.content = content
        self.level = level
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.top_p = top_p
        self.rerank_method = rerank_method
        
    def run(self):
        try:
            result = ""
            for chunk in self.service.generate_content(
                self.content, 
                self.level,
                self.model_name,
                self.temperature,
                self.max_tokens,
                self.top_p,
                self.rerank_method
            ):
                result += chunk
                self.chunk_ready.emit(chunk)
            
            self.result_ready.emit(result)
            
        except Exception as e:
            self.error_occurred.emit(str(e))


class VectorBaseLoadThread(QThread):
    """Поток для загрузки векторной базы"""
    finished = pyqtSignal(bool)
    progress_message = pyqtSignal(str)
    
    def __init__(self, service):
        super().__init__()
        self.service = service
        
    def run(self):
        try:
            self.progress_message.emit("Загрузка материалов...")
            success = self.service.load_vector_base()
            self.finished.emit(success)
        except Exception as e:
            self.progress_message.emit(f"Ошибка: {e}")
            self.finished.emit(False)


class ContentGenerationGUI(QWidget):
    def __init__(self, materials_path=None):
        super().__init__()
        self.materials_path = materials_path or "materials"
        self.service = ContentGenerationService(self.materials_path)
        self.current_generation_thread = None
        
        # Данные по этапам генерации
        self.generated_topics = []  # Список тем для лекций
        self.selected_topic = ""    # Выбранная тема
        self.generated_headers = [] # Заголовки слайдов
        self.generated_theses = []  # Тезисы слайдов
        self.generated_lecture = [] # Тексты лекций
        
        self.setup_ui()
        self.load_vector_base_async()
        
    def setup_ui(self):
        """Настройка пользовательского интерфейса по алгоритму из Приложения Б"""
        self.setWindowTitle("Генерация учебных материалов - RAG система")
        self.resize(1200, 800)

        # Главный layout с разделителем
        main_layout = QHBoxLayout()
        splitter = QSplitter(Qt.Horizontal)
        
        # Левая панель - настройки и управление
        left_panel = self.create_control_panel()
        splitter.addWidget(left_panel)
        
        # Правая панель - результаты генерации
        right_panel = self.create_results_panel()
        splitter.addWidget(right_panel)
        
        splitter.setSizes([400, 800])
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
        
    def create_control_panel(self):
        """Создание левой панели управления"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Заголовок
        title = QLabel("🎓 Генерация учебных материалов")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # 1. Настройки модели
        self.create_model_settings_group(layout)
        
        # 2. Шаг 1: Базовый промт
        self.create_initial_prompt_group(layout)
        
        # 3. Шаг 2: Выбор темы лекции
        self.create_topic_selection_group(layout)
        
        # 4. Управление итерациями
        self.create_iteration_control_group(layout)
        
        # 5. Сохранение результатов
        self.create_save_group(layout)
        
        # 6. Статус
        self.create_status_group(layout)
        
        layout.addStretch()
        return panel
        
    def create_model_settings_group(self, layout):
        """Группа настроек модели"""
        group = QGroupBox("⚙️ Настройки модели")
        group_layout = QVBoxLayout()
        
        # Модель
        model_layout = QHBoxLayout()
        model_layout.addWidget(QLabel("Модель:"))
        self.model_combo = QComboBox()
        self.model_combo.addItem("Загрузка...")
        model_layout.addWidget(self.model_combo)
        group_layout.addLayout(model_layout)
        
        # Параметры
        params_layout = QHBoxLayout()
        
        params_layout.addWidget(QLabel("T:"))
        self.temperature_combo = QComboBox()
        self.temperature_combo.addItems(["0.1", "0.2", "0.3", "0.4", "0.5"])
        self.temperature_combo.setCurrentText("0.2")
        params_layout.addWidget(self.temperature_combo)
        
        params_layout.addWidget(QLabel("Tokens:"))
        self.max_tokens_combo = QComboBox()
        self.max_tokens_combo.addItems(["1000", "1500", "2000", "3000"])
        self.max_tokens_combo.setCurrentText("1500")
        params_layout.addWidget(self.max_tokens_combo)
        
        params_layout.addWidget(QLabel("Rerank:"))
        self.rerank_combo = QComboBox()
        self.rerank_combo.addItems(["BM25", "TF-IDF"])
        params_layout.addWidget(self.rerank_combo)
        
        group_layout.addLayout(params_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def create_initial_prompt_group(self, layout):
        """Группа для базового промта (Шаг 1)"""
        group = QGroupBox("1️⃣ Базовый промт")
        group_layout = QVBoxLayout()
        
        # Тема курса
        group_layout.addWidget(QLabel("Общая тема курса:"))
        self.topic_input = QLineEdit()
        self.topic_input.setPlaceholderText("Например: Реляционные базы данных")
        group_layout.addWidget(self.topic_input)
        
        # Количество лекций
        lectures_layout = QHBoxLayout()
        lectures_layout.addWidget(QLabel("Количество лекций:"))
        self.lectures_count = QSpinBox()
        self.lectures_count.setRange(1, 20)
        self.lectures_count.setValue(10)
        lectures_layout.addWidget(self.lectures_count)
        lectures_layout.addStretch()
        group_layout.addLayout(lectures_layout)
        
        # Кнопка генерации списка тем
        self.generate_topics_btn = QPushButton("🔍 Найти темы для лекций")
        self.generate_topics_btn.clicked.connect(self.generate_lecture_topics)
        group_layout.addWidget(self.generate_topics_btn)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def create_topic_selection_group(self, layout):
        """Группа выбора конкретной темы лекции (Шаг 2)"""
        group = QGroupBox("2️⃣ Выбор темы лекции")
        group_layout = QVBoxLayout()
        
        group_layout.addWidget(QLabel("Выберите тему для детальной разработки:"))
        self.topics_list = QListWidget()
        self.topics_list.setMaximumHeight(150)
        self.topics_list.itemClicked.connect(self.on_topic_selected)
        group_layout.addWidget(self.topics_list)
        
        # Выбранная тема
        self.selected_topic_label = QLabel("Тема не выбрана")
        self.selected_topic_label.setStyleSheet("font-weight: bold; color: #0066cc;")
        self.selected_topic_label.setWordWrap(True)
        group_layout.addWidget(self.selected_topic_label)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def create_iteration_control_group(self, layout):
        """Группа управления итерациями (Уровни 1-3)"""
        group = QGroupBox("3️⃣ Пошаговая генерация")
        group_layout = QVBoxLayout()
        
        # Уровень 1: Заголовки слайдов
        level1_layout = QHBoxLayout()
        self.generate_headers_btn = QPushButton("📝 1. Генерировать заголовки слайдов")
        self.generate_headers_btn.clicked.connect(self.generate_slide_headers)
        self.generate_headers_btn.setEnabled(False)
        level1_layout.addWidget(self.generate_headers_btn)
        group_layout.addLayout(level1_layout)
        
        # Уровень 2: Тезисы
        level2_layout = QHBoxLayout()
        self.generate_theses_btn = QPushButton("📋 2. Генерировать тезисы по слайду")
        self.generate_theses_btn.clicked.connect(self.generate_slide_theses)
        self.generate_theses_btn.setEnabled(False)
        level2_layout.addWidget(self.generate_theses_btn)
        group_layout.addLayout(level2_layout)
        
        # Уровень 3: Развернутый текст
        level3_layout = QHBoxLayout()
        self.generate_lecture_btn = QPushButton("📚 3. Генерировать развернутый текст")
        self.generate_lecture_btn.clicked.connect(self.generate_lecture_text)
        self.generate_lecture_btn.setEnabled(False)
        level3_layout.addWidget(self.generate_lecture_btn)
        group_layout.addLayout(level3_layout)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def create_save_group(self, layout):
        """Группа сохранения результатов"""
        group = QGroupBox("💾 Сохранение")
        group_layout = QVBoxLayout()
        
        save_layout = QHBoxLayout()
        
        self.save_intermediate_btn = QPushButton("Промежуточные")
        self.save_intermediate_btn.clicked.connect(self.save_intermediate)
        save_layout.addWidget(self.save_intermediate_btn)
        
        self.save_final_btn = QPushButton("Итоговая лекция")
        self.save_final_btn.clicked.connect(self.save_final)
        save_layout.addWidget(self.save_final_btn)
        
        group_layout.addLayout(save_layout)
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def create_status_group(self, layout):
        """Группа статуса"""
        group = QGroupBox("📊 Статус")
        group_layout = QVBoxLayout()
        
        self.status_label = QLabel("🔄 Инициализация...")
        self.status_label.setWordWrap(True)
        group_layout.addWidget(self.status_label)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        group_layout.addWidget(self.progress_bar)
        
        group.setLayout(group_layout)
        layout.addWidget(group)
        
    def create_results_panel(self):
        """Создание правой панели с результатами"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        
        # Заголовок
        title = QLabel("📄 Результаты генерации")
        title.setFont(QFont("Arial", 14, QFont.Bold))
        title.setAlignment(Qt.AlignCenter)
        layout.addWidget(title)
        
        # Вкладки для разных уровней
        # Уровень 1: Заголовки слайдов
        layout.addWidget(QLabel("1️⃣ Заголовки слайдов (15 шт.):"))
        self.headers_list = QListWidget()
        self.headers_list.setMaximumHeight(200)
        self.headers_list.itemClicked.connect(self.on_header_selected)
        layout.addWidget(self.headers_list)
        
        # Уровень 2: Тезисы выбранного слайда
        self.current_header_label = QLabel("Выберите заголовок слайда ☝️")
        self.current_header_label.setStyleSheet("font-weight: bold; background-color: #f0f0f0; padding: 5px;")
        self.current_header_label.setWordWrap(True)
        layout.addWidget(self.current_header_label)
        
        layout.addWidget(QLabel("2️⃣ Тезисы слайда (5-7 пунктов):"))
        self.theses_list = QListWidget()
        self.theses_list.setMaximumHeight(150)
        self.theses_list.itemClicked.connect(self.on_thesis_selected)
        layout.addWidget(self.theses_list)
        
        # Уровень 3: Развернутый текст
        layout.addWidget(QLabel("3️⃣ Развернутый текст лекции (~5 мин):"))
        self.lecture_text = QTextEdit()
        self.lecture_text.setReadOnly(True)
        layout.addWidget(self.lecture_text)
        
        return panel
        
    def load_vector_base_async(self):
        """Асинхронная загрузка векторной базы"""
        self.status_label.setText("🔄 Загрузка базы знаний...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        self.vector_load_thread = VectorBaseLoadThread(self.service)
        self.vector_load_thread.progress_message.connect(self.update_status)
        self.vector_load_thread.finished.connect(self.on_vector_base_loaded)
        self.vector_load_thread.start()
        
    def on_vector_base_loaded(self, success):
        """Обработка результата загрузки векторной базы"""
        self.progress_bar.setVisible(False)
        
        if success:
            self.status_label.setText("✅ База знаний загружена. Готов к работе.")
            self.load_available_models()
        else:
            self.status_label.setText("⚠️ База знаний не загружена. Работа без RAG.")
            QMessageBox.warning(self, "Предупреждение", 
                               "База знаний не загружена. Генерация будет работать без контекста.")
        
    def load_available_models(self):
        """Загрузка списка доступных моделей"""
        try:
            models = self.service.get_available_models()
            self.model_combo.clear()
            self.model_combo.addItems(models)
        except Exception as e:
            self.model_combo.clear()
            self.model_combo.addItem("hf.co/t-tech/T-lite-it-1.0-Q8_0-GGUF:Q8_0")
            
    def update_status(self, message):
        """Обновление статуса"""
        self.status_label.setText(message)
        
    def get_generation_params(self):
        """Получение параметров генерации"""
        return {
            'model_name': self.model_combo.currentText(),
            'temperature': float(self.temperature_combo.currentText()),
            'max_tokens': int(self.max_tokens_combo.currentText()),
            'top_p': 0.3,
            'rerank_method': self.rerank_combo.currentText()
        }
        
    def set_ui_enabled(self, enabled):
        """Включение/отключение UI во время генерации"""
        self.generate_topics_btn.setEnabled(enabled)
        self.generate_headers_btn.setEnabled(enabled and bool(self.selected_topic))
        self.generate_theses_btn.setEnabled(enabled and len(self.headers_list.selectedItems()) > 0)
        self.generate_lecture_btn.setEnabled(enabled and len(self.theses_list.selectedItems()) > 0)
        
    # === ОСНОВНЫЕ МЕТОДЫ ГЕНЕРАЦИИ ===
    
    def generate_lecture_topics(self):
        """Шаг 1: Генерация списка тем для лекций"""
        topic = self.topic_input.text().strip()
        count = self.lectures_count.value()
        
        if not topic:
            QMessageBox.warning(self, "Ошибка", "Введите общую тему курса")
            return
            
        # Создаем базовый промт как в Приложении Б
        base_prompt = f"Общая тема: {topic}, количество лекций: {count}"
        
        self.start_generation(base_prompt, 0, "🔍 Поиск тем для лекций в базе знаний...")
        
    def generate_slide_headers(self):
        """Уровень 1: Генерация заголовков слайдов"""
        if not self.selected_topic:
            QMessageBox.warning(self, "Ошибка", "Сначала выберите тему лекции")
            return
            
        self.start_generation(self.selected_topic, 1, "📝 Генерация заголовков слайдов...")
        
    def generate_slide_theses(self):
        """Уровень 2: Генерация тезисов слайда"""
        selected_items = self.headers_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите заголовок слайда")
            return
            
        header = selected_items[0].text()
        self.start_generation(header, 2, "📋 Генерация тезисов слайда...")
        
    def generate_lecture_text(self):
        """Уровень 3: Генерация развернутого текста лекции"""
        selected_items = self.theses_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "Ошибка", "Выберите тезис из списка")
            return
            
        # Собираем все тезисы текущего слайда
        all_theses = []
        for i in range(self.theses_list.count()):
            all_theses.append(self.theses_list.item(i).text())
        
        theses_text = "\n".join(all_theses)
        header = self.current_header_label.text().replace("Выбранный слайд: ", "")
        
        content = f"Заголовок: {header}\n\nТезисы:\n{theses_text}"
        self.start_generation(content, 3, "📚 Генерация развернутого текста лекции...")
        
    def start_generation(self, content, level, status_message):
        """Запуск генерации контента"""
        self.set_ui_enabled(False)
        self.status_label.setText(status_message)
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)
        
        params = self.get_generation_params()
        
        self.current_generation_thread = ContentGenerationThread(
            self.service, content, level, **params
        )
        
        self.current_generation_thread.result_ready.connect(
            lambda result: self.on_generation_finished(result, level)
        )
        self.current_generation_thread.error_occurred.connect(self.on_generation_error)
        self.current_generation_thread.start()
        
    def on_generation_finished(self, result, level):
        """Обработка завершения генерации"""
        self.progress_bar.setVisible(False)
        self.set_ui_enabled(True)
        
        if level == 0:  # Список тем для лекций
            topics = self.service.parse_theses(result)
            self.generated_topics = topics
            self.topics_list.clear()
            self.topics_list.addItems(topics)
            self.status_label.setText(f"✅ Найдено {len(topics)} тем для лекций")
            
        elif level == 1:  # Заголовки слайдов
            headers = self.service.parse_theses(result)
            self.generated_headers = headers
            self.headers_list.clear()
            self.headers_list.addItems(headers)
            self.status_label.setText(f"✅ Сгенерировано {len(headers)} заголовков слайдов")
            
        elif level == 2:  # Тезисы слайда
            theses = self.service.parse_theses(result)
            self.generated_theses = theses
            self.theses_list.clear()
            self.theses_list.addItems(theses)
            self.status_label.setText(f"✅ Сгенерировано {len(theses)} тезисов")
            self.generate_lecture_btn.setEnabled(True)
            
        elif level == 3:  # Развернутый текст
            self.generated_lecture.append(result)
            self.lecture_text.setPlainText(result)
            self.status_label.setText("✅ Развернутый текст лекции готов")
            
    def on_generation_error(self, error_msg):
        """Обработка ошибок генерации"""
        self.progress_bar.setVisible(False)
        self.set_ui_enabled(True)
        self.status_label.setText("❌ Ошибка генерации")
        QMessageBox.critical(self, "Ошибка", f"Произошла ошибка: {error_msg}")
        
    # === ОБРАБОТЧИКИ ВЫБОРА ===
    
    def on_topic_selected(self, item):
        """Обработка выбора темы лекции"""
        self.selected_topic = item.text()
        self.selected_topic_label.setText(f"Выбранная тема: {self.selected_topic}")
        self.generate_headers_btn.setEnabled(True)
        
        # Очищаем результаты предыдущей темы
        self.headers_list.clear()
        self.theses_list.clear()
        self.lecture_text.clear()
        self.current_header_label.setText("Выберите заголовок слайда ☝️")
        
    def on_header_selected(self, item):
        """Обработка выбора заголовка слайда"""
        header = item.text()
        self.current_header_label.setText(f"Выбранный слайд: {header}")
        self.generate_theses_btn.setEnabled(True)
        
        # Очищаем предыдущие тезисы и текст
        self.theses_list.clear()
        self.lecture_text.clear()
        
    def on_thesis_selected(self, item):
        """Обработка выбора тезиса"""
        self.generate_lecture_btn.setEnabled(True)
        
    # === СОХРАНЕНИЕ ===
    
    def save_intermediate(self):
        """Сохранение промежуточных результатов"""
        if not self.generated_headers and not self.generated_theses:
            QMessageBox.warning(self, "Предупреждение", "Нет данных для сохранения")
            return
            
        try:
            filename = f"intermediate_{self.selected_topic.replace(' ', '_')}.txt"
            success = self.service.save_intermediate_results(
                self.generated_headers, self.generated_theses, filename
            )
            
            if success:
                QMessageBox.information(self, "Успех", f"Промежуточные результаты сохранены в {filename}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить файл")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")

    def save_final(self):
        """Сохранение итогового текста лекции"""
        if not self.generated_lecture:
            QMessageBox.warning(self, "Предупреждение", "Нет текста лекции для сохранения")
            return
            
        try:
            filename = f"lecture_{self.selected_topic.replace(' ', '_')}.txt"
            success = self.service.save_final_lecture(self.generated_lecture, filename)
            
            if success:
                QMessageBox.information(self, "Успех", f"Итоговая лекция сохранена в {filename}")
            else:
                QMessageBox.critical(self, "Ошибка", "Не удалось сохранить файл")
                
        except Exception as e:
            QMessageBox.critical(self, "Ошибка", f"Ошибка сохранения: {e}")