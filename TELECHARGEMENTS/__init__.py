# -*- coding: utf-8 -*-
# Python 3

# Ce fichier peut-être vide mais est impératif ! 
# Ce fichier indique à Python que le dossier qui le contient doit être traité comme un package Python.
# Le sous-dossier qui le contient sert à structurer le plugin.
# On y range certains modules qu'on importe dans le plugin principal.
# on peut aussi y regrouper les imports des modules
#from .TELECHARGEMENTS_commande1_BAO_ADL import DOWNLOADS_commande1_BAO_ADL
#from .TRAITEMENTS_BAO_ADL_commande2 import fonction2
# Ajoutez autant de lignes que nécessaire pour chaque module

# dans le plugin principal on ecrira: 
# from .BILANS import *
# Cela importera toutes les fonctions et classes définies dans __init__.py.

# N.B.:  On peut aussi importer le module entier 
# et accéder aux fonctions en utilisant la notation par points:
# import TRAITEMENTS.TRAITEMENTS_BAO_ADL_GPKG_TO_SHAP as TRAITEMENT_cmd1
# puis dans le code on utilise la fonction:
# TRAITEMENT_cmd1.fonction1()