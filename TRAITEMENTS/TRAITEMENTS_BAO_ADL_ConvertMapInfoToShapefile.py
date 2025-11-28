# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFileDialog, QMessageBox, QLineEdit
from qgis.PyQt.QtCore import Qt
from qgis.core import QgsVectorLayer, QgsProject
import os
import glob
import shutil
import csv
from datetime import datetime

class ConvertMapInfoToShapefileDialog(QDialog):
    def __init__(self, parent=None):
        super(ConvertMapInfoToShapefileDialog, self).__init__(parent)
        self.setWindowTitle("Conversion MapInfo vers Shapefile")
        self.setMinimumWidth(500)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Source directory
        source_layout = QHBoxLayout()
        self.source_label = QLabel("Dossier source:")
        self.source_line_edit = QLineEdit()
        self.source_browse_button = QPushButton("Parcourir...")
        source_layout.addWidget(self.source_label)
        source_layout.addWidget(self.source_line_edit)
        source_layout.addWidget(self.source_browse_button)

        # Archive directory
        archive_layout = QHBoxLayout()
        self.archive_label = QLabel("Dossier d'archive:")
        self.archive_line_edit = QLineEdit()
        self.archive_browse_button = QPushButton("Parcourir...")
        archive_layout.addWidget(self.archive_label)
        archive_layout.addWidget(self.archive_line_edit)
        archive_layout.addWidget(self.archive_browse_button)

        # Output directory
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Dossier de sortie:")
        self.output_line_edit = QLineEdit()
        self.output_browse_button = QPushButton("Parcourir...")
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_line_edit)
        output_layout.addWidget(self.output_browse_button)

        # Convert button
        self.convert_button = QPushButton("Convertir")
        self.convert_button.setStyleSheet("background-color: #4CAF50; color: white;")

        # Add widgets to layout
        layout.addLayout(source_layout)
        layout.addLayout(archive_layout)
        layout.addLayout(output_layout)
        layout.addWidget(self.convert_button)

        self.setLayout(layout)

        # Connect signals
        self.source_browse_button.clicked.connect(self.browse_source)
        self.archive_browse_button.clicked.connect(self.browse_archive)
        self.output_browse_button.clicked.connect(self.browse_output)
        self.convert_button.clicked.connect(self.convert)

    def browse_source(self):
        directory = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier source")
        if directory:
            self.source_line_edit.setText(directory)

    def browse_archive(self):
        directory = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier d'archive")
        if directory:
            self.archive_line_edit.setText(directory)

    def browse_output(self):
        directory = QFileDialog.getExistingDirectory(self, "Sélectionner le dossier de sortie")
        if directory:
            self.output_line_edit.setText(directory)

    def create_rtf_file(self, file_path, original_file_name, creation_date):
        """Crée un fichier RTF avec le nom du fichier original et sa date de création."""
        with open(file_path, 'w') as rtf_file:
            rtf_file.write("\\rtf1\\ansi\n")
            rtf_file.write(f"Nom du fichier original: {original_file_name}\\par\n")
            rtf_file.write(f"Date de création: {creation_date}\\par\n")

    def create_metadata_txt(self, output_dir, base_name, original_path):
        """Crée un fichier .txt avec le chemin originel de la couche MapInfo."""
        txt_file_path = os.path.join(output_dir, f"{base_name}_MD.txt")
        with open(txt_file_path, 'w') as txt_file:
            txt_file.write(f"Le fichier {base_name} provient d'une couche map info qui se trouvait sur: {original_path}\n")

    def convert(self):
        source_dir = self.source_line_edit.text()
        archive_dir = self.archive_line_edit.text()
        output_dir = self.output_line_edit.text()

        if not source_dir or not archive_dir or not output_dir:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner tous les dossiers.")
            return

        try:
            self.process_mapinfo_files(source_dir, archive_dir, output_dir)
            QMessageBox.information(self, "Succès", "Conversion terminée avec succès.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue: {e}")

    def process_mapinfo_files(self, source_dir, archive_dir, output_dir):
        # Créer les répertoires de sortie et d'archive s'ils n'existent pas
        os.makedirs(output_dir, exist_ok=True)
        os.makedirs(archive_dir, exist_ok=True)

        # Créer un fichier CSV pour enregistrer les informations sur les couches modifiées
        csv_file_path = os.path.join(output_dir, "couches_modifiees.csv")
        with open(csv_file_path, mode='w', newline='') as csv_file:
            writer = csv.writer(csv_file)
            writer.writerow(["Nom de la couche", "Date de création", "Chemin originel"])

            # Parcourir tous les fichiers .tab dans le répertoire source
            for tab_file in glob.glob(os.path.join(source_dir, '*.tab')):
                try:
                    # Obtenir le nom de base du fichier
                    base_name = os.path.splitext(os.path.basename(tab_file))[0]
                    # Obtenir la date de création du fichier
                    creation_time = os.path.getctime(tab_file)
                    creation_date = datetime.fromtimestamp(creation_time)
                    year = creation_date.strftime('%Y')

                    # Vérifier si un shapefile de même nom existe déjà
                    output_shapefile = os.path.join(output_dir, f"{base_name}.shp")
                    if os.path.exists(output_shapefile):
                        print(f"Un shapefile existe déjà pour {base_name}, pas de conversion.")
                        continue

                    # Convertir le fichier .tab en shapefile en utilisant ogr2ogr
                    conversion_command = f"ogr2ogr -f \"ESRI Shapefile\" \"{output_shapefile}\" \"{tab_file}\""
                    os.system(conversion_command)

                    # Charger le shapefile dans QGIS
                    layer = QgsVectorLayer(output_shapefile, base_name, "ogr")
                    if layer.isValid():
                        QgsProject.instance().addMapLayer(layer)

                    # Créer un fichier RTF
                    rtf_file_path = os.path.join(output_dir, f"{base_name}.rtf")
                    self.create_rtf_file(rtf_file_path, os.path.basename(tab_file), creation_date.strftime('%Y-%m-%d %H:%M:%S'))

                    # Créer un fichier .txt avec le chemin originel
                    self.create_metadata_txt(output_dir, base_name, source_dir)

                    # Écrire les informations dans le fichier CSV
                    writer.writerow([base_name, creation_date.strftime('%Y-%m-%d %H:%M:%S'), source_dir])

                    # Copier ou Déplacer tous les fichiers associés au fichier .tab vers le dossier d'archive
                    for ext in ['*.tab', '*.dat', '*.id', '*.map']:
                        for file in glob.glob(os.path.join(source_dir, f"{base_name}{os.path.splitext(ext)[0]}*")):
                            try:
                                shutil.copy(file, archive_dir)
                                #shutil.move(file, archive_dir)
                            except PermissionError as e:
                                print(f"Impossible de déplacer {file} : {e}")
                                continue
                except Exception as e:
                    print(f"Une erreur s'est produite lors du traitement de {tab_file} : {e}")
                    continue

class MainPluginConvertMapInfoToShapefile(object):
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        # Création de l'action
        self.action = QAction(QIcon("path/to/icon.png"), "Convertir MapInfo en Shapefile", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        # Ajout de l'action à la barre d'outils et au menu
        self.iface.addToolBarIcon(self.action)
        self.iface.addPluginToMenu("TRAITEMENTS", self.action)

    def unload(self):
        # Retirer l'action de la barre d'outils et du menu
        self.iface.removeToolBarIcon(self.action)
        self.iface.removePluginMenu("TRAITEMENTS", self.action)

    def run(self):
        dialog = ConvertMapInfoToShapefileDialog(self.iface.mainWindow())
        dialog.exec_()
