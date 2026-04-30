from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QStackedWidget, QComboBox, QFrame
)
from PyQt5.QtSvg import QSvgWidget
from PyQt5.QtCore import Qt
from ui.styles.style import get_global_stylesheet, apply_shadow_effect
from ui.home_page import HomePage
from ui.lang.language_manager import LanguageManager
from ui.modify_page import ModifyPage
from helper.resource_path import resource_path


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Générateur des créneaux de surveillance")
        self.setMinimumSize(1920, 1080)
        self.setStyleSheet(get_global_stylesheet())

        # Central widget + layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Header
        header = self._create_header()
        main_layout.addWidget(header)

        # Page stack
        self.stack = QStackedWidget()
        main_layout.addWidget(self.stack)

        # === Pages ===
        self.home_page = HomePage()
        self.modify_page = ModifyPage()

        # CONNECT IMPORTED SIGNAL FROM MODIFY PAGE TO EXPORT PANEL IN HOME PAGE
        self.modify_page.imported.connect(self.on_modify_imported)

        self.stack.addWidget(self.home_page)
        self.stack.addWidget(self.modify_page)

        # Navigation defaults
        self.btn_home.setChecked(True)
        self.switch_page(0)

    # ---------------------- #
    #   HEADER CONSTRUCTION  #
    # ---------------------- #
    def _create_header(self):
        header = QFrame()
        header.setObjectName("header")
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(15)
        apply_shadow_effect(header)

        # Logo
        logo_label = QSvgWidget(resource_path("data/input/isi.svg"))
        logo_label.setFixedSize(100, 60)
        layout.addWidget(logo_label, alignment=Qt.AlignLeft | Qt.AlignVCenter)

        # Nav buttons
        self.btn_home = QPushButton("Accueil")
        self.btn_modify = QPushButton("Modifier")
        for btn in [self.btn_home, self.btn_modify]:
            btn.setObjectName("navButton")
            btn.setCheckable(True)
            btn.setStyleSheet("border-radius: 4px;")
            apply_shadow_effect(btn)
            layout.addWidget(btn)

        self.btn_home.clicked.connect(lambda: self.switch_page(0))
        self.btn_modify.clicked.connect(lambda: self.switch_page(1))
        layout.addStretch()

        # Language selector
        lang_combo = QComboBox()
        lang_combo.addItems(["ar", "fr", "en"])
        lang_combo.setCurrentText("fr")
        lang_combo.setObjectName("langCombo")
        layout.addWidget(lang_combo, alignment=Qt.AlignRight)
        lang_combo.currentTextChanged.connect(self.on_language_changed)
        self.lang_manager = LanguageManager()

        return header

    # ---------------------- #
    #   PAGE SWITCH LOGIC    #
    # ---------------------- #
    def switch_page(self, index):
        self.stack.setCurrentIndex(index)
        self.btn_home.setChecked(index == 0)
        self.btn_modify.setChecked(index == 1)


    def on_language_changed(self, lang):
        self.lang_manager.set_language(lang)

    def on_modify_imported(self, df):
        """Receive imported DataFrame from ModifyPage and send it to ExportPanel"""
        result = {'final_df': df}  # match the format ExportPanel expects
        self.home_page.ExportPanel.set_result(result)
        self.switch_page(0)  # show HomePage automatically

