import sqlite3
import json
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
from contextlib import contextmanager


class DatabaseManager:
    """Менеджер базы данных для проектов генерации учебных материалов"""
    
    def __init__(self, db_path: str = "projects.db"):
        self.db_path = db_path
        self.init_database()
        
    def init_database(self):
        """Инициализация базы данных с созданием всех таблиц"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Создание таблиц
            cursor.executescript("""
                -- Таблица проектов
                CREATE TABLE IF NOT EXISTS projects (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    path TEXT NOT NULL,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    status TEXT DEFAULT 'not_started',
                    description TEXT DEFAULT '',
                    config TEXT DEFAULT '{}',  -- JSON конфигурация из .avtogen
                    CONSTRAINT chk_status CHECK (status IN ('not_started', 'in_progress', 'completed', 'error'))
                );
                
                -- Таблица модулей системы
                CREATE TABLE IF NOT EXISTS modules (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    display_name TEXT NOT NULL,
                    description TEXT,
                    module_type TEXT NOT NULL,  -- 'forward', 'reverse', 'common'
                    order_index INTEGER DEFAULT 0,
                    is_active BOOLEAN DEFAULT 1
                );
                
                -- Таблица выполнения модулей
                CREATE TABLE IF NOT EXISTS executions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    module_id INTEGER NOT NULL,
                    started_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    finished_at DATETIME,
                    status TEXT DEFAULT 'not_started',
                    progress INTEGER DEFAULT 0,  -- процент выполнения 0-100
                    error_message TEXT,
                    log_path TEXT,
                    input_files TEXT,  -- JSON список входных файлов
                    output_files TEXT,  -- JSON список выходных файлов
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    FOREIGN KEY (module_id) REFERENCES modules (id),
                    CONSTRAINT chk_exec_status CHECK (status IN ('not_started', 'in_progress', 'completed', 'error', 'skipped')),
                    CONSTRAINT chk_progress CHECK (progress >= 0 AND progress <= 100)
                );
                
                -- Таблица артефактов проекта
                CREATE TABLE IF NOT EXISTS artifacts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    project_id INTEGER NOT NULL,
                    execution_id INTEGER,  -- связь с выполнением модуля
                    name TEXT NOT NULL,  -- transcript, slides, audio, video, images
                    display_name TEXT,
                    file_path TEXT NOT NULL,
                    file_format TEXT,  -- pdf, pptx, mp3, mp4, json, txt
                    file_size INTEGER DEFAULT 0,  -- размер в байтах
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    is_final BOOLEAN DEFAULT 0,  -- итоговый или промежуточный
                    metadata TEXT DEFAULT '{}',  -- JSON метаданные (длительность, разрешение и т.д.)
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    FOREIGN KEY (execution_id) REFERENCES executions (id) ON DELETE SET NULL
                );
                
                -- Таблица логов выполнения
                CREATE TABLE IF NOT EXISTS logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    execution_id INTEGER,
                    project_id INTEGER,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    level TEXT NOT NULL,  -- DEBUG, INFO, WARNING, ERROR, CRITICAL
                    module_name TEXT,
                    message TEXT NOT NULL,
                    details TEXT,  -- дополнительная информация в JSON
                    FOREIGN KEY (execution_id) REFERENCES executions (id) ON DELETE CASCADE,
                    FOREIGN KEY (project_id) REFERENCES projects (id) ON DELETE CASCADE,
                    CONSTRAINT chk_log_level CHECK (level IN ('DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'))
                );
                
                -- Таблица конфигурации системы
                CREATE TABLE IF NOT EXISTS system_config (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key TEXT NOT NULL UNIQUE,
                    value TEXT NOT NULL,
                    description TEXT,
                    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
                );
                
                -- Индексы для улучшения производительности
                CREATE INDEX IF NOT EXISTS idx_projects_name ON projects (name);
                CREATE INDEX IF NOT EXISTS idx_projects_status ON projects (status);
                CREATE INDEX IF NOT EXISTS idx_executions_project_module ON executions (project_id, module_id);
                CREATE INDEX IF NOT EXISTS idx_executions_status ON executions (status);
                CREATE INDEX IF NOT EXISTS idx_artifacts_project ON artifacts (project_id);
                CREATE INDEX IF NOT EXISTS idx_logs_execution ON logs (execution_id);
                CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp);
                
                -- Триггеры для автоматического обновления времени
                CREATE TRIGGER IF NOT EXISTS update_projects_timestamp 
                    AFTER UPDATE ON projects
                    BEGIN
                        UPDATE projects SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                    END;
            """)
            
            # Заполнение базовых модулей
            self._populate_initial_modules(cursor)
            
            conn.commit()
            
    def _populate_initial_modules(self, cursor):
        """Заполнение таблицы модулей базовыми данными"""
        modules = [
            # Прямой ход (forward)
            ('materials_upload', 'Материалы для базы', 'Загрузка учебных материалов', 'forward', 1),
            ('content_generation', 'Генерация контента', 'Создание конспекта и тезисов', 'forward', 2),
            ('image_processing', 'Обработка изображений', 'Работа с ключевыми кадрами', 'forward', 3),
            ('final_content', 'Финальный контент', 'Создание итогового конспекта', 'forward', 4),
            ('presentation_gen', 'Генерация презентации', 'Создание презентации PPTX', 'forward', 5),
            ('audio_generation', 'Генерация аудио', 'Синтез речи', 'forward', 6),
            ('video_compilation', 'Сведение видео', 'Создание итогового видео', 'forward', 7),
            
            # Обратный ход (reverse)
            ('source_video', 'Видео исходное', 'Обработка исходного видео', 'reverse', 1),
            ('keyframe_extraction', 'Извлечение кадров', 'Выделение ключевых слайдов', 'reverse', 2),
            ('audio_recognition', 'Распознавание аудио', 'Транскрипция речи', 'reverse', 3),
            ('text_cleaning', 'Очистка текста', 'Удаление шумов из текста', 'reverse', 4),
            ('reverse_content', 'Обработка контента', 'Структурирование извлеченного контента', 'reverse', 5),
            
            # Общие модули (common)
            ('vector_base', 'Векторная база', 'Создание векторной базы знаний', 'common', 1),
            ('monitoring', 'Мониторинг', 'Отслеживание ресурсов системы', 'common', 2),
        ]
        
        cursor.executemany("""
            INSERT OR IGNORE INTO modules (name, display_name, description, module_type, order_index)
            VALUES (?, ?, ?, ?, ?)
        """, modules)
        
    @contextmanager
    def get_connection(self):
        """Контекстный менеджер для работы с соединением БД"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row  # Возвращает строки как словари
        try:
            yield conn
        finally:
            conn.close()
            
    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПРОЕКТАМИ ===
    
    def create_project(self, name: str, path: str, description: str = "", config: dict = None) -> int:
        """Создание нового проекта"""
        config = config or {}
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO projects (name, path, description, config)
                VALUES (?, ?, ?, ?)
            """, (name, path, description, json.dumps(config)))
            
            project_id = cursor.lastrowid
            
            # Создаем записи выполнения для всех модулей
            cursor.execute("SELECT id FROM modules WHERE is_active = 1")
            modules = cursor.fetchall()
            
            for module in modules:
                cursor.execute("""
                    INSERT INTO executions (project_id, module_id, status)
                    VALUES (?, ?, 'not_started')
                """, (project_id, module['id']))
            
            conn.commit()
            return project_id
            
    def get_project(self, project_id: int) -> Optional[Dict]:
        """Получение проекта по ID"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE id = ?", (project_id,))
            row = cursor.fetchone()
            
            if row:
                project = dict(row)
                project['config'] = json.loads(project['config'])
                return project
            return None
            
    def get_project_by_name(self, name: str) -> Optional[Dict]:
        """Получение проекта по имени"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM projects WHERE name = ?", (name,))
            row = cursor.fetchone()
            
            if row:
                project = dict(row)
                project['config'] = json.loads(project['config'])
                return project
            return None
            
    def get_all_projects(self) -> List[Dict]:
        """Получение всех проектов"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name, path, created_at, updated_at, status, description
                FROM projects ORDER BY updated_at DESC
            """)
            return [dict(row) for row in cursor.fetchall()]
            
    def update_project(self, project_id: int, **kwargs) -> bool:
        """Обновление проекта"""
        if not kwargs:
            return False
            
        # Специальная обработка config
        if 'config' in kwargs and isinstance(kwargs['config'], dict):
            kwargs['config'] = json.dumps(kwargs['config'])
            
        set_clause = ", ".join([f"{key} = ?" for key in kwargs.keys()])
        values = list(kwargs.values()) + [project_id]
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
                UPDATE projects SET {set_clause} WHERE id = ?
            """, values)
            conn.commit()
            return cursor.rowcount > 0
            
    def delete_project(self, project_id: int) -> bool:
        """Удаление проекта (каскадное удаление всех связанных данных)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM projects WHERE id = ?", (project_id,))
            conn.commit()
            return cursor.rowcount > 0
            
    # === МЕТОДЫ ДЛЯ РАБОТЫ С МОДУЛЯМИ ===
    
    def get_modules(self, module_type: str = None) -> List[Dict]:
        """Получение модулей (опционально по типу)"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            if module_type:
                cursor.execute("""
                    SELECT * FROM modules 
                    WHERE module_type = ? AND is_active = 1 
                    ORDER BY order_index
                """, (module_type,))
            else:
                cursor.execute("""
                    SELECT * FROM modules 
                    WHERE is_active = 1 
                    ORDER BY module_type, order_index
                """)
                
            return [dict(row) for row in cursor.fetchall()]
            
    def get_module_by_name(self, name: str) -> Optional[Dict]:
        """Получение модуля по имени"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM modules WHERE name = ?", (name,))
            row = cursor.fetchone()
            return dict(row) if row else None
            
    # === МЕТОДЫ ДЛЯ РАБОТЫ С ВЫПОЛНЕНИЕМ МОДУЛЕЙ ===
    
    def get_project_executions(self, project_id: int) -> List[Dict]:
        """Получение всех выполнений модулей для проекта"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.*, m.name as module_name, m.display_name, m.module_type
                FROM executions e
                JOIN modules m ON e.module_id = m.id
                WHERE e.project_id = ?
                ORDER BY m.module_type, m.order_index
            """, (project_id,))
            
            return [dict(row) for row in cursor.fetchall()]
            
    def update_execution_status(self, project_id: int, module_name: str, 
                              status: str, progress: int = None, 
                              error_message: str = None) -> bool:
        """Обновление статуса выполнения модуля"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Получаем execution_id
            cursor.execute("""
                SELECT e.id FROM executions e
                JOIN modules m ON e.module_id = m.id
                WHERE e.project_id = ? AND m.name = ?
            """, (project_id, module_name))
            
            row = cursor.fetchone()
            if not row:
                return False
                
            execution_id = row['id']
            
            # Обновляем статус
            update_fields = ["status = ?"]
            values = [status]
            
            if progress is not None:
                update_fields.append("progress = ?")
                values.append(progress)
                
            if error_message is not None:
                update_fields.append("error_message = ?")
                values.append(error_message)
                
            if status == 'in_progress' and progress is None:
                update_fields.append("started_at = CURRENT_TIMESTAMP")
            elif status in ['completed', 'error']:
                update_fields.append("finished_at = CURRENT_TIMESTAMP")
                
            values.append(execution_id)
            
            cursor.execute(f"""
                UPDATE executions SET {', '.join(update_fields)} WHERE id = ?
            """, values)
            
            conn.commit()
            return cursor.rowcount > 0
            
    def get_execution_status(self, project_id: int, module_name: str) -> Optional[str]:
        """Получение статуса выполнения модуля"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT e.status FROM executions e
                JOIN modules m ON e.module_id = m.id
                WHERE e.project_id = ? AND m.name = ?
            """, (project_id, module_name))
            
            row = cursor.fetchone()
            return row['status'] if row else None
            
    # === МЕТОДЫ ДЛЯ РАБОТЫ С АРТЕФАКТАМИ ===
    
    def add_artifact(self, project_id: int, name: str, file_path: str,
                    file_format: str = None, display_name: str = None,
                    execution_id: int = None, is_final: bool = False,
                    metadata: dict = None) -> int:
        """Добавление артефакта"""
        metadata = metadata or {}
        file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO artifacts 
                (project_id, execution_id, name, display_name, file_path, 
                 file_format, file_size, is_final, metadata)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (project_id, execution_id, name, display_name, file_path,
                  file_format, file_size, is_final, json.dumps(metadata)))
            
            conn.commit()
            return cursor.lastrowid
            
    def get_project_artifacts(self, project_id: int, is_final: bool = None) -> List[Dict]:
        """Получение артефактов проекта"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM artifacts WHERE project_id = ?"
            params = [project_id]
            
            if is_final is not None:
                query += " AND is_final = ?"
                params.append(is_final)
                
            query += " ORDER BY created_at DESC"
            
            cursor.execute(query, params)
            artifacts = []
            for row in cursor.fetchall():
                artifact = dict(row)
                artifact['metadata'] = json.loads(artifact['metadata'])
                artifacts.append(artifact)
                
            return artifacts
            
    # === МЕТОДЫ ДЛЯ РАБОТЫ С ЛОГАМИ ===
    
    def add_log(self, level: str, message: str, project_id: int = None,
               execution_id: int = None, module_name: str = None,
               details: dict = None):
        """Добавление записи в лог"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO logs (project_id, execution_id, level, module_name, message, details)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (project_id, execution_id, level, module_name, message,
                  json.dumps(details) if details else None))
            conn.commit()
            
    def get_logs(self, project_id: int = None, level: str = None, 
                limit: int = 100) -> List[Dict]:
        """Получение логов"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            query = "SELECT * FROM logs WHERE 1=1"
            params = []
            
            if project_id:
                query += " AND project_id = ?"
                params.append(project_id)
                
            if level:
                query += " AND level = ?"
                params.append(level)
                
            query += " ORDER BY timestamp DESC LIMIT ?"
            params.append(limit)
            
            cursor.execute(query, params)
            logs = []
            for row in cursor.fetchall():
                log = dict(row)
                if log['details']:
                    log['details'] = json.loads(log['details'])
                logs.append(log)
                
            return logs
            
    # === УТИЛИТЫ ===
    
    def get_project_statistics(self, project_id: int) -> Dict:
        """Получение статистики по проекту"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Общая статистика выполнения
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_modules,
                    SUM(CASE WHEN status = 'completed' THEN 1 ELSE 0 END) as completed,
                    SUM(CASE WHEN status = 'in_progress' THEN 1 ELSE 0 END) as in_progress,
                    SUM(CASE WHEN status = 'error' THEN 1 ELSE 0 END) as errors,
                    AVG(progress) as avg_progress
                FROM executions WHERE project_id = ?
            """, (project_id,))
            
            stats = dict(cursor.fetchone())
            
            # Количество артефактов
            cursor.execute("""
                SELECT COUNT(*) as total_artifacts,
                       SUM(CASE WHEN is_final = 1 THEN 1 ELSE 0 END) as final_artifacts
                FROM artifacts WHERE project_id = ?
            """, (project_id,))
            
            artifact_stats = dict(cursor.fetchone())
            stats.update(artifact_stats)
            
            return stats
            
    def export_project_data(self, project_id: int) -> Dict:
        """Экспорт всех данных проекта"""
        project = self.get_project(project_id)
        if not project:
            return {}
            
        return {
            'project': project,
            'executions': self.get_project_executions(project_id),
            'artifacts': self.get_project_artifacts(project_id),
            'logs': self.get_logs(project_id=project_id),
            'statistics': self.get_project_statistics(project_id)
        }


# === ПРИМЕР ИСПОЛЬЗОВАНИЯ ===
if __name__ == "__main__":
    # Инициализация БД
    db = DatabaseManager("test_projects.db")
    
    # Создание тестового проекта
    project_id = db.create_project(
        name="Test Project",
        path="/path/to/project",
        description="Тестовый проект для демонстрации",
        config={"language": "ru", "quality": "high"}
    )
    
    print(f"Создан проект с ID: {project_id}")
    
    # Обновление статуса модуля
    db.update_execution_status(project_id, "materials_upload", "in_progress", 50)
    db.update_execution_status(project_id, "materials_upload", "completed", 100)
    
    # Добавление артефакта
    db.add_artifact(
        project_id=project_id,
        name="source_materials",
        file_path="/path/to/materials.pdf",
        file_format="pdf",
        display_name="Исходные материалы"
    )
    
    # Получение статистики
    stats = db.get_project_statistics(project_id)
    print("Статистика проекта:", stats)
    
    # Получение всех проектов
    projects = db.get_all_projects()
    print("Все проекты:", projects)