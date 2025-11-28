#TELECHARGEMENTS_Import_Naïades_Pesticides_Etats_Eco2.py

import os
import pandas as pd
import numpy as np
from datetime import datetime
from pathlib import Path
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors

from qgis.PyQt.QtCore import QVariant, QDate, Qt, QSizeF
from qgis.PyQt.QtGui import QColor, QFont
from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QTabWidget, QWidget, QTextEdit, QLabel, QPushButton,
    QLineEdit, QDateEdit, QComboBox, QListWidget, QRadioButton, QGroupBox, QFileDialog, QMessageBox, QProgressBar, QCheckBox
)
from qgis.core import (
    QgsProject, QgsVectorLayer, QgsFeature, QgsGeometry, QgsPointXY, QgsField,
    QgsVectorFileWriter, QgsCoordinateReferenceSystem, QgsPalLayerSettings,
    QgsTextFormat, QgsDiagramRenderer, QgsPieDiagram, QgsHistogramDiagram,
    QgsLinearlyInterpolatedDiagramRenderer, QgsDiagramLayerSettings, QgsDiagramSettings,
    QgsExpression, QgsVectorLayerSimpleLabeling, QgsMarkerSymbol, QgsCategorizedSymbolRenderer, QgsRendererCategory
)
from qgis.gui import QgsMapCanvas

