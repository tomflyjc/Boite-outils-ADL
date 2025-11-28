from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox,
    QLineEdit, QTabWidget, QWidget, QGroupBox, QTextEdit, QProgressBar, QRadioButton,
    QTextBrowser
)
from qgis.PyQt.QtPrintSupport import QPrinter, QPrintDialog  # <-- Ajouté ici

from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal, QUrl
from qgis.PyQt.QtPrintSupport import QPrinter
from qgis.PyQt.QtGui import QPageSize, QPageLayout
import os
import csv
import pandas as pd
import plotly.express as px
from datetime import datetime
from xml.etree import ElementTree as ET

# ====================== THREAD POUR L'ANALYSE DES PROJETS QGIS ======================
class WorkerThread(QThread):
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    finished = pyqtSignal()

    def __init__(self, qgis_project_path=None, root_dir=None, output_dir=None):
        QThread.__init__(self)
        self.qgis_project_path = qgis_project_path
        self.root_dir = root_dir
        self.output_dir = output_dir
        self.stopped = False

    def run(self):
        try:
            all_qgis_projects = []
            all_layers_info = []
            inaccessible_dirs = []
            current_date = datetime.now().strftime("%Y%m%d")
            nom_dossier_export = f"Bilan_couches_sig_{current_date}"
            export_dir = os.path.join(self.output_dir, nom_dossier_export)
            os.makedirs(export_dir, exist_ok=True)

            if self.qgis_project_path:
                self.analyze_single_project(export_dir)
            elif self.root_dir:
                self.analyze_directory(export_dir, all_qgis_projects, all_layers_info, inaccessible_dirs)

        except Exception as e:
            self.message.emit(f"Erreur: {str(e)}")
        self.finished.emit()

    def analyze_single_project(self, export_dir):
        try:
            all_layers_info = []
            project_info = {
                'path': self.qgis_project_path,
                'nom': os.path.basename(self.qgis_project_path),
                'type': 'qgs' if self.qgis_project_path.lower().endswith('.qgs') else 'qgz',
                'size': os.stat(self.qgis_project_path).st_size,
                'modification_time': datetime.fromtimestamp(os.stat(self.qgis_project_path).st_mtime).strftime("%Y-%m-%d")
            }
            layers_info = self.read_qgis_project(self.qgis_project_path)
            for layer_info in layers_info:
                layer_info.update({'project_path': self.qgis_project_path})
                all_layers_info.append(layer_info)

            output_layers_info = os.path.join(export_dir, "layers_info.csv")
            with open(output_layers_info, 'w', newline='', encoding='utf-8') as f:
                writer = csv.DictWriter(f, fieldnames=all_layers_info[0].keys() if all_layers_info else [])
                if all_layers_info:
                    writer.writeheader()
                    writer.writerows(all_layers_info)

            self.message.emit(f"Analyse terminée. Résultats dans {export_dir}")

        except Exception as e:
            self.message.emit(f"Erreur: {str(e)}")

    def analyze_directory(self, export_dir, all_qgis_projects, all_layers_info, inaccessible_dirs):
        total_files = 0
        processed_files = 0
        for root, dirs, files in os.walk(self.root_dir):
            total_files += len([f for f in files if f.lower().endswith(('.qgs', '.qgz'))])

        if total_files == 0:
            self.message.emit("Aucun fichier QGIS trouvé.")
            return

        for root, dirs, files in os.walk(self.root_dir):
            if self.stopped:
                return
            for file in files:
                if self.stopped:
                    return
                if file.lower().endswith(('.qgs', '.qgz')):
                    file_path = os.path.join(root, file)
                    processed_files += 1
                    progress = int((processed_files / total_files) * 100)
                    self.progress.emit(progress)
                    try:
                        stat_info = os.stat(file_path)
                        first_level_dir = os.path.normpath(root).split(os.sep)[-1] if len(os.path.normpath(root).split(os.sep)) > 1 else ""
                        project_info = {
                            'path': file_path,
                            'nom': os.path.basename(file_path),
                            'premier_niveau_arborescence': first_level_dir,
                            'type': 'qgs' if file.lower().endswith('.qgs') else 'qgz',
                            'size': stat_info.st_size,
                            'modification_time': datetime.fromtimestamp(stat_info.st_mtime).strftime("%Y-%m-%d")
                        }
                        all_qgis_projects.append(project_info)
                        layers_info = self.read_qgis_project(file_path)
                        for layer_info in layers_info:
                            layer_info.update({
                                'project_path': file_path,
                                'premier_niveau_arborescence': first_level_dir
                            })
                            all_layers_info.append(layer_info)
                    except Exception as e:
                        inaccessible_dirs.append({'directory': file_path, 'error': str(e)})

        output_qgis_projects = os.path.join(export_dir, "qgis_projects.csv")
        output_layers_info = os.path.join(export_dir, "layers_info.csv")
        output_inaccessible_dirs = os.path.join(export_dir, "inaccessible_dirs.csv")

        with open(output_qgis_projects, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_qgis_projects[0].keys() if all_qgis_projects else [])
            if all_qgis_projects:
                writer.writeheader()
                writer.writerows(all_qgis_projects)

        with open(output_layers_info, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=all_layers_info[0].keys() if all_layers_info else [])
            if all_layers_info:
                writer.writeheader()
                writer.writerows(all_layers_info)

        with open(output_inaccessible_dirs, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=inaccessible_dirs[0].keys() if inaccessible_dirs else [])
            if inaccessible_dirs:
                writer.writeheader()
                writer.writerows(inaccessible_dirs)

        self.message.emit(f"Analyse terminée. Résultats dans {export_dir}")
    

    def read_qgis_project(self, project_path):
        layers_info = []
        try:
            if project_path.lower().endswith('.qgz'):
                return layers_info
            tree = ET.parse(project_path)
            root = tree.getroot()
            for maplayer in root.findall('.//maplayer'):
                layer_info = {
                    'layer_name': maplayer.get('name', ''),
                    'layer_path': maplayer.find('datasource').text if maplayer.find('datasource') is not None else '',
                    'layer_type': maplayer.get('type', ''),
                    'layer_size': 0
                }
                if layer_info['layer_path'] and os.path.exists(layer_info['layer_path']):
                    try:
                        layer_info['layer_size'] = os.path.getsize(layer_info['layer_path'])
                    except Exception:
                        pass
                layers_info.append(layer_info)
        except Exception as e:
            print(f"Erreur: {str(e)}")
        return layers_info

