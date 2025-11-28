# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                 QLineEdit, QMessageBox, QProgressBar, QTextEdit,
                                 QTabWidget, QWidget, QFileDialog, QAction, QComboBox)
from qgis.PyQt.QtCore import Qt, QThread, pyqtSignal, QVariant
from qgis.core import (QgsVectorLayer, QgsProject, QgsVectorFileWriter, QgsFeature,
                       QgsGeometry, QgsField, QgsFields, QgsFeatureSink)
import os
import pandas as pd
import re
from datetime import datetime

class BassinsMobiliteWorker(QThread):
    """Thread pour créer les couches des bassins de mobilité"""
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    finished = pyqtSignal(bool)

    def __init__(self, communes_path, population_path, epci_path, bassins_path, communes_info_path, epci_info_path, output_path, output_format):
        super().__init__()
        self.communes_path = communes_path
        self.population_path = population_path
        self.epci_path = epci_path
        self.bassins_path = bassins_path
        self.communes_info_path = communes_info_path
        self.epci_info_path = epci_info_path
        self.output_path = output_path
        self.output_format = output_format
        self.stopped = False

    def run(self):
        try:
            self.message.emit("Démarrage du traitement des bassins de mobilité...")

            # Charger la couche des communes
            self.message.emit("Chargement de la couche des communes...")
            communes_layer = QgsVectorLayer(self.communes_path, "communes", "ogr")
            if not communes_layer.isValid():
                self.message.emit("Erreur: Impossible de charger la couche des communes.")
                self.finished.emit(False)
                return
            if not communes_layer.crs().isValid():
                self.message.emit("Erreur: La couche des communes n'a pas de système de coordonnées défini.")
                self.finished.emit(False)
                return

            # Charger les données supplémentaires des communes
            self.message.emit("Chargement des données supplémentaires des communes...")
            communes_info = pd.read_csv(self.communes_info_path)

            # Filtrer les communes pour le département 21
            self.message.emit("Filtrage des communes pour le département 21...")
            communes_21 = []
            for feature in communes_layer.getFeatures():
                if feature['DEP'] == '21':
                    communes_21.append(feature)
            if not communes_21:
                self.message.emit("Erreur: Aucune commune trouvée pour le département 21.")
                self.finished.emit(False)
                return

            # Charger les données de population
            self.message.emit("Chargement des données de population...")
            population_data = pd.read_csv(self.population_path)
            population_data['INSEE_COM'] = population_data['Code département'] + population_data['Code commune']

            # Joindre les données de population et communes_info aux communes
            self.message.emit("Jointure des données de population et communes...")
            communes_21_dict = {f['INSEE_COM']: f for f in communes_21}
            population_dict = population_data.set_index('INSEE_COM')['Population totale'].to_dict()
            communes_info_dict = communes_info.set_index('DEPCOM').to_dict('index')
            communes_21_pop = []
            for insee_com, feature in communes_21_dict.items():
                pop = population_dict.get(insee_com, 0)
                info = communes_info_dict.get(insee_com, {})
                feature.setAttributes(feature.attributes() + [pop, info.get('EPCI', '')])
                communes_21_pop.append(feature)

            # Charger la couche des EPCI
            self.message.emit("Chargement de la couche des EPCI...")
            epci_layer = QgsVectorLayer(self.epci_path, "epci", "ogr")
            if not epci_layer.isValid():
                self.message.emit("Erreur: Impossible de charger la couche des EPCI.")
                self.finished.emit(False)
                return

            # Charger les données supplémentaires des EPCI
            self.message.emit("Chargement des données supplémentaires des EPCI...")
            epci_info = pd.read_csv(self.epci_info_path)

            # Filtrer les EPCI du département 21
            self.message.emit("Filtrage des EPCI pour le département 21...")
            epci_codes = set(f.attributes()[-1] for f in communes_21_pop if f.attributes()[-1])
            epci_21 = []
            for feature in epci_layer.getFeatures():
                if feature['CODE_SIREN'] in epci_codes:
                    epci_21.append(feature)

            # Sommer la population par EPCI
            self.message.emit("Calcul de la population totale par EPCI...")
            epci_pop_dict = {}
            for feature in communes_21_pop:
                epci_code = feature.attributes()[-1]
                pop = feature.attributes()[-2]
                epci_pop_dict[epci_code] = epci_pop_dict.get(epci_code, 0) + (pop if pop else 0)

            # Charger les données des bassins de mobilité
            self.message.emit("Chargement des données des bassins de mobilité...")
            bassins_mobilite_21 = pd.read_csv(self.bassins_path)
            bassins_mobilite_21['epci_codes'] = bassins_mobilite_21['territoire_s_concerne_s'].str.findall(r'\b\d{9}\b')
            bassins_mobilite_21_long = bassins_mobilite_21.explode('epci_codes')

            # Créer la couche des bassins de mobilité
            self.message.emit("Création de la couche des bassins de mobilité...")
            fields = QgsFields()
            fields.append(QgsField("bassin", QVariant.String))
            fields.append(QgsField("pop_totale", QVariant.Double))
            fields.append(QgsField("m_a_j", QVariant.String))
            fields.append(QgsField("nb_epci", QVariant.Int))
            fields.append(QgsField("date_crea", QVariant.String))
            fields.append(QgsField("Contrat_Op", QVariant.String))
            fields.append(QgsField("lien_COp", QVariant.String))
            fields.append(QgsField("PAMS", QVariant.String))
            fields.append(QgsField("remarque", QVariant.String))
            fields.append(QgsField("EPCI", QVariant.String))

            output_layer = QgsVectorLayer(f"MultiPolygon?crs={communes_layer.crs().authid()}", "Bassins_Mobilite_D21", "memory")
            output_layer.dataProvider().addAttributes(fields)
            output_layer.updateFields()

            bassin_groups = bassins_mobilite_21_long.groupby('nom_du_bassin')
            for bassin_name, group in bassin_groups:
                if self.stopped:
                    self.message.emit("Traitement annulé par l'utilisateur.")
                    self.finished.emit(False)
                    return
                # Sommer la population
                epci_codes = group['epci_codes'].tolist()
                pop_totale = sum(epci_pop_dict.get(code, 0) for code in epci_codes)
                # Regrouper les géométries
                geometries = [f.geometry() for f in epci_21 if f['CODE_SIREN'] in epci_codes]
                if not geometries:
                    continue
                union_geom = geometries[0]
                for geom in geometries[1:]:
                    union_geom = union_geom.combine(geom)
                # Créer la feature
                feature = QgsFeature(fields)
                feature.setGeometry(union_geom)
                bassin_info = bassins_mobilite_21[bassins_mobilite_21['nom_du_bassin'] == bassin_name].iloc[0]
                feature.setAttributes([
                    bassin_name.replace("BFC-", ""),
                    pop_totale,
                    str(bassin_info.get('last_update', '')),
                    int(bassin_info.get('nombre_d_epci_dans_le_bassin', 0)),
                    str(bassin_info.get('date_de_creation_du_bassin', '')),
                    str(bassin_info.get('contrat_operationnel', '')),
                    str(bassin_info.get('lien_vers_le_contrat_operationnel', '')),
                    str(bassin_info.get('plan_d_action_pour_la_mobilite_solidaire_pams', '')),
                    str(bassin_info.get('commentaires', '')),
                    str(bassin_info.get('territoire_s_concerne_s', ''))
                ])
                output_layer.dataProvider().addFeature(feature)

            # Sauvegarder la couche
            self.message.emit("Enregistrement de la couche finale...")
            options = QgsVectorFileWriter.SaveVectorOptions()
            options.driverName = "ESRI Shapefile" if self.output_format == "shp" else "GPKG"
            options.layerName = "Bassins_Mobilite_D21" if self.output_format == "gpkg" else None
            transform_context = QgsProject.instance().transformContext()
            error = QgsVectorFileWriter.writeAsVectorFormatV2(
                output_layer,
                self.output_path,
                transform_context,
                options
            )
            if error[0] != QgsVectorFileWriter.NoError:
                self.message.emit(f"Erreur lors de l'enregistrement: {error[1]}")
                self.finished.emit(False)
                return

            # Charger la couche dans QGIS
            output_layer = QgsVectorLayer(self.output_path, "Bassins_Mobilite_D21", "ogr")
            if output_layer.isValid():
                QgsProject.instance().addMapLayer(output_layer)
                self.message.emit("Couche ajoutée au projet QGIS.")
            else:
                self.message.emit("Erreur: Impossible de charger la couche enregistrée.")
                self.finished.emit(False)
                return

            self.message.emit(f"Traitement terminé. Fichier enregistré: {self.output_path}")
            self.finished.emit(True)

        except Exception as e:
            self.message.emit(f"Erreur inattendue: {str(e)}")
            self.finished.emit(False)