class ImportNaïadesPesticidesEtatsEcoDialog(QDialog):
    def __init__(self, iface, parent=None):
        super(ImportNaïadesPesticidesEtatsEcoDialog, self).__init__(parent)
        self.iface = iface
        self.setWindowTitle("Pesticides Etat Eco Naiades")
        self.setMinimumWidth(800)
        self.initialize_subst()
        self.setup_ui()

    def initialize_subst(self):
        # Dictionnaire des substances
        polluants_specifiques_synthetiques = {
            1101: ['Alachlore', 0.3, 0.7, 'polluants_specifiques_synthetiques'],
            1955: ['Chloroalcanes C10-13', 0.4, 1.4, 'polluants_specifiques_synthetiques'],
            1464: ['Chlorfenvin-phos', 0.1, 0.3, 'polluants_specifiques_synthetiques'],
            1083: ['Chlorpyrifos', 0.03, 0.1, 'polluants_specifiques_synthetiques'],
            5534: ['Pesticides cyclodiènes', 0.01, 9999, 'polluants_specifiques_synthetiques'],
            7146: ['DDT total', 0.025, 9999, 'polluants_specifiques_synthetiques'],
            1148: ['para-para-DDT', 0.01, 9999, 'polluants_specifiques_synthetiques'],
            1951: ['Azoxystrobine', 0.95, 9999, 'polluants_specifiques_synthetiques'],
            1278: ['Toluène', 74, 9999, 'polluants_specifiques_synthetiques'],
            1847: ['Phosphate de tributyle', 82, 9999, 'polluants_specifiques_synthetiques'],
            1584: ['Biphényle', 3.3, 9999, 'polluants_specifiques_synthetiques'],
            5526: ['Boscalid', 11.6, 9999, 'polluants_specifiques_synthetiques'],
            1796: ['Métaldéhyde', 60.6, 9999, 'polluants_specifiques_synthetiques'],
            1694: ['Tebuconazole', 1, 9999, 'polluants_specifiques_synthetiques'],
            1474: ['Chlorprophame', 4, 9999, 'polluants_specifiques_synthetiques'],
            1780: ['Xylène', 1, 9999, 'polluants_specifiques_synthetiques'],
            1209: ['Linuron', 1, 9999, 'polluants_specifiques_synthetiques'],
            1713: ['Thiabendazole', 1.2, 9999, 'polluants_specifiques_synthetiques'],
            1234: ['Pendiméthaline', 0.02, 9999, 'polluants_specifiques_synthetiques'],
            1105: ['Aminotriazole', 0.08, 9999, 'polluants_specifiques_synthetiques'],
            1882: ['Nicosulfuron', 0.035, 9999, 'polluants_specifiques_synthetiques'],
            1667: ['Oxadiazon', 0.09, 9999, 'polluants_specifiques_synthetiques'],
            1907: ['AMPA', 452, 9999, 'polluants_specifiques_synthetiques'],
            1506: ['Glyphosate', 28, 9999, 'polluants_specifiques_synthetiques'],
            1113: ['Bentazone', 70, 9999, 'polluants_specifiques_synthetiques'],
            1212: ['2,4 MCPA', 0.5, 9999, 'polluants_specifiques_synthetiques'],
            1814: ['Diflufenicanil', 0.01, 9999, 'polluants_specifiques_synthetiques'],
            1359: ['Cyprodinil', 0.026, 9999, 'polluants_specifiques_synthetiques'],
            1877: ['Imidaclopride', 0.2, 9999, 'polluants_specifiques_synthetiques'],
            1206: ['Iprodione', 0.35, 9999, 'polluants_specifiques_synthetiques'],
            1141: ['2,4D', 2.2, 9999, 'polluants_specifiques_synthetiques']
        }

        polluants_tab_44 = {
            1105: ['Aminotriazole', 0.08, 9999, 'polluants_tab_44'],
            1882: ['Nicosulfuron', 0.035, 9999, 'polluants_tab_44'],
            1667: ['Oxadiazon', 0.09, 9999, 'polluants_tab_44'],
            1907: ['AMPA', 452, 9999, 'polluants_tab_44'],
            1506: ['Glyphosate', 28, 9999, 'polluants_tab_44'],
            1113: ['Bentazone', 70, 9999, 'polluants_tab_44'],
            1212: ['2,4 MCPA', 0.5, 9999, 'polluants_tab_44'],
            1814: ['Diflufenicanil', 0.01, 9999, 'polluants_tab_44'],
            1359: ['Cyprodinil', 0.026, 9999, 'polluants_tab_44'],
            1877: ['Imidaclopride', 0.2, 9999, 'polluants_tab_44'],
            1206: ['Iprodione', 0.35, 9999, 'polluants_tab_44'],
            1141: ['2,4D', 2.2, 9999, 'polluants_tab_44'],
            1951: ['Azoxystrobine', 0.95, 9999, 'polluants_tab_44'],
            1278: ['Toluène', 74, 9999, 'polluants_tab_44'],
            1847: ['Phosphate de tributyle', 82, 9999, 'polluants_tab_44'],
            1584: ['Biphényle', 3.3, 9999, 'polluants_tab_44'],
            5526: ['Boscalid', 11.6, 9999, 'polluants_tab_44'],
            1796: ['Métaldéhyde', 60.6, 9999, 'polluants_tab_44'],
            1694: ['Tebuconazole', 1, 9999, 'polluants_tab_44'],
            1474: ['Chlorprophame', 4, 9999, 'polluants_tab_44'],
            1780: ['Xylène', 1, 9999, 'polluants_tab_44'],
            1209: ['Linuron', 1, 9999, 'polluants_tab_44'],
            1713: ['Thiabendazole', 1.2, 9999, 'polluants_tab_44'],
            1234: ['Pendiméthaline', 0.02, 9999, 'polluants_tab_44']
        }

        polluants_specifiques_non_synthetiques_tab_43 = {
            1383: ['Zinc', 7.8, 9999, 'polluants_specifiques_non_synthetiques_tab_43'],
            1369: ['Arsenic', 0.83, 9999, 'polluants_specifiques_non_synthetiques_tab_43'],
            1392: ['Cuivre', 1, 9999, 'polluants_specifiques_non_synthetiques_tab_43'],
            1389: ['Chrome', 3.4, 9999, 'polluants_specifiques_non_synthetiques_tab_43']
        }

        subst_autres = {
            1940: ['Thiafluamide', 0.04, 0.16, 'autres substances'],
            1092: ['Prosulfocarbe', 0.1, 12, 'autres substances'],
            1414: ['Propyzamide', 8, 9999, 'autres substances'],
            1136: ['Chlortoluron', 0.1, 2, 'autres substances'],
            1215: ['Metamitrone', 4, 22, 'autres substances'],
            1678: ['Dimethenamide-p (dmta-p)', 0.2, 1.3, 'autres substances']
        }

        self.subst = {}
        self.subst.update(polluants_specifiques_synthetiques)
        self.subst.update(polluants_tab_44)
        self.subst.update(polluants_specifiques_non_synthetiques_tab_43)
        self.subst.update(subst_autres)

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()

        # Onglet Instructions
        self.instructions_tab = QWidget()
        self.setup_instructions_tab()
        self.tabs.addTab(self.instructions_tab, "Instructions")

        # Onglet Traitement (avec sous-onglets)
        self.analysis_tab = QWidget()
        self.setup_analysis_tab()
        self.tabs.addTab(self.analysis_tab, "Traitement")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def setup_instructions_tab(self):
        layout = QVBoxLayout()
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        instructions = """
        <h2>Pesticides Etat Eco Naiades</h2>
        <h3>Fonctionnalités :</h3>
        <p>Ce module permet d'automatiser l'analyse des données de concentrations en pesticides de la base Naïades. Il génère des URLs pour télécharger les données, traite les fichiers CSV pour calculer les moyennes par station et les dépassements des normes NQE-MA et NQE-CMA, et crée des couches SIG dans QGIS.</p>

        <h3>Données nécessaires :</h3>
        <p>- Accès à internet pour générer et utiliser les URLs de téléchargement Naïades.<br>
        - Fichiers CSV téléchargés (Stations.csv et Analyses.csv) placés dans un dossier dédié.<br>
        - QGIS pour la visualisation des couches.</p>

        <h3>Utilisation :</h3>
        <ol>
        <li>Dans l'onglet "Génération URL", choisissez le mode (par région ou par départements), les dates, et génère l'URL. Utilisez-la pour télécharger les données via le site Naïades (un email avec lien de téléchargement sera envoyé).</li>
        <li>Dans l'onglet "Traitements Pandas", sélectionnez le dossier contenant les CSV téléchargés et lancez le traitement pour calculer moyennes et dépassements.</li>
        <li>Dans l'onglet "Création Couches SIG", sélectionnez le dossier d'export et créez les couches GPKG à partir des résultats.</li>
        <li>Dans l'onglet "Graphiques", sélectionnez les types de graphiques à générer via les cases à cocher et lancez la génération pour toutes les paires station-substance.</li>
        </ol>

        <h3>Types de graphiques disponibles :</h3>
        <ul>
        <li>Évolution des concentrations (scatter plot).</li>
        <li>Dépassements mensuels (histogramme empilé).</li>
        <li>Heatmap des dépassements mensuels.</li>
        <li>Boxplot de la variabilité mensuelle.</li>
        <li>Ligne de tendance (moyenne mobile).</li>
        <li>Histogramme cumulatif des dépassements.</li>
        </ul>
        <p>Export en PNG pour tous les graphiques.</p>
        """
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_analysis_tab(self):
        layout = QVBoxLayout()
        self.sub_tabs = QTabWidget()

        # Sous-onglet Génération URL
        self.url_tab = QWidget()
        self.setup_url_tab()
        self.sub_tabs.addTab(self.url_tab, "Génération URL")

        # Sous-onglet Traitements Pandas
        self.pandas_tab = QWidget()
        self.setup_pandas_tab()
        self.sub_tabs.addTab(self.pandas_tab, "Traitements Pandas")

        # Sous-onglet Création Couches SIG
        self.sig_tab = QWidget()
        self.setup_sig_tab()
        self.sub_tabs.addTab(self.sig_tab, "Création Couches SIG")

        # Sous-onglet Graphiques
        self.graphs_tab = QWidget()
        self.setup_graphs_tab()
        self.sub_tabs.addTab(self.graphs_tab, "Graphiques")

        layout.addWidget(self.sub_tabs)
        self.analysis_tab.setLayout(layout)

    def setup_url_tab(self):
        layout = QVBoxLayout()

        # GroupBox pour mode
        mode_group = QGroupBox("Mode de sélection géographique")
        mode_layout = QHBoxLayout()
        self.radio_region = QRadioButton("Par Région")
        self.radio_dept = QRadioButton("Par Département")
        self.radio_region.setChecked(True)
        mode_layout.addWidget(self.radio_region)
        mode_layout.addWidget(self.radio_dept)
        mode_group.setLayout(mode_layout)
        layout.addWidget(mode_group)

        # Liste pour sélection
        self.list_widget = QListWidget()
        self.list_widget.setSelectionMode(QListWidget.MultiSelection)
        layout.addWidget(QLabel("Sélectionnez les zones :"))
        layout.addWidget(self.list_widget)

        # Dates
        dates_layout = QHBoxLayout()
        dates_layout.addWidget(QLabel("Date début :"))
        self.date_debut = QDateEdit()
        self.date_debut.setDate(QDate(2015, 1, 1))
        dates_layout.addWidget(self.date_debut)
        dates_layout.addWidget(QLabel("Date fin :"))
        self.date_fin = QDateEdit()
        self.date_fin.setDate(QDate.currentDate())
        dates_layout.addWidget(self.date_fin)
        layout.addLayout(dates_layout)

        # Bouton générer URL
        btn_generate = QPushButton("Générer URL")
        btn_generate.clicked.connect(self.generate_url)
        layout.addWidget(btn_generate)

        # Affichage URL
        self.url_text = QTextEdit()
        self.url_text.setReadOnly(True)
        layout.addWidget(QLabel("URL générée :"))
        layout.addWidget(self.url_text)

        # Mise à jour liste initiale
        self.update_list_widget()

        self.radio_region.toggled.connect(self.update_list_widget)
        self.radio_dept.toggled.connect(self.update_list_widget)

        self.url_tab.setLayout(layout)

    def update_list_widget(self):
        self.list_widget.clear()
        if self.radio_region.isChecked():
            regions = [
                "Bourgogne_Franche_Comte", "Nouvelle_Aquitaine", "Auvergne_Rhone_Alpes",
                "Bretagne", "Centre_Val_de_Loire", "Grand_Est", "Hauts_de_France",
                "Ile_de_France", "Normandie", "Occitanie", "Pays_de_la_Loire",
                "Provence_Alpes_Cote_d_Azur"
            ]
            self.list_widget.addItems(regions)
        else:
            depts = [str(i).zfill(2) for i in range(1, 96)] + ["2A", "2B"]
            self.list_widget.addItems(depts)

    def generate_url(self):
        try:
            date_debut = self.date_debut.date().toString("dd-MM-yyyy")
            date_fin = self.date_fin.date().toString("dd-MM-yyyy")
            toto = ','.join(map(str, self.subst.keys()))
            selected = [item.text() for item in self.list_widget.selectedItems()]
            if self.radio_region.isChecked():
                dpts_dict = {
                    "Auvergne_Rhone_Alpes": "01,03,07,15,26,38,42,43,63,69,73,74",
                    "Bourgogne_Franche_Comte": "21,25,39,58,70,71,89,90",
                    "Bretagne": "22,29,35,56",
                    "Centre_Val_de_Loire": "18,28,36,37,41,45",
                    "Grand_Est": "08,10,51,52,54,55,57,67,68,88",
                    "Hauts_de_France": "02,59,60,62,80",
                    "Ile_de_France": "75,77,78,91,92,93,94,95",
                    "Normandie": "14,27,50,61,76",
                    "Nouvelle_Aquitaine": "16,17,19,23,24,27,33,40,47,64,79,86,87",
                    "Occitanie": "09,11,12,30,31,32,34,46,48,65,66,81,82",
                    "Pays_de_la_Loire": "44,49,53,72,85",
                    "Provence_Alpes_Cote_d_Azur": "04,05,06,13,83,84"
                }
                dpts = ','.join([dpts_dict[s] for s in selected])
            else:
                dpts = ','.join(selected)

            if not dpts:
                raise ValueError("Sélectionnez au moins une zone.")

            url = f"http://naiades.eaufrance.fr/acces-donnees#/physicochimie/resultats?debut={date_debut}&fin={date_fin}&departements={dpts}&parametres={toto}"
            self.url_text.setText(url)
            QMessageBox.information(self, "Succès", "URL générée. Copiez-la et utilisez-la sur le site Naïades.")
        except Exception as e:
            QMessageBox.critical(self, "Erreur", str(e))

    def setup_pandas_tab(self):
        layout = QVBoxLayout()

        # Sélection dossier CSV
        folder_layout = QHBoxLayout()
        self.folder_line = QLineEdit()
        btn_browse = QPushButton("Parcourir...")
        btn_browse.clicked.connect(self.browse_folder)
        folder_layout.addWidget(QLabel("Dossier des CSV :"))
        folder_layout.addWidget(self.folder_line)
        folder_layout.addWidget(btn_browse)
        layout.addLayout(folder_layout)

        # Bouton traitement
        btn_process = QPushButton("Lancer Traitements")
        btn_process.clicked.connect(self.process_pandas)
        layout.addWidget(btn_process)

        # Progress bar
        self.progress = QProgressBar()
        layout.addWidget(self.progress)

        # Log
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        layout.addWidget(QLabel("Log :"))
        layout.addWidget(self.log_text)

        self.pandas_tab.setLayout(layout)

    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner Dossier CSV")
        if folder:
            self.folder_line.setText(folder)

    def process_pandas(self):
        try:
            folder = self.folder_line.text()
            if not folder:
                raise ValueError("Sélectionnez un dossier.")

            self.progress.setValue(0)
            self.log_text.clear()

            # Lecture Stations.csv
            df_stations = pd.read_csv(os.path.join(folder, "Stations.csv"), sep=';', encoding='utf8', low_memory=False)
            self.log_text.append("Stations lues.")
            self.progress.setValue(10)

            # Lecture Analyses.csv
            df_analyses = pd.read_csv(os.path.join(folder, "Analyses.csv"), sep=';', encoding='utf8', low_memory=False)
            self.log_text.append("Analyses lues.")
            self.progress.setValue(20)

            # Créer df_subst
            df_subst = pd.DataFrame.from_dict(self.subst, orient='index', columns=['LbLongParamètre', 'NQE-MA', 'NQE-CMA', 'Type_polluants'])
            self.log_text.append("Dictionnaire des substances créé.")
            self.progress.setValue(30)

            # Mise en dataframe des colonnes utiles
            df = df_analyses.loc[:, ('CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'DateAna', 'CdParametre', 'LbLongParamètre', 'RsAna', 'LqAna')]
            df_analyses_LQ = pd.merge(df, df_subst[['NQE-MA', 'NQE-CMA']], left_on=['CdParametre'], right_index=True, how='left')
            self.log_text.append("Jointure NQE effectuée.")
            self.progress.setValue(40)

            # Nombre de mesures par substance
            table0 = df_analyses_LQ.pivot_table(
                values='RsAna',
                index=['CdParametre', 'LbLongParamètre'],
                aggfunc='count'
            )
            table0 = pd.DataFrame(table0.to_records())
            table0['nb_mesures'] = table0['RsAna']
            table0 = table0.drop(columns=['RsAna'])

            # Cas où NQE-MA < LQ
            mask = df_analyses_LQ['NQE-MA'] < df_analyses_LQ['LqAna']
            table1 = df_analyses_LQ[mask].pivot_table(
                values='NQE-MA',
                index=['CdParametre', 'LbLongParamètre'],
                aggfunc='count'
            )
            table1 = pd.DataFrame(table1.to_records())
            table1['nbNQMAsupLQ'] = table1['NQE-MA']
            table1 = table1.drop(columns=['NQE-MA'])

            # Ratio
            table2 = pd.merge(table0, table1['nbNQMAsupLQ'], left_index=True, right_index=True, how='left')
            table2['pourcentage'] = (100 * table2['nbNQMAsupLQ'] / table2['nb_mesures']).round(2)
            table3 = table2.sort_values(by=['pourcentage'], ascending=False)
            self.log_text.append("Analyse des limites de quantification terminée.")
            self.progress.setValue(50)

            # Extraction par stations et années
            df_analyses_2 = df_analyses_LQ.loc[:, ('CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'DateAna', 'CdParametre', 'LbLongParamètre', 'RsAna', 'LqAna', 'NQE-MA', 'NQE-CMA')]
            df_analyses_2['Annee'] = df_analyses_2['DateAna'].str[:4]
            df_analyses_3 = df_analyses_2.iloc[:, [0, 1, 3, 4, 5, 6, 7, 8, 9]]
            new_index = ['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'Annee', 'CdParametre', 'LbLongParamètre', 'RsAna', 'LqAna', 'NQE-MA', 'NQE-CMA']
            df_analyses_4 = df_analyses_3.reindex(columns=new_index)
            self.progress.setValue(60)

            # Calcul du nombre d'analyses par substance et année
            nb_val_table = df_analyses_4.pivot_table(
                index=['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'CdParametre', 'LbLongParamètre', 'NQE-MA', 'NQE-CMA'],
                values='RsAna',
                columns='Annee',
                aggfunc='count',
                fill_value=0
            )
            liste_annees = [titre for titre in nb_val_table.columns]  # Définir liste_annees ici
            nb_val_table = pd.DataFrame(nb_val_table.to_records())
            for year in liste_annees:
                titre = 'nb_M_' + year
                nb_val_table[titre] = nb_val_table[year]
            nb_val_table = nb_val_table.drop(columns=liste_annees)
            self.log_text.append("Calcul du nombre d'analyses terminé.")
            self.progress.setValue(65)

            # Calcul des dépassements NQE-MA
            mask = df_analyses_4['RsAna'] > df_analyses_4['NQE-MA']
            nb_val_supMA_table = df_analyses_4[mask].pivot_table(
                index=['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'CdParametre', 'LbLongParamètre', 'NQE-MA', 'NQE-CMA'],
                values='RsAna',
                columns='Annee',
                aggfunc='count',
                fill_value=0
            )
            nb_val_supMA_table.columns = [titre.replace(titre, "supMA_%s" % titre) for titre in nb_val_supMA_table.columns]
            nb_val_supMA_table_2 = pd.DataFrame(nb_val_supMA_table.to_records())
            nb_depassements_annuel_NQE_MA = nb_val_supMA_table_2.loc[:, :]
            self.log_text.append("Dépassements NQE-MA calculés.")
            self.progress.setValue(70)

            # Calcul des moyennes annuelles
            df_analyses_5 = df_analyses_4.copy()
            df_analyses_5['RsAna'] = np.select(
                [(df_analyses_5['RsAna'].notnull()) & (df_analyses_5['RsAna'] < df_analyses_5['LqAna'])],
                [df_analyses_5['LqAna'] / 2],
                df_analyses_5['RsAna']
            )
            table = df_analyses_5.pivot_table(
                index=['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'CdParametre', 'LbLongParamètre', 'NQE-MA', 'LqAna'],
                values='RsAna',
                columns='Annee',
                aggfunc={'RsAna': [len, np.mean]},
                fill_value=0
            )
            liste_annees = [multi_index[1] for multi_index in table.columns if multi_index[0] == 'mean']  # Extraire les années uniques
            flattened = pd.DataFrame(table.to_records())
            flattened.columns = [titre.replace("('len', '", "nb_").replace("')", "") for titre in flattened.columns]
            flattened.columns = [titre.replace("('mean', '", "moy_").replace("')", "") for titre in flattened.columns]
            self.progress.setValue(75)

            # Suppression des moyennes avec moins de 4 mesures
            for year in liste_annees:
                col = 'nb_' + year
                titre = 'moy_' + year
                flattened[titre] = np.select([flattened[col] < 4], [0], default=flattened[titre])
            table_2 = flattened.loc[:, :]
            self.log_text.append("Moyennes annuelles calculées.")
            self.progress.setValue(80)

            # Identification des non-respects NQE-MA
            for year in liste_annees:
                col = 'moy_' + year
                titre_MA = str(year) + '_MA'
                conditions_non_respect = [
                    (table_2['LqAna'] > table_2['NQE-MA']) & (table_2[col] > table_2['LqAna']),
                    (table_2['LqAna'] > table_2['NQE-MA']) & (table_2[col] <= table_2['LqAna']),
                    (table_2['LqAna'] <= table_2['NQE-MA']) & (table_2[col] > table_2['NQE-MA'])
                ]
                choices = [1, np.nan, 1]
                table_2[titre_MA] = np.select(conditions_non_respect, choices, default=np.nan)
            table_3 = table_2.loc[:, :]
            liste_col_subset = [year + '_MA' for year in liste_annees]
            nb_depassements_NQE_MA = table_3.dropna(subset=liste_col_subset, how='all')
            self.log_text.append("Non-respects NQE-MA identifiés.")
            self.progress.setValue(85)

            # Dépassements NQE-CMA
            depassements_NQE_CMA = df_analyses_5
            depassements_NQE_CMA['depasse_NQE_CMA'] = np.where(depassements_NQE_CMA['RsAna'] > depassements_NQE_CMA['NQE-CMA'], 1, 0)
            nb_depassements_NQE_CMA = depassements_NQE_CMA.pivot_table(
                index=['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'CdParametre', 'LbLongParamètre'],
                values='depasse_NQE_CMA',
                columns='Annee',
                aggfunc={'depasse_NQE_CMA': np.sum},
                fill_value=0
            )
            nb_depassements_NQE_CMA_plat = pd.DataFrame(nb_depassements_NQE_CMA.to_records())
            liste_col = [col for col in nb_depassements_NQE_CMA_plat.columns if col not in ['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'CdParametre', 'LbLongParamètre']]
            for col in liste_col:
                titre = col + '_CMA'
                nb_depassements_NQE_CMA_plat[titre] = nb_depassements_NQE_CMA_plat[col]
            nb_depassements_NQE_CMA_plat_1 = nb_depassements_NQE_CMA_plat.drop(columns=liste_col)
            self.log_text.append("Dépassements NQE-CMA calculés.")
            self.progress.setValue(90)

            # Table finale
            liste_id = ['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'CdParametre', 'LbLongParamètre']
            depassements_NQE_MA_CMA = pd.merge(nb_val_table, nb_depassements_annuel_NQE_MA, left_on=liste_id, right_on=liste_id, how='left')
            depassements_NQE_MA_CMA = pd.merge(depassements_NQE_MA_CMA, nb_depassements_NQE_MA, left_on=liste_id, right_on=liste_id, how='left')
            depassements_NQE_MA_CMA = pd.merge(depassements_NQE_MA_CMA, nb_depassements_NQE_CMA_plat_1, left_on=liste_id, right_on=liste_id, how='left')
            depassements_NQE_MA_CMA_pb = depassements_NQE_MA_CMA.fillna(0).replace(0, np.nan)
            depassements_NQE_MA_CMA_pb.to_csv(os.path.join(folder, "depassements_NQE_MA_CMA.csv"), sep=';', index=False, encoding='utf8')
            self.log_text.append("Table finale créée et exportée.")
            self.progress.setValue(95)

            # Décompactage en tables annuelles
            Dico_Annees = {}
            for year in liste_annees:
                titre = 'stations_nb_depassements_NQE_CMA_' + year
                liste_f = liste_id + ['moy_' + year, 'nb_M_' + year, 'supMA_' + year, year + '_MA', year + '_CMA']
                Dico_Annees[titre] = [liste_f, year]

            dico_dataframe = {}
            for key in Dico_Annees.keys():
                dff = depassements_NQE_MA_CMA_pb[Dico_Annees[key][0]]
                year = Dico_Annees[key][1]
                list_of_cols = [col for col in dff.columns if col not in liste_id and col != 'nb_M_' + year]
                dff = dff.dropna(how='all', subset=list_of_cols)
                dff = pd.merge(
                    dff,
                    df_stations[['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'CoordXStationMesureEauxSurface',
                                 'CoordYStationMesureEauxSurface', 'CdProjStationMesureEauxSurface', 'LibelleProjection',
                                 'CodeCommune', 'LbCommune', 'CodeDepartement', 'LbDepartement', 'CodeRegion',
                                 'LbRegion', 'CdMasseDEau', 'CdEuMasseDEau', 'NomMasseDEau', 'CdEuSsBassinDCEAdmin',
                                 'NomSsBassinDCEAdmin', 'CdBassinDCE', 'CdEuBassinDCE', 'NomEuBassinDCE',
                                 'CdTronconHydrographique', 'CdCoursdEau', 'NomCoursdEau']],
                    left_on=['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface'],
                    right_on=['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface'],
                    how='left'
                )
                dico_dataframe[key] = [dff, year]
                dff.to_csv(
                    os.path.join(folder, f"{key}.csv"),
                    sep=';',
                    header=True,
                    index=False,
                    encoding='utf8'
                )
                self.log_text.append(f"Table annuelle {key} exportée.")

            self.progress.setValue(100)
            self.log_text.append("Traitement terminé.")
            return True
        except Exception as e:
            self.log_text.append(f"Erreur: {str(e)}")
            return False

    def setup_sig_tab(self):
        layout = QVBoxLayout()

        # Sélection dossier export
        export_layout = QHBoxLayout()
        self.export_line = QLineEdit()
        btn_export_browse = QPushButton("Parcourir...")
        btn_export_browse.clicked.connect(self.browse_export_folder)
        export_layout.addWidget(QLabel("Dossier d'export GPKG :"))
        export_layout.addWidget(self.export_line)
        export_layout.addWidget(btn_export_browse)
        layout.addLayout(export_layout)

        # Bouton création couches
        btn_create = QPushButton("Créer Couches SIG")
        btn_create.clicked.connect(self.create_sig_layers)
        layout.addWidget(btn_create)

        # Log
        self.sig_log = QTextEdit()
        self.sig_log.setReadOnly(True)
        layout.addWidget(QLabel("Log SIG :"))
        layout.addWidget(self.sig_log)

        self.sig_tab.setLayout(layout)

    def browse_export_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner Dossier Export")
        if folder:
            self.export_line.setText(folder)

    def create_sig_layers(self):
        try:
            export_folder = self.export_line.text()
            if not export_folder:
                raise ValueError("Sélectionnez un dossier d'export.")

            self.sig_log.clear()

            # Mappage des types Pandas vers les types QVariant (QGIS)
            type_mapping = {
                'object': QVariant.String,
                'int64': QVariant.Int,
                'int32': QVariant.Int,
                'float64': QVariant.Double,
                'float32': QVariant.Double,
                'bool': QVariant.Bool
            }

            # Parcourir les fichiers CSV dans le dossier d'export
            for file in os.listdir(export_folder):
                if file.endswith(".csv") and "stations_nb_depassements" in file:
                    df = pd.read_csv(os.path.join(export_folder, file), sep=';')
                    layer_name = file.replace(".csv", "")

                    # Créer une couche mémoire
                    layer = QgsVectorLayer("Point?crs=EPSG:2154", layer_name, "memory")
                    pr = layer.dataProvider()

                    # Ajouter les champs
                    for col in df.columns:
                        if col not in ['CoordXStationMesureEauxSurface', 'CoordYStationMesureEauxSurface']:
                            col_type = str(df[col].dtype)
                            qgis_type = type_mapping.get(col_type, QVariant.String)
                            pr.addAttributes([QgsField(col, qgis_type)])
                    layer.updateFields()

                    # Ajouter les entités
                    for _, row in df.iterrows():
                        feat = QgsFeature()
                        x = row['CoordXStationMesureEauxSurface']
                        y = row['CoordYStationMesureEauxSurface']
                        feat.setGeometry(QgsGeometry.fromPointXY(QgsPointXY(x, y)))
                        attrs = [row[col] for col in df.columns if col not in ['CoordXStationMesureEauxSurface', 'CoordYStationMesureEauxSurface']]
                        feat.setAttributes(attrs)
                        pr.addFeature(feat)

                    # Exporter vers GPKG
                    gpkg_path = os.path.join(export_folder, layer_name + ".gpkg")
                    options = QgsVectorFileWriter.SaveVectorOptions()
                    options.driverName = "GPKG"
                    options.layerName = layer_name
                    QgsVectorFileWriter.writeAsVectorFormatV3(
                        layer,
                        gpkg_path,
                        QgsProject.instance().transformContext(),
                        options
                    )

                    # Charger la couche GPKG dans QGIS
                    gpkg_layer = QgsVectorLayer(gpkg_path, layer_name, "ogr")
                    QgsProject.instance().addMapLayer(gpkg_layer)

                    # Configurer les diagrammes et étiquettes
                    self.setup_thematic_analysis(gpkg_layer)

                    self.sig_log.append(f"Couche {layer_name} créée, ajoutée, et analyse thématique configurée.")

            QMessageBox.information(self, "Succès", "Couches SIG créées et ajoutées à QGIS avec analyse thématique.")
        except Exception as e:
            self.sig_log.append(f"Erreur: {str(e)}")
            QMessageBox.critical(self, "Erreur", str(e))

    def setup_thematic_analysis(self, layer):
        try:
            # Diagramme en camembert pour NQE-MA
            pie_settings = QgsDiagramSettings()
            pie_settings.categoryAttributes = [field.name() for field in layer.fields() if 'supMA' in field.name()]
            pie_settings.categoryColors = [
                QColor(255, 0, 0, 204),
                QColor(0, 255, 0, 204),
                QColor(0, 0, 255, 204),
                QColor(255, 255, 0, 204),
                QColor(255, 0, 255, 204)
            ]
            pie_settings.opacity = 0.8
            pie_settings.size = QSizeF(50.0, 50.0)
            pie_settings.enabled = True

            pie_renderer = QgsLinearlyInterpolatedDiagramRenderer()
            pie_renderer.setLowerValue(0.0)
            pie_renderer.setUpperValue(10.0)
            pie_renderer.setDiagram(QgsPieDiagram())
            pie_renderer.setDiagramSettings(pie_settings)

            pie_layer_settings = QgsDiagramLayerSettings()
            pie_layer_settings.setPlacement(QgsDiagramLayerSettings.AroundPoint)
            pie_layer_settings.setPriority(5)
            pie_layer_settings.setZIndex(0)
            layer.setDiagramLayerSettings(pie_layer_settings)
            layer.setDiagramRenderer(pie_renderer)

            # Diagramme en barres pour NQE-CMA
            bar_settings = QgsDiagramSettings()
            bar_settings.categoryAttributes = [field.name() for field in layer.fields() if '_CMA' in field.name()]
            bar_settings.categoryColors = [
                QColor(200, 0, 0, 204),
                QColor(0, 200, 0, 204),
                QColor(0, 0, 200, 204),
                QColor(200, 200, 0, 204),
                QColor(200, 0, 200, 204)
            ]
            bar_settings.opacity = 0.8
            bar_settings.size = QSizeF(50.0, 50.0)
            bar_settings.enabled = True

            bar_renderer = QgsLinearlyInterpolatedDiagramRenderer()
            bar_renderer.setLowerValue(0.0)
            bar_renderer.setUpperValue(10.0)
            bar_renderer.setDiagram(QgsHistogramDiagram())
            bar_renderer.setDiagramSettings(bar_settings)

            bar_layer_settings = QgsDiagramLayerSettings()
            bar_layer_settings.setPlacement(QgsDiagramLayerSettings.OverPoint)
            bar_layer_settings.setPriority(4)
            bar_layer_settings.setZIndex(1)
            layer.setDiagramLayerSettings(bar_layer_settings)
            layer.setDiagramRenderer(bar_renderer)

            # Étiquettes
            label_settings = QgsPalLayerSettings()
            label_settings.fieldName = (
                "concat(\"LbStationMesureEauxSurface\", '\\n', "
                "array_to_string(array_distinct(array_agg(\"LbLongParamètre\")), ', '))"
            )
            label_settings.isExpression = True
            label_settings.placement = QgsPalLayerSettings.AroundPoint
            label_settings.dist = 10

            text_format = QgsTextFormat()
            text_format.setFont(QFont("Arial", 10))
            text_format.setSize(10)
            label_settings.setFormat(text_format)

            labeling = QgsVectorLayerSimpleLabeling(label_settings)
            layer.setLabeling(labeling)
            layer.setLabelsEnabled(True)

            # Correction pour symboles proportionnels
            category_field = 'LbLongParamètre'
            size_expression = QgsExpression('"supMA_" + "Annee"')  # Ex. dépassements MA
            renderer = QgsCategorizedSymbolRenderer(category_field)
            unique_substances = [f['LbLongParamètre'] for f in layer.getFeatures() if f['LbLongParamètre']]
            colors = [QColor.fromHslF(i / len(unique_substances), 0.5, 0.5) for i in range(len(unique_substances))]  # Couleurs dynamiques
            for i, substance in enumerate(set(unique_substances)):
                symbol = QgsMarkerSymbol.createSimple({'color': colors[i].name(), 'size_expression': size_expression.expression()})
                renderer.addCategory(QgsRendererCategory(substance, symbol, substance))
            layer.setRenderer(renderer)

            layer.triggerRepaint()
            self.iface.layerTreeView().refreshLayerSymbology(layer.id())
            self.iface.mapCanvas().refresh()

        except Exception as e:
            self.sig_log.append(f"Erreur dans setup_thematic_analysis: {str(e)}")
            raise

    def setup_graphs_tab(self):
        layout = QVBoxLayout()

        # Sélection dossier CSV
        folder_layout = QHBoxLayout()
        self.graphs_folder_line = QLineEdit()
        btn_browse = QPushButton("Parcourir...")
        btn_browse.clicked.connect(self.browse_graphs_folder)
        folder_layout.addWidget(QLabel("Dossier des CSV :"))
        folder_layout.addWidget(self.graphs_folder_line)
        folder_layout.addWidget(btn_browse)
        layout.addLayout(folder_layout)

        # Cases à cocher pour types de graphiques
        self.graph_types = {
            "Evolution": QCheckBox("Évolution des concentrations"),
            "Mensuel": QCheckBox("Dépassements mensuels"),
            "Heatmap": QCheckBox("Heatmap des dépassements mensuels"),
            "Boxplot": QCheckBox("Boxplot de la variabilité mensuelle"),
            "Tendance": QCheckBox("Ligne de tendance"),
            "Cumulatif": QCheckBox("Histogramme cumulatif")
        }
        graphs_group = QGroupBox("Sélectionnez les graphiques à générer")
        graphs_layout = QVBoxLayout()
        for checkbox in self.graph_types.values():
            checkbox.setChecked(True)
            graphs_layout.addWidget(checkbox)
        graphs_group.setLayout(graphs_layout)
        layout.addWidget(graphs_group)

        # Bouton générer graphiques
        btn_generate = QPushButton("Générer Graphiques")
        btn_generate.clicked.connect(self.generate_graphs)
        layout.addWidget(btn_generate)

        # Progress bar
        self.graphs_progress = QProgressBar()
        layout.addWidget(self.graphs_progress)

        # Log
        self.graphs_log = QTextEdit()
        self.graphs_log.setReadOnly(True)
        layout.addWidget(QLabel("Log :"))
        layout.addWidget(self.graphs_log)

        self.graphs_tab.setLayout(layout)

    def browse_graphs_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner Dossier CSV")
        if folder:
            self.graphs_folder_line.setText(folder)
    
    def generate_graphs(self):
        try:
            folder = self.graphs_folder_line.text()
            if not folder:
                raise ValueError("Sélectionnez un dossier.")

            self.graphs_progress.setValue(0)
            self.graphs_log.clear()

            # Vérifier les permissions d'écriture
            if not os.access(folder, os.W_OK):
                raise PermissionError(f"Pas de permission d'écriture dans le dossier {folder}.")

            # Charger Analyses.csv
            df_analyses = pd.read_csv(os.path.join(folder, "Analyses.csv"), sep=';', encoding='utf8', low_memory=False)
            self.graphs_log.append("Analyses lues.")
            self.graphs_progress.setValue(10)

            # Nettoyer les données : supprimer les lignes avec DateAna non valide
            df_analyses = df_analyses.dropna(subset=['DateAna'])
            df_analyses = df_analyses[df_analyses['DateAna'].str.match(r'^\d{4}-\d{2}-\d{2}.*')]

            # Convertir CdParametre et CdStationMesureEauxSurface en int64, gérer les valeurs non valides
            df_analyses = df_analyses.dropna(subset=['CdParametre', 'CdStationMesureEauxSurface'])
            try:
                df_analyses['CdParametre'] = pd.to_numeric(df_analyses['CdParametre'], errors='coerce').astype('Int64')
                df_analyses['CdStationMesureEauxSurface'] = pd.to_numeric(df_analyses['CdStationMesureEauxSurface'], errors='coerce').astype('Int64')
            except Exception as e:
                self.graphs_log.append(f"Erreur lors de la conversion des types CdParametre ou CdStationMesureEauxSurface: {str(e)}")
                raise
            invalid_rows = df_analyses[df_analyses['CdParametre'].isna() | df_analyses['CdStationMesureEauxSurface'].isna()]
            if not invalid_rows.empty:
                self.graphs_log.append(f"Avertissement: {len(invalid_rows)} lignes avec CdParametre ou CdStationMesureEauxSurface non valides supprimées.")
                df_analyses = df_analyses.dropna(subset=['CdParametre', 'CdStationMesureEauxSurface'])

            # Utiliser self.subst
            df_subst = pd.DataFrame.from_dict(self.subst, orient='index', columns=['LbLongParamètre', 'NQE-MA', 'NQE-CMA', 'Type_polluants'])

            # Créer df_analyses_LQ
            df = df_analyses.loc[:, ('CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'DateAna', 'CdParametre', 'LbLongParamètre', 'RsAna', 'LqAna')]
            df_analyses_LQ = pd.merge(df, df_subst[['NQE-MA', 'NQE-CMA']], left_on=['CdParametre'], right_index=True, how='left')
            df_analyses_LQ['Annee'] = df_analyses_LQ['DateAna'].str[:4]
            # Filtrer les années non valides
            liste_annees = sorted([str(y) for y in df_analyses_LQ['Annee'].unique() if pd.notna(y) and y.isdigit() and 2015 <= int(y) <= 2025])
            if not liste_annees:
                raise ValueError("Aucune année valide trouvée dans Analyses.csv.")
            self.graphs_log.append(f"Années trouvées: {liste_annees}")
            self.graphs_progress.setValue(20)

            # Vérifier les lignes avec DateAna invalide
            invalid_dates = df_analyses_LQ[df_analyses_LQ['Annee'].isna() | ~df_analyses_LQ['Annee'].astype(str).str.isdigit()]
            if not invalid_dates.empty:
                self.graphs_log.append(f"Avertissement: {len(invalid_dates)} lignes avec DateAna invalide ou manquante.")

            # Charger dico_dataframe depuis les CSV annuels
            dico_dataframe = {}
            for file in os.listdir(folder):
                if file.startswith("stations_nb_depassements_NQE_CMA_") and file.endswith(".csv"):
                    year = file.split("_")[-1].replace(".csv", "")
                    if year not in liste_annees:
                        self.graphs_log.append(f"Ignorer fichier {file}: année {year} non valide.")
                        continue
                    try:
                        df_year = pd.read_csv(os.path.join(folder, file), sep=';')
                        # Convertir CdParametre et CdStationMesureEauxSurface en int64 dans df_year
                        df_year = df_year.dropna(subset=['CdParametre', 'CdStationMesureEauxSurface'])
                        try:
                            df_year['CdParametre'] = pd.to_numeric(df_year['CdParametre'], errors='coerce').astype('Int64')
                            df_year['CdStationMesureEauxSurface'] = pd.to_numeric(df_year['CdStationMesureEauxSurface'], errors='coerce').astype('Int64')
                        except Exception as e:
                            self.graphs_log.append(f"Erreur lors de la conversion des types dans {file}: {str(e)}")
                            raise
                        invalid_year_rows = df_year[df_year['CdParametre'].isna() | df_year['CdStationMesureEauxSurface'].isna()]
                        if not invalid_year_rows.empty:
                            self.graphs_log.append(f"Avertissement: {len(invalid_year_rows)} lignes non valides dans {file} supprimées.")
                            df_year = df_year.dropna(subset=['CdParametre', 'CdStationMesureEauxSurface'])
                        dico_dataframe[f"stations_nb_depassements_NQE_CMA_{year}"] = [df_year, year]
                        self.graphs_log.append(f"Fichier chargé: {file}")
                    except Exception as e:
                        self.graphs_log.append(f"Erreur lors du chargement de {file}: {str(e)}")
            if not dico_dataframe:
                raise ValueError("Aucun fichier annuel valide trouvé.")
            self.graphs_progress.setValue(30)

            # Construction de Dico_dpt_year pour toutes les années
            Dico_dpt_year = {}
            for key in dico_dataframe.keys():
                df = dico_dataframe[key][0].copy()
                year = dico_dataframe[key][1]
                liste_id = ['CdParametre', 'LbLongParamètre', 'CdStationMesureEauxSurface', 'LbStationMesureEauxSurface']
                liste_dpt = df['CodeDepartement'].unique()
                for departement in liste_dpt:
                    if pd.isna(departement):
                        self.graphs_log.append(f"Département {departement} ignoré (valeur manquante).")
                        continue
                    key_D = f"{departement}_{year}"
                    Dico_dpt_year[key_D] = [departement, year, {}]
                    dff = df[df['CodeDepartement'] == departement]
                    if dff.empty:
                        self.graphs_log.append(f"Aucune donnée pour le département {departement} en {year}.")
                        continue
                    # Fusion avec types harmonisés
                    dff2 = pd.merge(df_analyses_LQ, dff, on=liste_id, how='inner')
                    dff2 = dff2.drop_duplicates()
                    dff3 = dff2.set_index(['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'CdParametre', 'LbLongParamètre'])
                    dff3 = pd.DataFrame(dff3.to_records()).drop_duplicates()
                    dff3 = dff3[['CdStationMesureEauxSurface', 'LbStationMesureEauxSurface', 'CdParametre', 'LbLongParamètre', 'Annee', 'DateAna', 'RsAna', 'NQE-MA', 'NQE-CMA']]

                    liste_station = dff['CdStationMesureEauxSurface'].unique()
                    liste_produit = dff['CdParametre'].unique()
                    Dico_stations_produits = {}
                    for sta in liste_station:
                        ds = dff3[dff3['CdStationMesureEauxSurface'] == sta]
                        if len(ds) == 0:
                            self.graphs_log.append(f"Aucune donnée pour la station {sta}.")
                            continue
                        nom_station = ds['LbStationMesureEauxSurface'].unique()[0] if len(ds['LbStationMesureEauxSurface'].unique()) > 0 else f"Station_{sta}"
                        for prod in liste_produit:
                            dp = ds[ds['CdParametre'] == prod]
                            if len(dp) == 0:
                                self.graphs_log.append(f"Aucune donnée pour la station {sta}, produit {prod}.")
                                continue
                            nom_produit = dp['LbLongParamètre'].unique()[0] if len(dp['LbLongParamètre'].unique()) > 0 else f"Produit_{prod}"
                            Dico_prod_year = {}
                            for y in liste_annees:
                                dpyear = dp[dp['Annee'] == y]
                                if len(dpyear) > 0:
                                    Dico_prod_year[y] = [dpyear]
                            Dico_stations_produits[f"{sta}_{prod}"] = [sta, nom_station, prod, nom_produit, Dico_prod_year]
                            # Export CSV par station-produit
                            titre_csv = f"Departement_{departement}_Station_{nom_station}_{sta}_et_produit_{nom_produit}_{prod}.csv"
                            try:
                                dp.to_csv(os.path.join(folder, titre_csv), sep=';', index=False, encoding='utf8')
                                self.graphs_log.append(f"CSV exporté: {titre_csv}")
                            except Exception as e:
                                self.graphs_log.append(f"Erreur lors de l'export CSV {titre_csv}: {str(e)}")
                        Dico_dpt_year[key_D][2] = Dico_stations_produits

            self.graphs_progress.setValue(40)
            self.graphs_log.append("Dico_dpt_year construit.")

            # Dictionnaire des couleurs par année
            Dico_color_year = {
                '2020': 'black', '2019': 'red', '2018': 'orange', '2017': 'yellow', '2016': 'purple',
                '2015': 'pink', '2014': 'limegreen', '2013': 'blue', '2021': 'green', '2022': 'cyan',
                '2023': 'magenta', '2024': 'brown', '2025': 'darkblue'
            }

            # Génération des graphiques
            total_pairs = sum(len(Dico_dpt_year[key_D][2]) for key_D in Dico_dpt_year)
            if total_pairs == 0:
                raise ValueError("Aucune paire station-substance valide trouvée pour générer les graphiques.")
            processed_pairs = 0

            # (Code jusqu'à la boucle for key_dpt in Dico_dpt_year.keys() inchangé, voir réponse précédente)

            for key_dpt in Dico_dpt_year.keys():
                dpt = Dico_dpt_year[key_dpt][0]
                year = Dico_dpt_year[key_dpt][1]
                dico_dpt = Dico_dpt_year[key_dpt][2]

                for key_sta_pro in dico_dpt.keys():
                    sta = dico_dpt[key_sta_pro][0]
                    nom_sta = dico_dpt[key_sta_pro][1]
                    prod = dico_dpt[key_sta_pro][2]
                    nom_pro = dico_dpt[key_sta_pro][3]
                    dico_sta_pro = dico_dpt[key_sta_pro][4]

                    # Préparer les données pour les graphiques
                    has_data = False
                    max_rs_ana = 0
                    months = range(1, 13)
                    ma_values = []
                    cma_values = []
                    labels = []
                    colors = []
                    has_monthly_data = False
                    all_years_data = []

                    for y in dico_sta_pro.keys():
                        dpyear = dico_sta_pro[y][0]
                        if dpyear.empty:
                            self.graphs_log.append(f"Données vides pour station {sta}, produit {prod}, année {y}")
                            continue
                        if dpyear['RsAna'].isna().all() or dpyear['DateAna'].isna().all():
                            self.graphs_log.append(f"Données invalides (RsAna ou DateAna manquants) pour station {sta}, produit {prod}, année {y}")
                            continue
                        dpyear['Month'] = pd.to_datetime(dpyear['DateAna'], errors='coerce').dt.month
                        if dpyear['Month'].isna().all():
                            self.graphs_log.append(f"Mois invalides pour station {sta}, produit {prod}, année {y}")
                            continue
                        has_data = True
                        if dpyear['RsAna'].max() > max_rs_ana:
                            max_rs_ana = dpyear['RsAna'].max()
                        depass_ma = dpyear[dpyear['RsAna'] > dpyear['NQE-MA']].groupby('Month').size().reindex(months, fill_value=0)
                        depass_cma = dpyear[dpyear['RsAna'] > dpyear['NQE-CMA']].groupby('Month').size().reindex(months, fill_value=0)
                        if depass_ma.sum() > 0 or depass_cma.sum() > 0:
                            has_monthly_data = True
                        ma_values.append(depass_ma.to_numpy())  # Convertir en NumPy explicitement
                        cma_values.append(depass_cma.to_numpy())  # Convertir en NumPy explicitement
                        labels.extend([f"{y} MA", f"{y} CMA"])
                        colors.extend([Dico_color_year.get(y, 'gray'), Dico_color_year.get(y, 'gray')])
                        all_years_data.append(dpyear)

                    if not has_data:
                        self.graphs_log.append(f"Aucune donnée valide pour générer les graphiques pour station {sta}, produit {prod}")
                        continue

                    # Concaténer toutes les données pour les graphiques combinés
                    combined_data = pd.concat(all_years_data)

                    # Graphique 1: Évolution des concentrations
                    if self.graph_types["Evolution"].isChecked():
                        plt.figure(figsize=(10, 6))
                        for y in dico_sta_pro.keys():
                            dpyear = dico_sta_pro[y][0]
                            if dpyear.empty or dpyear['RsAna'].isna().all() or dpyear['DateAna'].isna().all():
                                continue
                            color_year = Dico_color_year.get(y, 'gray')
                            date_x = pd.to_datetime(dpyear['DateAna'], errors='coerce')
                            rs_ana = dpyear['RsAna']
                            if date_x.isna().all() or rs_ana.isna().all():
                                continue
                            plt.scatter(date_x, rs_ana, c=color_year, label=y, s=50)

                        nqe_ma = combined_data['NQE-MA'].unique()[0] if not combined_data.empty else 0
                        nqe_cma = combined_data['NQE-CMA'].unique()[0] if not combined_data.empty else 0
                        if pd.notna(nqe_ma) and nqe_ma != 9999:
                            plt.axhline(y=nqe_ma, linestyle='--', color='blue', label='NQE-MA')
                        if pd.notna(nqe_cma) and nqe_cma != 9999:
                            plt.axhline(y=nqe_cma, linestyle='--', color='red', label='NQE-CMA')

                        if pd.notna(max_rs_ana) and max_rs_ana > 0:
                            plt.ylim(0, max_rs_ana * 1.1)
                        else:
                            plt.ylim(0, 1)

                        plt.title(f"Département: {dpt} Station: {nom_sta} ({sta})\nProduit: {nom_pro} ({prod}) - Évolution Concentrations")
                        plt.xlabel("Date")
                        plt.ylabel("Concentrations (µg/L)")
                        plt.legend()
                        plt.grid(True)
                        plt.tight_layout()

                        titre = f"Departement_{dpt}_Station_{nom_sta}_{sta}_Produit_{nom_pro}_{prod}_Evolution.png"
                        try:
                            plt.savefig(os.path.join(folder, titre))
                            self.graphs_log.append(f"Graphique évolution exporté: {titre}")
                        except Exception as e:
                            self.graphs_log.append(f"Erreur lors de l'export du graphique {titre}: {str(e)}")
                        plt.close()

                    # Graphique 2: Dépassements mensuels
                    if self.graph_types["Mensuel"].isChecked() and has_monthly_data:
                        plt.figure(figsize=(10, 6))
                        ma_values = np.array(ma_values)
                        cma_values = np.array(cma_values)
                        bottom = np.zeros(len(months))
                        for i, (ma, cma, year) in enumerate(zip(ma_values, cma_values, dico_sta_pro.keys())):
                            color_year = Dico_color_year.get(year, 'gray')
                            plt.bar(months, ma, bottom=bottom, color=color_year, label=f"{year} MA")
                            bottom += ma
                            plt.bar(months, cma, bottom=bottom, color=color_year, alpha=0.5, label=f"{year} CMA")
                            bottom += cma

                        plt.title(f"Département: {dpt} Station: {nom_sta} ({sta})\nProduit: {nom_pro} ({prod}) - Dépassements Mensuels")
                        plt.xlabel("Mois")
                        plt.ylabel("Nombre de Dépassements")
                        plt.xticks(months, ['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec'])
                        plt.legend()
                        plt.grid(True, axis='y')
                        plt.tight_layout()

                        titre_month = f"Departement_{dpt}_Station_{nom_sta}_{sta}_Produit_{nom_pro}_{prod}_Mensuel.png"
                        try:
                            plt.savefig(os.path.join(folder, titre_month))
                            self.graphs_log.append(f"Graphique mensuel exporté: {titre_month}")
                        except Exception as e:
                            self.graphs_log.append(f"Erreur lors de l'export du graphique {titre_month}: {str(e)}")
                        plt.close()

                    # Graphique 3: Heatmap des dépassements mensuels
                    if self.graph_types["Heatmap"].isChecked() and has_monthly_data:
                        monthly_data = pd.pivot_table(combined_data, index='Annee', columns='Month', values='RsAna', aggfunc='count', fill_value=0)
                        fig, ax = plt.subplots(figsize=(10, 6))
                        cax = ax.imshow(monthly_data.to_numpy(), cmap='YlOrRd', norm=mcolors.LogNorm(vmin=1, vmax=monthly_data.max().max() + 1))
                        ax.set_xticks(range(12))
                        ax.set_xticklabels(['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec'])
                        ax.set_yticks(range(len(monthly_data.index)))
                        ax.set_yticklabels(monthly_data.index)
                        plt.colorbar(cax, label='Nombre de Dépassements')
                        plt.title(f"Département: {dpt} Station: {nom_sta} - Heatmap Dépassements Mensuels")
                        titre_heatmap = f"Departement_{dpt}_Station_{nom_sta}_{sta}_Produit_{nom_pro}_{prod}_Heatmap.png"
                        try:
                            plt.savefig(os.path.join(folder, titre_heatmap))
                            self.graphs_log.append(f"Graphique heatmap exporté: {titre_heatmap}")
                        except Exception as e:
                            self.graphs_log.append(f"Erreur lors de l'export du graphique {titre_heatmap}: {str(e)}")
                        plt.close()

                    # Graphique 4: Boxplot de la variabilité mensuelle
                    if self.graph_types["Boxplot"].isChecked() and has_data:
                        plt.figure(figsize=(10, 6))
                        combined_data.boxplot(column='RsAna', by='Month', ax=plt.gca())
                        plt.axhline(y=nqe_ma, linestyle='--', color='blue', label='NQE-MA')
                        plt.axhline(y=nqe_cma, linestyle='--', color='red', label='NQE-CMA')
                        plt.title(f"Département: {dpt} Station: {nom_sta} - Variabilité Mensuelle des Concentrations")
                        plt.xlabel("Mois")
                        plt.ylabel("Concentrations (µg/L)")
                        plt.legend()
                        plt.suptitle('')
                        titre_boxplot = f"Departement_{dpt}_Station_{nom_sta}_{sta}_Produit_{nom_pro}_{prod}_Boxplot.png"
                        try:
                            plt.savefig(os.path.join(folder, titre_boxplot))
                            self.graphs_log.append(f"Graphique boxplot exporté: {titre_boxplot}")
                        except Exception as e:
                            self.graphs_log.append(f"Erreur lors de l'export du graphique {titre_boxplot}: {str(e)}")
                        plt.close()

                    # Graphique 5: Ligne de tendance (moyenne mobile)
                    if self.graph_types["Tendance"].isChecked() and has_data:
                        plt.figure(figsize=(10, 6))
                        dpyear_sorted = combined_data.sort_values('DateAna')
                        rolling_mean = dpyear_sorted['RsAna'].rolling(window=5, min_periods=1).mean().to_numpy()  # Convertir en NumPy
                        plt.plot(pd.to_datetime(dpyear_sorted['DateAna']).to_numpy(), rolling_mean, color='black', linestyle='-', linewidth=2, label='Moyenne Mobile')
                        plt.axhline(y=nqe_ma, linestyle='--', color='blue', label='NQE-MA')
                        plt.axhline(y=nqe_cma, linestyle='--', color='red', label='NQE-CMA')
                        plt.title(f"Département: {dpt} Station: {nom_sta} - Tendance des Concentrations")
                        plt.xlabel("Date")
                        plt.ylabel("Concentrations (µg/L)")
                        plt.legend()
                        plt.grid(True)
                        plt.tight_layout()
                        titre_tendance = f"Departement_{dpt}_Station_{nom_sta}_{sta}_Produit_{nom_pro}_{prod}_Tendance.png"
                        try:
                            plt.savefig(os.path.join(folder, titre_tendance))
                            self.graphs_log.append(f"Graphique ligne de tendance exporté: {titre_tendance}")
                        except Exception as e:
                            self.graphs_log.append(f"Erreur lors de l'export du graphique {titre_tendance}: {str(e)}")
                        plt.close()

                    # Graphique 6: Histogramme cumulatif
                    if self.graph_types["Cumulatif"].isChecked() and has_monthly_data:
                        plt.figure(figsize=(10, 6))
                        ma_values = np.array(ma_values)
                        cma_values = np.array(cma_values)
                        bottom = np.zeros(len(months))
                        for i, (ma, cma, year) in enumerate(zip(ma_values, cma_values, dico_sta_pro.keys())):
                            color_year = Dico_color_year.get(year, 'gray')
                            plt.bar(months, ma, bottom=bottom, color=color_year, label=f"{year} MA")
                            bottom += ma
                            plt.bar(months, cma, bottom=bottom, color=color_year, alpha=0.5, label=f"{year} CMA")
                            bottom += cma
                        ax1 = plt.gca()
                        ax2 = ax1.twinx()
                        # Conversion explicite en NumPy pour éviter l'erreur d'indexation
                        ma_sum = np.sum(ma_values, axis=0)
                        cma_sum = np.sum(cma_values, axis=0)
                        cum_ma = np.cumsum(ma_sum) / ma_sum.sum() * 100 if ma_sum.sum() > 0 else np.zeros(len(months))
                        cum_cma = np.cumsum(cma_sum) / cma_sum.sum() * 100 if cma_sum.sum() > 0 else np.zeros(len(months))
                        ax2.plot(months, cum_ma, color='blue', linestyle='--', label='Cumul MA (%)')
                        ax2.plot(months, cum_cma, color='red', linestyle='--', label='Cumul CMA (%)')
                        ax2.set_ylabel('Pourcentage Cumulatif')
                        ax1.set_title(f"Département: {dpt} Station: {nom_sta} - Dépassements Mensuels et Cumulatifs")
                        ax1.set_xlabel("Mois")
                        ax1.set_ylabel("Nombre de Dépassements")
                        ax1.set_xticks(months)
                        ax1.set_xticklabels(['Jan', 'Fev', 'Mar', 'Avr', 'Mai', 'Juin', 'Juil', 'Aou', 'Sep', 'Oct', 'Nov', 'Dec'])
                        ax1.legend(loc='upper left')
                        ax2.legend(loc='upper right')
                        ax1.grid(True, axis='y')
                        plt.tight_layout()
                        titre_cumulatif = f"Departement_{dpt}_Station_{nom_sta}_{sta}_Produit_{nom_pro}_{prod}_Cumulatif.png"
                        try:
                            plt.savefig(os.path.join(folder, titre_cumulatif))
                            self.graphs_log.append(f"Graphique cumulatif exporté: {titre_cumulatif}")
                        except Exception as e:
                            self.graphs_log.append(f"Erreur lors de l'export du graphique {titre_cumulatif}: {str(e)}")
                        plt.close()

                    processed_pairs += 1
                    self.graphs_progress.setValue(40 + int(60 * processed_pairs / total_pairs))

            self.graphs_progress.setValue(100)
            self.graphs_log.append(f"Graphiques générés pour {processed_pairs} paires station-substance.")
            QMessageBox.information(self, "Succès", f"Graphiques générés pour {processed_pairs} paires. Fichiers PNG exportés dans le dossier.")
        except Exception as e:
            self.graphs_log.append(f"Erreur: {str(e)}")
            QMessageBox.critical(self, "Erreur", str(e))