# ====================== DIALOGUE PRINCIPAL ======================
class BilanProjetQGISDialog(QDialog):
    def __init__(self, parent=None):
        super(BilanProjetQGISDialog, self).__init__(parent)
        self.setWindowTitle("Bilan des Projets QGIS")
        self.setMinimumWidth(800)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.instructions_tab = QWidget()
        self.setup_instructions_tab()
        self.analysis_tab = QWidget()
        self.setup_analysis_tab()
        self.treemap_tab = QWidget()
        self.setup_treemap_tab()
        self.tabs.addTab(self.instructions_tab, "Instructions")
        self.tabs.addTab(self.analysis_tab, "Analyse")
        self.tabs.addTab(self.treemap_tab, "Treemap")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def setup_instructions_tab(self):
        layout = QVBoxLayout()
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        instructions = """
        <h2>Module de Bilan des Projets QGIS</h2>
        <h3>Fonctionnalités :</h3>
        <p>Ce module permet d'analyser un projet QGIS unique ou tous les projets d'un dossier, puis de visualiser les résultats sous forme de treemap interactive avec Plotly.</p>
        <ul>
            <li>Analyse des projets QGIS (.qgs ou .qgz).</li>
            <li>Extraction des métadonnées et des couches.</li>
            <li>Génération de CSV et de treemap interactive.</li>
            <li>Export en HTML et PDF.</li>
        </ul>
        <h3>Utilisation :</h3>
        <ol>
            <li>Choisissez le mode d'analyse (projet unique ou dossier).</li>
            <li>Sélectionnez la source et le dossier de sortie.</li>
            <li>Cliquez sur "Démarrer l'analyse".</li>
            <li>Utilisez l'onglet "Treemap" pour visualiser les résultats.</li>
        </ol>
        """
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_analysis_tab(self):
        layout = QVBoxLayout()
        # Mode d'analyse
        self.mode_group = QGroupBox("Mode d'analyse")
        mode_layout = QVBoxLayout()
        self.single_project_radio = QRadioButton("Analyser un projet QGIS unique")
        self.directory_radio = QRadioButton("Analyser tous les projets d'un dossier")
        self.single_project_radio.setChecked(True)
        mode_layout.addWidget(self.single_project_radio)
        mode_layout.addWidget(self.directory_radio)
        self.mode_group.setLayout(mode_layout)
        layout.addWidget(self.mode_group)

        # Source à analyser
        self.source_group = QGroupBox("Source à analyser")
        source_layout = QHBoxLayout()
        self.source_line_edit = QLineEdit()
        self.source_browse_button = QPushButton("Parcourir...")
        source_layout.addWidget(self.source_line_edit)
        source_layout.addWidget(self.source_browse_button)
        self.source_group.setLayout(source_layout)
        layout.addWidget(self.source_group)

        # Dossier de sortie
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Dossier de sortie:")
        self.output_line_edit = QLineEdit()
        self.output_browse_button = QPushButton("Parcourir...")
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_line_edit)
        output_layout.addWidget(self.output_browse_button)

        # Bouton d'analyse
        self.analyze_button = QPushButton("Démarrer l'analyse")
        self.analyze_button.setStyleSheet("background-color: #4CAF50; color: white;")

        # Barre de progression et messages
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)

        # Ajout des widgets
        layout.addLayout(output_layout)
        layout.addWidget(self.analyze_button)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.message_text)
        self.analysis_tab.setLayout(layout)

        # Connexions
        self.source_browse_button.clicked.connect(self.browse_source)
        self.output_browse_button.clicked.connect(self.browse_output)
        self.analyze_button.clicked.connect(self.start_analysis)
        self.single_project_radio.toggled.connect(self.update_browse_mode)
        self.directory_radio.toggled.connect(self.update_browse_mode)

    def update_browse_mode(self):
        self.source_line_edit.clear()

    def browse_source(self):
        if self.single_project_radio.isChecked():
            file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un projet QGIS", "", "Fichiers QGIS (*.qgs *.qgz)")
            if file_path:
                self.source_line_edit.setText(file_path)
        else:
            directory = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier")
            if directory:
                self.source_line_edit.setText(directory)

    def browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier de sortie")
        if directory:
            self.output_line_edit.setText(directory)

    def start_analysis(self):
        source_path = self.source_line_edit.text()
        output_dir = self.output_line_edit.text()
        if not source_path or not output_dir:
            QMessageBox.warning(self, "Erreur", "Veuillez spécifier une source et un dossier de sortie.")
            return

        if self.single_project_radio.isChecked():
            self.worker = WorkerThread(qgis_project_path=source_path, output_dir=output_dir)
        else:
            self.worker = WorkerThread(root_dir=source_path, output_dir=output_dir)

        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.message.connect(self.message_text.append)
        self.worker.finished.connect(self.analysis_finished)
        self.worker.start()
        self.analyze_button.setEnabled(False)

    def analysis_finished(self):
        self.analyze_button.setEnabled(True)
        QMessageBox.information(self, "Analyse terminée", "L'analyse est terminée.")

        # Pré-remplir le chemin du fichier layers_info.csv
        output_dir = self.output_line_edit.text()
        if output_dir:
            current_date = datetime.now().strftime("%Y%m%d")
            nom_dossier_export = f"Bilan_couches_sig_{current_date}"
            export_dir = os.path.join(output_dir, nom_dossier_export)
            layers_info_path = os.path.join(export_dir, "layers_info.csv")
            if os.path.exists(layers_info_path):
                self.treemap_csv_line_edit.setText(layers_info_path)
                
    def setup_treemap_tab(self):
        layout = QVBoxLayout()

        # Sélection du CSV
        csv_layout = QHBoxLayout()
        self.treemap_csv_label = QLabel("Fichier CSV (layers_info.csv) :")
        self.treemap_csv_line_edit = QLineEdit()
        self.treemap_csv_browse_button = QPushButton("Parcourir...")
        csv_layout.addWidget(self.treemap_csv_label)
        csv_layout.addWidget(self.treemap_csv_line_edit)
        csv_layout.addWidget(self.treemap_csv_browse_button)

        # Bouton pour générer la treemap
        self.treemap_generate_button = QPushButton("Générer la Treemap")
        self.treemap_generate_button.setStyleSheet("background-color: #4CAF50; color: white;")

        # Zone pour afficher le HTML (QTextBrowser)
        self.treemap_text_browser = QTextBrowser()
        self.treemap_text_browser.setMinimumHeight(500)

        # Boutons d'export
        export_layout = QHBoxLayout()
        self.treemap_export_html_button = QPushButton("Exporter en HTML")
        self.treemap_export_html_button.setStyleSheet("background-color: #2196F3; color: white;")
        self.treemap_export_pdf_button = QPushButton("Exporter en PDF")
        self.treemap_export_pdf_button.setStyleSheet("background-color: #FF5722; color: white;")
        self.treemap_export_html_button.setEnabled(False)
        self.treemap_export_pdf_button.setEnabled(False)
        export_layout.addWidget(self.treemap_export_html_button)
        export_layout.addWidget(self.treemap_export_pdf_button)

        # Ajout des widgets
        layout.addLayout(csv_layout)
        layout.addWidget(self.treemap_generate_button)
        layout.addWidget(self.treemap_text_browser)
        layout.addLayout(export_layout)
        self.treemap_tab.setLayout(layout)

        # Connexions
        self.treemap_csv_browse_button.clicked.connect(self.browse_treemap_csv)
        self.treemap_generate_button.clicked.connect(self.generate_treemap)
        self.treemap_export_html_button.clicked.connect(self.export_treemap_to_html)
        self.treemap_export_pdf_button.clicked.connect(self.export_treemap_to_pdf)
    """
    def setup_treemap_tab(self):
        layout = QVBoxLayout()

        # Sélection du CSV
        csv_layout = QHBoxLayout()
        self.treemap_csv_label = QLabel("Fichier CSV (layers_info.csv) :")
        self.treemap_csv_line_edit = QLineEdit()
        self.treemap_csv_browse_button = QPushButton("Parcourir...")
        csv_layout.addWidget(self.treemap_csv_label)
        csv_layout.addWidget(self.treemap_csv_line_edit)
        csv_layout.addWidget(self.treemap_csv_browse_button)

        # Bouton pour générer la treemap
        self.treemap_generate_button = QPushButton("Générer la Treemap")
        self.treemap_generate_button.setStyleSheet("background-color: #4CAF50; color: white;")

        # Zone pour afficher le HTML (QTextBrowser)
        self.treemap_text_browser = QTextBrowser()
        self.treemap_text_browser.setMinimumHeight(500)

        # Boutons d'export
        export_layout = QHBoxLayout()
        self.treemap_export_html_button = QPushButton("Exporter en HTML")
        self.treemap_export_html_button.setStyleSheet("background-color: #2196F3; color: white;")
        self.treemap_export_pdf_button = QPushButton("Exporter en PDF")
        self.treemap_export_pdf_button.setStyleSheet("background-color: #FF5722; color: white;")
        self.treemap_export_html_button.setEnabled(False)
        self.treemap_export_pdf_button.setEnabled(False)
        export_layout.addWidget(self.treemap_export_html_button)
        export_layout.addWidget(self.treemap_export_pdf_button)

        # Ajout des widgets
        layout.addLayout(csv_layout)
        layout.addWidget(self.treemap_generate_button)
        layout.addWidget(self.treemap_text_browser)
        layout.addLayout(export_layout)
        self.treemap_tab.setLayout(layout)

        # Connexions
        self.treemap_csv_browse_button.clicked.connect(self.browse_treemap_csv)
        self.treemap_generate_button.clicked.connect(self.generate_treemap)
        self.treemap_export_html_button.clicked.connect(self.export_treemap_to_html)
        self.treemap_export_pdf_button.clicked.connect(self.export_treemap_to_pdf)
    """
    def browse_treemap_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner layers_info.csv", "", "CSV Files (*.csv)")
        if file_path:
            self.treemap_csv_line_edit.setText(file_path)
    def generate_treemap(self):
        csv_path = self.treemap_csv_line_edit.text()
        if not csv_path:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier CSV.")
            return

        try:
            # Charger le CSV dans un DataFrame Pandas
            df = pd.read_csv(csv_path)

            # Nettoyer les données : ignorer les tailles nulles ou négatives
            df = df[df['layer_size'] > 0]

            # Extraire le nom du projet
            df['project'] = df['project_path'].apply(lambda x: os.path.basename(x) if pd.notna(x) else "Inconnu")

            # Extraire le nom de la couche depuis layer_path si layer_name est vide
            df['layer_name'] = df.apply(
                lambda row: os.path.basename(row['layer_path']) if pd.isna(row['layer_name']) or row['layer_name'] == "" else row['layer_name'],
                axis=1
            )

            # Créer une colonne "id" pour identifier chaque ligne de manière unique
            df['id'] = df['project'] + "_" + df['layer_name']

            # Créer une colonne "parent" pour la hiérarchie
            df['parent'] = "Root"

            # Créer la treemap avec Plotly
            fig = px.treemap(
                df,
                names='id',
                parents='parent',
                values='layer_size',
                color='project',
                color_discrete_sequence=px.colors.qualitative.Plotly,
                title="Répartition des tailles des couches par projet QGIS",
                hover_data=['layer_path', 'project'],
                height=600
            )

            # Sauvegarder le graphique en HTML
            self.current_html_path = os.path.join(os.path.dirname(csv_path), "treemap.html")
            fig.write_html(self.current_html_path)

            # Charger le HTML dans QTextBrowser
            with open(self.current_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            self.treemap_text_browser.setHtml(html_content)

            # Activer les boutons d'export
            self.treemap_export_html_button.setEnabled(True)
            self.treemap_export_pdf_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de générer la treemap : {str(e)}")
    """
    def generate_treemap(self):
        csv_path = self.treemap_csv_line_edit.text()
        if not csv_path:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier CSV.")
            return

        try:
            # Charger le CSV dans un DataFrame Pandas
            df = pd.read_csv(csv_path)

            # Nettoyer les données : ignorer les tailles nulles ou négatives
            df = df[df['layer_size'] > 0]

            # Extraire le nom du projet
            df['project'] = df['project_path'].apply(lambda x: os.path.basename(x) if pd.notna(x) else "Inconnu")

            # Extraire le nom de la couche depuis layer_path si layer_name est vide
            df['layer_name'] = df.apply(
                lambda row: os.path.basename(row['layer_path']) if pd.isna(row['layer_name']) or row['layer_name'] == "" else row['layer_name'],
                axis=1
            )

            # Créer une colonne "id" pour identifier chaque ligne de manière unique
            df['id'] = df['project'] + "_" + df['layer_name']

            # Créer une colonne "parent" pour la hiérarchie (tous les projets ont le même parent "Root")
            df['parent'] = "Root"

            # Créer la treemap avec Plotly (structure hiérarchique explicite)
            fig = px.treemap(
                df,
                names='id',  # Nom de chaque feuille
                parents='parent',  # Parent commun pour tous les projets
                values='layer_size',
                color='project',  # Une couleur par projet
                color_discrete_sequence=px.colors.qualitative.Plotly,
                title="Répartition des tailles des couches par projet QGIS",
                hover_data=['layer_path', 'project'],
                height=600
            )

            # Sauvegarder le graphique en HTML
            self.current_html_path = os.path.join(os.path.dirname(csv_path), "treemap.html")
            fig.write_html(self.current_html_path)

            # Charger le HTML dans QTextBrowser
            with open(self.current_html_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            self.treemap_text_browser.setHtml(html_content)

            # Activer les boutons d'export
            self.treemap_export_html_button.setEnabled(True)
            self.treemap_export_pdf_button.setEnabled(True)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Impossible de générer la treemap : {str(e)}")

    """
    
    def export_treemap_to_html(self):
        if not hasattr(self, 'current_html_path'):
            QMessageBox.warning(self, "Erreur", "Aucune treemap générée.")
            return

        html_path, _ = QFileDialog.getSaveFileName(self, "Exporter en HTML", "", "HTML Files (*.html)")
        if html_path:
            import shutil
            shutil.copy(self.current_html_path, html_path)
            QMessageBox.information(self, "Export terminé", f"Treemap exportée en HTML : {html_path}")

    def export_treemap_to_pdf(self):
        if not hasattr(self, 'current_html_path'):
            QMessageBox.warning(self, "Erreur", "Aucune treemap générée.")
            return

        pdf_path, _ = QFileDialog.getSaveFileName(self, "Exporter en PDF", "", "PDF Files (*.pdf)")
        if pdf_path:
            try:
                # Créer un QPrinter pour le PDF
                printer = QPrinter()
                printer.setOutputFormat(QPrinter.PdfFormat)
                printer.setOutputFileName(pdf_path)

                # Définir la taille de la page en utilisant QPageSize
                page_size = QPageSize(QPageSize.A4)
                printer.setPageSize(page_size)

                # Définir l'orientation en paysage
                printer.setOrientation(QPrinter.Landscape)  # Utilisation directe de QPrinter.Landscape

                # Imprimer le contenu du QTextBrowser
                self.treemap_text_browser.print_(printer)

                QMessageBox.information(self, "Export terminé", f"Treemap exportée en PDF : {pdf_path}")

            except Exception as e:
                QMessageBox.critical(self, "Erreur", f"Impossible d'exporter en PDF : {str(e)}")



# ====================== PLUGIN PRINCIPAL ======================
class MainPluginBilanProjetQGIS(object):
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        self.action = QAction("Bilan des Projets QGIS", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("BILANS", self.action)

    def unload(self):
        self.iface.removePluginMenu("BILANS", self.action)

    def run(self):
        dialog = BilanProjetQGISDialog(self.iface.mainWindow())
        dialog.exec_()
