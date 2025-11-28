# Fichier : TRAITEMENTS_Terres_a_disposition.py
import os
import pandas as pd
from qgis.core import (
    QgsVectorLayer, QgsFeatureRequest, QgsFeature, QgsGeometry,
    QgsVectorFileWriter, QgsProject, QgsField, QgsFields, QgsVectorDataProvider
)
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QTextEdit, QLabel, QLineEdit,
    QPushButton, QFileDialog, QMessageBox, QFormLayout, QProgressBar, QTextBrowser,QHBoxLayout
)
from qgis.PyQt.QtGui import QRegExpValidator, QColor
from qgis.PyQt.QtCore import Qt, QRegExp, QVariant

class TerresADispositionDialog(QDialog):
    def __init__(self, iface, parent=None):
        super(TerresADispositionDialog, self).__init__(parent)
        self.iface = iface
        self.setWindowTitle("Terres à disposition")
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
        layout = QVBoxLayout()
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        instructions = """
        <h2>Terres à disposition</h2>
        <h3>Fonctionnalités :</h3>
        <p>Ce module permet de calculer les surfaces supplémentaires pour un numéro de PACAGE en 2025 par rapport à 2024.</p>
        <h3>Données nécessaires :</h3>
        <p>- Couche P24 : W:\\2_DOSSIERS\\AGRICULTURE\\EXPLOITATION_ELEVAGE\\STRUCTURE\\PAC\\p24\\P24.shp</p>
        <p>- Couche P25 : W:\\2_DOSSIERS\\AGRICULTURE\\EXPLOITATION_ELEVAGE\\STRUCTURE\\PAC\\p25\\P25.shp</p>
        <p>- Couche cadastrale : W:\\2_DOSSIERS\\AGRICULTURE\\EXPLOITATION_ELEVAGE\\STRUCTURE\\cadastre\\parcelles-21-valide.shp</p>
        <p>Le champ pour le filtrage est 'PACAGE' (type String, taille 10).</p>
        <h3>Utilisation :</h3>
        <ol>
            <li>Vérifiez que les chemins des couches sont corrects et accessibles.</li>
            <li>Saisissez un numéro de PACAGE (9 chiffres, ex : 021155950).</li>
            <li>Choisissez un dossier d'export.</li>
            <li>Cliquez sur 'Lancer le traitement'.</li>
        </ol>
        """
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_analysis_tab(self):
        layout = QFormLayout()

        # Chemins des couches
        # Chemins des couches P24
        self.p24_path_edit = QLineEdit(r"W:\2_DOSSIERS\AGRICULTURE\EXPLOITATION_ELEVAGE\STRUCTURE\PAC\p24\P24.shp")
        self.p24_label = QLabel("Couches de îlots PACAGE année n-1 :")
        self.p24_status = QLabel("Vérification en cours...")
        self.p24_browse_button = QPushButton("Ou sélectionner autre fichier")
        self.p24_browse_button.clicked.connect(lambda: self.choose_layer_path(self.p24_path_edit, self.p24_status))
        p24_layout = QHBoxLayout()
        p24_layout.addWidget(self.p24_path_edit)
        p24_layout.addWidget(self.p24_browse_button)
        layout.addRow(self.p24_label, p24_layout)
        layout.addRow("", self.p24_status)

        # Chemins des couches P25
        self.p25_path_edit = QLineEdit(r"W:\2_DOSSIERS\AGRICULTURE\EXPLOITATION_ELEVAGE\STRUCTURE\PAC\p25\P25.shp")
        self.p25_label = QLabel("Couches de îlots PACAGE année n :")
        self.p25_status = QLabel("Vérification en cours...")
        self.p25_browse_button = QPushButton("Ou sélectionner autre fichier")
        self.p25_browse_button.clicked.connect(lambda: self.choose_layer_path(self.p25_path_edit, self.p25_status))
        p25_layout = QHBoxLayout()
        p25_layout.addWidget(self.p25_path_edit)
        p25_layout.addWidget(self.p25_browse_button)
        layout.addRow(self.p25_label, p25_layout)
        layout.addRow("", self.p25_status)

        # Chemins des couches cadastrales
        self.cadastre_path_edit = QLineEdit(r"W:\2_DOSSIERS\AGRICULTURE\EXPLOITATION_ELEVAGE\STRUCTURE\cadastre\parcelles-21-valide.shp")
        self.cadastre_label = QLabel("Couches des parcelles cadastrales :")
        self.cadastre_status = QLabel("Vérification en cours...")
        self.cadastre_browse_button = QPushButton("Ou sélectionner autre fichier")
        self.cadastre_browse_button.clicked.connect(lambda: self.choose_layer_path(self.cadastre_path_edit, self.cadastre_status))
        cadastre_layout = QHBoxLayout()
        cadastre_layout.addWidget(self.cadastre_path_edit)
        cadastre_layout.addWidget(self.cadastre_browse_button)
        layout.addRow(self.cadastre_label, cadastre_layout)
        layout.addRow("", self.cadastre_status)


        # Vérification des couches
        self.check_layers()

        # Numéro de PACAGE
        self.pacage_label = QLabel("Numéro de PACAGE (9 chiffres) :")
        self.pacage_input = QLineEdit()
        validator = QRegExpValidator(QRegExp(r"^\d{9}$"))
        self.pacage_input.setValidator(validator)
        layout.addRow(self.pacage_label, self.pacage_input)

        # Dossier d'export
        self.export_dir_label = QLabel("Dossier d'export :")
        self.export_dir_input = QLineEdit()
        self.export_dir_button = QPushButton("Choisir dossier")
        self.export_dir_button.clicked.connect(self.choose_export_dir)
        layout.addRow(self.export_dir_label, self.export_dir_input)
        layout.addRow("", self.export_dir_button)

        # Journal des logs
        self.log_text = QTextBrowser()
        self.log_text.setMaximumHeight(100)
        layout.addRow(QLabel("Journal des logs :"), self.log_text)

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        layout.addRow("Progression :", self.progress_bar)

        # Bouton de traitement
        self.run_button = QPushButton("Lancer le traitement")
        self.run_button.clicked.connect(self.run_processing)
        layout.addRow(self.run_button)

        self.result_label = QLabel("")
        layout.addRow(self.result_label)
        self.analysis_tab.setLayout(layout)
    
    def choose_layer_path(self, line_edit, status_label):
        """Ouvre une boîte de dialogue pour choisir un fichier de couche."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Sélectionner une couche",
            "",
            "Fichiers SIG (*.shp *.gpkg *.geojson)"
        )
        if file_path:
            line_edit.setText(file_path)
            self.check_layer(file_path, status_label)
            
    def check_layer(self, path, status_label):
        """Vérifie la validité d'une couche et met à jour le statut."""
        if os.path.exists(path):
            layer = QgsVectorLayer(path, "temp", "ogr")
            if layer.isValid():
                status_label.setText("Couche trouvée ✅")
                status_label.setStyleSheet("color: green;")
                return True
            else:
                status_label.setText("Couche invalide ❌")
                status_label.setStyleSheet("color: red;")
                return False
        else:
            status_label.setText("Chemin introuvable ❌")
            status_label.setStyleSheet("color: red;")
            return False

    def check_layers(self):
        """Vérifie la disponibilité de toutes les couches."""
        self.p24_ok = self.check_layer(self.p24_path_edit.text(), self.p24_status)
        self.p25_ok = self.check_layer(self.p25_path_edit.text(), self.p25_status)
        self.cadastre_ok = self.check_layer(self.cadastre_path_edit.text(), self.cadastre_status)

    def choose_export_dir(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Choisir dossier d'export")
        if dir_path:
            self.export_dir_input.setText(dir_path)

    def create_spatial_index_if_needed(self, layer, layer_name):
        """Crée un index spatial si nécessaire et log l'action."""
        provider = layer.dataProvider()
        if not provider.createSpatialIndex():
            self.log_text.append(f"⚠️ Index spatial créé pour la couche {layer_name}.")
        else:
            self.log_text.append(f"✅ Index spatial déjà présent pour la couche {layer_name}.")

    def run_processing(self):
        try:
            self.progress_bar.setValue(0)
            self.log_text.clear()
            pacage = self.pacage_input.text()
            if len(pacage) != 9 or not pacage.isdigit():
                raise ValueError("Le numéro de PACAGE doit avoir exactement 9 chiffres.")
            export_dir = self.export_dir_input.text()
            if not export_dir:
                raise ValueError("Veuillez choisir un dossier d'export.")

            # Chemins des couches
            p24_path = self.p24_path_edit.text()
            p25_path = self.p25_path_edit.text()
            cadastre_path = self.cadastre_path_edit.text()

            # Vérification finale des couches
            self.progress_bar.setValue(5)
            p24_layer = QgsVectorLayer(p24_path, "P24", "ogr")
            p25_layer = QgsVectorLayer(p25_path, "P25", "ogr")
            cadastre_layer = QgsVectorLayer(cadastre_path, "Cadastre", "ogr")

            if not all([p24_layer.isValid(), p25_layer.isValid(), cadastre_layer.isValid()]):
                raise ValueError("Une ou plusieurs couches ne sont pas valides.")

            # Vérification et création des index spatiaux
            self.progress_bar.setValue(10)
            self.log_text.append("🔍 Vérification des index spatiaux...")
            self.create_spatial_index_if_needed(p24_layer, "P24")
            self.create_spatial_index_if_needed(p25_layer, "P25")
            self.create_spatial_index_if_needed(cadastre_layer, "Cadastre")

            # Vérification du champ PACAGE
            self.progress_bar.setValue(20)
            if 'PACAGE' not in [f.name() for f in p24_layer.fields()] or 'PACAGE' not in [f.name() for f in p25_layer.fields()]:
                raise ValueError("Le champ 'PACAGE' n'existe pas dans les couches P24 ou P25.")

            # Filtrage des features pour le PACAGE
            self.progress_bar.setValue(30)
            filter_expr = f"PACAGE = '{pacage}'"
            p24_features = list(p24_layer.getFeatures(QgsFeatureRequest().setFilterExpression(filter_expr)))
            p25_features = list(p25_layer.getFeatures(QgsFeatureRequest().setFilterExpression(filter_expr)))

            if not p25_features:
                raise ValueError(f"Le numéro de PACAGE {pacage} n'est pas présent dans la table P25.")

            # Log
            self.log_text.append(f"📊 Filtrage des îlots pour PACAGE {pacage} : {len(p24_features)} en P24, {len(p25_features)} en P25.")

            # Création des couches temporaires
            self.progress_bar.setValue(40)
            fields = QgsFields()
            fields.append(QgsField("PACAGE", QVariant.String, len=10))
            fields.append(QgsField("NUM_ILOT", QVariant.Int, len=5))
            fields.append(QgsField("NUM_PARCEL", QVariant.Int, len=4))
            fields.append(QgsField("SF_ADM_DE", QVariant.Double, len=10))
            fields.append(QgsField("SF_ADM_CO", QVariant.Double, len=10))

            # Création de couches temporaires pour les features filtrées
            p24_temp = QgsVectorLayer("MultiPolygon?crs=epsg:2154", "P24_filtered", "memory")
            p24_temp.dataProvider().addAttributes(fields)
            p24_temp.updateFields()
            p24_temp.startEditing()
            for feat in p24_features:
                new_feat = QgsFeature(fields)
                new_feat.setGeometry(feat.geometry())
                new_feat.setAttributes([
                    feat['PACAGE'],
                    feat['NUM_ILOT'] if 'NUM_ILOT' in feat else None,
                    feat['NUM_PARCEL'] if 'NUM_PARCEL' in feat else None,
                    feat['SF_ADM_DE'] if 'SF_ADM_DE' in feat else None,
                    feat['SF_ADM_CO'] if 'SF_ADM_CO' in feat else None
                ])
                p24_temp.dataProvider().addFeature(new_feat)
            p24_temp.commitChanges()

            p25_temp = QgsVectorLayer("MultiPolygon?crs=epsg:2154", "P25_filtered", "memory")
            p25_temp.dataProvider().addAttributes(fields)
            p25_temp.updateFields()
            p25_temp.startEditing()
            for feat in p25_features:
                new_feat = QgsFeature(fields)
                new_feat.setGeometry(feat.geometry())
                new_feat.setAttributes([
                    feat['PACAGE'],
                    feat['NUM_ILOT'],
                    feat['NUM_PARCEL'],
                    feat['SF_ADM_DE'],
                    feat['SF_ADM_CO']
                ])
                p25_temp.dataProvider().addFeature(new_feat)
            p25_temp.commitChanges()
            self.progress_bar.setValue(50)
            # Calcul de la différence (P25 minus P24) avec PyQGIS
            diff_layer = QgsVectorLayer("MultiPolygon?crs=epsg:2154", "Ilots_ou_parties_d_ilots_nouveaux_en_2025", "memory")
            diff_provider = diff_layer.dataProvider()
            diff_provider.addAttributes(fields)
            diff_layer.updateFields()
            diff_layer.startEditing()
            
            self.log_text.append("✅ Assemblage en une seule geométrie de toutes celles de l'année 2024.")
            # Combiner toutes les géométries P24 en une seule pour la différence
            p24_combined = None
            if p24_features:
                p24_geometries = [f.geometry() for f in p24_features]
                p24_combined = QgsGeometry.unaryUnion(p24_geometries)
            self.progress_bar.setValue(60)
            
            # Effectuer la différence pour chaque feature de P25
            self.log_text.append("✅ Différences avec les ilots 2025.")
            total_area = 0
            for p25_feature in p25_features:
                p25_geom = p25_feature.geometry()
                if p24_combined:
                    diff_geom = p25_geom.difference(p24_combined)
                else:
                    diff_geom = p25_geom  # Si pas de P24, toute la géométrie est en plus
                if not diff_geom.isEmpty():
                    total_area += diff_geom.area() / 10000  # En hectares
                    new_feature = QgsFeature(fields)
                    new_feature.setGeometry(diff_geom)
                    new_feature.setAttributes([
                        p25_feature['PACAGE'],
                        p25_feature['NUM_ILOT'],
                        p25_feature['NUM_PARCEL'],
                        p25_feature['SF_ADM_DE'],
                        p25_feature['SF_ADM_CO']
                    ])
                    diff_provider.addFeature(new_feature)

            diff_layer.commitChanges()
            if diff_layer.isValid():
                QgsProject.instance().addMapLayer(diff_layer)
                self.progress_bar.setValue(70)
            else:
                raise ValueError("La couche d'intersection n'est pas valide.")
            
            
            # Sauvegarde de la couche différence en GPKG
            diff_output = os.path.join(export_dir, "terres_plus_2025.gpkg")
            QgsVectorFileWriter.writeAsVectorFormat(diff_layer, diff_output, "UTF-8", diff_layer.crs(), "GPKG")
            
            
            # Vérification de la couche différence
            diff_layer = QgsVectorLayer(diff_output, "Terres plus 2025", "ogr")
            if not diff_layer.isValid():
                raise ValueError("La couche de différence n'est pas valide.")

            # Affichage de la surface totale
            self.result_label.setText(f"Surface totale en plus : {total_area:.2f} ha")
             
            self.log_text.append("✅ Recherche des parcelles cadastrales intersectées correspondantes.")
            # Intersection avec cadastre
            
            # Intersection avec cadastre
            self.progress_bar.setValue(80)
            self.log_text.append("🔄 Intersection avec les parcelles cadastrales...")

            # Récupération des champs de la couche cadastrale
            cadastre_fields = cadastre_layer.fields()
            intersect_fields = QgsFields()

            # Ajout des champs de la couche P25 (pour les attributs PACAGE, etc.)
            intersect_fields.append(QgsField("PACAGE", QVariant.String, len=10))
            intersect_fields.append(QgsField("NUM_ILOT", QVariant.Int, len=5))
            intersect_fields.append(QgsField("NUM_PARCEL", QVariant.Int, len=4))
            intersect_fields.append(QgsField("SF_ADM_DE", QVariant.Double, len=10))
            intersect_fields.append(QgsField("SF_ADM_CO", QVariant.Double, len=10))

            # Ajout des champs de la couche cadastrale
            for field in cadastre_fields:
                intersect_fields.append(field)

            # Ajout d'un champ pour la surface intersectée
            intersect_fields.append(QgsField("SF_INTERSECT", QVariant.Double, len=10, prec=2))
            intersect_fields.append(QgsField("ID_PARCELLE", QVariant.Int, len=10))

            # Création de la couche d'intersection
            intersect_layer = QgsVectorLayer("MultiPolygon?crs=epsg:2154", "Parcelles_intersectees", "memory")
            intersect_provider = intersect_layer.dataProvider()
            intersect_provider.addAttributes(intersect_fields.toList())
            intersect_layer.updateFields()
            intersect_layer.startEditing()

            # Récupération des features de la couche de différence (P25 - P24)
            diff_features = list(diff_layer.getFeatures())

            # Récupération des features cadastrales
            cadastre_features = {f.id(): f for f in cadastre_layer.getFeatures()}

            # Intersection et création des features
            for diff_feature in diff_features:
                diff_geom = diff_feature.geometry()
                for cadastre_id, cadastre_feature in cadastre_features.items():
                    cadastre_geom = cadastre_feature.geometry()
                    inter_geom = diff_geom.intersection(cadastre_geom)
                    if not inter_geom.isEmpty():
                        new_feature = QgsFeature(intersect_fields)
                        new_feature.setGeometry(inter_geom)

                        # Attributs de la couche P25
                        new_feature.setAttribute("PACAGE", diff_feature["PACAGE"])
                        new_feature.setAttribute("NUM_ILOT", diff_feature["NUM_ILOT"])
                        new_feature.setAttribute("NUM_PARCEL", diff_feature["NUM_PARCEL"])
                        new_feature.setAttribute("SF_ADM_DE", diff_feature["SF_ADM_DE"])
                        new_feature.setAttribute("SF_ADM_CO", diff_feature["SF_ADM_CO"])

                        # Attributs de la couche cadastrale
                        for i, field in enumerate(cadastre_fields):
                            new_feature.setAttribute(i + 5, cadastre_feature[field.name()])  # +5 car on a déjà 5 champs avant

                        # ID de la parcelle cadastrale
                        new_feature.setAttribute("ID_PARCELLE", cadastre_id)

                        # Surface intersectée (en hectares)
                        surface_ha = inter_geom.area() / 10000
                        new_feature.setAttribute("SF_INTERSECT", surface_ha)

                        intersect_provider.addFeature(new_feature)

            intersect_layer.commitChanges()

            # Sauvegarde de la couche intersectée en GPKG
            intersect_output = os.path.join(export_dir, "parcelles_cadastrales_intersectees.gpkg")
            QgsVectorFileWriter.writeAsVectorFormat(intersect_layer, intersect_output, "UTF-8", intersect_layer.crs(), "GPKG")

            # Chargement et affichage de la couche intersectée
            intersect_layer = QgsVectorLayer(intersect_output, "Parcelles cadastrales intersectées", "ogr")
            if intersect_layer.isValid():
                QgsProject.instance().addMapLayer(intersect_layer)
                self.log_text.append("✅ Couche des parcelles intersectées générée et ajoutée à la carte.")
                self.progress_bar.setValue(100)
                self.log_text.append("✅ Traitement terminé avec succès !")
                
            else:
                raise ValueError("La couche d'intersection n'est pas valide.")

            QMessageBox.information(self, "Succès", "Traitement terminé. Couches exportées et ajoutées à la carte.")

        except ValueError as ve:
            QMessageBox.warning(self, "Erreur de saisie", str(ve))
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {str(e)}")

            
 

class MainPluginTerresADisposition:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        dialog = TerresADispositionDialog(self.iface)
        dialog.exec_()
