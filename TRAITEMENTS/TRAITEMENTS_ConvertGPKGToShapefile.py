# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                 QFileDialog, QMessageBox, QLineEdit, QComboBox, QCheckBox,
                                 QGroupBox, QFormLayout, QTextEdit)
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsVectorLayer, QgsProject, QgsMapLayer, QgsStyle, QgsSymbol
from qgis.utils import iface
import os
import re
import glob
import shutil
import csv
from datetime import datetime
from pathlib import Path

class ConvertGPKGToShapefileDialog(QDialog):
    def __init__(self, parent=None):
        super(ConvertGPKGToShapefileDialog, self).__init__(parent)
        self.setWindowTitle("Conversion GPKG vers Shapefile")
        self.setMinimumWidth(600)
        self.setup_ui()
        self.show_instructions()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Instructions
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        self.instructions_text.setFixedHeight(100)
        layout.addWidget(self.instructions_text)

        # GPKG file selection
        gpkg_layout = QHBoxLayout()
        self.gpkg_label = QLabel("Fichier GPKG source:")
        self.gpkg_line_edit = QLineEdit()
        self.gpkg_browse_button = QPushButton("Parcourir...")
        gpkg_layout.addWidget(self.gpkg_label)
        gpkg_layout.addWidget(self.gpkg_line_edit)
        gpkg_layout.addWidget(self.gpkg_browse_button)

        # Output directory selection
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Dossier de sortie:")
        self.output_line_edit = QLineEdit()
        self.output_browse_button = QPushButton("Parcourir...")
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_line_edit)
        output_layout.addWidget(self.output_browse_button)

        # Layer selection
        self.layer_group = QGroupBox("Couches à convertir")
        layer_layout = QVBoxLayout()
        self.layer_combo = QComboBox()
        layer_layout.addWidget(self.layer_combo)
        self.layer_group.setLayout(layer_layout)

        # Filter options
        self.filter_group = QGroupBox("Filtres (optionnel)")
        filter_layout = QFormLayout()
        self.filter_check = QCheckBox("Appliquer un filtre")
        self.field_combo = QComboBox()
        self.value_line = QLineEdit()
        filter_layout.addRow(self.filter_check)
        filter_layout.addRow("Champ:", self.field_combo)
        filter_layout.addRow("Valeur:", self.value_line)
        self.filter_group.setLayout(filter_layout)
        self.filter_group.setEnabled(False)

        # Convert button
        self.convert_button = QPushButton("Convertir")
        self.convert_button.setStyleSheet("background-color: #4CAF50; color: white;")

        # Add widgets to layout
        layout.addLayout(gpkg_layout)
        layout.addLayout(output_layout)
        layout.addWidget(self.layer_group)
        layout.addWidget(self.filter_group)
        layout.addWidget(self.convert_button)

        self.setLayout(layout)

        # Connect signals
        self.gpkg_browse_button.clicked.connect(self.browse_gpkg)
        self.output_browse_button.clicked.connect(self.browse_output)
        self.gpkg_line_edit.textChanged.connect(self.load_layers)
        self.filter_check.stateChanged.connect(self.toggle_filter)
        self.convert_button.clicked.connect(self.convert)

    def show_instructions(self):
        instructions = """
        Ce module permet de convertir une ou plusieurs couches d'un fichier GeoPackage (GPKG) en Shapefiles.

        Fonctionnalités :
        - Conversion des couches GPKG en Shapefiles.
        - Application de filtres pour ne convertir que certaines entités.
        - Création de fichiers de métadonnées (.rtf) pour chaque Shapefile généré.
        - Conservation des styles et des étiquettes du GPKG source.
        - Renommage des Shapefiles selon les valeurs des filtres appliqués.

        Instructions :
        1. Sélectionnez un fichier GPKG source.
        2. Sélectionnez un dossier de sortie.
        3. Choisissez la ou les couches à convertir.
        4. (Optionnel) Appliquez un filtre pour ne convertir que certaines entités.
        5. Cliquez sur "Convertir" pour lancer la conversion.
        """
        self.instructions_text.setPlainText(instructions)

    def browse_gpkg(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner le fichier GPKG", "", "GeoPackage Files (*.gpkg)")
        if file_path:
            self.gpkg_line_edit.setText(file_path)

    def browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier de sortie")
        if directory:
            self.output_line_edit.setText(directory)

    def load_layers(self):
        gpkg_path = self.gpkg_line_edit.text()
        if not gpkg_path:
            return

        self.layer_combo.clear()
        gpkg_file = QgsVectorLayer(gpkg_path, "temp", "ogr")
        if not gpkg_file.isValid():
            QMessageBox.warning(self, "Erreur", "Le fichier GPKG n'est pas valide.")
            return

        # Get all layers in the GPKG file
        layers = QgsProject.instance().addMapLayers([gpkg_file], False)
        if not layers:
            QMessageBox.warning(self, "Erreur", "Aucune couche trouvée dans le fichier GPKG.")
            return

        layer = layers[0]
        sublayers = layer.dataProvider().subLayers()
        for sublayer in sublayers:
            self.layer_combo.addItem(sublayer.desc(), sublayer)

        # Load fields for filter
        self.field_combo.clear()
        if self.layer_combo.count() > 0:
            layer_name = self.layer_combo.itemData(0)
            layer = QgsVectorLayer(f"{gpkg_path}|layername={layer_name}", "temp_layer", "ogr")
            if layer.isValid():
                for field in layer.fields():
                    self.field_combo.addItem(field.name())

    def toggle_filter(self, state):
        self.filter_group.setEnabled(state == Qt.Checked)

    def sanitize_filename(self, name):
        # Remove special characters and accents
        name = re.sub(r'[^\w\-_. ]', '_', name)
        name = name.replace(' ', '_')
        return name

    def create_rtf_file(self, file_path, metadata):
        """Crée un fichier RTF avec les métadonnées."""
        with open(file_path, 'w', encoding='utf-8') as rtf_file:
            rtf_file.write("\\rtf1\\ansi\\ansicpg1252\\deff0\\deflang1036\n")
            rtf_file.write("{\\fonttbl{\\f0\\fnil\\fcharset0 Arial;}}\n")
            rtf_file.write("\\viewkind4\\uc1\\pard\\f0\\fs20\n")
            rtf_file.write(f"Nom du fichier original: {metadata['source_name']}\\par\n")
            rtf_file.write(f"Date de création: {metadata['creation_date']}\\par\n")
            rtf_file.write(f"Couche source: {metadata['layer_name']}\\par\n")
            rtf_file.write("\\par\n")
            rtf_file.write("Description:\\par\n")
            rtf_file.write(metadata['description'].replace('\n', '\\par\n'))
            rtf_file.write("\\par\n")

    def convert(self):
        gpkg_path = self.gpkg_line_edit.text()
        output_dir = self.output_line_edit.text()

        if not gpkg_path or not output_dir:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier GPKG et un dossier de sortie.")
            return

        if self.layer_combo.count() == 0:
            QMessageBox.warning(self, "Erreur", "Aucune couche disponible pour la conversion.")
            return

        selected_layer_index = self.layer_combo.currentIndex()
        if selected_layer_index < 0:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner une couche à convertir.")
            return

        layer_name = self.layer_combo.itemData(selected_layer_index)
        layer_uri = f"{gpkg_path}|layername={layer_name}"
        layer = QgsVectorLayer(layer_uri, layer_name, "ogr")

        if not layer.isValid():
            QMessageBox.warning(self, "Erreur", "La couche sélectionnée n'est pas valide.")
            return

        # Apply filter if needed
        filter_expr = None
        if self.filter_check.isChecked():
            field_name = self.field_combo.currentText()
            field_value = self.value_line.text()
            if field_name and field_value:
                filter_expr = f"\"{field_name}\" = '{field_value}'"
                layer.setSubsetString(filter_expr)

        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Get layer metadata
        creation_date = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        source_name = os.path.basename(gpkg_path)
        description = f"""
        Ce Shapefile a été généré à partir de la couche '{layer_name}' du fichier GPKG '{source_name}'.
        {f"Filtre appliqué: {filter_expr}" if filter_expr else "Aucun filtre appliqué."}

        Informations sur la conversion:
        - Date de conversion: {creation_date}
        - Logiciel utilisé: QGIS
        - Module: Convertisseur GPKG vers Shapefile

        Description du processus:
        Le module convertit les couches GeoPackage en Shapefiles tout en conservant les styles et les étiquettes.
        Si un filtre est appliqué, seuls les éléments correspondant au filtre sont convertis.
        Les Shapefiles générés sont renommés selon les valeurs des filtres appliqués.
        Un fichier de métadonnées (.rtf) est créé pour chaque Shapefile généré.
        """

        # Sanitize layer name for filename
        base_name = self.sanitize_filename(layer_name)
        if filter_expr:
            field_name = self.field_combo.currentText()
            field_value = self.value_line.text()
            sanitized_value = self.sanitize_filename(field_value)
            base_name = f"{base_name}_{field_name}_{sanitized_value}"

        # Export to Shapefile
        output_shapefile = os.path.join(output_dir, f"{base_name}.shp")
        error = QgsVectorFileWriter.writeAsVectorFormat(layer, output_shapefile, "UTF-8", layer.crs(), "ESRI Shapefile")
        if error != QgsVectorFileWriter.NoError:
            QMessageBox.warning(self, "Erreur", f"Erreur lors de la conversion: {QgsVectorFileWriter.errorMessage(error)}")
            return

        # Create metadata file
        metadata = {
            'source_name': source_name,
            'creation_date': creation_date,
            'layer_name': layer_name,
            'description': description
        }
        rtf_file_path = os.path.join(output_dir, f"{base_name}_MD.rtf")
        self.create_rtf_file(rtf_file_path, metadata)

        # Export style if available
        style_path = os.path.join(output_dir, f"{base_name}.qml")
        layer.saveNamedStyle(style_path)

        # Load the Shapefile into QGIS
        output_layer = QgsVectorLayer(output_shapefile, base_name, "ogr")
        if output_layer.isValid():
            QgsProject.instance().addMapLayer(output_layer)

        QMessageBox.information(self, "Succès", f"Conversion terminée avec succès. Le Shapefile a été enregistré sous {output_shapefile}")

class MainPluginConvertGPKGToShapefile(object):
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        # Création de l'action
        self.action = QAction(QIcon("path/to/icon.png"), "Convertir GPKG en Shapefile", self.iface.mainWindow())
        self.action.triggered.connect(self.run)

    def unload(self):
        # Retirer l'action de la barre d'outils et du menu
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("TRAITEMENTS", self.action)

    def run(self):
        dialog = ConvertGPKGToShapefileDialog(self.iface.mainWindow())
        dialog.exec_()
