# ga_config_dialog.py
from PyQt5.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QSpinBox, QPushButton

class GAConfigDialog(QDialog):
    """Dialog to configure Genetic Algorithm parameters."""
    def __init__(self, parent=None, population=70, generations=300):
        super().__init__(parent)
        self.setWindowTitle("Paramètres GA")
        self.setFixedSize(250, 150)
        
        self.population = population
        self.generations = generations
        
        self.setup_ui()
    
    def setup_ui(self):
        layout = QVBoxLayout()
        
        # Population
        pop_layout = QHBoxLayout()
        pop_label = QLabel("Population:")
        self.pop_spin = QSpinBox()
        self.pop_spin.setMinimum(10)
        self.pop_spin.setMaximum(1000)
        self.pop_spin.setValue(self.population)
        pop_layout.addWidget(pop_label)
        pop_layout.addWidget(self.pop_spin)
        layout.addLayout(pop_layout)
        
        # Generations
        gen_layout = QHBoxLayout()
        gen_label = QLabel("Nombre de générations:")
        self.gen_spin = QSpinBox()
        self.gen_spin.setMinimum(10)
        self.gen_spin.setMaximum(1000)
        self.gen_spin.setValue(self.generations)
        gen_layout.addWidget(gen_label)
        gen_layout.addWidget(self.gen_spin)
        layout.addLayout(gen_layout)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.ok_btn = QPushButton("OK")
        self.cancel_btn = QPushButton("Annuler")
        self.ok_btn.clicked.connect(self.accept)
        self.cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(self.ok_btn)
        btn_layout.addWidget(self.cancel_btn)
        layout.addLayout(btn_layout)
        
        self.setLayout(layout)
    
    def get_values(self):
        """Return user-set values (population, generations)."""
        return self.pop_spin.value(), self.gen_spin.value()
