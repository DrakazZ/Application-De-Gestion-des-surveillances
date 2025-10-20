# utils/language_manager.py
import os, json
from PyQt5.QtCore import QObject, pyqtSignal, Qt
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

class LanguageManager(QObject):
    language_changed = pyqtSignal()
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(LanguageManager, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        super().__init__()
        self.current_lang = "fr"
        self.translations = {
            "en": {
                "dashboard": "Dashboard",
                "summary": "Summary",
                "violations": "Violations",
                "charts": "Charts",
                "save": "Save Settings",
                "grade_config": "Rank Limit Configuration"
            },
            "fr": {
                "dashboard": "Tableau de bord",
                "summary": "Résumé",
                "violations": "Infractions",
                "charts": "Graphes",
                "save": "Enregistrer les paramètres",
                "grade_config": "Configuration des limites de rang"
            },
            "ar": {
                "dashboard": "لوحة التحكم",
                "summary": "الملخص",
                "violations": "المخالفات",
                "charts": "الرسوم البيانية",
                "save": "حفظ الإعدادات",
                "grade_config": "تحديد حد الرتبة"
            }
        }

    def translate(self, key: str) -> str:
        return self.translations[self.current_lang].get(key, key)

    def set_language(self, lang_code: str):
        if lang_code != self.current_lang:
            self.current_lang = lang_code
            direction = Qt.RightToLeft if lang_code == "ar" else Qt.LeftToRight

            for widget in QApplication.topLevelWidgets():
                widget.setLayoutDirection(direction)

            # Update font globally
            if lang_code == "ar":
                QApplication.setFont(QFont("Noto Naskh Arabic", 10))
            else:
                QApplication.setFont(QFont("Segoe UI", 10))

            self.language_changed.emit()
