# -*- coding: utf-8 -*-
from qgis.PyQt.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
                                 QFileDialog, QMessageBox, QLineEdit, QComboBox, QTextEdit,
                                 QTabWidget, QWidget, QProgressBar, QGraphicsView, QGraphicsScene)
from qgis.PyQt.QtCore import Qt, QRectF, QThread, pyqtSignal
from qgis.PyQt.QtGui import QColor, QBrush, QPen, QFont, QPainter
from qgis.PyQt.QtPrintSupport import QPrinter
import os
import csv
import math
from datetime import datetime
from collections import defaultdict

class TreeMapItem:
    def __init__(self, name, size, path=None, color=None):
        self.name = name
        self.size = size
        self.path = path
        self.color = color
        self.children = []
        self.rect = QRectF()
        self.parent = None

    def add_child(self, child):
        child.parent = self
        self.children.append(child)

    def total_size(self):
        return self.size + sum(child.total_size() for child in self.children)

class TreeMapView(QGraphicsView):
    def __init__(self, parent=None):
        super(TreeMapView, self).__init__(parent)
        self.scene = QGraphicsScene(self)
        self.setScene(self.scene)
        self.root = None
        self.colors = [
            QColor(255, 127, 14), QColor(44, 160, 44), QColor(31, 119, 180),
            QColor(255, 152, 150), QColor(197, 27, 125), QColor(227, 119, 194),
            QColor(148, 103, 189), QColor(140, 86, 75), QColor(227, 119, 194)
        ]
        self.current_color_index = 0

    def build_treemap(self, data, width, height):
        self.root = self.create_tree(data)
        if self.root.total_size() > 0:  # Vérifier que la taille totale est > 0
            self.calculate_rectangles(self.root, 0, 0, width, height)
            self.draw_treemap()
        else:
            print("Aucune donnée valide pour construire la treemap")

    def create_tree(self, data):
        root = TreeMapItem("Root", 0)

        # Organiser les données par dossier et type
        folder_data = defaultdict(lambda: defaultdict(int))

        for item in data:
            if 'folder' in item and 'size' in item:
                try:
                    size = float(item['size'])
                    if size > 0:  # Ignorer les tailles nulles ou négatives
                        folder_data[item['folder']][item['type']] += size
                except (ValueError, KeyError):
                    continue

        # Créer les nœuds pour chaque dossier
        for folder, types in folder_data.items():
            folder_node = TreeMapItem(folder, 0)
            root.add_child(folder_node)

            # Créer les nœuds pour chaque type de données dans le dossier
            for data_type, size in types.items():
                if size > 0:  # Ignorer les tailles nulles
                    type_node = TreeMapItem(data_type, size, folder)
                    folder_node.add_child(type_node)

        return root

    def calculate_rectangles(self, node, x, y, width, height):
        if not node.children:
            node.rect = QRectF(x, y, width, height)
            return

        total_size = node.total_size()
        if total_size <= 0:  # Éviter la division par zéro
            return

        current_x = x
        current_y = y

        # Trier les enfants par taille (descendant)
        node.children.sort(key=lambda child: child.total_size(), reverse=True)

        for child in node.children:
            child_size = child.total_size() / total_size
            if width > height:
                # Disposition horizontale
                child_width = width * child_size
                self.calculate_rectangles(child, current_x, current_y, child_width, height)
                current_x += child_width
            else:
                # Disposition verticale
                child_height = height * child_size
                self.calculate_rectangles(child, current_x, current_y, width, child_height)
                current_y += child_height

    def draw_treemap(self):
        self.scene.clear()

        def draw_node(node):
            if node == self.root:
                return

            # Définir la couleur
            if node.parent == self.root:
                self.current_color_index = (self.current_color_index + 1) % len(self.colors)
            color = self.colors[self.current_color_index] if node.parent == self.root else \
                    self.colors[self.current_color_index].lighter(130)

            # Dessiner le rectangle
            rect = self.scene.addRect(node.rect, QPen(Qt.black, 0.5), QBrush(color))

            # Ajouter le texte
            if node.rect.width() > 30 and node.rect.height() > 20:
                text = self.scene.addText(node.name)
                text.setPos(node.rect.x() + 2, node.rect.y() + 2)

                # Ajouter la taille si le rectangle est assez grand
                if node.rect.width() > 80 and node.rect.height() > 30:
                    size_text = self.scene.addText(self.format_size(node.size))
                    size_text.setPos(node.rect.x() + 2, node.rect.y() + 18)

            # Dessiner les enfants
            for child in node.children:
                draw_node(child)

        draw_node(self.root)

    def format_size(self, size):
        """Formate la taille en unités lisibles"""
        if size <= 0:
            return "0 o"
        elif size < 1024:
            return f"{size:.1f} o"
        elif size < 1024 * 1024:
            return f"{size / 1024:.1f} Ko"
        elif size < 1024 * 1024 * 1024:
            return f"{size / (1024 * 1024):.1f} Mo"
        else:
            return f"{size / (1024 * 1024 * 1024):.1f} Go"

    def export_to_pdf(self, file_path, title):
        """Exporter la treemap en PDF"""
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)
        printer.setPageSize(QPrinter.A4)
        printer.setPageOrientation(QPrinter.Landscape)

        painter = QPainter(printer)
        self.render(painter)

        # Ajouter le titre
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(printer.pageRect().center().x() - 150, 50, title)
        painter.end()

