# -*- coding: utf-8 -*-
"""
Zones de Protection et de Préservation – Bilan départemental
Plugin Boite_a_outils_ADL
Version finale – 20 novembre 2025
→ Toutes les couches sauvegardées sur disque + symbologie thématique + fenêtre non modale
"""
import os
from datetime import datetime
import processing
from PyQt5.QtCore import QVariant
from PyQt5.QtGui import QColor
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsField, QgsFields, QgsFeature, QgsGeometry,
    QgsCoordinateReferenceSystem, QgsVectorFileWriter, QgsCategorizedSymbolRenderer,
    QgsRendererCategory, QgsSymbol, QgsSingleSymbolRenderer,
    QgsSimpleFillSymbolLayer, QgsLinePatternFillSymbolLayer, QgsFillSymbol
)
from qgis.gui import QgsFileWidget
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QTextEdit, QPushButton,
    QLineEdit, QLabel, QMessageBox, QProgressBar
)


class TreemapZonesProtectDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Zones de Protection et de Préservation – Bilan départemental")
        self.setMinimumSize(1100, 800)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        self.tab_instructions = QWidget()
        self.tab_data = QWidget()
        self.tab_analysis = QWidget()
        self.tab_layout = QWidget()

        self.setup_instructions_tab()
        self.setup_data_loading_tab()
        self.setup_analysis_tab()
        self.setup_layout_tab()

        self.tabs.addTab(self.tab_instructions, "Instructions")
        self.tabs.addTab(self.tab_data, "Chargement des données")
        self.tabs.addTab(self.tab_analysis, "Analyse")
        self.tabs.addTab(self.tab_layout, "Mise en page")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    # ===================================================================
    # 1. INSTRUCTIONS
    # ===================================================================
    def setup_instructions_tab(self):
        layout = QVBoxLayout()
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        instructions = """
        <h2 style="color:#006400;">Zones de Protection et de Préservation – Bilan départemental</h2>
        <h3 style="color:#006400;">Version finale – 20 novembre 2025</h3>
        <p>Ce module calcule les surfaces de protection sur le département de la Côte-d'Or et génère une couche synthèse avec 4 catégories :</p>
        <ul>
            <li><span style="color:#6A994E;"><b>Forte stricte</b></span> → vert pastel foncé (#6A994E) – opacité  60 %</li>
            <li><span style="color:#F2CC8F;"><b>Faible stricte</b></span> → beige pastel clair (#F2CC8F) – opacité 60 %</li>
            <li><span style="color:#F2CC8F;"><b>Mixte</b></span> → fond beige + hachures vert foncé 45° – opacité 60 %</li>
            <li><b>Sans zones</b> → transparent avec contour noir</li>
        </ul>
        <p>Toutes les couches (clipées, unions, catégories, synthèse) sont <b>sauvegardées sur disque</b> dans le dossier choisi et <b>restent visibles</b> même après fermeture du module.</p>
        <p>La fenêtre est non modale → vous pouvez zoomer, sélectionner, modifier les couches pendant et après le traitement.</p>
        """
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.tab_instructions.setLayout(layout)

    # ===================================================================
    # 2. CHARGEMENT DES DONNÉES
    # ===================================================================
    def setup_data_loading_tab(self):
        layout = QVBoxLayout()
        default_paths = {
            "Cœur de Parc national de forêts": "M:/NATURE_PAYSAGE_BIODIVERSITE/N_ZONAGES_NATURE/PN_FORET/coeur_data_gouv_pnforets/Coeur_data_gouv_PNForets.shp",
            "Réserve biologique": "M:/NATURE_PAYSAGE_BIODIVERSITE/N_ZONAGES_NATURE/rb/rb2020_10/N_ENP_RB_S_000_D21.shp",
            "Réserve naturelle (RNN)": "M:/NATURE_PAYSAGE_BIODIVERSITE/N_ZONAGES_NATURE/rnn/N_ENP_RNN_S_000_D21.shp",
            "Réserve naturelle (RNR)": "M:/NATURE_PAYSAGE_BIODIVERSITE/N_ZONAGES_NATURE/rnr/N_ENP_RNR_S_000_D21.shp",
            "Arrêtés de protection": "M:/NATURE_PAYSAGE_BIODIVERSITE/N_ZONAGES_NATURE/N_APPB_ZINF_S_R21/N_ENP_APB_S_000_D21.shp",
            "Aire optimale d'adhésion du Parc national": "M:/NATURE_PAYSAGE_BIODIVERSITE/N_ZONAGES_NATURE/PN_FORET/aoa_2021_pnforets/AOA_2021_PNForets.shp",
            "Parc naturel régional du Morvan": "M:/NATURE_PAYSAGE_BIODIVERSITE/N_ZONAGES_NATURE/N_PARC_REG_ZINF_S_R27.shp",
            "Zones spéciales de conservation (Natura 2000)": "M:/NATURE_PAYSAGE_BIODIVERSITE/N_ZONAGES_NATURE/NATURA_2000/ZSC_natura2000/N_ZSC_S_D21.shp",
            "Zones de protection spéciale (Natura 2000)": "M:/NATURE_PAYSAGE_BIODIVERSITE/N_ZONAGES_NATURE/NATURA_2000/n_zps_s_r27/N_ZPS_S_D21.shp",
            "Limites départementales": "N:/ADMIN_EXPRESS/N_ADE_DEPT_S_000_D21.shp"
        }
        self.path_editors = {}
        self.path_status = {}
        for layer_name, default_path in default_paths.items():
            layout.addWidget(QLabel(f"<b>{layer_name} :</b>"))
            line_edit = QLineEdit(default_path)
            layout.addWidget(line_edit)
            self.path_editors[layer_name] = line_edit
            status_label = QLabel("Statut : non vérifié")
            layout.addWidget(status_label)
            self.path_status[layer_name] = status_label

        self.check_paths_button = QPushButton("Vérifier les chemins des couches")
        self.check_paths_button.clicked.connect(self.check_layer_paths)
        layout.addWidget(self.check_paths_button)
        self.tab_data.setLayout(layout)

    def check_layer_paths(self):
        for layer_name, edit in self.path_editors.items():
            path = edit.text()
            if os.path.exists(path):
                self.path_status[layer_name].setText('<font color="green"><b>✓ Couche trouvée</b></font>')
            else:
                self.path_status[layer_name].setText('<font color="red"><b>✗ Couche non trouvée</b></font>')

    # ===================================================================
    # 3. ANALYSE
    # ===================================================================
    def setup_analysis_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("<h3>Dossier de sortie</h3>"))
        self.export_folder_widget = QgsFileWidget()
        self.export_folder_widget.setStorageMode(QgsFileWidget.GetDirectory)
        layout.addWidget(self.export_folder_widget)

        self.run_button = QPushButton("Exécuter l'analyse complète")
        self.run_button.clicked.connect(self.run_analysis)
        layout.addWidget(self.run_button)

        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        layout.addWidget(QLabel("<b>Journal détaillé :</b>"))
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(self.log_text)

        self.tab_analysis.setLayout(layout)

    def log_message(self, message):
        self.log_text.append(f"<b>{datetime.now().strftime('%H:%M:%S')}</b> → {message}")
        self.log_text.ensureCursorVisible()

    # ------------------------------------------------------------------
    # Utilitaires
    # ------------------------------------------------------------------
    def reproject_layer(self, layer, name, target_crs):
        if layer.crs() == target_crs:
            return layer
        self.log_message(f"Reprojection de {name} en Lambert 93")
        result = processing.run("native:reprojectlayer", {
            'INPUT': layer,
            'TARGET_CRS': target_crs,
            'OUTPUT': 'memory:'
        })['OUTPUT']
        return result

    def fix_geometries(self, layer):
        if not layer or layer.featureCount() == 0:
            return layer
        self.log_message("Correction des géométries invalides...")
        return processing.run("native:fixgeometries", {'INPUT': layer, 'OUTPUT': 'memory:'})['OUTPUT']

    def save_and_add_layer(self, layer, name, color=None, group=None):
        if not layer or not layer.isValid() or layer.featureCount() == 0:
            return None
        # Sauvegarde sur disque
        safe_name = name.replace(" ", "_").replace("(", "").replace(")", "").replace("/", "_")
        path = os.path.join(self.output_folder, f"{safe_name}_au_{self.date_str}.shp")
        QgsVectorFileWriter.writeAsVectorFormat(layer, path, "UTF-8", self.crs_lambert93, "ESRI Shapefile")

        # Chargement depuis disque (persistance garantie)
        loaded = QgsVectorLayer(path, name, "ogr")
        if not loaded.isValid():
            return None

        # Symbologie
        symbol = QgsSymbol.defaultSymbol(loaded.geometryType())
        fill = symbol.symbolLayer(0)
        if color:
            fill.setColor(QColor(color))
        fill.setStrokeColor(QColor("black"))
        fill.setStrokeWidth(0.4)
        loaded.setRenderer(QgsSingleSymbolRenderer(symbol))

        if group:
            group.addLayer(loaded)
        else:
            QgsProject.instance().addMapLayer(loaded)

        self.log_message(f"Couche sauvegardée et ajoutée : <font color='{color or 'black'}'><b>{name}</b></font>")
        return loaded

    # ------------------------------------------------------------------
    # Analyse principale
    # ------------------------------------------------------------------
    def run_analysis(self):
        export_folder = self.export_folder_widget.filePath()
        if not export_folder:
            QMessageBox.critical(self, "Erreur", "Veuillez sélectionner un dossier de sortie.")
            return

        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.log_text.clear()
        self.log_message("<h3>=== DÉMARRAGE DE L'ANALYSE ===</h3>")

        self.crs_lambert93 = QgsCoordinateReferenceSystem("EPSG:2154")
        self.date_str = datetime.now().strftime("%Y%m%d")
        self.output_folder = os.path.join(export_folder, f"Bilan_zones_Protect_Preserv_au_{self.date_str}")
        os.makedirs(self.output_folder, exist_ok=True)

        root = QgsProject.instance().layerTreeRoot()
        groupe_fortes = root.findGroup("Zones de protections fortes") or root.insertGroup(0, "Zones de protections fortes")
        groupe_faibles = root.findGroup("Zones de protections faibles") or root.insertGroup(1, "Zones de protections faibles")

        try:
            # Département
            dept_path = self.path_editors["Limites départementales"].text()
            dept_layer = QgsVectorLayer(dept_path, "Limites départementales", "ogr")
            dept_layer = self.reproject_layer(dept_layer, "Département", self.crs_lambert93)
            dept_layer = self.fix_geometries(dept_layer)
            self.save_and_add_layer(dept_layer, "Limites départementales", color=None)

            fortes = ["Cœur de Parc national de forêts", "Réserve biologique", "Réserve naturelle (RNN)",
                      "Réserve naturelle (RNR)", "Arrêtés de protection"]
            faibles = ["Aire optimale d'adhésion du Parc national", "Parc naturel régional du Morvan",
                       "Zones spéciales de conservation (Natura 2000)", "Zones de protection spéciale (Natura 2000)"]

            def load_and_clip(names, target_group, color):
                clipped_layers = []
                for name in names:
                    path = self.path_editors[name].text()
                    if not os.path.exists(path):
                        self.log_message(f"⚠️ Fichier manquant : {name}")
                        continue
                    lyr = QgsVectorLayer(path, name, "ogr")
                    if not lyr.isValid() or lyr.featureCount() == 0:
                        continue
                    lyr = self.reproject_layer(lyr, name, self.crs_lambert93)
                    lyr = self.fix_geometries(lyr)
                    clipped = processing.run("native:clip", {
                        'INPUT': lyr, 'OVERLAY': dept_layer, 'OUTPUT': 'memory:'
                    })['OUTPUT']
                    if clipped.featureCount() > 0:
                        clipped_layers.append(clipped)
                        self.save_and_add_layer(clipped, f"{name} (découpée 21)", color=color, group=target_group)
                return clipped_layers

            forte_clipped = load_and_clip(fortes, groupe_fortes, "#cc0000")
            faible_clipped = load_and_clip(faibles, groupe_faibles, "#ffaa00")
            self.progress_bar.setValue(40)

            def clean_union(layers):
                if not layers:
                    return None
                union = layers[0]
                for l in layers[1:]:
                    union = processing.run("native:union", {'INPUT': union, 'OVERLAY': l, 'OUTPUT': 'memory:'})['OUTPUT']
                union = processing.run("native:buffer", {'INPUT': union, 'DISTANCE': 0, 'OUTPUT': 'memory:'})['OUTPUT']
                return self.fix_geometries(union)

            zone_forte = clean_union(forte_clipped)
            if zone_forte:
                self.save_and_add_layer(zone_forte, "Union zones fortes", "#cc0000", groupe_fortes)

            zone_faible = clean_union(faible_clipped)
            if zone_faible:
                self.save_and_add_layer(zone_faible, "Union zones faibles", "#ffaa00", groupe_faibles)
            self.progress_bar.setValue(60)

            mixte = None
            if zone_forte and zone_faible:
                mixte = processing.run("native:intersection", {'INPUT': zone_forte, 'OVERLAY': zone_faible, 'OUTPUT': 'memory:'})['OUTPUT']
                mixte = self.fix_geometries(mixte)
                self.save_and_add_layer(mixte, "Zones mixtes", "#ff00ff", groupe_fortes)
            self.progress_bar.setValue(75)

            def strict(base, subtract, name, color, group):
                if not base:
                    return None
                if not subtract:
                    result = base
                else:
                    result = processing.run("native:difference", {'INPUT': base, 'OVERLAY': subtract, 'OUTPUT': 'memory:'})['OUTPUT']
                    result = self.fix_geometries(result)
                self.save_and_add_layer(result, name, color, group)
                return result

            forte_stricte = strict(zone_forte, mixte, "Forte stricte", "#8B0000", groupe_fortes)
            faible_stricte = strict(zone_faible, mixte, "Faible stricte", "#FFA500", groupe_faibles)
            self.progress_bar.setValue(85)

            # Sans protection
            protected_layers = [l for l in [forte_stricte, faible_stricte, mixte] if l and l.featureCount() > 0]
            union_protected = None
            if protected_layers:
                union_protected = protected_layers[0]
                for l in protected_layers[1:]:
                    union_protected = processing.run("native:union", {'INPUT': union_protected, 'OVERLAY': l, 'OUTPUT': 'memory:'})['OUTPUT']
                union_protected = self.fix_geometries(union_protected)

            sans_protection = None
            if union_protected:
                sans_protection = processing.run("native:difference", {
                    'INPUT': dept_layer, 'OVERLAY': union_protected, 'OUTPUT': 'memory:'})['OUTPUT']
                sans_protection = self.fix_geometries(sans_protection)
                self.save_and_add_layer(sans_protection, "Sans protection", "#ffffff", groupe_faibles)
            self.progress_bar.setValue(90)

            # Calcul surfaces
            def get_area(layer):
                return sum(f.geometry().area() for f in layer.getFeatures()) if layer and layer.featureCount() > 0 else 0.0

            a_forte = get_area(forte_stricte)
            a_faible = get_area(faible_stricte)
            a_mixte = get_area(mixte)
            a_sans = get_area(sans_protection)
            total = a_forte + a_faible + a_mixte + a_sans or 1

            # Synthèse finale
            fields = QgsFields()
            fields.append(QgsField("Protection", QVariant.String))
            fields.append(QgsField("area_ha", QVariant.Double, len=12, prec=2))
            fields.append(QgsField("area_m2", QVariant.Double, len=12, prec=0))
            fields.append(QgsField("Pourc", QVariant.Double, len=6, prec=2))

            synthese = QgsVectorLayer("MultiPolygon?crs=epsg:2154", "synthese_temp", "memory")
            pr = synthese.dataProvider()
            pr.addAttributes(fields)
            synthese.updateFields()

            def add_multipart(layer, label, area):
                if not layer or layer.featureCount() == 0:
                    return
                collected = processing.run("native:collect", {'INPUT': layer, 'OUTPUT': 'memory:'})['OUTPUT']
                geom = next(collected.getFeatures()).geometry()
                f = QgsFeature(fields)
                f.setGeometry(geom)
                f["Protection"] = label
                f["area_ha"] = round(area / 10000.0, 2)
                f["area_m2"] = round(area)
                f["Pourc"] = round((area / total) * 100, 2)
                pr.addFeature(f)

            add_multipart(forte_stricte, "Forte stricte", a_forte)
            add_multipart(faible_stricte, "Faible stricte", a_faible)
            add_multipart(mixte, "Mixte", a_mixte)
            add_multipart(sans_protection, "Sans zones", a_sans)
            synthese.updateExtents()

            # Symbologie finale
            categories = []
            sym_forte = QgsSymbol.defaultSymbol(synthese.geometryType())
            sym_forte.symbolLayer(0).setColor(QColor(106, 153, 78, 153))
            sym_forte.symbolLayer(0).setStrokeColor(QColor("black"))
            sym_forte.symbolLayer(0).setStrokeWidth(0.4)
            categories.append(QgsRendererCategory("Forte stricte", sym_forte, "Forte stricte"))

            sym_faible = QgsSymbol.defaultSymbol(synthese.geometryType())
            sym_faible.symbolLayer(0).setColor(QColor(242, 204, 143, 153))
            sym_faible.symbolLayer(0).setStrokeColor(QColor("black"))
            sym_faible.symbolLayer(0).setStrokeWidth(0.4)
            categories.append(QgsRendererCategory("Faible stricte", sym_faible, "Faible stricte"))

            sym_mixte = QgsFillSymbol()
            fond = QgsSimpleFillSymbolLayer(QColor(242, 204, 143, 153), strokeColor=QColor("#6A994E"), strokeWidth=0.4)
            hatch = QgsLinePatternFillSymbolLayer()
            hatch.setColor(QColor("#6A994E"))
            hatch.setDistance(5)
            hatch.setLineWidth(0.8)
            hatch.setLineAngle(45)
            sym_mixte.appendSymbolLayer(fond)
            sym_mixte.appendSymbolLayer(hatch)
            categories.append(QgsRendererCategory("Mixte", sym_mixte, "Mixte"))

            sym_sans = QgsSymbol.defaultSymbol(synthese.geometryType())
            sym_sans.symbolLayer(0).setColor(QColor(0, 0, 0, 0))
            sym_sans.symbolLayer(0).setStrokeColor(QColor("black"))
            sym_sans.symbolLayer(0).setStrokeWidth(0.6)
            categories.append(QgsRendererCategory("Sans zones", sym_sans, "Sans zones"))

            synthese.setRenderer(QgsCategorizedSymbolRenderer("Protection", categories))

            # Sauvegarde finale
            synthese_path = os.path.join(self.output_folder, f"zones_protection_synthese_au_{self.date_str}.shp")
            QgsVectorFileWriter.writeAsVectorFormat(synthese, synthese_path, "UTF-8", self.crs_lambert93, "ESRI Shapefile")
            synthese_loaded = QgsVectorLayer(synthese_path, f"Zones de protection – Synthèse au {self.date_str}", "ogr")
            QgsProject.instance().addMapLayer(synthese_loaded)

            self.progress_bar.setValue(100)
            self.log_message("<h3 style='color:green'>ANALYSE TERMINÉE – TOUTES COUCHES SAUVEGARDÉES</h3>")
            QMessageBox.information(self, "Succès", f"Traitement terminé !\nToutes les couches sont sauvegardées dans :\n{self.output_folder}")

        except Exception as e:
            self.log_message(f"<font color='red'>ERREUR : {str(e)}</font>")
            QMessageBox.critical(self, "Erreur", str(e))

    def setup_layout_tab(self):
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Mise en page A0 disponible dans la version complète"))
        self.tab_layout.setLayout(layout)


# ===================================================================
# Lancement du plugin – fenêtre non modale
# ===================================================================
class MainPluginTreemapZonesProtect:
    def __init__(self, iface):
        self.iface = iface
        self.dialog = None

    def run(self):
        if self.dialog is None:
            self.dialog = TreemapZonesProtectDialog(self.iface.mainWindow())
            self.dialog.show()
            self.dialog.finished.connect(self.on_dialog_finished)
        else:
            self.dialog.activateWindow()
            self.dialog.raise_()

    def on_dialog_finished(self):
        self.dialog = None