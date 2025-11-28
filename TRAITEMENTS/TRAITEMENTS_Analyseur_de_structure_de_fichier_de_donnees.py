
# Fichier : TRAITEMENTS/TRAITEMENTS_Analyseur_de_structure_de_fichier_de_donnée.py

import os
import pandas as pd
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QTabWidget, QWidget, QTextEdit, QLineEdit, QPushButton, QFileDialog, QMessageBox, QLabel, QHBoxLayout
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsVectorLayer, QgsWkbTypes, QgsRectangle

class MainPluginAnalyseurDeStructure(QDialog):
    def __init__(self, iface, parent=None):
        super(MainPluginAnalyseurDeStructure, self).__init__(parent)
        self.iface = iface
        self.setWindowTitle("Analyseur de Structure de Fichier de Données")
        self.setMinimumWidth(800)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        # Onglet Instructions
        self.instructions_tab = QWidget()
        self.setup_instructions_tab()
        # Onglet Traitement
        self.analysis_tab = QWidget()
        self.setup_analysis_tab()
        self.tabs.addTab(self.instructions_tab, "Instructions")
        self.tabs.addTab(self.analysis_tab, "Traitement")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def setup_instructions_tab(self):
        """Configurer l'onglet Instructions avec une description détaillée."""
        layout = QVBoxLayout()
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        instructions = """
<h2>Analyseur de Structure de Fichier de Données</h2>
<h3>Fonctionnalités :</h3>
<p>Ce module permet d'analyser la structure d'un fichier de données géographiques ou non (comme CSV, XLS/XLSX, Shapefile, GPKG, GPX, GeoJSON, etc.) sans divulguer les données sensibles. Il extrait des informations comme l'encodage (si détectable), les noms, types et tailles des champs, et pour les données géographiques : le système de projection, le type de géométrie et l'emprise.</p>
<p>Les résultats sont affichés dans l'interface et peuvent être exportés dans un fichier RTF.</p>
<h3>Données nécessaires :</h3>
<p>- Un fichier de données (formats supportés : CSV, XLS/XLSX, SHP, GPKG, GPX, GeoJSON, etc.).</p>
<p>- Un chemin de sortie pour exporter le fichier RTF (optionnel).</p>
<h3>Utilisation :</h3>
<ol>
    <li>Dans l'onglet Traitement, cliquez sur "Sélectionner le fichier" pour choisir le fichier à analyser.</li>
    <li>Le module analysera automatiquement la structure et affichera les résultats dans la zone de texte.</li>
    <li>Pour exporter, saisissez ou sélectionnez un chemin de fichier RTF et cliquez sur "Exporter en RTF".</li>
    <li>En cas d'erreur, un message s'affichera.</li>
</ol>
<p>Note : L'encodage est assumé UTF-8 par défaut pour les fichiers texte ; une détection avancée n'est pas implémentée sans dépendances externes.</p>
"""
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_analysis_tab(self):
        """Configurer l'onglet Traitement avec l'interface utilisateur."""
        layout = QVBoxLayout()

        # Sélection du fichier d'entrée
        input_layout = QHBoxLayout()
        self.input_file_line = QLineEdit()
        self.input_file_line.setPlaceholderText("Chemin du fichier de données...")
        input_button = QPushButton("Sélectionner le fichier")
        input_button.clicked.connect(self.select_input_file)
        input_layout.addWidget(self.input_file_line)
        input_layout.addWidget(input_button)
        layout.addLayout(input_layout)

        # Zone d'affichage des résultats
        self.results_text = QTextEdit()
        self.results_text.setReadOnly(True)
        layout.addWidget(QLabel("Description de la structure :"))
        layout.addWidget(self.results_text)

        # Sélection du fichier de sortie RTF
        output_layout = QHBoxLayout()
        self.output_file_line = QLineEdit()
        self.output_file_line.setPlaceholderText("Chemin du fichier RTF de sortie...")
        output_button = QPushButton("Sélectionner le fichier RTF")
        output_button.clicked.connect(self.select_output_file)
        export_button = QPushButton("Exporter en RTF")
        export_button.clicked.connect(self.export_to_rtf)
        output_layout.addWidget(self.output_file_line)
        output_layout.addWidget(output_button)
        output_layout.addWidget(export_button)
        layout.addLayout(output_layout)

        self.analysis_tab.setLayout(layout)

    def select_input_file(self):
        """Ouvrir un dialogue pour sélectionner le fichier d'entrée et lancer l'analyse."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier de données", "", "Tous fichiers (*.*);;CSV (*.csv);;Excel (*.xls *.xlsx);;Shapefile (*.shp);;GPKG (*.gpkg);;GPX (*.gpx);;GeoJSON (*.geojson)")
        if file_path:
            self.input_file_line.setText(file_path)
            self.analyze_file(file_path)

    def analyze_file(self, file_path):
        """Analyser la structure du fichier et afficher les résultats."""
        try:
            ext = os.path.splitext(file_path)[1].lower()
            description = f"Fichier : {file_path}\n"
            description += "Encodage : UTF-8 (assumé, non détecté dynamiquement)\n\n"

            # Vérifier si le fichier est géographique
            is_spatial = ext in ['.shp', '.gpkg', '.gpx', '.geojson']

            if is_spatial:
                # Charger comme couche vectorielle QGIS
                layer = QgsVectorLayer(file_path, "layer", "ogr")
                if not layer.isValid():
                    raise Exception("Impossible de charger le fichier comme couche vectorielle.")

                # Champs
                fields = layer.fields()
                description += "Champs :\n"
                for field in fields:
                    description += f"- Nom : {field.name()}, Type : {field.typeName()}, Taille : {field.length()}\n"

                # Informations géographiques
                description += "\nType de géométrie : " + QgsWkbTypes.displayString(layer.wkbType()) + "\n"
                description += "Système de projection : " + layer.crs().authid() + "\n"
                extent: QgsRectangle = layer.extent()
                description += f"Emprise : XMin: {extent.xMinimum()}, YMin: {extent.yMinimum()}, XMax: {extent.xMaximum()}, YMax: {extent.yMaximum()}\n"

            elif ext == '.csv':
                # Charger le CSV avec pandas
                try:
                    df = pd.read_csv(file_path, encoding='utf-8')
                except UnicodeDecodeError:
                    df = pd.read_csv(file_path, encoding='latin1')  # Fallback encoding
                # Champs
                description += "Champs :\n"
                for column in df.columns:
                    dtype = str(df[column].dtype)
                    description += f"- Nom : {column}, Type : {dtype}, Taille : Non applicable (CSV)\n"
                description += "\nType de géométrie : Non géographique\n"

                # Vérifier si le CSV contient des colonnes de coordonnées
                if any(col.lower() in ['x', 'y', 'latitude', 'longitude', 'geom', 'geometry'] for col in df.columns):
                    description += "Note : Des colonnes suggérant des données géographiques (x, y, latitude, longitude, geom) sont présentes, mais aucune géométrie n'a été chargée.\n"

            elif ext in ['.xls', '.xlsx']:
                # Charger le fichier Excel avec pandas
                try:
                    df = pd.read_excel(file_path, engine='openpyxl')
                except Exception as e:
                    raise Exception(f"Erreur lors du chargement du fichier Excel : {str(e)}")
                # Champs
                description += "Champs :\n"
                for column in df.columns:
                    dtype = str(df[column].dtype)
                    description += f"- Nom : {column}, Type : {dtype}, Taille : Non applicable (Excel)\n"
                description += "\nType de géométrie : Non géographique\n"

            else:
                raise Exception("Format de fichier non supporté ou non reconnu.")

            self.results_text.setPlainText(description)

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de l'analyse : {str(e)}")
            self.results_text.clear()

    def select_output_file(self):
        """Ouvrir un dialogue pour sélectionner le fichier de sortie RTF."""
        file_path, _ = QFileDialog.getSaveFileName(self, "Sélectionner le fichier RTF de sortie", "", "RTF (*.rtf)")
        if file_path:
            self.output_file_line.setText(file_path)

    def export_to_rtf(self):
        """Exporter la description dans un fichier RTF (format texte simple avec extension RTF)."""
        output_path = self.output_file_line.text()
        if not output_path:
            QMessageBox.warning(self, "Avertissement", "Veuillez sélectionner un fichier de sortie.")
            return

        try:
            description = self.results_text.toPlainText()
            if not description:
                raise Exception("Aucune description à exporter.")

            # Écrire en RTF basique (header simple + texte)
            rtf_content = r'{\rtf1\ansi\deff0 {\fonttbl {\f0 Courier;}} \f0\fs20 ' + description.replace('\n', '\\par ') + '}'
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(rtf_content)
            QMessageBox.information(self, "Succès", "Exportation réussie.")

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de l'exportation : {str(e)}")

    def run(self):
        self.exec_()