class BassinsMobiliteDialog(QDialog):
    """Dialogue principal pour le traitement des bassins de mobilité"""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Création des bassins de mobilité")
        self.setMinimumSize(600, 500)
        self.setup_ui()

    def setup_ui(self):
        """Configurer l'interface utilisateur avec onglets"""
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.instructions_tab = QWidget()
        self.processing_tab = QWidget()
        self.setup_instructions_tab()
        self.setup_processing_tab()
        self.tabs.addTab(self.instructions_tab, "Instructions")
        self.tabs.addTab(self.processing_tab, "Traitement")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def setup_instructions_tab(self):
        """Configurer l'onglet Instructions"""
        layout = QVBoxLayout()
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        instructions = """
        <h2>Module de Création des Bassins de Mobilité</h2>
        <h3>Source des données:</h3>
        <p>Ce module utilise les données suivantes:</p>
        <ul>
            <li>Couche des communes (Shapefile, ex: BDCARTO COMMUNE.shp)</li>
            <li>Données supplémentaires des communes (CSV, avec DEPCOM, DEP, EPCI)</li>
            <li>Données de population par commune (CSV, avec Code département, Code commune, Population totale)</li>
            <li>Couche des EPCI (Shapefile, ex: BDCARTO EPCI.shp)</li>
            <li>Données supplémentaires des EPCI (CSV, avec EPCI, CODE_SIREN)</li>
            <li>Données des bassins de mobilité (CSV, avec nom_du_bassin, territoire_s_concerne_s, etc.)</li>
        </ul>
        <h3>Fonctionnalités:</h3>
        <p>Ce module permet de:</p>
        <ul>
            <li>Filtrer les communes et EPCI pour le département 21 (Côte-d'Or)</li>
            <li>Joindre les données de population et EPCI</li>
            <li>Regrouper les géométries par bassin de mobilité</li>
            <li>Calculer la population totale par bassin</li>
            <li>Nettoyer et renommer les champs (ex: nom_du_bassin → bassin)</li>
            <li>Enregistrer la couche finale en Shapefile ou GeoPackage</li>
            <li>Ajouter la couche au projet QGIS</li>
        </ul>
        <h3>Utilisation:</h3>
        <ol>
            <li>Spécifiez les chemins vers les fichiers d'entrée dans l'onglet Traitement</li>
            <li>Vérifiez que les fichiers existent (message vert si valide)</li>
            <li>Sélectionnez un fichier de sortie et son format (Shapefile ou GeoPackage)</li>
            <li>Cliquez sur "Lancer le traitement"</li>
            <li>La couche sera créée et ajoutée au projet QGIS</li>
        </ol>
        <h3>Remarques:</h3>
        <ul>
            <li>Les fichiers doivent être accessibles et valides</li>
            <li>Le dossier de sortie doit avoir des permissions d'écriture</li>
            <li>Les couches shapefile doivent avoir un système de coordonnées défini (ex: EPSG:2154)</li>
        </ul>
        """
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_processing_tab(self):
        """Configurer l'onglet Traitement"""
        layout = QVBoxLayout()
        # Titre des données
        self.title_text = QTextEdit()
        self.title_text.setReadOnly(True)
        self.title_text.setFixedHeight(50)
        self.title_text.append("<h3>Bassins de Mobilité - Côte-d'Or (21)</h3>")
        layout.addWidget(self.title_text)
        # Chemins des fichiers
        self.paths = {}
        files = [
            ("Couche des communes (Shapefile)", "*.shp"),
            ("Données supplémentaires des communes (CSV)", "*.csv"),
            ("Données de population (CSV)", "*.csv"),
            ("Couche des EPCI (Shapefile)", "*.shp"),
            ("Données supplémentaires des EPCI (CSV)", "*.csv"),
            ("Données des bassins de mobilité (CSV)", "*.csv"),
            ("Fichier de sortie (Shapefile ou GeoPackage)", "*.shp *.gpkg")
        ]
        for label, file_filter in files:
            h_layout = QHBoxLayout()
            lbl = QLabel(label)
            line_edit = QLineEdit()
            browse_btn = QPushButton("Parcourir...")
            status_text = QTextEdit()
            status_text.setReadOnly(True)
            status_text.setFixedHeight(30)
            status_text.append('<span style="color:red;">Vérification présence de la donnée</span>')
            h_layout.addWidget(lbl)
            h_layout.addWidget(line_edit)
            h_layout.addWidget(browse_btn)
            layout.addLayout(h_layout)
            layout.addWidget(status_text)
            self.paths[label] = {'line_edit': line_edit, 'browse_btn': browse_btn, 'status_text': status_text}
            browse_btn.clicked.connect(lambda _, le=line_edit, st=status_text, f=file_filter: self.browse_file(le, st, f))
            line_edit.textChanged.connect(lambda _, le=line_edit, st=status_text: self.validate_path(le, st))
        # Format de sortie
        output_format_layout = QHBoxLayout()
        self.output_format_label = QLabel("Format de sortie:")
        self.output_format_combo = QComboBox()
        self.output_format_combo.addItems(["Shapefile (.shp)", "GeoPackage (.gpkg)"])
        output_format_layout.addWidget(self.output_format_label)
        output_format_layout.addWidget(self.output_format_combo)
        output_format_layout.addStretch()
        layout.addLayout(output_format_layout)
        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        layout.addWidget(self.progress_bar)
        # Zone de message
        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)
        self.message_text.setFixedHeight(100)
        layout.addWidget(self.message_text)
        # Boutons
        button_layout = QHBoxLayout()
        self.process_button = QPushButton("Lancer le traitement")
        self.process_button.setStyleSheet("background-color: #4CAF50; color: white;")
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.setStyleSheet("background-color: #F44336; color: white;")
        self.cancel_button.setEnabled(False)
        button_layout.addWidget(self.process_button)
        button_layout.addWidget(self.cancel_button)
        layout.addLayout(button_layout)
        self.processing_tab.setLayout(layout)
        # Connexion des signaux
        self.process_button.clicked.connect(self.start_processing)
        self.cancel_button.clicked.connect(self.cancel_processing)

    def browse_file(self, line_edit, status_text, file_filter):
        """Ouvrir une boîte de dialogue pour sélectionner un fichier"""
        if line_edit == self.paths["Fichier de sortie (Shapefile ou GeoPackage)"]['line_edit']:
            file_path, _ = QFileDialog.getSaveFileName(self, "Sélectionner le fichier de sortie", "",
                                                      "Shapefile (*.shp);;GeoPackage (*.gpkg)")
        else:
            file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner le fichier", "", file_filter)
        if file_path:
            line_edit.setText(file_path)
            self.validate_path(line_edit, status_text)

    def validate_path(self, line_edit, status_text):
        """Valider l'existence du fichier"""
        file_path = line_edit.text()
        if file_path == self.paths["Fichier de sortie (Shapefile ou GeoPackage)"]['line_edit'].text():
            if os.path.isdir(os.path.dirname(file_path)) and os.access(os.path.dirname(file_path), os.W_OK):
                status_text.setHtml('<span style="color:green;">Dossier de sortie valide</span>')
            else:
                status_text.setHtml('<span style="color:red;">Vérification présence de la donnée</span>')
        else:
            if os.path.isfile(file_path):
                status_text.setHtml('<span style="color:green;">Données trouvées</span>')
            else:
                status_text.setHtml('<span style="color:red;">Vérification présence de la donnée</span>')

    def start_processing(self):
        """Démarrer le traitement"""
        paths = {
            "communes": self.paths["Couche des communes (Shapefile)"]['line_edit'].text(),
            "communes_info": self.paths["Données supplémentaires des communes (CSV)"]['line_edit'].text(),
            "population": self.paths["Données de population (CSV)"]['line_edit'].text(),
            "epci": self.paths["Couche des EPCI (Shapefile)"]['line_edit'].text(),
            "epci_info": self.paths["Données supplémentaires des EPCI (CSV)"]['line_edit'].text(),
            "bassins": self.paths["Données des bassins de mobilité (CSV)"]['line_edit'].text(),
            "output": self.paths["Fichier de sortie (Shapefile ou GeoPackage)"]['line_edit'].text()
        }
        for key, path in paths.items():
            if not path:
                QMessageBox.warning(self, "Erreur", f"Le fichier {key} est manquant.")
                return
            if key != "output" and not os.path.isfile(path):
                QMessageBox.warning(self, "Erreur", f"Le fichier {key} n'existe pas.")
                return
        if not os.access(os.path.dirname(paths["output"]), os.W_OK):
            QMessageBox.warning(self, "Erreur", "Vous n'avez pas les permissions d'écriture dans le dossier de sortie.")
            return
        output_format = "shp" if self.output_format_combo.currentText().startswith("Shapefile") else "gpkg"
        # Vérifier l'extension du fichier de sortie
        if not paths["output"].lower().endswith(f".{output_format}"):
            paths["output"] = os.path.splitext(paths["output"])[0] + f".{output_format}"
        # Désactiver les widgets
        self.process_button.setEnabled(False)
        self.cancel_button.setEnabled(True)
        self.output_format_combo.setEnabled(False)
        for p in self.paths.values():
            p['line_edit'].setEnabled(False)
            p['browse_btn'].setEnabled(False)
        self.progress_bar.setValue(0)
        self.message_text.clear()
        self.message_text.append("Début du traitement...")
        # Démarrer le thread
        self.worker = BassinsMobiliteWorker(
            paths["communes"], paths["population"], paths["epci"], paths["bassins"],
            paths["communes_info"], paths["epci_info"], paths["output"], output_format
        )
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.message.connect(self.message_text.append)
        self.worker.finished.connect(self.on_processing_finished)
        self.worker.start()

    def cancel_processing(self):
        """Annuler le traitement"""
        if hasattr(self, 'worker') and self.worker.isRunning():
            self.worker.stopped = True
            self.worker.wait()
            self.message_text.append("Traitement annulé par l'utilisateur.")
        self.process_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.output_format_combo.setEnabled(True)
        for p in self.paths.values():
            p['line_edit'].setEnabled(True)
            p['browse_btn'].setEnabled(True)

    def on_processing_finished(self, success):
        """Traiter la fin du traitement"""
        self.process_button.setEnabled(True)
        self.cancel_button.setEnabled(False)
        self.output_format_combo.setEnabled(True)
        for p in self.paths.values():
            p['line_edit'].setEnabled(True)
            p['browse_btn'].setEnabled(True)
        if success:
            QMessageBox.information(self, "Succès", "Traitement terminé avec succès.")
        else:
            QMessageBox.warning(self, "Erreur", "Le traitement a échoué. Voir les messages pour plus de détails.")

class MainPluginBassinsMobilite:
    """Classe pour intégrer le module au plugin principal"""
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        """Initialiser l'interface du module"""
        self.action = QAction("Créer bassins de mobilité", self.iface.mainWindow())
        self.action.triggered.connect(self.run)
        self.iface.addPluginToMenu("PROCESSING", self.action)

    def unload(self):
        """Nettoyer lors de la désactivation du plugin"""
        self.iface.removePluginMenu("PROCESSING", self.action)

    def run(self):
        """Exécuter le module"""
        dialog = BassinsMobiliteDialog(self.iface.mainWindow())
        dialog.exec_()