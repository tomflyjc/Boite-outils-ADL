import os
import csv
import platform
from datetime import datetime
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QTextEdit,
    QPushButton, QFileDialog, QTableWidget, QTableWidgetItem,
    QMessageBox, QLineEdit, QProgressBar, QHBoxLayout, QLabel, QApplication
)

def debug_method(func):
    def wrapper(*args, **kwargs):
        print(f"Méthode {func.__name__} appelée avec {len(args)} arguments !")
        return func(*args, **kwargs)
    return wrapper

class PreparationArchivageDialog(QDialog):
    def __init__(self, parent=None):
        super(PreparationArchivageDialog, self).__init__(parent)
        self.setWindowTitle("Préparation Archivage")
        self.setup_ui()
        self.resize(900, 600)
        print("Dialogue initialisé avec succès.")

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
        <h2>Préparation Archivage</h2>
        <h3>Fonctionnalités :</h3>
        <p>Ce module analyse les données géographiques dans un dossier et génère un fichier CSV avec des métadonnées étendues.</p>

        <h3>Colonnes du CSV :</h3>
        <ul>
            <li><b>Chemin</b> : Chemin complet du fichier géographique.</li>
            <li><b>Nom de la couche</b> : Nom du fichier.</li>
            <li><b>Date de création</b> : Date de création du fichier.</li>
            <li><b>Dernière modification</b> : Date de dernière modification du contenu.</li>
            <li><b>Dernière consultation</b> : Dernière date d'accès au fichier.</li>
            <li><b>Propriétaire</b> : Propriétaire du fichier (Unix uniquement).</li>
            <li><b>Poids (Ko)</b> : Taille du fichier en kilo-octets.</li>
            <li><b>Commentaires</b> : Champ libre pour ajouter des commentaires.</li>
            <li><b>Action</b> : Action à effectuer sur le fichier (<i>à archiver</i>, <i>à supprimer</i>, ou <i>RAS</i>).</li>
            <li><b>Bascule</b> : Champ libre pour indiquer une bascule éventuelle.</li>
            <li><b>Amélioration</b> : Champ libre pour indiquer des améliorations à apporter.</li>
        </ul>

        <h3>Utilisation :</h3>
        <ol>
            <li>Sélectionnez un dossier via le bouton "Parcourir...".</li>
            <li>Choisissez un dossier de destination pour le fichier CSV (par défaut : même dossier que les données).</li>
            <li>Cliquez sur "Analyser" pour générer le CSV.</li>
        </ol>
        """
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_analysis_tab(self):
        """Configurer l'onglet Traitements."""
        layout = QVBoxLayout()

        # Sélection du dossier source
        source_layout = QHBoxLayout()
        self.source_label = QLabel("Dossier à traiter:")
        self.source_line_edit = QLineEdit()
        self.source_browse_button = QPushButton("Parcourir...")
        self.source_browse_button.clicked.connect(self.on_browse_source_folder_clicked)
        source_layout.addWidget(self.source_label)
        source_layout.addWidget(self.source_line_edit)
        source_layout.addWidget(self.source_browse_button)
        layout.addLayout(source_layout)

        # Sélection du dossier de destination pour le CSV
        dest_layout = QHBoxLayout()
        self.dest_label = QLabel("Dossier de destination du CSV:")
        self.dest_line_edit = QLineEdit()
        self.dest_browse_button = QPushButton("Parcourir...")
        self.dest_browse_button.clicked.connect(self.on_browse_dest_folder_clicked)
        dest_layout.addWidget(self.dest_label)
        dest_layout.addWidget(self.dest_line_edit)
        dest_layout.addWidget(self.dest_browse_button)
        layout.addLayout(dest_layout)

        # Bouton pour lancer l'analyse
        self.btn_analyze = QPushButton("Analyser")
        self.btn_analyze.clicked.connect(self.analyze_folder)
        layout.addWidget(self.btn_analyze)

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addWidget(self.progress_bar)

        # Tableau pour afficher les résultats
        self.result_table = QTableWidget()
        self.result_table.setColumnCount(12)  # 12 colonnes au total
        self.result_table.setHorizontalHeaderLabels([
            "Chemin", "Nom de la couche", "Date de création",
            "Dernière modification", "Dernière consultation", "Propriétaire",
            "Poids (Ko)", "Commentaires", "Action", "Bascule", "Amélioration"
        ])
        layout.addWidget(self.result_table)

        self.analysis_tab.setLayout(layout)

    @debug_method
    def on_browse_source_folder_clicked(self, *args):
        """Méthode appelée quand le bouton 'Parcourir...' pour le dossier source est cliqué."""
        print("Bouton 'Parcourir...' (source) cliqué !")
        directory = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier à traiter",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if directory:
            self.source_line_edit.setText(directory)
            self.selected_folder = directory
            # Mettre à jour le dossier de destination par défaut
            self.dest_line_edit.setText(directory)
            print(f"Dossier source sélectionné : {directory}")

    @debug_method
    def on_browse_dest_folder_clicked(self, *args):
        """Méthode appelée quand le bouton 'Parcourir...' pour le dossier de destination est cliqué."""
        print("Bouton 'Parcourir...' (destination) cliqué !")
        directory = QFileDialog.getExistingDirectory(
            self,
            "Sélectionner le dossier de destination du CSV",
            "",
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks
        )
        if directory:
            self.dest_line_edit.setText(directory)
            print(f"Dossier de destination sélectionné : {directory}")

    def get_file_owner(self, file_path):
        """Récupère le propriétaire du fichier (Unix uniquement)."""
        if platform.system() == "Linux":
            import pwd
            file_stats = os.stat(file_path)
            uid = file_stats.st_uid
            try:
                return pwd.getpwuid(uid).pw_name
            except:
                return "Inconnu"
        else:
            return "Non disponible"

    def analyze_folder(self):
        """Analyser le dossier sélectionné et générer le fichier CSV."""
        try:
            if not hasattr(self, 'selected_folder') or not self.selected_folder:
                QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un dossier source d'abord.")
                return

            self.progress_bar.setValue(0)

            # Compter le nombre total de fichiers géographiques
            geo_extensions = ('.shp', '.gpkg', '.tab', '.gpx', '.kml', '.kmz', '.geojson')
            total_files = 0
            for root, _, files in os.walk(self.selected_folder):
                for file in files:
                    if file.lower().endswith(geo_extensions):
                        total_files += 1

            if total_files == 0:
                QMessageBox.warning(self, "Avertissement", "Aucun fichier géographique trouvé dans le dossier.")
                return

            # Initialiser la liste des fichiers géographiques
            geo_files = []
            processed_files = 0

            # Parcourir les fichiers et mettre à jour la barre de progression
            for root, _, files in os.walk(self.selected_folder):
                for file in files:
                    if file.lower().endswith(geo_extensions):
                        file_path = os.path.join(root, file)
                        file_stats = os.stat(file_path)
                        geo_files.append({
                            'path': file_path,
                            'name': file,
                            'creation_date': datetime.fromtimestamp(file_stats.st_ctime).strftime('%Y-%m-%d'), # '%Y-%m-%d %H:%M:%S'
                            'last_modified': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d'),
                            'last_access': datetime.fromtimestamp(file_stats.st_atime).strftime('%Y-%m-%d'),
                            'size_kb': file_stats.st_size / 1024
                        })
                        processed_files += 1
                        # Mettre à jour la barre de progression
                        progress = int((processed_files / total_files) * 100)
                        self.progress_bar.setValue(progress)
                        QApplication.processEvents()  # Forcer la mise à jour de l'interface

            # Récupérer le dossier de destination
            dest_folder = self.dest_line_edit.text()
            if not dest_folder:
                dest_folder = self.selected_folder

            # Générer le fichier CSV dans le dossier de destination
            folder_name = os.path.basename(self.selected_folder)
            csv_filename = f"bilan_donnees_geographiques_{folder_name}.csv"
            csv_filepath = os.path.join(dest_folder, csv_filename)
            self.create_csv_file(geo_files, csv_filepath)

            # Remplir le tableau
            self.populate_result_table(geo_files)
            self.progress_bar.setValue(100)

            QMessageBox.information(self, "Succès", f"Fichier CSV généré : {csv_filepath}")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Erreur : {str(e)}")
            self.progress_bar.setValue(0)

    def create_csv_file(self, geo_files, csv_filepath):
        """Créer le fichier CSV avec les colonnes supplémentaires."""
        headers = [
            "Chemin", "Nom de la couche", "Date de création",
            "Dernière modification", "Dernière consultation", "Propriétaire",
            "Poids (Ko)", "Commentaires", "Action", "Bascule", "Amélioration"
        ]
        with open(csv_filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            for file_info in geo_files:
                writer.writerow([
                    file_info['path'],
                    file_info['name'],
                    file_info['creation_date'],
                    file_info['last_modified'],
                    file_info['last_access'],
                    f"{file_info['size_kb']:.2f}",
                    "",  # Commentaires (vide)
                    "RAS",  # Action (par défaut)
                    "",  # Bascule (vide)
                    ""   # Amélioration (vide)
                ])

    def populate_result_table(self, geo_files):
        """Remplir le tableau avec les résultats, y compris les colonnes supplémentaires."""
        self.result_table.setRowCount(len(geo_files))
        for row, file_info in enumerate(geo_files):
            self.result_table.setItem(row, 0, QTableWidgetItem(file_info['path']))
            self.result_table.setItem(row, 1, QTableWidgetItem(file_info['name']))
            self.result_table.setItem(row, 2, QTableWidgetItem(file_info['creation_date']))
            self.result_table.setItem(row, 3, QTableWidgetItem(file_info['last_modified']))
            self.result_table.setItem(row, 4, QTableWidgetItem(file_info['last_access']))
            self.result_table.setItem(row, 5, QTableWidgetItem(f"{file_info['size_kb']:.2f} Ko"))

            # Colonnes vides ou pré-remplies
            self.result_table.setItem(row, 6, QTableWidgetItem(""))  # Commentaires
            self.result_table.setItem(row, 7, QTableWidgetItem("RAS"))  # Action (par défaut)
            self.result_table.setItem(row, 8, QTableWidgetItem(""))  # Bascule
            self.result_table.setItem(row, 9, QTableWidgetItem(""))  # Amélioration

class MainPluginPreparationArchivage:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None

    def run(self):
        try:
            if self.dialog is None:
                self.dialog = PreparationArchivageDialog(self.iface.mainWindow())
            self.dialog.exec_()  # Utilisation de exec_() pour un dialogue modal
        except Exception as e:
            QMessageBox.critical(self.iface.mainWindow(), "Erreur", f"Erreur : {str(e)}")
