# -*- coding: utf-8 -*-
# Python 3
"""
/***************************************************************************
 plugin Boite à Outil Administateur de Données
Produit une copie locale d'un projet donné (couches et projet QGIS) ainsi
que des tableaux de rapport de dernière copie/mise à jour des couches du projet et du projet lui-même
Vérifie ensuite au lancement si une couche ou le projet a été mis à jour pour garder à jour la version locale.
                              -------------------
        begin                : 2025-08-28
        deployment           :
        copyright            : (C) 2025 par Jean-Christophe Baudin
        email                : jean-christophe.baudin@cote-dor.gouv.fr
 ***************************************************************************/
# icônes produites par M. Julie Briand (Bachelor of Technology in Multimedia and Internet)
# contact: julie.briand35@gmail.com
/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtWidgets import QAction, QMessageBox, QToolButton, QMenu
from qgis.core import QgsProject
from qgis.PyQt.QtCore import *
from qgis.PyQt.QtGui import *
from .data_manager_BAO_ADL import DataManager_BAO_ADL
from .About_BAO_ADL import AboutDialog_BAO_ADL
import os

from .TELECHARGEMENTS.TELECHARGEMENTS_Import_Naïades_Pesticides_Etats_Eco2 import ImportNaïadesPesticidesEtatsEcoDialog
from .STATISTIQUES.STATISTIQUES_ESSENCE_BDForet_R import MainPluginForetParESSENCE
from .TRAITEMENTS.TRAITEMENTS_Preparation_Archivage import MainPluginPreparationArchivage
from .TRAITEMENTS.TRAITEMENTS_Activation_Archivage import MainPluginActivationArchivage
from .TRAITEMENTS.TRAITEMENTS_Analyseur_de_structure_de_fichier_de_donnees import MainPluginAnalyseurDeStructure
from .TRAITEMENTS.TRAITEMENTS_CarteDynamiqueAgricole import CarteDynamiqueAgricoleDialog

# Fonction de reconstruction du chemin absolu vers la ressource image
def resolve(name, basepath=None):
    if not basepath:
        basepath = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(basepath, name)

def getThemeIcon(theName):
    basepath = os.path.dirname(os.path.realpath(__file__))
    myDefPathIcons = os.path.join(basepath, "icons", theName)
    return myDefPathIcons if QFile.exists(myDefPathIcons) else ""

def get_plugin_directory():
    current_file_path = os.path.abspath(__file__)
    plugin_directory = os.path.dirname(current_file_path)
    return plugin_directory

class MainPlugin_BAO_ADL(object):

    def __init__(self, iface):
        self.name = "boite_a_outil_ADL"
        # Initialise et sauvegarde l'interface QGIS en cours
        self.iface = iface
        self.dossier_plugin = os.path.dirname(__file__)
        # Création d'une instance de DataManager
        self.data_manager = DataManager_BAO_ADL()
    
    def initGui(self):
        # Création du menu principal
        self.menu = QMenu("boite_a_outil_ADL", self.iface.mainWindow())

        # Création du bouton dans la barre d'outils
        self.tool_button = QToolButton()
        self.tool_button.setIcon(QIcon(getThemeIcon("BAO_ADL_icon.jpg")))
        self.tool_button.setPopupMode(QToolButton.InstantPopup)
        self.tool_button.setToolTip("Local Data Administrator Workbench")

        # Création d'une nouvelle QToolBar pour le plugin
        self.toolbar = self.iface.addToolBar("boite_a_outil_ADL")
        self.toolbar.setObjectName("boite_a_outil_ADL_Toolbar")
        self.toolbar.addWidget(self.tool_button)
 
        # Déclaration de l'icône about
        about_icon = QIcon(getThemeIcon("about.png"))
        
        ##########################################################################################
        #      1)  Etape de création des icones et de déclaration des actions
        ##########################################################################################
        
        #-----------------------------------------------------
        # Définition des icônes et des  actions  TELECHARGEMENTS
        #-----------------------------------------------------
        
        TELECHARGEMENTS_icon = QIcon(getThemeIcon("TELECHARGEMENTS.jpg"))
        
        self.pesticides_etat_eco_naiades_action = QAction(TELECHARGEMENTS_icon, "Pesticides Etat Eco Naiades", self.iface.mainWindow())
        self.pesticides_etat_eco_naiades_action.setObjectName("PESTICIDES_ETAT_ECO_NAIADES")

        #-----------------------------------------------------
        # Définition des icônes et des  actions  GBDD
        #-----------------------------------------------------
        gbdd_icon = QIcon(getThemeIcon("GBDD.jpg"))
       
        self.GBDD_Import_en_masse_depuis_un_dossier_action = QAction(gbdd_icon, "imports en masse dans gb_ddt21", self.iface.mainWindow())
        self.GBDD_Import_en_masse_depuis_un_dossier_action.setObjectName("imports_en_masse_dans_gb_ddt21")
        
        
        #-----------------------------------------------------
        # Définition des icônes et des  actions  TRAITEMENTS
        #-----------------------------------------------------
        traitements_icon = QIcon(getThemeIcon("TRAITEMENTS.jpg"))
        
        self.terres_a_disposition_action = QAction(traitements_icon, "Terres a disposition", self.iface.mainWindow())
        self.terres_a_disposition_action.setObjectName("Terres_a_disposition")

        self.fabrication_couches_bassins_de_mobilites_action= QAction(traitements_icon, "Fabrication couche des bassins de mobilité", self.iface.mainWindow())
        self.fabrication_couches_bassins_de_mobilites_action.setObjectName("Fabrication couche des bassins de mobilité")
        
        self.carte_dynamique_action = QAction(traitements_icon, "Carte Dynamique Agricole", self.iface.mainWindow())
        self.carte_dynamique_action.setObjectName("carte_dynamique_agricole")
      
        # Ajout de l'action pour ConvertMapInfoToShapefile
        convert_mapinfo_icon = QIcon(getThemeIcon("TRAITEMENTS.jpg"))  # Assurez-vous que cette icône existe
        self.traitements_convert_mapinfo_action = QAction(convert_mapinfo_icon, "Convertir MapInfo en Shapefile", self.iface.mainWindow())
        self.traitements_convert_mapinfo_action.setObjectName("TRAITEMENTS_ConvertMapInfo")
        
        # Ajout de l'action pour ConvertGPKGToShapefile
        convert_gpkg_icon = QIcon(getThemeIcon("TRAITEMENTS.jpg"))  # Assurez-vous que cette icône existe
        self.traitements_convert_gpkg_action = QAction(convert_gpkg_icon, "Convertir GPKG en Shapefile", self.iface.mainWindow())
        self.traitements_convert_gpkg_action.setObjectName("TRAITEMENTS_ConvertGPKG")
   
        self.traitements_activation_archivage_action = QAction(traitements_icon, "Activation_Archivage", self.iface.mainWindow())
        self.traitements_activation_archivage_action.setObjectName("Activation Archivage")
        
        self.traitements_preparation_archivage_action = QAction(traitements_icon, "Préparation_Archivage", self.iface.mainWindow())
        self.traitements_preparation_archivage_action.setObjectName("Preparation Archivage")

        self.analyseur_de_structure_action = QAction(traitements_icon, "Analyseur de Structure de Fichier de Données", self.iface.mainWindow())
        self.analyseur_de_structure_action.setObjectName("TRAITEMENTS_Analyseur_de_structure_de_fichier_de_donnée")
      
        
        #-----------------------------------------------------
        # Définition des icônes et des  actions  BILANS
        #-----------------------------------------------------
        bilans_icon = QIcon(getThemeIcon("BILANS.jpg"))
        
        # Ajout de l'action pour Bilan Projet QGIS
        bilan_projet_QGIS_icon=QIcon(getThemeIcon("BILANS.jpg")) 
        self.bilans_projet_qgis_action = QAction(bilan_projet_QGIS_icon,"Bilan des Projets QGIS", self.iface.mainWindow())
        self.bilans_projet_qgis_action.setObjectName("BILANS_Projet_QGIS")
        # Définition de l'icône et de l'action pour Bilan Treemap
        bilan_projet_QGIS_Treemap_icon=QIcon(getThemeIcon("BILANS.jpg"))
        self.bilans_treemap_action = QAction(bilan_projet_QGIS_Treemap_icon,"Bilan des volumes - Treemap", self.iface.mainWindow())
        self.bilans_treemap_action.setObjectName("BILANS_Treemap")
        # Définition de l'icône et de l'action TREEMAP_ZONES_PROTECT
        CALCUL_ZONES_PROTECT_icon = QIcon(getThemeIcon("BILANS.jpg"))  
        self.calcul_zones_protect_action = QAction(CALCUL_ZONES_PROTECT_icon, "Calcul des Zones de Protection", self.iface.mainWindow())
        self.calcul_zones_protect_action.setObjectName("CALCUL_ZONES_PROTECT")
        
        #-----------------------------------------------------
        # Définition des icônes et des  actions  STATISTIQUES
        #-----------------------------------------------------
        statistiques_icon = QIcon(getThemeIcon("STATISTIQUES.jpg"))
          
        self.foret_par_essence_action = QAction(statistiques_icon, "Foret_Par_ESSENCE", self.iface.mainWindow())
        self.foret_par_essence_action.setObjectName("FORET_PAR_ESSENCE")
        
        Treemap_icon1= QIcon(getThemeIcon("Treemap_icon1.png"))
        self.treemap_action = QAction(Treemap_icon1, "treemap", self.iface.mainWindow())
        self.treemap_action.setObjectName("Treemap")

        self.about_action = QAction(about_icon, "À propos", self.iface.mainWindow())
        self.about_action.setObjectName("about")
        
        ######################################################################################################
        ####  2)  ETAPE DE Construction des sous-menus par ajout de l'action au sous-menu correspondant
        ######################################################################################################
        
        # Ajout de l'action au sous-menu TELECHARGEMENTS
        self.sousmenu_TELECHARGEMENTS = QMenu("Téléchargements de données", self.menu)
        self.sousmenu_TELECHARGEMENTS.setIcon(TELECHARGEMENTS_icon)
        self.sousmenu_TELECHARGEMENTS.addAction(self.pesticides_etat_eco_naiades_action)

        
        # Ajout de l'action au sous-menu GBDD Gestion Base de Données
         
        self.sousmenu_GBDD = QMenu("imports en masse des couches d'un dossier dans la base de données gb_ddt21", self.menu)
        self.sousmenu_GBDD.setIcon(gbdd_icon)
        self.sousmenu_GBDD.addAction(self.GBDD_Import_en_masse_depuis_un_dossier_action)
        
       
        
        # Ajout de l'action au sous-menu TRAITEMENTS
        self.sousmenu_TRAITEMENTS = QMenu("Outils de traitements de données", self.menu)
        self.sousmenu_TRAITEMENTS.setIcon(traitements_icon)
        self.sousmenu_TRAITEMENTS.addAction(self.traitements_convert_mapinfo_action)
        self.sousmenu_TRAITEMENTS.addAction(self.traitements_convert_gpkg_action)
        self.sousmenu_TRAITEMENTS.addAction(self.traitements_preparation_archivage_action)
        self.sousmenu_TRAITEMENTS.addAction(self.traitements_activation_archivage_action)
        self.sousmenu_TRAITEMENTS.addAction(self.analyseur_de_structure_action)
        self.sousmenu_TRAITEMENTS.addAction(self.carte_dynamique_action)
        self.sousmenu_TRAITEMENTS.addAction(self.fabrication_couches_bassins_de_mobilites_action)
        self.sousmenu_TRAITEMENTS.addAction(self.terres_a_disposition_action)
    

        # Ajout de l'action au sous-menu BILANS
        self.sousmenu_BILANS = QMenu("Bilans administration de données", self.menu)
        self.sousmenu_BILANS.setIcon(bilans_icon)
        self.sousmenu_BILANS.addAction(self.bilans_projet_qgis_action)
        self.sousmenu_BILANS.addAction(self.bilans_treemap_action)
        self.sousmenu_BILANS.addAction(self.calcul_zones_protect_action)
        
        # Ajout de l'action au sous-menu STATISTIQUES
        self.sousmenu_STATISTIQUES = QMenu("Statistiques administration de données", self.menu)
        self.sousmenu_STATISTIQUES.setIcon(statistiques_icon)
        self.sousmenu_STATISTIQUES.addAction(self.foret_par_essence_action)
        self.sousmenu_STATISTIQUES.addAction(self.treemap_action)
       
        # Ajout des sous-menus au menu principal
        self.menu.addMenu(self.sousmenu_TELECHARGEMENTS)
        self.menu.addMenu(self.sousmenu_GBDD)
        self.menu.addMenu(self.sousmenu_TRAITEMENTS)
        self.menu.addMenu(self.sousmenu_BILANS)
        self.menu.addMenu(self.sousmenu_STATISTIQUES)
        self.menu.addSeparator()
        self.menu.addAction(self.about_action)

        # Associer le menu au bouton
        self.tool_button.setMenu(self.menu)

        # Ajouter le menu à la barre de menus de QGIS
        menu_bar = self.iface.mainWindow().menuBar()
        actions = menu_bar.actions()
        last_action = actions[-5]  # Insérer avant le 5ème menu en partant de la fin
        menu_bar.insertMenu(last_action, self.menu)

        ######################################################################################################
        ####  3) ETAPE DE connexion de l'action à la fonction
        ######################################################################################################
        self.pesticides_etat_eco_naiades_action.triggered.connect(self.on_pesticides_etat_eco_naiades)
    
        self.GBDD_Import_en_masse_depuis_un_dossier_action.triggered.connect(self.on_GBDD_Import_en_masse_depuis_un_dossier)
        
           
        self.traitements_convert_mapinfo_action.triggered.connect(self.on_traitements_convert_mapinfo)
        self.traitements_convert_gpkg_action.triggered.connect(self.on_traitements_convert_gpkg)
        self.traitements_preparation_archivage_action.triggered.connect(self.on_traitements_preparation_archivage)
        self.traitements_activation_archivage_action.triggered.connect(self.on_traitements_activation_archivage)
        self.analyseur_de_structure_action.triggered.connect(self.on_analyseur_de_structure)
        self.carte_dynamique_action.triggered.connect(self.on_carte_dynamique_agricole)
        self.fabrication_couches_bassins_de_mobilites_action.triggered.connect(self.on_Fabrication_couches_Bassins_de_Mobilites)
        self.terres_a_disposition_action.triggered.connect(self.on_terres_a_disposition)
        
   
        self.bilans_projet_qgis_action.triggered.connect(self.on_bilans_projet_qgis)
        self.bilans_treemap_action.triggered.connect(self.on_bilans_treemap)
        self.calcul_zones_protect_action.triggered.connect(self.on_calcul_zones_protect)
        
        self.foret_par_essence_action.triggered.connect(self.on_statistiques_foret_par_essence)
        self.treemap_action.triggered.connect(self.on_statistiques_treemap)
        
        self.about_action.triggered.connect(self.doInfo)

    
            
    def unload(self):
        # Supprimer le widget (QToolButton) de la toolbar
        #_self.toolbar.removeWidget(self.tool_button)
      
        # Supprimer la toolbar
        self.iface.mainWindow().removeToolBar(self.toolbar)
       
        
        # Retirer l'action du menu
        self.iface.removePluginMenu("GBDD", self.import_admin_express_action)
      
      
        self.iface.removePluginMenu("TRAITEMENTS", self.traitements_preparation_archivage_action)
        self.iface.removePluginMenu("TRAITEMENTS", self.traitements_activation_archivage_action)
        self.iface.removePluginMenu("TRAITEMENTS", self.analyseur_de_structure_action)
        self.iface.removePluginMenu("TELECHARGEMENTS", self.pesticides_etat_eco_naiades_action)
        self.iface.removePluginMenu("TRAITEMENTS", self.carte_dynamique_action)
        self.iface.removePluginMenu("TRAITEMENTS", self.un_paquet_gpkg_action)
       
        # Retirer le menu de la barre de menus
        # Supprimer le menu
        self.menu.deleteLater()

    def doInfo(self):
        dlg = AboutDialog_BAO_ADL()
        dlg.exec_()

    def run(self):
        basepath = get_plugin_directory()
        data_dir = os.path.join(basepath, 'projet_local')

        if not os.path.exists(data_dir):
            QgsProject.instance().clear()
            os.makedirs(data_dir)
            QMessageBox.information(None, "Information", "Première utilisation : choisissez un projet QGIS.")
            self.showInitialDialog()
        else:
            self.showSecondDialog()

    def showInitialDialog(self):
        try:
            from .InitialDialog_BAO_ADL import InitialDialog_BAO_ADL
            self.dialogInitial = InitialDialog_BAO_ADL(self.data_manager)
            self.dialogInitial.exec_()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer InitialDialog_BAO_ADL: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")

    def showSecondDialog(self):
        try:
            from .SecondDialog_BAO_ADL import SecondUseDialog_BAO_ADL
            self.dialogSecond = SecondUseDialog_BAO_ADL(self.data_manager)
            self.dialogSecond.exec_()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer SecondUseDialog_BAO_ADL: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")


    ######################################################################################################
    ####  4) ETAPE de définition des méthodes pour instancier les modules
    ####
    ####  On place le bloc avec ceux de son menu (TElECHARMENTS, BILANS, ...etc)
    ####
    ######################################################################################################
   
    ##---------------------------------------------------------------------------------------------
    #  Méthodes qui instancient les modules TELECHARGEMENTS
    ##---------------------------------------------------------------------------------------------
      
    def on_pesticides_etat_eco_naiades(self):
        try:
            from .TELECHARGEMENTS.TELECHARGEMENTS_Import_Naïades_Pesticides_Etats_Eco2 import ImportNaïadesPesticidesEtatsEcoDialog
            pesticides_etat_eco_naiades_plugin = ImportNaïadesPesticidesEtatsEcoDialog(self.iface)
            pesticides_etat_eco_naiades_plugin.exec_()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer ImportNaïadesPesticidesEtatsEcoDialog: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")

      
   
    
    ##---------------------------------------------------------------------------------------------
    #  Méthodes qui instancient les modules GBDD
    ##---------------------------------------------------------------------------------------------
 
    def on_GBDD_Import_en_masse_depuis_un_dossier (self):
        try:
            from .GBDD.GBDD_Import_en_masse_depuis_un_dossier import ImportFromFolderDialog
            dialog = ImportFromFolderDialog(self.iface.mainWindow())
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue : {e}")
   
    
    ##------------------------------------------------------------------------------------------------------------    
    #  Méthodes qui instancient les modules les TRAITEMENTS de TYPE ET de ETL - Extract Transform Load 
    ##--------------------------------------------------------------------------------------------------------------        
    
    
    def on_terres_a_disposition(self):
        try:
            from .TRAITEMENTS.TRAITEMENTS_Terres_a_disposition import MainPluginTerresADisposition
            terres_a_disposition_plugin = MainPluginTerresADisposition(self.iface)
            terres_a_disposition_plugin.run()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginTerresADisposition: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")
        
    def on_carte_dynamique_agricole(self):
        try:
            from .TRAITEMENTS.TRAITEMENTS_CarteDynamiqueAgricole import CarteDynamiqueAgricoleDialog
            dialog = CarteDynamiqueAgricoleDialog()
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue : {e}")
    
    def on_Fabrication_couches_Bassins_de_Mobilites(self):
        try:
            import os
            print("Chemin actuel:", os.path.dirname(os.path.abspath(__file__)))
            print("Contenu du dossier TRAITEMENTS:", os.listdir(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'TRAITEMENTS')))
            from .TRAITEMENTS.TRAITEMENTS_Fabrication_couches_Bassins_de_Mobilites import MainPluginBassinsMobilite
            main_plugin_bpc = MainPluginBassinsMobilite(self.iface)
            main_plugin_bpc.initGui()
            main_plugin_bpc.run()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginBassinsMobilite: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")


    def on_traitements_convert_mapinfo(self):
        try:
            from .TRAITEMENTS.TRAITEMENTS_BAO_ADL_ConvertMapInfoToShapefile import MainPluginConvertMapInfoToShapefile
            convert_plugin = MainPluginConvertMapInfoToShapefile(self.iface)
            convert_plugin.run()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginConvertMapInfoToShapefile: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")

    def on_traitements_convert_gpkg(self):
        try:
            from .TRAITEMENTS.TRAITEMENTS_ConvertGPKGToShapefile import MainPluginConvertGPKGToShapefile
            convert_plugin = MainPluginConvertGPKGToShapefile(self.iface)
            convert_plugin.run()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginConvertGPKGToShapefile: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")
            
    
    def on_traitements_preparation_archivage(self):
        try:
            from .TRAITEMENTS.TRAITEMENTS_Preparation_Archivage import MainPluginPreparationArchivage
            Preparation_Archivage_plugin = MainPluginPreparationArchivage(self.iface)
            Preparation_Archivage_plugin.run()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginPreparationArchivage: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")


    def on_traitements_activation_archivage(self):
        try:
            from .TRAITEMENTS.TRAITEMENTS_Activation_Archivage import MainPluginActivationArchivage
            Activation_Archivage_plugin = MainPluginActivationArchivage(self.iface)
            Activation_Archivage_plugin.run()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginActivationArchivage: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")
    
   
    def on_analyseur_de_structure(self):
        try:
            from .TRAITEMENTS.TRAITEMENTS_Analyseur_de_structure_de_fichier_de_donnees import MainPluginAnalyseurDeStructure
            analyseur_plugin = MainPluginAnalyseurDeStructure(self.iface)
            analyseur_plugin.run()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginAnalyseurDeStructure: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")
    
    ##------------------------------------------------------------------------------------------------------------    
    #  Méthodes qui instancient les modules de type BILANS
    ##--------------------------------------------------------------------------------------------------------------   


    def on_bilans_projet_qgis(self):
        try:
            from .BILANS.BILAN_projet_QGIS import MainPluginBilanProjetQGIS
            bilan_plugin = MainPluginBilanProjetQGIS(self.iface)
            bilan_plugin.run()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginBilanProjetQGIS: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")

    def on_bilans_treemap(self):
        try:
            from .BILANS.BILAN_treemap import MainPluginBilanTreemap
            treemap_plugin = MainPluginBilanTreemap(self.iface)
            treemap_plugin.run()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginBilanTreemap: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")
            
    # 2. Ajout de la méthode pour instancier le module
    def on_calcul_zones_protect(self):
        try:
            from .BILANS.BILANS_ZonesProtect import TreemapZonesProtectDialog
            dialog = TreemapZonesProtectDialog(self.iface.mainWindow())
            dialog.exec_()
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")

    ##------------------------------------------------------------------------------------------------------------    
    #  Méthodes qui instancient les modules de type STATISTIQUES
    ##-------------------------------------------------------------------------------------------------------------- 

    def on_statistiques_foret_par_essence(self):
        try:
            from .STATISTIQUES.STATISTIQUES_ESSENCE_BDForet_R import MainPluginForetParESSENCE
            foret_par_essence_plugin = MainPluginForetParESSENCE(self.iface)
            foret_par_essence_plugin.run()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginForetParESSENCE: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")
            
    def on_statistiques_treemap(self):
        try:
            from .STATISTIQUES.STATISTIQUES_treemap import MainPluginTreemap
            treemap = MainPluginTreemap(self.iface)
            treemap.run()
        except ImportError as e:
            QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginTreemap: {e}")
        except Exception as e:
            QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")       