class WorkerThread(QThread):
    progress = pyqtSignal(int)
    message = pyqtSignal(str)
    finished = pyqtSignal(list)

    def __init__(self, csv_path):
        QThread.__init__(self)
        self.csv_path = csv_path
        self.stopped = False

    def run(self):
        try:
            data = []
            with open(self.csv_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f, delimiter=',')
                total_rows = sum(1 for row in reader)
                f.seek(0)
                next(reader)  # Skip header

                for i, row in enumerate(reader):
                    if self.stopped:
                        return

                    try:
                        # Extraire le dossier à partir du chemin
                        path = row.get('path', '')
                        if not path:
                            continue

                        # Nettoyer le chemin (remplacer les \ par /)
                        path = path.replace('\\', '/')

                        # Extraire le lecteur et le premier niveau d'arborescence
                        parts = path.split('/')
                        if len(parts) >= 3:
                            lecteur = parts[0]
                            premier_niveau = parts[2]  # parts[1] est vide après le split de W:/
                            folder = f"{lecteur}/{premier_niveau}"
                        else:
                            folder = "Inconnu"

                        # Extraire les autres informations
                        nom = row.get('nom', '')
                        data_type = row.get('type', 'unknown')
                        size = float(row.get('size', 0))
                        modification_time = row.get('modification_time', '')

                        data.append({
                            'folder': folder,
                            'type': data_type,
                            'size': size,
                            'path': path,
                            'nom': nom,
                            'modification_time': modification_time
                        })

                    except Exception as e:
                        print(f"Erreur lors du traitement de la ligne {i}: {str(e)}")
                        continue

                    # Mettre à jour la progression
                    progress = int((i + 1) / total_rows * 100)
                    self.progress.emit(progress)

            self.finished.emit(data)

        except Exception as e:
            self.message.emit(f"Erreur lors du chargement du fichier CSV: {str(e)}")
            self.finished.emit([])

