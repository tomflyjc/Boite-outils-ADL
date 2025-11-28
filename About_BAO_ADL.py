from qgis.PyQt.QtCore import QFile, QSize, Qt
from qgis.PyQt.QtGui import QFont, QPixmap
from qgis.PyQt.QtWidgets import (
    QVBoxLayout, QLabel, QTextEdit, QPushButton, QDialog, QApplication,
    QTabWidget, QWidget, QScrollArea
)
import os
import sys

def get_theme_icon(icon_name):
    """Retourne le chemin absolu d'une icône si elle existe."""
    basepath = os.path.dirname(os.path.realpath(__file__))
    icon_path = os.path.join(basepath, "icons", icon_name)
    return icon_path if QFile.exists(icon_path) else None

class AboutDialog_BAO_ADL(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("À propos de la Boite à outils pour l'administration de données")
        self.setFixedSize(900, 700)
        self.setWindowFlags(self.windowFlags() & ~Qt.WindowContextHelpButtonHint)

        # Création du QTabWidget
        self.tabs = QTabWidget()
        self.tab_info = QWidget()
        self.tab_new_module = QWidget()
        self.tab_integration = QWidget()
        self.tab_data_manager = QWidget()  # Déclaration du widget pour l'onglet DataManager

        # Configuration des onglets
        self.setup_info_tab()
        self.setup_new_module_tab()
        self.setup_integration_tab()
        self.setup_data_manager_tab()  # Appel de la méthode de configuration
        
        # Ajout des onglets
        self.tabs.addTab(self.tab_info, "Information")
        self.tabs.addTab(self.tab_new_module, "Créer un nouveau module avec l'IA")
        self.tabs.addTab(self.tab_integration, "Intégration d'un nouveau module")
        self.tabs.addTab(self.tab_data_manager, "Gestion des données globales avec DataManager")  # Ajout
         
        # Layout principal
        layout = QVBoxLayout()
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def setup_info_tab(self):
        """Configurer l'onglet Information."""
        layout = QVBoxLayout()

        # Ajout de l'icône
        icon_path = get_theme_icon("BAO_ADL_icon.jpg")
        if icon_path:
            icon_label = QLabel()
            icon_pixmap = QPixmap(icon_path).scaledToWidth(100, Qt.SmoothTransformation)
            icon_label.setPixmap(icon_pixmap)
            icon_label.setAlignment(Qt.AlignCenter)
            layout.addWidget(icon_label)

        # Ajout du titre
        title_label = QLabel("Boite à outils pour l'administration de données locales")
        title_font = QFont()
        title_font.setPointSize(14)
        title_font.setBold(True)
        title_label.setFont(title_font)
        title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(title_label)

        # Ajout de la version
        version_label = QLabel("Version 1.0.1 (23 septembre 2025)")
        version_font = QFont()
        version_font.setPointSize(10)
        version_font.setItalic(True)
        version_label.setFont(version_font)
        version_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(version_label)

        # Ajout de la description
        description = QTextEdit()
        description.setReadOnly(True)
        description.setPlainText(self._get_description_text())
        description.setFont(QFont("Sans Serif", 10))
        layout.addWidget(description)

        # Ajout du bouton OK
        ok_button = QPushButton("OK")
        ok_button.setFixedWidth(100)
        ok_button.clicked.connect(self.accept)
        ok_button_layout = QVBoxLayout()
        ok_button_layout.setAlignment(Qt.AlignCenter)
        ok_button_layout.addWidget(ok_button)
        layout.addLayout(ok_button_layout)

        self.tab_info.setLayout(layout)

    def setup_new_module_tab(self):
        """Configurer l'onglet Créer un nouveau module avec l'IA."""
        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout()

        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setPlainText(self._get_new_module_text())
        instructions.setFont(QFont("Sans Serif", 10))
        content_layout.addWidget(instructions)

        content.setLayout(content_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.tab_new_module.setLayout(layout)

    def setup_integration_tab(self):
        """Configurer l'onglet Intégration d'un nouveau module."""
        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout()

        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setPlainText(self._get_integration_text())
        instructions.setFont(QFont("Sans Serif", 10))
        content_layout.addWidget(instructions)

        content.setLayout(content_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.tab_integration.setLayout(layout)


    def setup_data_manager_tab(self):
        """Configurer l'onglet Gestion des données globales avec DataManager."""
        layout = QVBoxLayout()
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        content_layout = QVBoxLayout()

        instructions = QTextEdit()
        instructions.setReadOnly(True)
        instructions.setPlainText(self._get_data_manager_text())
        instructions.setFont(QFont("Sans Serif", 10))
        content_layout.addWidget(instructions)

        content.setLayout(content_layout)
        scroll.setWidget(content)
        layout.addWidget(scroll)

        self.tab_data_manager.setLayout(layout)
        
    def _get_description_text(self):
        """Retourne le texte pour la description."""
        return """
Boite à outils pour l'administration de données est un plugin conçu pour fournir une série d'outils pour l'administration de données locales dans QGIS.

Notre travail repose souvent sur des scripts qui sont autant d'outils locaux de type "ETL" (Extact-Transform-Load). 
L'Extraction-Transformation-Chargement est en somme à la base de l'administration locale de données.

Comment regrouper et faciliter non seulement la création et l'utilisation de tels outils ?

Ce plugin est une tentative élaborée au niveau du Bureau Gestion et Analyse Territoriale de la Direction Départementale des Territoires de Côte-d'Or pour y parvenir.
On utilise pour se faire le langage python avec la seule richesse des fonctionnalités de QGIS ("PyQGIS") et l'assistance de l'Intelligence Artificielle.
Ce plugin est pensé pour permettre à chacun, même sans notion du langage python, de créer son outil grâce à l'IA.
Un tel outil sera ici appelé module du plugin Boite_a_outils_ADL.

L'onglet "Créer un nouveau module avec l'IA" fournit pour ce faire le prompt nécessaire à l'IA.
Nous recommandons pour des raisons de réproductibilité l'utilisation de MISTRAL AI.
Nous rappelons pour des raisons de sécurité de ne jamais fournir à une IA aucune information personnelle ou nominative et à fortiori "sensible" !

L'Onglet "intégration d'un nouveau module" indique où placer dans le code principal du plugin (fichier Boite_a_outils_ADL.py), les lignes de code nécessaires pour l'ajout d'un nouveau module.
Si vous n'êtes pas familier des interfaces de développment, nous recommandons l'utilisation du logiciel de traitement de texte Notepad+ pour "ouvrir" le fichier Boite_a_outils_ADL.py et le modifier.
Notepad+ permet en effet dans son onglet "Langage" la sélection du langage Python.
Ceci rend plus aisé la lecture du code par une mise en forme idoine et vous assure du respect des indentations propres et nécessaires au langage Python.

L'Onglet "Gestion des données globales avec DataManager"  présente un script particuliers du plugin qui vise à permettre des développements futurs de modules "interconnectés".
Il d'agit de pouvoir manipuler des variables entre modules, d'un module à l'autre. 
Cet onglet décrit comment l'utiliser.

Ce plugin ne fait pas partie du moteur de QGIS. 
Toute demande est à adresser à l'auteur pour le corps de l'outil et les modules sauf autre mention:

    Jean-Christophe Baudin
    DDT21 SUCAT/BGAT
    jean-christophe.baudin@cote-dor.gouv.fr



        """

    def _get_new_module_text(self):
        """Retourne le texte pour la création d'un nouveau module."""
        return """
Le texte ci-dessous est à modifier dans sa partie 5:
"Je souhaite que tu génères un module pour mon plugin avec les spécifications suivantes:"
Cette partie devra détailler tous les éléments de votre traitements:
- données en entrée - forme de la demande de ces données - tâches élémentaires séquencées à accomplir 
- données en sortie avec leurs spécificités - mise en forme, format, encodage, système de projection, etc...
Ainsi modifié et recopié à partir du titre "Prompt... " , fourni à une IA, il doit générer le code d'un module opérationnel pour le plugin.

Prompt pour la génération d'un module pour Boite_a_outils_ADL

Contexte :
Je développe un plugin QGIS nommé Boite_a_outils_ADL, qui est organisé en modules thématiques (BILANS, TRAITEMENTS, TELECHARGEMENTS, etc.). Chaque module suit une structure standardisée avec deux onglets : Instructions et Analyse.

Je souhaite que tu m'aides à générer un nouveau module pour ce plugin. Voici les éléments nécessaires pour que tu puisses me fournir un code complet et prêt à l'emploi.

1. Structure du Module
Le module doit suivre la structure standard avec deux onglets :
    • setup_instructions_tab(self) : Onglet "Instructions" contenant une description détaillée du module, des données nécessaires, et des instructions d'utilisation.
    • setup_operations_tab(self) : Onglet "Traitement" contenant l'interface utilisateur pour interagir avec le module (boutons, champs de saisie, visualisations, etc.).

Exemple de structure de base :

class NouveauModuleDialog(QDialog):
    def __init__(self, parent=None):
        super(NouveauModuleDialog, self).__init__(parent)
        self.setWindowTitle("Titre du Module")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        # Onglet Instructions
        self.instructions_tab = QWidget()
        self.setup_instructions_tab()
        # Onglet Traitement
        self.analysis_tab = QWidget()
        self.setup_operations_tab()
        self.tabs.addTab(self.instructions_tab, "Instructions")
        self.tabs.addTab(self.analysis_tab, "Traitement")
        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def setup_instructions_tab(self):
        \"\"\"Configurer l'onglet Instructions avec une description détaillée.\"\"\"
        layout = QVBoxLayout()
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)
        instructions = \"\"\"
<h2>Titre du Module</h2>
<h3>Fonctionnalités :</h3>
<p>Description des fonctionnalités du module...</p>
<h3>Données nécessaires :</h3>
<p>Liste des données ou fichiers requis...</p>
<h3>Utilisation :</h3>
<ol>
    <li>Étape 1...</li>
    <li>Étape 2...</li>
</ol>
\"\"\"
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_operations_tab(self):
        \"\"\"Configurer l'onglet Traitement avec l'interface utilisateur.\"\"\"
        layout = QVBoxLayout()
        # Ajouter ici les widgets pour l'interface de Traitement (boutons, champs de saisie, etc.)
        self.analysis_tab.setLayout(layout)

2. Intégration au Plugin Principal
Pour intégrer le module au plugin principal (Boite_a_outils_ADL.py), il faut ajouter :
    1. L'import du module dans les imports du fichier principal.
    2. Une méthode pour instancier et exécuter le module.
    3. L'action et l'icône pour le menu.
    4. La connexion de l'action au menu correspondant.

Exemple de code à ajouter dans Boite_a_outils_ADL.py :

# 1. Ajout de l'import
from .NOM_DU_DOSSIER.NOM_DU_MODULE import MainPluginNouveauModule

# 2. Ajout de la méthode pour instancier le module
def on_nouveau_module(self):
    try:
        from .NOM_DU_DOSSIER.NOM_DU_MODULE import MainPluginNouveauModule
        nouveau_module_plugin = MainPluginNouveauModule(self.iface)
        nouveau_module_plugin.run()
    except ImportError as e:
        QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginNouveauModule: {e}")
    except Exception as e:
        QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")

# 3. Dans la méthode initGui, ajoutez :
# Définition de l'icône et de l'action
module_icon = getThemeIcon("nom_icone.png")  # Assurez-vous que l'icône existe dans le dossier icons/
self.nouveau_module_action = QAction(QIcon(module_icon), "Nom du Module", self.iface.mainWindow())
self.nouveau_module_action.setObjectName("NOM_DU_MODULE")
# Ajout de l'action au sous-menu correspondant (ex: BILANS, TRAITEMENTS, etc.)
self.sousmenu_NOM_DU_MENU.addAction(self.nouveau_module_action)
# Connexion de l'action à la méthode
self.nouveau_module_action.triggered.connect(self.on_nouveau_module)

# 4. Dans la méthode unload, ajoutez :
# Retirer l'action du menu
self.iface.removePluginMenu("NOM_DU_MENU", self.nouveau_module_action)

3. Emplacement et Nom du Fichier du Module
    • Où sauvegarder le fichier ? Le fichier du module doit être placé dans un sous-dossier du plugin, en fonction de sa thématique :
        ◦ BILANS/ pour les modules de bilans et Traitements.
        ◦ TRAITEMENTS/ pour les modules de traitement de données.
        ◦ TELECHARGEMENTS/ pour les modules de téléchargement.
        ◦ GBDD/ pour les modules liés à Postgre/postgis
        ◦ STATISTIQUES/ pour les modules qui produisent des statistiques
        ◦ GESTION_DES_SUP/ pour les modules liés à la production de sEvitude d’Utilité Publique

    • Comment nommer le fichier ? Le fichier doit suivre la convention de nommage : NOM_DU_MENU_NomDuModule.py Exemples :
        ◦ BILANS_TraitementVolumes.py (pour un module d'Traitement dans le menu BILANS)
        ◦ TRAITEMENTS_ConversionGPKG.py (pour un module de traitement dans le menu TRAITEMENTS)
        ◦ TELECHARGEMENTS_TelechargementDonnees.py (pour un module de téléchargement dans le menu TELECHARGEMENTS)

4.Points Clés à Respecter
    1. Utilisation exclusive de PyQGIS : Le module doit utiliser uniquement les bibliothèques PyQGIS et PyQt (pas de dépendances externes comme GeoPandas).
    2. Gestion des erreurs : Inclure des blocs try/except pour gérer les erreurs et afficher des messages clairs à l'utilisateur.
    3. Documentation : Inclure des commentaires clairs dans le code et une notice d'utilisation dans l'onglet "Instructions".
    4. Les fenêtres auront une largeur minimale : self.setMinimumWidth(800)

5.Je souhaite que tu génères un module pour mon plugin avec les spécifications suivantes :
    1. Nom du module : Mon_module_de_….
    2. Menu parent : [par exemple : GBDD].
    3. Fonctionnalité principale et Données nécessaires :
        1) Créer une Qcombobox pour choisir un fichier ou des fichiers tel que
        2) Vérifier que …
        3) Demander à l’utilisateur un paramètre…
        4) Effectuer les traitements/opérations
        5) Importe dans le schéma le ou les couches créées
        6) Choisir un dossier d’export pour sauvegarder au format… les couches..
    4. Nom du fichier : [par exemple..Import_ADMIN_EXPRESS_gb_ddt21.py]
    5. Icône : [par exemple… GBDD.jpg]

6.Structure attendue :
    • Utilise la classe NouveauModuleDialog avec les méthodes setup_instructions_tab et setup_operations_tab.
    • Fournis le code complet du module.
    • Fournis les lignes de code à ajouter dans Boite_a_outils_ADL.py pour l'intégration (import, méthode, action, et connexion).
        """

    def _get_integration_text(self):
        """Retourne le texte pour l'intégration d'un nouveau module."""
        return """
Intégration d'un nouveau module au plugin principal

Voici les étapes pour intégrer un nouveau module au plugin principal Boite_a_outils_ADL.py :

# 1. Ajout de l'import (au début, avec les autres imports)
from .TELECHARGEMENTS.TELECHARGEMENT_ADMIN_EXPRESS import MainPluginTelechargementAdminExpress

# 2. Ajout de la méthode pour instancier le module (dans la classe du plugin)
def on_telechargement_admin_express(self):
    try:
        from .TELECHARGEMENTS.TELECHATELECHARGEMENTSRGEMENT_ADMIN_EXPRESS import MainPluginTelechargementAdminExpress
        telechargement_admin_express_plugin = MainPluginTelechargementAdminExpress(self.iface)
        telechargement_admin_express_plugin.run()
    except ImportError as e:
        QMessageBox.critical(None, "Erreur d'importation", f"Impossible d'importer MainPluginTelechargementAdminExpress: {e}")
    except Exception as e:
        QMessageBox.critical(None, "Erreur", f"Une erreur est survenue: {e}")

# 3. Dans la méthode initGui, ajoutez :
# Définition de l'icône et de l'action
module_icon = getThemeIcon("telechargement_admin_express.png")  # Assurez-vous que l'icône existe dans le dossier icons/
self.telechargement_admin_express_action = QAction(QIcon(module_icon), "Téléchargement ADMIN-EXPRESS", self.iface.mainWindow())
self.telechargement_admin_express_action.setObjectName("TELECHARGEMENT_ADMIN_EXPRESS")
# Ajout de l'action au sous-menu correspondant
self.sousmenu_TELECHARGEMENTS.addAction(self.telechargement_admin_express_action)
# Connexion de l'action à la méthode
self.telechargement_admin_express_action.triggered.connect(self.on_telechargement_admin_express)

# 4. Dans la méthode unload, ajoutez :
# Retirer l'action du menu
self.iface.removePluginMenu("TELECHARGEMENTS", self.telechargement_admin_express_action)
        """
    
    
    
    def _get_data_manager_text(self):
        """Retourne le texte pour l'onglet DataManager."""
        return """
Gestion des données globales avec DataManager

1. Intérêt du fichier data_manager_BAO_ADL.py
---------------------------------------------
Le fichier data_manager_BAO_ADL.py permet de centraliser et partager des données ou des paramètres entre tous les modules du plugin. Il agit comme un "gestionnaire de données globales", évitant ainsi la redondance de code et facilitant la maintenance.

Par exemple, il permet de :
    • Stocker des chemins de dossiers ou de fichiers utilisés par plusieurs modules.
    • Définir des variables ou des dictionnaires accessibles partout dans le plugin.
    • Centraliser la logique de gestion des chemins ou des ressources partagées.

2. Structure actuelle du fichier
---------------------------------
Voici un extrait du code actuel de data_manager_BAO_ADL.py :

```python
# -*- coding: utf-8 -*-
# Python 3
import os
import csv

def get_plugin_directory():
    # Obtenir le chemin du fichier courant
    current_file_path = os.path.abspath(__file__)
    # Déterminer le répertoire parent (le dossier du plugin)
    plugin_directory = os.path.dirname(current_file_path)
    return plugin_directory

class DataManager_BAO_ADL:
    def __init__(self):
        self.basepath = get_plugin_directory()  # Répertoire où se trouve le plugin
        self.data_dir = os.path.join(self.basepath, 'projet_local')
        self.local_folder = self.basepath + "/projet_local/"
        self.DicoGBDD = {}  # Dictionnaire pour stocker des données globales
        
3. Comment utiliser DataManager pour créer des variables globales ?
------------------------------------------------------------------
Pour utiliser DataManager dans un module, suivez ces étapes :
a. Importer DataManager
Dans le module où vous souhaitez utiliser les données globales, commencez par importer DataManager :
from ..data_manager_BAO_ADL import DataManager_BAO_ADL

b. Instancier DataManager
Créez une instance de DataManager dans votre module :
data_manager = DataManager_BAO_ADL()

c. Accéder aux variables globales
Vous pouvez maintenant accéder aux variables globales définies dans DataManager, par exemple :
# Accéder au répertoire local
local_folder = data_manager.local_folder
# Accéder au dictionnaire global
dico_gbdd = data_manager.DicoGBDD

d. Ajouter une nouvelle variable globale
Pour ajouter une nouvelle variable globale, modifiez la classe DataManager_BAO_ADL dans le fichier data_manager_BAO_ADL.py :
class DataManager_BAO_ADL:
    def __init__(self):
        self.basepath = get_plugin_directory()
        self.data_dir = os.path.join(self.basepath, 'projet_local')
        self.local_folder = self.basepath + "/projet_local/"
        self.DicoGBDD = {}  # Dictionnaire pour stocker des données globales
        self.nouvelle_variable = "valeur par défaut"  # Nouvelle variable globale
        
e. Utiliser la nouvelle variable dans un module
Après avoir ajouté la variable, vous pouvez l'utiliser dans n'importe quel module :
nouvelle_valeur = data_manager.nouvelle_variable

4. Bonnes pratiques
------------------------------------------------------------------

• Évitez de surcharger DataManager avec trop de variables globales. Privilégiez les variables vraiment partagées entre plusieurs modules.
• Documentez chaque variable globale ajoutée pour faciliter la maintenance.
• Utilisez des noms explicites pour les variables globales.
• Si une variable n'est utilisée que dans un seul module, déclarez-la localement plutôt que globalement.
    """       
        
        
     
        
        
if __name__ == "__main__":
    app = QApplication(sys.argv)
    dialog = AboutDialog_BAO_ADL()
    dialog.exec_()
    sys.exit(app.exec_())
