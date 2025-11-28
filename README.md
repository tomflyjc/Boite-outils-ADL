
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