class BilanTreemapDialog(QDialog):
    def __init__(self, parent=None):
        super(BilanTreemapDialog, self).__init__(parent)
        self.setWindowTitle("Bilan des volumes de données - Treemap")
        self.setMinimumSize(800, 600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout()

        # Onglets
        self.tabs = QTabWidget()

        # Onglet Instructions
        self.instructions_tab = QWidget()
        self.setup_instructions_tab()

        # Onglet Analyse
        self.analysis_tab = QWidget()
        self.setup_analysis_tab()

        self.tabs.addTab(self.instructions_tab, "Instructions")
        self.tabs.addTab(self.analysis_tab, "Analyse")

        layout.addWidget(self.tabs)
        self.setLayout(layout)

    def setup_instructions_tab(self):
        layout = QVBoxLayout()
        self.instructions_text = QTextEdit()
        self.instructions_text.setReadOnly(True)

        instructions = """
        <h2>Module de Bilan des Volumes de Données - Treemap</h2>

        <h3>Fonctionnalités :</h3>
        <p>Ce module permet de visualiser sous forme de treemap (carte en arbre) la répartition des volumes de données
        des projets QGIS et de leurs couches. La treemap montre :</p>
        <ul>
            <li>Les grands dossiers contenant les données</li>
            <li>Les projets QGIS et leurs couches</li>
            <li>La taille des données en octets, Ko, Mo ou Go</li>
        </ul>

        <h3>Données nécessaires :</h3>
        <p>Le fichier CSV doit contenir les colonnes suivantes :</p>
        <ul>
            <li><b>path</b> : Le chemin complet du fichier (ex: W:/2_DOSSIERS/FORET\carte_travail.qgz)</li>
            <li><b>nom</b> : Le nom du fichier</li>
            <li><b>type</b> : Le type de fichier (qgs, qgz, shp, etc.)</li>
            <li><b>size</b> : La taille du fichier en octets</li>
            <li><b>modification_time</b> : La date de modification</li>
        </ul>

        <h3>Format attendu :</h3>
        <pre>
path,nom,nom_du_lecteur,premier_niveau_arborescence,type,size,modification_time
W:/2_DOSSIERS/FORET\carte_travail.qgz,carte_travail.qgz,qgz,391836,2024-03-12
W:/2_DOSSIERS/FORET\MAP_foret.qgz,MAP_foret.qgz,qgz,175396,2020-06-24
        </pre>

        <h3>Utilisation :</h3>
        <ol>
            <li>Sélectionnez un fichier CSV contenant les informations sur les projets et couches</li>
            <li>Cliquez sur "Charger les données"</li>
            <li>Visualisez la treemap générée</li>
            <li>Exportez en PDF si nécessaire</li>
        </ol>
        """
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_analysis_tab(self):
        layout = QVBoxLayout()

        # Sélection du fichier CSV
        csv_layout = QHBoxLayout()
        self.csv_label = QLabel("Fichier CSV:")
        self.csv_line_edit = QLineEdit()
        self.csv_browse_button = QPushButton("Parcourir...")
        csv_layout.addWidget(self.csv_label)
        csv_layout.addWidget(self.csv_line_edit)
        csv_layout.addWidget(self.csv_browse_button)

        # Bouton pour charger les données
        self.load_button = QPushButton("Charger les données")
        self.load_button.setStyleSheet("background-color: #4CAF50; color: white;")

        # Barre de progression
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)

        # Zone de message
        self.message_text = QTextEdit()
        self.message_text.setReadOnly(True)
        self.message_text.setFixedHeight(100)

        # Zone de visualisation de la treemap
        self.treemap_view = TreeMapView()
        self.treemap_view.setMinimumHeight(400)

        # Bouton pour exporter en PDF
        self.export_button = QPushButton("Exporter en PDF")
        self.export_button.setStyleSheet("background-color: #2196F3; color: white;")
        self.export_button.setEnabled(False)

        # Ajout des widgets au layout
        layout.addLayout(csv_layout)
        layout.addWidget(self.progress_bar)
        layout.addWidget(self.message_text)
        layout.addWidget(self.load_button)
        layout.addWidget(self.treemap_view)
        layout.addWidget(self.export_button)

        self.analysis_tab.setLayout(layout)

        # Connexion des signaux
        self.csv_browse_button.clicked.connect(self.browse_csv)
        self.load_button.clicked.connect(self.load_data)
        self.export_button.clicked.connect(self.export_to_pdf)

    def browse_csv(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Sélectionner le fichier CSV", "", "CSV Files (*.csv)")
        if file_path:
            self.csv_line_edit.setText(file_path)

    def load_data(self):
        csv_path = self.csv_line_edit.text()
        if not csv_path:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner un fichier CSV.")
            return

        # Désactiver les boutons pendant le traitement
        self.load_button.setEnabled(False)
        self.export_button.setEnabled(False)
        self.progress_bar.setValue(0)
        self.message_text.clear()
        self.message_text.append(f"Chargement du fichier: {csv_path}")

        # Démarrer le thread de traitement
        self.worker = WorkerThread(csv_path)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.message.connect(self.message_text.append)
        self.worker.finished.connect(self.on_data_loaded)
        self.worker.start()

    def on_data_loaded(self, data):
        self.load_button.setEnabled(True)

        if not data:
            QMessageBox.warning(self, "Erreur", "Aucune donnée valide trouvée dans le fichier CSV.")
            return

        self.message_text.append(f"Fichier chargé avec succès. {len(data)} entrées valides trouvées.")

        # Filtrer les données avec taille > 0
        filtered_data = [item for item in data if item['size'] > 0]

        if not filtered_data:
            QMessageBox.warning(self, "Erreur", "Aucune donnée avec une taille valide (>0) trouvée.")
            return

        # Générer la treemap
        self.treemap_view.build_treemap(filtered_data, 800, 500)
        self.export_button.setEnabled(True)

    def export_to_pdf(self, file_path, title):
        """Exporter la treemap en PDF."""
        printer = QPrinter()
        printer.setOutputFormat(QPrinter.PdfFormat)
        printer.setOutputFileName(file_path)

        # Utiliser QPageLayout pour définir l'orientation
        page_layout = QPageLayout(QPageSize(QPageSize.A4), QPageLayout.Landscape, QMarginsF())
        printer.setPageLayout(page_layout)

        painter = QPainter(printer)
        self.render(painter)

        # Ajouter le titre
        painter.setFont(QFont("Arial", 14, QFont.Bold))
        painter.drawText(printer.pageRect().center().x() - 150, 50, title)
        painter.end()


class MainPluginBilanTreemap(object):
    def __init__(self, iface):
        self.iface = iface

    def initGui(self):
        # Création de l'action
        self.action = QAction("Bilan des volumes - Treemap", self.iface.mainWindow())
        self.action.triggered.connect(self.run)

        # Ajouter l'action au menu BILANS
        self.iface.addPluginToMenu("BILANS", self.action)

    def unload(self):
        # Retirer l'action du menu
        self.iface.removePluginMenu("BILANS", self.action)

    def run(self):
        dialog = BilanTreemapDialog(self.iface.mainWindow())
        dialog.exec_()
