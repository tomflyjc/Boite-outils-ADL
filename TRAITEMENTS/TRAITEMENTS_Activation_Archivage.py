import os
import csv
import shutil
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QTextEdit,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem, QMessageBox
)

class ActivationArchivageDialog(QDialog):
    def __init__(self, parent=None):
        super(ActivationArchivageDialog, self).__init__(parent)
        self.setWindowTitle("Activation Archivage")
        self.archive_root = r"W:\99_ARCHIVES\ARCHIVES_GEOBASE"
        self.setup_ui()

    def setup_ui(self):
        """Configure l'interface utilisateur."""
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Onglet Instructions
        self.instructions_tab = QWidget()
        self.setup_instructions_tab()

        # Onglet Traitements
        self.analysis_tab = QWidget()
        self.setup_analysis_tab()

        self.tabs.addTab(self.instructions_tab, "Instructions")
        self.tabs.addTab(self.analysis_tab, "Traitements")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def setup_instructions_tab(self):
        """Configurer l'onglet Instructions."""
        layout = QVBoxLayout()
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        instructions = """
        <h2>Activation Archivage</h2>
        <h3>Fonctionnalités :</h3>
        <p>Ce module traite un fichier CSV généré par le module de préparation, en archivant ou marquant pour suppression les couches géographiques selon la colonne 'Action'.</p>

        <h3>Données nécessaires :</h3>
        <p>Un fichier CSV contenant les informations des données géographiques, avec une colonne 'Action' indiquant 'à supprimer' ou 'à archiver'.</p>

        <h3>Utilisation :</h3>
        <ol>
            <li>Sélectionner un fichier CSV via le bouton "Choisir un fichier CSV".</li>
            <li>Cliquer sur "Activer" pour traiter les enregistrements et copier les couches dans l'archive.</li>
            <li>Vérifier les opérations effectuées dans le dossier d'archive.</li>
        </ol>
        """
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_analysis_tab(self):
        """Configurer l'onglet Traitements."""
        layout = QVBoxLayout()

        # Bouton pour choisir le fichier CSV
        self.btn_select_csv = QPushButton("Choisir un fichier CSV")
        self.btn_select_csv.clicked.connect(self.select_csv)
        layout.addWidget(self.btn_select_csv)

        # Bouton pour lancer le traitement
        self.btn_activate = QPushButton("Activer")
        self.btn_activate.clicked.connect(self.activate_archivage)
        layout.addWidget(self.btn_activate)

        # Tableau pour afficher les résultats
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(9)
        self.result_table.setHorizontalHeaderLabels([
            "Chemin", "Nom de la couche", "Date de création", "Date dernière utilisation",
            "Poids (Ko)", "Commentaires", "Action", "Bascule", "Amélioration"
        ])
        layout.addWidget(self.result_table)

        self.analysis_tab.setLayout(layout)

    def select_csv(self):
        """Ouvrir une boîte de dialogue pour choisir un fichier CSV."""
        try:
            csv_file, _ = QFileDialog.getOpenFileName(
                self, "Sélectionner un fichier CSV", "", "CSV files (*.csv)"
            )
            if csv_file:
                self.selected_csv = csv_file
                QMessageBox.information(self, "Fichier sélectionné", f"Fichier choisi : {csv_file}")
                self.load_csv_data()
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors de la sélection du fichier : {e}")

    def load_csv_data(self):
        """Charger les données du CSV et les afficher dans le tableau."""
        try:
            with open(self.selected_csv, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                self.csv_data = list(reader)

            self.result_table.setRowCount(len(self.csv_data))
            for row_idx, row in enumerate(self.csv_data):
                for col_idx, header in enumerate(self.result_table.horizontalHeaderLabels()):
                    self.result_table.setItem(row_idx, col_idx, QTableWidgetItem(row.get(header, '')))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du chargement du CSV : {e}")

    def activate_archivage(self):
        """Traiter le fichier CSV et effectuer les opérations d'archivage."""
        try:
            if not hasattr(self, 'selected_csv') or not self.selected_csv:
                QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un fichier CSV d'abord.")
                return

            if not hasattr(self, 'csv_data'):
                self.load_csv_data()

            processed = 0
            for row in self.csv_data:
                action = row.get('Action', '').strip().lower()
                if action in ['à supprimer', 'à archiver']:
                    original_path = row.get('Chemin', '').strip()
                    if os.path.exists(original_path):
                        self.process_layer(row)
                        processed += 1

            QMessageBox.information(self, "Succès", f"Traitement terminé. {processed} couches traitées.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur lors du traitement : {e}")

    def process_layer(self, row):
        """Traiter une couche spécifique en fonction de l'action."""
        original_path = row['Chemin']
        action = row['Action'].strip().lower()
        dir_path = os.path.dirname(original_path)
        base, ext = os.path.splitext(os.path.basename(original_path))
        now = datetime.now()

        if action == 'à supprimer':
            suppress_year = now.year + 5
            current_month = now.month
            postfix = f"_A_SUPPRIMER_le_{suppress_year}_{current_month:02d}"
        elif action == 'à archiver':
            today = now.strftime('%Y_%m_%d')
            postfix = f"_archivee_le_{today}"
        else:
            return

        new_base = base + postfix

        # Calculer le chemin relatif par rapport au dossier parent commun
        rel_dir = os.path.relpath(dir_path, os.path.dirname(os.path.dirname(original_path)))
        target_dir = os.path.normpath(os.path.join(self.archive_root, rel_dir))
        os.makedirs(target_dir, exist_ok=True)

        # Copier les fichiers de la couche
        layer_files = self.get_layer_files(original_path)
        for src, rel_name in layer_files:
            new_rel_name = new_base + os.path.splitext(rel_name)[1]
            tgt = os.path.join(target_dir, new_rel_name)
            shutil.copy2(src, tgt)

    def get_layer_files(self, path):
        """Récupérer tous les fichiers associés à une couche géographique."""
        dir_ = os.path.dirname(path)
        base, ext = os.path.splitext(os.path.basename(path))

        if ext.lower() == '.shp':
            extensions = [
                '.shp', '.shx', '.dbf', '.prj', '.sbn', '.sbx', '.fbn', '.fbx',
                '.ain', '.aih', '.ixs', '.mxs', '.atx', '.shp.xml', '.cpg'
            ]
        elif ext.lower() == '.tab':
            extensions = ['.tab', '.dat', '.id', '.map', '.ind']
        else:
            return [(path, os.path.basename(path))]

        files = []
        for e in extensions:
            f = os.path.join(dir_, base + e)
            if os.path.exists(f):
                files.append((f, base + e))
        return files

class MainPluginActivationArchivage:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None

    def run(self):
        try:
            self.dialog = ActivationArchivageDialog(self.iface.mainWindow())
            self.dialog.exec_()
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Erreur", f"Erreur lors de l'exécution du module : {e}")
