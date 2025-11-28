# Fichier : TRAITEMENTS_CarteDynamiqueAgricole.py
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QTextEdit,
    QPushButton, QFileDialog, QLabel, QLineEdit, QMessageBox,
    QInputDialog, QHBoxLayout, QProgressBar, QTextBrowser, QApplication
)
from qgis.PyQt.QtCore import Qt, QTimer
from qgis.PyQt.QtGui import QColor
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsMapLayer, QgsDataSourceUri,
    QgsCoordinateReferenceSystem, QgsCoordinateTransform,
    QgsLayoutExporter, QgsPrintLayout, QgsLayoutItemMap, QgsLayoutItemHtml,
    QgsFeature, QgsGeometry, QgsField, QgsVectorFileWriter
)
from qgis.gui import QgsMapCanvas
import os
import pandas as pd
import time

class CarteDynamiqueAgricoleDialog(QDialog):
    def __init__(self, parent=None):
        super(CarteDynamiqueAgricoleDialog, self).__init__(parent)
        self.setWindowTitle("Carte Dynamique Agricole")
        self.setMinimumWidth(800)

        # Chemins par défaut
        self.default_parcelle_path = "N:/CADASTRE/PCI_EXPRESS/N_PARCELLE_PCIe_021.shp"
        self.default_zone_path = "W:/2_DOSSIERS/AMENAGEMENT_URBANISME/ZONAGES_ETUDE/Doc_cadre_PV/DC_21_L93.shp"

        # Initialisation
        self.parcelle_layer = None
        self.ilot_layer = None
        self.zone_layer = None
        self.parcelles_filtered = None
        self.jointure_df = None

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
        layout = QVBoxLayout()
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        instructions = """
<h2>Carte Dynamique Agricole</h2>
<h3>Fonctionnalités :</h3>
<p>Ce module permet de générer une carte interactive des parcelles agricoles et cadastrales dans une zone d'étude, avec export en HTML.</p>
<h3>Données nécessaires :</h3>
<ul>
    <li>Couche des parcelles cadastrales (Shapefile : N:/CADASTRE/PCI_EXPRESS/N_PARCELLE_PCIe_021.shp).</li>
    <li>Couche des ilots agricoles (PostGIS : gb_ddt21.x_agriculture_restreint.parcelle_rpg_s_021_2024).</li>
    <li>Couche de la zone d'étude (Shapefile : W:/2_DOSSIERS/.../DC_21_L93.shp).</li>
</ul>
<h3>Utilisation :</h3>
<ol>
    <li>Vérifiez les chemins des couches Shapefile.</li>
    <li>Connectez-vous à PostGIS pour charger les ilots agricoles.</li>
    <li>Cliquez sur "Générer la Carte" et suivez la progression.</li>
    <li>Exportez la carte en HTML.</li>
</ol>
"""
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_analysis_tab(self):
        layout = QVBoxLayout()

        # Parcelles cadastrales
        self.parcelle_path_edit = QLineEdit(self.default_parcelle_path)
        self.parcelle_path_edit.setReadOnly(True)
        self.parcelle_path_button = QPushButton("Vérifier Chemin")
        self.parcelle_path_button.clicked.connect(self.check_parcelle_path)
        self.parcelle_status_label = QLabel("Statut : Non vérifié")
        self.parcelle_status_label.setStyleSheet("color: grey;")

        # Ilots agricoles (PostGIS)
        self.ilot_connect_button = QPushButton("Se connecter à PostGIS")
        self.ilot_connect_button.clicked.connect(self.connect_to_postgis)
        self.ilot_status_label = QLabel("Statut : Non connecté")
        self.ilot_status_label.setStyleSheet("color: grey;")

        # Zone d'étude
        self.zone_path_edit = QLineEdit(self.default_zone_path)
        self.zone_path_edit.setReadOnly(True)
        self.zone_path_button = QPushButton("Vérifier Chemin")
        self.zone_path_button.clicked.connect(self.check_zone_path)
        self.zone_status_label = QLabel("Statut : Non vérifié")
        self.zone_status_label.setStyleSheet("color: grey;")

        # ProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)

        # Zone de log
        self.log_text = QTextBrowser()
        self.log_text.setMaximumHeight(150)

        # Boutons
        self.generate_button = QPushButton("Générer la Carte")
        self.generate_button.clicked.connect(self.generate_map)
        self.export_button = QPushButton("Exporter en HTML")
        self.export_button.clicked.connect(self.export_to_html)

        # Ajout des widgets
        layout.addWidget(QLabel("Parcelles Cadastrales :"))
        layout.addWidget(self.parcelle_path_edit)
        layout.addWidget(self.parcelle_path_button)
        layout.addWidget(self.parcelle_status_label)

        layout.addWidget(QLabel("Ilots Agricoles (PostGIS) :"))
        layout.addWidget(self.ilot_connect_button)
        layout.addWidget(self.ilot_status_label)

        layout.addWidget(QLabel("Zone d'Étude :"))
        layout.addWidget(self.zone_path_edit)
        layout.addWidget(self.zone_path_button)
        layout.addWidget(self.zone_status_label)

        layout.addWidget(QLabel("Progression :"))
        layout.addWidget(self.progress_bar)

        layout.addWidget(QLabel("Logs :"))
        layout.addWidget(self.log_text)

        layout.addWidget(self.generate_button)
        layout.addWidget(self.export_button)

        self.analysis_tab.setLayout(layout)

    def log_message(self, message):
        self.log_text.append(message)
        QApplication.processEvents()  # Force la mise à jour de l'interface

    def check_parcelle_path(self):
        if os.path.exists(self.default_parcelle_path):
            self.parcelle_layer = QgsVectorLayer(self.default_parcelle_path, "Parcelles Cadastrales", "ogr")
            if self.parcelle_layer.isValid():
                self.parcelle_status_label.setText("Couche trouvée et valide.")
                self.parcelle_status_label.setStyleSheet("color: green;")
                QgsProject.instance().addMapLayer(self.parcelle_layer)  # Ajout à QGIS
                self.log_message("✅ Couche des parcelles cadastrales chargée et ajoutée à QGIS.")
            else:
                self.parcelle_status_label.setText("Erreur : couche invalide.")
                self.parcelle_status_label.setStyleSheet("color: red;")
                self.log_message("❌ Erreur : couche des parcelles cadastrales invalide.")
        else:
            self.parcelle_status_label.setText("Erreur : chemin introuvable.")
            self.parcelle_status_label.setStyleSheet("color: red;")
            self.log_message("❌ Erreur : chemin des parcelles cadastrales introuvable.")

    def check_zone_path(self):
        if os.path.exists(self.default_zone_path):
            self.zone_layer = QgsVectorLayer(self.default_zone_path, "Zone d'Étude", "ogr")
            if self.zone_layer.isValid():
                self.zone_status_label.setText("Couche trouvée et valide.")
                self.zone_status_label.setStyleSheet("color: green;")
                QgsProject.instance().addMapLayer(self.zone_layer)  # Ajout à QGIS
                self.log_message("✅ Couche de la zone d'étude chargée et ajoutée à QGIS.")
            else:
                self.zone_status_label.setText("Erreur : couche invalide.")
                self.zone_status_label.setStyleSheet("color: red;")
                self.log_message("❌ Erreur : couche de la zone d'étude invalide.")
        else:
            self.zone_status_label.setText("Erreur : chemin introuvable.")
            self.zone_status_label.setStyleSheet("color: red;")
            self.log_message("❌ Erreur : chemin de la zone d'étude introuvable.")

    def connect_to_postgis(self):
        user, ok1 = QInputDialog.getText(self, "Connexion PostGIS", "Identifiant :")
        if not ok1:
            return
        password, ok2 = QInputDialog.getText(self, "Connexion PostGIS", "Mot de passe :", QLineEdit.Password)
        if not ok2:
            return

        self.log_message("🔄 Connexion à PostGIS en cours...")

        uri = QgsDataSourceUri()
        uri.setConnection("10.21.8.40", "5432", "gb_ddt21", user, password)
        uri.setDataSource("x_agriculture_restreint", "parcelle_rpg_s_021_2024", "geom", "", "id")

        self.ilot_layer = QgsVectorLayer(uri.uri(False), "Ilots Agricoles 2024", "postgres")
        if self.ilot_layer.isValid():
            self.ilot_status_label.setText("Connexion réussie. Couche chargée.")
            self.ilot_status_label.setStyleSheet("color: green;")
            QgsProject.instance().addMapLayer(self.ilot_layer)  # Ajout à QGIS
            self.log_message("✅ Connexion à PostGIS réussie. Couche des ilots agricoles ajoutée à QGIS.")
        else:
            self.ilot_status_label.setText("Erreur : impossible de charger la couche.")
            self.ilot_status_label.setStyleSheet("color: red;")
            self.log_message("❌ Erreur : impossible de charger la couche des ilots agricoles.")

    def transform_to_wgs84(self, layer, step_start, step_end):
        for step in range(step_start, step_end + 1):
            self.progress_bar.setValue(step)
            QApplication.processEvents()  # Met à jour l'interface

        self.log_message(f"🔄 Transformation de {layer.name()} en WGS84...")

        crs_dest = QgsCoordinateReferenceSystem("EPSG:4326")
        transform = QgsCoordinateTransform(layer.crs(), crs_dest, QgsProject.instance())

        features = list(layer.getFeatures())
        total_features = len(features)
        for i, feature in enumerate(features):
            # Mise à jour de la ProgressBar par feature
            current_step = step_start + int((i / total_features) * (step_end - step_start))
            self.progress_bar.setValue(current_step)
            QApplication.processEvents()

            geom = feature.geometry()
            geom.transform(transform)
            layer.dataProvider().changeGeometryValues({feature.id(): geom})

        self.log_message(f"✅ Transformation de {layer.name()} terminée.")

    def filter_intersecting_parcelles(self, step_start, step_end):
        for step in range(step_start, step_end + 1):
            self.progress_bar.setValue(step)
            QApplication.processEvents()

        self.log_message("🔄 Filtrage des parcelles intersectant la zone d'étude...")

        zone_features = [f for f in self.zone_layer.getFeatures()]
        parcelles_intersect = []

        total_parcelles = self.parcelle_layer.featureCount()
        for i, parcelle in enumerate(self.parcelle_layer.getFeatures()):
            # Mise à jour de la ProgressBar par parcelle
            current_step = step_start + int((i / total_parcelles) * (step_end - step_start))
            self.progress_bar.setValue(current_step)
            QApplication.processEvents()

            for zone in zone_features:
                if parcelle.geometry().intersects(zone.geometry()):
                    parcelles_intersect.append(parcelle)
                    break

        # Créer une couche mémoire pour les parcelles filtrées
        filtered_layer = QgsVectorLayer("Polygon?crs=EPSG:4326", "Parcelles filtrées", "memory")
        filtered_layer.dataProvider().addAttributes(self.parcelle_layer.fields())
        filtered_layer.dataProvider().addFeatures(parcelles_intersect)

        # Ajouter la couche au projet QGIS
        QgsProject.instance().addMapLayer(filtered_layer)
        self.log_message("✅ Couche des parcelles filtrées créée et ajoutée à QGIS.")

        return filtered_layer

    def perform_join_and_calculs(self, step_start, step_end):
        for step in range(step_start, step_end + 1):
            self.progress_bar.setValue(step)
            QApplication.processEvents()

        self.log_message("🔄 Jointure et calculs en cours...")

        # Extraire les données en DataFrame pandas
        parcelles_df = pd.DataFrame([f.attributes() for f in self.parcelles_filtered.getFeatures()])
        ilots_df = pd.DataFrame([f.attributes() for f in self.ilot_layer.getFeatures()])

        # Jointure sur num_ilot
        jointure_df = pd.merge(parcelles_df, ilots_df, on="num_ilot", how="left")

        # Sauvegarder le DataFrame intermédiaire dans un fichier CSV
        csv_path = os.path.join(os.path.expanduser("~"), "jointure_intermediaire.csv")
        jointure_df.to_csv(csv_path, index=False)
        self.log_message(f"📁 Tableau intermédiaire sauvegardé : {csv_path}")

        # Calcul de surface (en hectares)
        total_features = self.parcelles_filtered.featureCount()
        for i, feature in enumerate(self.parcelles_filtered.getFeatures()):
            current_step = step_start + int((i / total_features) * (step_end - step_start))
            self.progress_bar.setValue(current_step)
            QApplication.processEvents()

            area = feature.geometry().area() / 10000
            self.parcelles_filtered.dataProvider().changeAttributeValues({feature.id(): {"surface": area}})

        self.log_message("✅ Jointure et calculs terminés.")
        return jointure_df

    def generate_map(self):
        try:
            if not (self.parcelle_layer and self.ilot_layer and self.zone_layer):
                QMessageBox.warning(self, "Erreur", "Veuillez charger toutes les couches.")
                return

            self.progress_bar.setValue(0)
            self.log_message("🚀 Début de la génération de la carte...")

            # 1. Transformer les couches en WGS84 (10% à 20%)
            self.transform_to_wgs84(self.parcelle_layer, 10, 20)
            self.transform_to_wgs84(self.zone_layer, 20, 30)

            # 2. Filtrer les parcelles intersectant la zone (30% à 60%)
            self.parcelles_filtered = self.filter_intersecting_parcelles(30, 60)

            # 3. Jointure et calculs (60% à 90%)
            self.jointure_df = self.perform_join_and_calculs(60, 90)

            # 4. Créer le canva de la carte (90% à 100%)
            self.log_message("🗺️ Création de la carte...")
            self.canvas = QgsMapCanvas()
            self.canvas.setLayers([self.parcelles_filtered, self.ilot_layer, self.zone_layer])
            self.canvas.zoomToFullExtent()

            self.progress_bar.setValue(100)
            self.log_message("🎉 Carte générée avec succès !")

            QMessageBox.information(self, "Succès", "Carte générée avec succès !")

        except Exception as e:
            self.log_message(f"❌ Erreur : {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Erreur : {str(e)}")

    def export_to_html(self):
        try:
            if not hasattr(self, 'canvas'):
                QMessageBox.warning(self, "Erreur", "Veuillez d'abord générer la carte.")
                return

            self.log_message("📤 Export de la carte en HTML...")

            # Créer un layout pour l'export
            layout = QgsPrintLayout(QgsProject.instance())
            layout.initializeDefaults()

            # Ajouter une carte au layout
            map_item = QgsLayoutItemMap(layout)
            map_item.setRect(20, 20, 20, 20)
            map_item.setExtent(self.canvas.extent())
            layout.addLayoutItem(map_item)

            # Exporter en HTML
            exporter = QgsLayoutExporter(layout)
            output_path = os.path.join(os.path.expanduser("~"), "carte_agricole.html")
            exporter.exportToHtml(output_path, QgsLayoutExporter.HtmlExportSettings())

            self.log_message(f"📁 Carte exportée vers : {output_path}")
            QMessageBox.information(self, "Succès", f"Carte exportée vers : {output_path}")

        except Exception as e:
            self.log_message(f"❌ Erreur : {str(e)}")
            QMessageBox.critical(self, "Erreur", f"Erreur : {str(e)}")
