 
# STATISTIQUES_ESSENCE_BDForet_R.py
# Module pour générer des graphiques sur les essences forestières en utilisant uniquement PyQGIS, PyQt et Plotly.

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QTextEdit, QPushButton, QMessageBox,
    QScrollArea, QTextBrowser, QLineEdit, QComboBox, QHBoxLayout, QLabel, QFileDialog
)
from PyQt5.QtCore import QUrl, QVariant
from PyQt5.QtGui import QColor
from qgis.core import QgsVectorLayer, QgsProject, QgsField, QgsFields, QgsFeature, QgsGeometry, QgsPointXY, QgsVectorFileWriter
import os
import tempfile
import shutil
import plotly.express as px
import plotly.graph_objects as go
from collections import defaultdict
from pathlib import *
import pandas as pd  # Ajout de l'import pandas
import math

# Monkey-patch pour ajouter .append() si absent (pour pandas >= 2.0)
if not hasattr(pd.DataFrame, 'append'):
    def append(self, other, ignore_index=False):
        return pd.concat([self, other], ignore_index=ignore_index)
    pd.DataFrame.append = append

# ----------------------------------------------------------------------
#── UTILITAIRES POUR LE TREEMAP (slice‑and‑dice) ───────────────────────
# ----------------------------------------------------------------------
def compute_treemap_rects(sizes, outer_rect, horizontal=True):
    """
    Retourne une liste de QRectF (x0, y0, x1, y1) pour chaque taille.
    *sizes* : liste d’aires (float) déjà normalisées à la même unité que *outer_rect*.
    *outer_rect* : (xmin, ymin, xmax, ymax)
    *horizontal* : orientation du premier découpage.
    """
    if not sizes:
        return []

    total = sum(sizes)
    if total == 0:
        return []

    if len(sizes) == 1:
        return [outer_rect]

    # Sépare les tailles en deux groupes approximativement égaux en aire
    half = total / 2.0
    acc = 0.0
    split_idx = 0
    for i, a in enumerate(sizes):
        acc += a
        if acc >= half:
            split_idx = i + 1
            break
    if split_idx == 0:
        split_idx = 1  # Au moins un dans le groupe gauche

    left_sizes = sizes[:split_idx]
    right_sizes = sizes[split_idx:]

    # Calcul des sous-rectangles
    x0, y0, x1, y1 = outer_rect
    width = x1 - x0
    height = y1 - y0

    if horizontal:
        left_width = width * (sum(left_sizes) / total)
        left_rect = (x0, y0, x0 + left_width, y1)
        right_rect = (x0 + left_width, y0, x1, y1)
    else:
        left_height = height * (sum(left_sizes) / total)
        left_rect = (x0, y0, x1, y0 + left_height)
        right_rect = (x0, y0 + left_height, x1, y1)

    # Récursion sur chaque groupe avec orientation inversée
    left_geo = compute_treemap_rects(left_sizes, left_rect, not horizontal)
    right_geo = compute_treemap_rects(right_sizes, right_rect, not horizontal)

    # Fusionner
    return left_geo + right_geo
# ----------------------------------------------------------------------

