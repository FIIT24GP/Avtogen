import os
import json
import shutil
from typing import Optional, List, Dict, Any
from database_manager import DatabaseManager


class ProjectService:
    """Сервисный слой для работы с проектами. Абстрагирует UI от БД."""
    
    def __init__(self, project_path: str = "C:\\Avtogen", db_path: str = "projects.db"):
        self.project_path = project_path
        self.db = DatabaseManager(db_path)
        
    # === МЕТОДЫ ДЛЯ РАБОТЫ С ПРОЕКТАМИ ===
    
    def get_all_projects(self) -> List[Dict[str, Any]]:
        """Получение всех проектов с информацией о синхронизации."""
        result = []
        
        try:
            # Получаем проекты из БД
            db_projects = self.db.get_all_projects()
            db_project_dict = {proj['name']: proj for proj in db_projects}
            
            # Получаем проекты из файловой системы
            fs_projects = set()
            if os.path.exists(self.project_path):
                for folder in os.listdir(self.project_path):
                    folder_path = os.path.join(self.project_path, folder)
                    if os.path.isdir(folder_path):
                        fs_projects.add(folder)
            
            # Объединяем информацию
            all_project_names = set(db_project_dict.keys()).union(fs_projects)
            
            for project_name in sorted(all_project_names):
                project_info = {
                    'name': project_name,
                    'in_database': project_name in db_project_dict,
                    'in_filesystem': project_name in fs_projects,
                    'path': os.path.join(self.project_path, project_name),
                    'db_data': db_project_dict.get(project_name),
                    'display_name': self._get_display_name(project_name, 
                                                         project_name in db_project_dict,
                                                         project_name in fs_projects)
                }
                result.append(project_info)
                
        except Exception as e:
            raise Exception(f"Ошибка при получении списка проектов: {e}")
            
        return result
    
    def _get_display_name(self, name: str, in_db: bool, in_fs: bool) -> str:
        """Формирование отображаемого имени проекта с метками синхронизации."""
        display_name = name
        if not in_db:
            display_name += " [не в БД]"
        elif not in_fs:
            display_name += " [нет папки]"
        return display_name
    
    def get_project_by_name(self, name: str) -> Optional[Dict[str, Any]]:
        """Получение проекта по имени с полной информацией."""
        projects = self.get_all_projects()
        for project in projects:
            if project['name'] == name:
                return project
        return None
    
    def create_project(self, name: str, description: str = "") -> Dict[str, Any]:
        """Создание нового проекта в БД и файловой системе."""
        project_full_path = os.path.join(self.project_path, name)
        
        # Проверяем существование
        if self.db.get_project_by_name(name) or os.path.exists(project_full_path):
            raise ValueError(f"Проект '{name}' уже существует")
        
        try:
            # Создание папки проекта
            os.makedirs(project_full_path)
            
            # Создание стандартных подпапок
            subfolders = [
                "materials", "source_video", "source_notes", 
                "source_images", "final_video", "final_audio",
                "final_notes", "final_presentation"
            ]
            
            for subfolder in subfolders:
                os.makedirs(os.path.join(project_full_path, subfolder), exist_ok=True)
            
            # Создание записи в БД
            project_id = self.db.create_project(
                name=name,
                path=project_full_path,
                description=description,
                config={}
            )
            
            # Создание .avtogen файла
            self._create_avtogen_file(project_full_path, name, description)
            
            return {
                'id': project_id,
                'name': name,
                'path': project_full_path,
                'description': description
            }
            
        except Exception as e:
            # Откат изменений при ошибке
            if os.path.exists(project_full_path):
                shutil.rmtree(project_full_path, ignore_errors=True)
                
            if 'project_id' in locals():
                try:
                    self.db.delete_project(project_id)
                except:
                    pass
                    
            raise Exception(f"Ошибка при создании проекта: {e}")
    
    def delete_project(self, name: str) -> bool:
        """Удаление проекта из БД и файловой системы."""
        try:
            # Удаление из БД
            project = self.db.get_project_by_name(name)
            if project:
                self.db.delete_project(project['id'])
            
            # Удаление папки
            project_path = os.path.join(self.project_path, name)
            if os.path.exists(project_path):
                shutil.rmtree(project_path)
            
            return True
            
        except Exception as e:
            raise Exception(f"Ошибка при удалении проекта: {e}")
    
    def sync_projects(self) -> Dict[str, int]:
        """Синхронизация проектов между файловой системой и БД."""
        stats = {
            'added_to_db': 0,
            'created_folders': 0,
            'errors': 0
        }
        
        try:
            if not os.path.exists(self.project_path):
                return stats
                
            # Синхронизация: добавляем в БД проекты из файловой системы
            for folder in os.listdir(self.project_path):
                folder_path = os.path.join(self.project_path, folder)
                if os.path.isdir(folder_path):
                    existing_project = self.db.get_project_by_name(folder)
                    
                    if not existing_project:
                        try:
                            description, config = self._load_avtogen_data(folder_path, folder)
                            
                            self.db.create_project(
                                name=folder,
                                path=folder_path,
                                description=description,
                                config=config
                            )
                            stats['added_to_db'] += 1
                            
                        except Exception as e:
                            print(f"Ошибка синхронизации проекта {folder}: {e}")
                            stats['errors'] += 1
            
            return stats
            
        except Exception as e:
            raise Exception(f"Ошибка при синхронизации: {e}")
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ С ОПИСАНИЕМ ===
    
    def get_project_description(self, name: str) -> str:
        """Получение описания проекта (сначала из БД, потом из .avtogen)."""
        description = ""
        
        # Сначала пытаемся загрузить из БД
        project = self.db.get_project_by_name(name)
        if project:
            description = project.get('description', '')
        
        # Если в БД нет описания, загружаем из .avtogen файла
        if not description:
            project_path = os.path.join(self.project_path, name)
            avtogen_file = os.path.join(project_path, f"{name}.avtogen")
            
            try:
                if os.path.exists(avtogen_file):
                    with open(avtogen_file, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        description = data.get("Description", "")
            except Exception as e:
                print(f"Ошибка при загрузке описания из .avtogen: {e}")
        
        return description
    
    def update_project_description(self, name: str, description: str) -> bool:
        """Обновление описания проекта в БД и .avtogen файле."""
        try:
            # Обновление в БД
            project = self.db.get_project_by_name(name)
            if project:
                self.db.update_project(project['id'], description=description)
            
            # Обновление в .avtogen файле
            self._update_avtogen_description(name, description)
            
            return True
            
        except Exception as e:
            print(f"Ошибка при сохранении описания: {e}")
            return False
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ СО СТАТУСАМИ ===
    
    def get_workflow_statuses(self, name: str) -> Dict[str, str]:
        """Получение статусов этапов работы проекта."""
        project = self.db.get_project_by_name(name)
        if not project:
            return {}
            
        try:
            executions = self.db.get_project_executions(project['id'])
            statuses = {}
            
            for execution in executions:
                module_name = execution['module_name']
                status = execution['status']
                statuses[module_name] = status
                
            return statuses
        except Exception as e:
            print(f"Ошибка при получении статусов из БД: {e}")
            return {}
    
    def update_module_status(self, project_name: str, module_name: str, 
                           status: str, progress: int = None) -> bool:
        """Обновление статуса модуля."""
        try:
            project = self.db.get_project_by_name(project_name)
            if not project:
                return False
                
            return self.db.update_execution_status(
                project['id'], 
                module_name, 
                status, 
                progress
            )
        except Exception as e:
            print(f"Ошибка при обновлении статуса модуля: {e}")
            return False
    
    # === МЕТОДЫ ДЛЯ РАБОТЫ С АРТЕФАКТАМИ ===
    
    def add_artifact(self, project_name: str, name: str, file_path: str,
                    file_format: str = None, display_name: str = None,
                    is_final: bool = False, metadata: dict = None) -> Optional[int]:
        """Добавление артефакта проекта."""
        try:
            project = self.db.get_project_by_name(project_name)
            if not project:
                return None
                
            return self.db.add_artifact(
                project_id=project['id'],
                name=name,
                file_path=file_path,
                file_format=file_format,
                display_name=display_name,
                is_final=is_final,
                metadata=metadata or {}
            )
        except Exception as e:
            print(f"Ошибка при добавлении артефакта: {e}")
            return None
    
    def get_project_artifacts(self, project_name: str) -> List[Dict]:
        """Получение артефактов проекта."""
        try:
            project = self.db.get_project_by_name(project_name)
            if not project:
                return []
                
            return self.db.get_project_artifacts(project['id'])
        except Exception as e:
            print(f"Ошибка при получении артефактов: {e}")
            return []
    
    # === ВСПОМОГАТЕЛЬНЫЕ МЕТОДЫ ===
    
    def _create_avtogen_file(self, project_path: str, project_name: str, description: str = ""):
        """Создание .avtogen файла для проекта."""
        avtogen_file = os.path.join(project_path, f"{project_name}.avtogen")
        
        initial_data = {
            "Project_Name": project_name,
            "Offset": 0,
            "Slide_Style": "По умолчанию", 
            "Timings": 5,
            "Description": description,
            "Workflow_Status": {
                "materials_upload": "not_started",
                "content_generation": "not_started",
                "image_processing": "not_started",
                "final_content": "not_started",
                "presentation_gen": "not_started",
                "audio_generation": "not_started",
                "video_compilation": "not_started",
                "source_video": "not_started",
                "keyframe_extraction": "not_started",
                "audio_recognition": "not_started",
                "text_cleaning": "not_started",
                "reverse_content": "not_started",
                "vector_base": "not_started",
                "monitoring": "not_started"
            }
        }
        
        with open(avtogen_file, 'w', encoding='utf-8') as f:
            json.dump(initial_data, f, ensure_ascii=False, indent=2)
    
    def _update_avtogen_description(self, project_name: str, description: str):
        """Обновление описания в .avtogen файле."""
        project_path = os.path.join(self.project_path, project_name)
        avtogen_file = os.path.join(project_path, f"{project_name}.avtogen")
        
        try:
            # Загружаем существующие данные или создаем новые
            if os.path.exists(avtogen_file):
                with open(avtogen_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
            else:
                data = {
                    "Project_Name": project_name,
                    "Offset": 0,
                    "Slide_Style": "По умолчанию",
                    "Timings": 5,
                    "Workflow_Status": {}
                }
            
            # Обновляем описание
            data["Description"] = description
            
            # Сохраняем файл
            with open(avtogen_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
        except Exception as e:
            raise Exception(f"Ошибка при обновлении .avtogen файла: {e}")
    
    def _load_avtogen_data(self, project_path: str, project_name: str) -> tuple:
        """Загрузка данных из .avtogen файла."""
        avtogen_file = os.path.join(project_path, f"{project_name}.avtogen")
        description = ""
        config = {}
        
        try:
            if os.path.exists(avtogen_file):
                with open(avtogen_file, 'r', encoding='utf-8') as f:
                    avtogen_data = json.load(f)
                    description = avtogen_data.get("Description", "")
                    config = {
                        "offset": avtogen_data.get("Offset", 0),
                        "slide_style": avtogen_data.get("Slide_Style", "По умолчанию"),
                        "timings": avtogen_data.get("Timings", 5)
                    }
        except Exception as e:
            print(f"Ошибка чтения .avtogen для {project_name}: {e}")
            
        return description, config
    
    def get_avtogen_data(self, project_name: str) -> Optional[Dict]:
        """Получение данных из .avtogen файла проекта."""
        project_path = os.path.join(self.project_path, project_name)
        avtogen_file = os.path.join(project_path, f"{project_name}.avtogen")
        
        try:
            if os.path.exists(avtogen_file):
                with open(avtogen_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Ошибка при чтении .avtogen файла: {e}")
            
        return None
    
    def get_project_statistics(self, project_name: str) -> Dict:
        """Получение статистики по проекту."""
        project = self.db.get_project_by_name(project_name)
        if not project:
            return {}
            
        try:
            return self.db.get_project_statistics(project['id'])
        except Exception as e:
            print(f"Ошибка при получении статистики: {e}")
            return {}
    
    def ensure_project_directory(self) -> bool:
        """Обеспечение существования директории проектов."""
        if not os.path.exists(self.project_path):
            try:
                os.makedirs(self.project_path)
                return True
            except OSError as e:
                raise Exception(f"Не удалось создать директорию проектов: {e}")
        return True