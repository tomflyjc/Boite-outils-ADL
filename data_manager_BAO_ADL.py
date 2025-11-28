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

####################################################################################
class DataManager_BAO_ADL:
    def __init__(self):
        super().__init__()
        
        self.basepath=get_plugin_directory() #  est le répertoire où se trouve le plugin
        self.data_dir = os.path.join(self.basepath, 'projet_local')
        # Dossier local où les couches sont stockées :                
        self.local_folder = self.basepath + "/projet_local/"  
        #self.local_folder= os.path.join(self.basepath, 'projet_local')
        self.DicoGBDD={}
        
                
        self.regions = [
            ("Auvergne-Rhône-Alpes", "84"),
            ("Bourgogne-Franche-Comté", "27"),
            ("Bretagne", "53"),
            ("Centre-Val de Loire", "24"),
            ("Corse", "94"),
            ("Grand Est", "44"),
            ("Hauts-de-France", "32"),
            ("Île-de-France", "11"),
            ("Normandie", "28"),
            ("Nouvelle-Aquitaine", "75"),
            ("Occitanie", "76"),
            ("Pays de la Loire", "52"),
            ("Provence-Alpes-Côte d'Azur", "93")
        ]
        self.departments = [
            ("Ain", "01"), ("Aisne", "02"), ("Allier", "03"), ("Alpes-de-Haute-Provence", "04"),
            ("Hautes-Alpes", "05"), ("Alpes-Maritimes", "06"), ("Ardèche", "07"), ("Ardennes", "08"),
            ("Ariège", "09"), ("Aube", "10"), ("Aude", "11"), ("Aveyron", "12"), ("Bouches-du-Rhône", "13"),
            ("Calvados", "14"), ("Cantal", "15"), ("Charente", "16"), ("Charente-Maritime", "17"),
            ("Cher", "18"), ("Corrèze", "19"), ("Corse-du-Sud", "2A"), ("Haute-Corse", "2B"),
            ("Côte-d'Or", "21"), ("Côtes-d'Armor", "22"), ("Creuse", "23"), ("Dordogne", "24"),
            ("Doubs", "25"), ("Drôme", "26"), ("Eure", "27"), ("Eure-et-Loir", "28"), ("Finistère", "29"),
            ("Gard", "30"), ("Haute-Garonne", "31"), ("Gers", "32"), ("Gironde", "33"), ("Hérault", "34"),
            ("Ille-et-Vilaine", "35"), ("Indre", "36"), ("Indre-et-Loire", "37"), ("Isère", "38"),
            ("Jura", "39"), ("Landes", "40"), ("Loir-et-Cher", "41"), ("Loire", "42"), ("Haute-Loire", "43"),
            ("Loire-Atlantique", "44"), ("Loiret", "45"), ("Lot", "46"), ("Lot-et-Garonne", "47"),
            ("Lozère", "48"), ("Maine-et-Loire", "49"), ("Manche", "50"), ("Marne", "51"),
            ("Haute-Marne", "52"), ("Mayenne", "53"), ("Moselle", "57"), ("Meurthe-et-Moselle", "54"),
            ("Meuse", "55"), ("Morbihan", "56"), ("Nièvre", "58"), ("Nord", "59"), ("Oise", "60"),
            ("Orne", "61"), ("Pas-de-Calais", "62"), ("Puy-de-Dôme", "63"), ("Pyrénées-Atlantiques", "64"),
            ("Hautes-Pyrénées", "65"), ("Pyrénées-Orientales", "66"), ("Bas-Rhin", "67"), ("Haut-Rhin", "68"),
            ("Rhône", "69"), ("Haute-Saône", "70"), ("Saône-et-Loire", "71"), ("Sarthe", "72"),
            ("Savoie", "73"), ("Haute-Savoie", "74"), ("Paris", "75"), ("Seine-Maritime", "76"),
            ("Seine-et-Marne", "77"), ("Yvelines", "78"), ("Deux-Sèvres", "79"), ("Somme", "80"),
            ("Tarn", "81"), ("Tarn-et-Garonne", "82"), ("Var", "83"), ("Vaucluse", "84"), ("Vendée", "85"),
            ("Vienne", "86"), ("Haute-Vienne", "87"), ("Vosges", "88"), ("Yonne", "89"), ("Territoire de Belfort", "90"),
            ("Essonne", "91"), ("Hauts-de-Seine", "92"), ("Seine-Saint-Denis", "93"), ("Val-de-Marne", "94"),
            ("Val-d'Oise", "95"), ("Guadeloupe", "971"), ("Martinique", "972"), ("Guyane", "973"),
            ("La Réunion", "974"), ("Mayotte", "976")
        ]         
        
#####################################################################################