class ForetParESSENCEDialog(QDialog):
    def __init__(self, parent=None, iface=None):
        super(ForetParESSENCEDialog, self).__init__(parent)
        self.iface = iface
        self.setWindowTitle("Foret_Par_ESSENCE")
        
        self.setMinimumWidth(800)
        
        self.temp_dir = None
        self.layer = None
        self.treemap_layer = None
        self.default_shapefile_path = r"W:\3_PROJETS\ATLAS_21\Forêt\BD_FORET_D21.shp"
        self.is_default_path = True  # Track if default path is being used
        self.count_dict = None
        self.surface_dict_ha = None
        self.surface_dict_m2 = None
        self.total_area_m2 = None
        self.setup_ui()

    def setup_ui(self):
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
        """Configurer l'onglet Instructions avec une description détaillée."""
        layout = QVBoxLayout()
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        instructions = """
        <h2>Foret_Par_ESSENCE</h2>
        <h3>Fonctionnalités :</h3>
        <p>Produit des graphiques montrant la distribution des essences forestières par nombre d'occurrences et par surface (en pourcentage).</p>
        <h3>Données nécessaires :</h3>
        <p>Un fichier SHP contenant un champ attributaire pour les essences.</p>
        <h3>Utilisation :</h3>
        <ol>
            <li>Sélectionnez le fichier SHP dans l'onglet Traitements.</li>
            <li>Utilisez le bouton "Afficher les champs attributaires" pour charger les champs.</li>
            <li>Choisissez le champ attributaire représentant les essences.</li>
            <li>Cliquez sur le bouton "Générer les Graphiques".</li>
            <li>Les graphiques s'afficheront dans l'interface.</li>
        </ol>
        """
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_analysis_tab(self):
        """Configurer l'onglet Analyse avec l'interface utilisateur."""
        layout = QVBoxLayout()
        chemin_de_base = self.default_shapefile_path
        
        projet_name = Path(chemin_de_base).stem
        nom_projet = f"{projet_name}.qgs"
         
        # Sélection de la couche shapefile
        shapefile_layout = QHBoxLayout()
        self.shapefile_label = QLabel("Chemin vers la couche SHP:")
        self.shapefile_line_edit = QLineEdit(chemin_de_base)
        self.shapefile_browse_button = QPushButton("Parcourir...")
        self.show_fields_button = QPushButton("Afficher les champs attributaires")
        self.shapefile_status_label = QLabel()
        shapefile_layout.addWidget(self.shapefile_label)
        shapefile_layout.addWidget(self.shapefile_line_edit)
        shapefile_layout.addWidget(self.shapefile_browse_button)
        shapefile_layout.addWidget(self.show_fields_button)
        shapefile_layout.addWidget(self.shapefile_status_label)
        layout.addLayout(shapefile_layout)

        # Sélection du champ attributaire
        field_layout = QHBoxLayout()
        self.field_label = QLabel("Variable qualitative/catégorielle:")
        self.field_combo_box = QComboBox()
        field_layout.addWidget(self.field_label)
        field_layout.addWidget(self.field_combo_box)
        layout.addLayout(field_layout)
        
        # Ajout : Sélection du dossier de sauvegarde des graphiques
        save_layout = QHBoxLayout()
        self.save_label = QLabel("Dossier de sauvegarde des graphiques :")
        self.save_line_edit = QLineEdit()
        self.save_browse_button = QPushButton("Parcourir...")
        save_layout.addWidget(self.save_label)
        save_layout.addWidget(self.save_line_edit)
        save_layout.addWidget(self.save_browse_button)
        layout.addLayout(save_layout)
        
        # Ajout : Sélection du fichier de sortie pour le treemap
        output_layout = QHBoxLayout()
        self.output_label = QLabel("Chemin du fichier de sortie pour le treemap :")
        self.output_line_edit = QLineEdit()
        self.output_browse_button = QPushButton("Parcourir...")
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["SHP", "GPKG"])
        output_layout.addWidget(self.output_label)
        output_layout.addWidget(self.output_line_edit)
        output_layout.addWidget(self.output_browse_button)
        output_layout.addWidget(self.output_format_combo)
        layout.addLayout(output_layout)
        
        # Bouton pour générer les graphiques
        self.run_button = QPushButton("Générer les Graphiques")
        self.run_button.clicked.connect(self.generate_graphs)
        layout.addWidget(self.run_button)
        
        # Bouton pour générer le treemap
        self.treemap_button = QPushButton("Générer le Treemap")
        self.treemap_button.clicked.connect(self.create_treemap_layer)
        layout.addWidget(self.treemap_button)

        # Scroll area pour les graphiques
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_content)

        # Utilisation de QTextBrowser pour afficher les graphiques
        self.count_browser = QTextBrowser()
        self.scroll_layout.addWidget(self.count_browser)

        self.surface_browser = QTextBrowser()
        self.scroll_layout.addWidget(self.surface_browser)

        self.scroll_area.setWidget(self.scroll_content)
        layout.addWidget(self.scroll_area)

        self.analysis_tab.setLayout(layout)

        # Connexions
        self.shapefile_browse_button.clicked.connect(self.browse_shapefile)
        self.shapefile_line_edit.textChanged.connect(self.check_shapefile)
        self.save_browse_button.clicked.connect(self.browse_save_dir)
        self.show_fields_button.clicked.connect(self.load_attribute_fields)
        self.output_browse_button.clicked.connect(self.browse_output_file)

    def browse_shapefile(self):
        """Ouvrir une boîte de dialogue pour sélectionner un fichier SHP."""
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner un fichier SHP", "", "Shapefiles (*.shp)")
        if file_path:
            self.shapefile_line_edit.setText(file_path)
            self.is_default_path = (file_path == self.default_shapefile_path)
    
    def browse_save_dir(self):
        """Ouvrir une boîte de dialogue pour sélectionner un dossier de sauvegarde."""
        dir_path = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier de sauvegarde")
        if dir_path:
            self.save_line_edit.setText(dir_path)
    
    def browse_output_file(self):
        """Ouvrir une boîte de dialogue pour sélectionner le fichier de sortie pour le treemap."""
        format_text = self.output_format_combo.currentText()
        if format_text == "SHP":
            filter = "Shapefiles (*.shp)"
            ext = ".shp"
        else:
            filter = "GeoPackages (*.gpkg)"
            ext = ".gpkg"
        file_path, _ = QFileDialog.getSaveFileName(self, "Sélectionner le fichier de sortie", "", filter)
        if file_path:
            if not file_path.endswith(ext):
                file_path += ext
            self.output_line_edit.setText(file_path)

    def check_shapefile(self):
        """Vérifier si la couche SHP existe et mettre à jour l'interface."""
        shapefile_path = self.shapefile_line_edit.text()
        if os.path.exists(shapefile_path):
            self.shapefile_status_label.setText("Couche trouvée")
            self.shapefile_status_label.setStyleSheet("color: green;")
            self.is_default_path = (shapefile_path == self.default_shapefile_path)
        else:
            self.shapefile_status_label.setText("Couche non trouvée")
            self.shapefile_status_label.setStyleSheet("color: red;")
            self.field_combo_box.clear()

    def load_attribute_fields(self):
        """Charger les champs attributaires dans la QComboBox."""
        shapefile_path = self.shapefile_line_edit.text()
        if not os.path.exists(shapefile_path):
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier SHP valide.")
            return

        # Charger la couche pour obtenir les champs attributaires
        self.layer = QgsVectorLayer(shapefile_path, os.path.basename(shapefile_path), "ogr")
        if self.layer.isValid():
            fields = [field.name() for field in self.layer.fields()]
            self.field_combo_box.clear()
            self.field_combo_box.addItems(fields)
            
            # Pré-sélectionner "ESSENCE" si la couche est BD_FORET_D21.shp et que c'est le chemin par défaut
            if self.is_default_path and os.path.basename(shapefile_path) == "BD_FORET_D21.shp" and "ESSENCE" in fields:
                self.field_combo_box.setCurrentText("ESSENCE")
        else:
            self.field_combo_box.clear()
            QMessageBox.warning(self, "Erreur", "Impossible de charger la couche shapefile.")
    
    def compute_statistics(self):
        """Calculer les statistiques à partir de la couche."""
        shapefile_path = self.shapefile_line_edit.text()
        if not os.path.exists(shapefile_path):
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier SHP valide.")
            return False
        field_name = self.field_combo_box.currentText()
        if not field_name:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un champ attributaire.")
            return False
        
        # Charger la couche shapefile si nécessaire
        if self.layer is None or self.layer.source() != shapefile_path:
            self.layer = QgsVectorLayer(shapefile_path, os.path.basename(shapefile_path), "ogr")
            if not self.layer.isValid():
                QMessageBox.critical(self, "Erreur", "Impossible de charger la couche shapefile.")
                return False
        
        # Ajouter la couche à QGIS
        QgsProject.instance().addMapLayer(self.layer)
        
        # Initialiser les dictionnaires pour les données
        self.count_dict = defaultdict(int)
        self.surface_dict_m2 = defaultdict(float)

        # Traiter les données
        for feature in self.layer.getFeatures():
            essence = feature.attribute(field_name)
            if essence and not (str(essence).startswith('NR') or str(essence).startswith('NC')):
                self.count_dict[essence] += 1
                area_m2 = feature.geometry().area()
                self.surface_dict_m2[essence] += area_m2

        if not self.count_dict:
            QMessageBox.critical(self, "Erreur", "Aucune donnée valide trouvée dans la couche.")
            return False

        self.total_area_m2 = sum(self.surface_dict_m2.values())
        self.surface_dict_ha = {k: v / 10000 for k, v in self.surface_dict_m2.items()}
        
        return True
    
    def generate_graphs(self):
        """Générer les graphiques et le treemap en utilisant Plotly."""
        if not self.compute_statistics():
            return
        
        export_dir = self.save_line_edit.text()
        if not export_dir:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un dossier de sauvegarde dans le champ prévu.")
            return
        
        try:
            if self.temp_dir:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = tempfile.mkdtemp()

            total_surface_ha = sum(self.surface_dict_ha.values())
            percent_dict = {k: (v / total_surface_ha * 100) if total_surface_ha > 0 else 0 for k, v in self.surface_dict_ha.items()}

            # Trier les essences
            essences_count = sorted(self.count_dict.keys(), key=lambda k: self.count_dict[k])
            essences_surface = sorted(percent_dict.keys(), key=lambda k: percent_dict[k])

            # Fonction pour générer la palette de couleurs
            def hex_to_rgb(h):
                h = h.lstrip('#')
                return tuple(int(h[i:i+2], 16) for i in (0, 2, 4))

            def rgb_to_hex(rgb):
                return '#%02x%02x%02x' % rgb

            def color_ramp(start, end, n):
                if n == 0:
                    return []
                if n == 1:
                    return [start]
                s = hex_to_rgb(start)
                e = hex_to_rgb(end)
                return [rgb_to_hex((int(s[0] + (e[0] - s[0]) * i / (n - 1)),
                                    int(s[1] + (e[1] - s[1]) * i / (n - 1)),
                                    int(s[2] + (e[2] - s[2]) * i / (n - 1)))) for i in range(n)]

            # Graphique pour les counts
            n_count = len(essences_count)
            palette_count = color_ramp("#96C291", "#016A70", n_count)

            fig_count = go.Figure()
            fig_count.add_trace(go.Bar(
                y=essences_count,
                x=[self.count_dict[e] for e in essences_count],
                orientation='h',
                marker_color=palette_count,
                width=0.6
            ))

            annotations = []
            threshold = 1587  # Seuil adapté du script R original
            for essence in essences_count:
                cnt = self.count_dict[essence]
                if cnt < threshold:
                    annotations.append({
                        'x': cnt + 50,
                        'y': essence,
                        'text': f"<b>{essence}</b>",
                        'showarrow': False,
                        'xanchor': 'left',
                        'font': {'color': "#016A70", 'size': 12}
                    })
                else:
                    annotations.append({
                        'x': 50,
                        'y': essence,
                        'text': f"<b>{essence}</b>",
                        'showarrow': False,
                        'xanchor': 'left',
                        'font': {'color': "white", 'size': 12}
                    })

            fig_count.update_layout(
                annotations=annotations,
                xaxis=dict(
                    side='top',
                    showticklabels=False,
                    showline=False,
                    showgrid=False,
                    zeroline=False
                ),
                yaxis=dict(
                    showticklabels=False,
                    showline=True,
                    linecolor='black',
                    showgrid=False,
                    zeroline=False
                ),
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=20, r=20, t=20, b=20),
                height=800,
                width=600
            )

            # Graphique pour les surfaces
            n_surface = len(essences_surface)
            palette_surface = color_ramp("#96C291", "#016A70", n_surface)

            fig_surface = go.Figure()
            fig_surface.add_trace(go.Bar(
                y=essences_surface,
                x=[percent_dict[e] for e in essences_surface],
                orientation='h',
                marker_color=palette_surface,
                width=0.6
            ))

            fig_surface.update_layout(
                xaxis=dict(
                    title='Pourcentage',
                    showline=True,
                    showgrid=True,
                    gridcolor='lightgray',
                    zeroline=False
                ),
                yaxis=dict(
                    showticklabels=True,
                    showline=True,
                    showgrid=False,
                    zeroline=False
                ),
                showlegend=False,
                plot_bgcolor='white',
                paper_bgcolor='white',
                margin=dict(l=20, r=20, t=20, b=20),
                height=800,
                width=600
            )

            # Enregistrer en HTML temporaire
            count_html_path = os.path.join(self.temp_dir, "count_plot.html")
            fig_count.write_html(count_html_path, include_plotlyjs='cdn')

            surface_html_path = os.path.join(self.temp_dir, "surface_plot.html")
            fig_surface.write_html(surface_html_path, include_plotlyjs='cdn')

            # Charger dans les QTextBrowser
            with open(count_html_path, 'r', encoding='utf-8') as f:
                count_html_content = f.read()
            self.count_browser.setHtml(count_html_content)

            with open(surface_html_path, 'r', encoding='utf-8') as f:
                surface_html_content = f.read()
            self.surface_browser.setHtml(surface_html_content)
            
            
            # Préparation des données pour le treemap
            # On utilise une simple liste de dictionnaires (pas de DataFrame.append)
            treemap_data = [
                {
                    "Essence": essence,
                    "Nombre": self.count_dict[essence],
                    "Surface (ha)": self.surface_dict_ha[essence],
                }
                for essence in self.count_dict.keys()
            ]

            # Si vous avez besoin d’un DataFrame (par ex. pour filtrer, trier …) :
            df_treemap = pd.DataFrame(treemap_data)          # ← conversion instantanée
            # (facultatif) : trier par surface décroissante
            df_treemap = df_treemap.sort_values(
                "Surface (ha)", ascending=False
            ).reset_index(drop=True)

            # Génération du treemap avec Plotly
            fig_treemap = px.treemap(
                df_treemap,               # ← on passe le DataFrame
                path=["Essence"],
                values="Surface (ha)",
                color="Nombre",
                color_continuous_scale="Viridis",
                title="Treemap des essences par surface (ha) et nombre d'occurrences",
            )

            # -------------------------------------------------
            # Export des trois graphiques (count, surface, treemap)
            # -------------------------------------------------
            layer_name      = os.path.splitext(os.path.basename(self.shapefile_line_edit.text()))[0]
            attribute_name  = self.field_combo_box.currentText()
            count_fname     = f"{layer_name}_{attribute_name}_count.html"
            surface_fname   = f"{layer_name}_{attribute_name}_surface.html"
            treemap_fname   = f"{layer_name}_{attribute_name}_treemap.html"

            fig_count.write_html(   os.path.join(export_dir, count_fname),   include_plotlyjs='cdn')
            fig_surface.write_html( os.path.join(export_dir, surface_fname), include_plotlyjs='cdn')
            fig_treemap.write_html( os.path.join(export_dir, treemap_fname), include_plotlyjs='cdn')

            QMessageBox.information(
                self, "Export réussi",
                f"Les graphiques ont été exportés vers : {export_dir}"
            )

        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue : {str(e)}")
    
    def create_treemap_layer(self):
        """Créer et exporter la couche treemap."""
        if not self.compute_statistics():
            return
        
        export_dir = self.save_line_edit.text()
        if not export_dir:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un dossier de sauvegarde pour générer automatiquement le nom du treemap.")
            return
        
        layer_name = os.path.splitext(os.path.basename(self.shapefile_line_edit.text()))[0]
        attribute_name = self.field_combo_box.currentText()
        format_text = self.output_format_combo.currentText()
        ext = ".shp" if format_text == "SHP" else ".gpkg"
        treemap_fname = f"{layer_name}_{attribute_name}_treemap{ext}"
        output_path = os.path.join(export_dir, treemap_fname)
        
        try:
            # Trier les aires en ordre décroissant
            areas_sorted = sorted(self.surface_dict_m2.items(), key=lambda x: x[1], reverse=True)
            cats = [k for k, v in areas_sorted]
            sizes = [v for k, v in areas_sorted]
            
            total = self.total_area_m2
            if total == 0:
                QMessageBox.warning(self, "Erreur", "La surface totale est nulle.")
                return
            
            # Calculer les dimensions du grand rectangle
            aspect = 1.6
            h = math.sqrt(total / aspect)
            w = aspect * h
            outer_rect = (0.0, 0.0, w, h)
            
            # Calculer les rectangles
            rects = compute_treemap_rects(sizes, outer_rect)
            
            # Obtenir l'étendue de la couche originale
            ext = self.layer.extent()
            xmin_orig = ext.xMinimum()
            ymin_orig = ext.yMinimum()
            xmax_orig = ext.xMaximum()
            ymax_orig = ext.yMaximum()
            height_orig = ymax_orig - ymin_orig
            gap = height_orig * 0.05
            
            # Calculer les décalages pour positionner le treemap en dessous
            x_shift = (xmin_orig + xmax_orig) / 2 - w / 2
            y_shift = ymin_orig - h - gap
            
            # Ajuster les coordonnées des rectangles
            adjusted_rects = []
            for rect in rects:
                x0, y0, x1, y1 = rect
                adjusted_rect = (x0 + x_shift, y0 + y_shift, x1 + x_shift, y1 + y_shift)
                adjusted_rects.append(adjusted_rect)
            rects = adjusted_rects
            
            # Créer la couche mémoire
            fields = QgsFields()
            #category="category"
            category=attribute_name
            fields.append(QgsField(category, QVariant.String))
            fields.append(QgsField("area_m2", QVariant.Double))
            
            crs = self.layer.crs()
            self.treemap_layer = QgsVectorLayer(f"Polygon?crs={crs.authid()}", "treemap", "memory")
            pr = self.treemap_layer.dataProvider()
            pr.addAttributes(fields)
            self.treemap_layer.updateFields()
            
            for i, rect in enumerate(rects):
                feat = QgsFeature()
                x0, y0, x1, y1 = rect
                polygon = [[QgsPointXY(x0, y0), QgsPointXY(x1, y0), QgsPointXY(x1, y1), QgsPointXY(x0, y1)]]
                geom = QgsGeometry.fromPolygonXY(polygon)
                feat.setGeometry(geom)
                feat.setAttributes([cats[i], sizes[i]])
                pr.addFeature(feat)
            
            self.treemap_layer.updateExtents()
            
            # Exporter la couche
            driver = "ESRI Shapefile" if format_text == "SHP" else "GPKG"
            error = QgsVectorFileWriter.writeAsVectorFormat(self.treemap_layer, output_path, "UTF-8", crs, driver)
            if error[0] == QgsVectorFileWriter.NoError:
                # Charger la couche exportée dans QGIS
                exported_layer = QgsVectorLayer(output_path, os.path.basename(output_path), "ogr")
                if exported_layer.isValid():
                    QgsProject.instance().addMapLayer(exported_layer)
                    QMessageBox.information(self, "Succès", f"Treemap exporté vers {output_path} et ouvert dans QGIS.")
                else:
                    QMessageBox.warning(self, "Avertissement", f"Treemap exporté vers {output_path}, mais impossible de l'ouvrir dans QGIS.")
            else:
                QMessageBox.critical(self, "Erreur", f"Échec de l'export : {error[1]}")
            
            # Nettoyage du layer temporaire
            self.treemap_layer = None
            
        except Exception as e:
            QMessageBox.critical(self, "Erreur", f"Une erreur est survenue lors de la création du treemap : {str(e)}")
    
    def closeEvent(self, event):
        if self.temp_dir:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        if self.treemap_layer:
            self.treemap_layer = None
        super().closeEvent(event)

class MainPluginForetParESSENCE:
    def __init__(self, iface):
        self.iface = iface

    def run(self):
        dialog = ForetParESSENCEDialog(parent=self.iface.mainWindow(), iface=self.iface)
        dialog.exec_()
 