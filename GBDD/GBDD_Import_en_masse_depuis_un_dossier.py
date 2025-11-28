from qgis.PyQt.QtWidgets import (
    QDialog, QVBoxLayout, QTabWidget, QWidget, QTextEdit,
    QPushButton, QLabel, QLineEdit, QMessageBox,
    QComboBox, QFileDialog, QCheckBox, QListWidget, QListWidgetItem, QHBoxLayout
)
from qgis.PyQt.QtCore import Qt, QVariant
from qgis.core import QgsVectorLayer
import os
import psycopg2
from psycopg2 import sql
import csv

class SelectUniqueIdDialog(QDialog):
    def __init__(self, fields, parent=None):
        super(SelectUniqueIdDialog, self).__init__(parent)
        self.setWindowTitle("Sélectionner l'identifiant unique")
        self.setMinimumWidth(600)
        self.fields = fields
        self.selected_field = None
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        # Tableau pour afficher les champs
        self.table = QListWidget()
        for field in self.fields:
            item = QListWidgetItem(f"{field['name']} ({field['type']}) - Exemple: {field['example']}")
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Unchecked)
            self.table.addItem(item)

        layout.addWidget(QLabel("Sélectionnez le champ à utiliser comme identifiant unique :"))
        layout.addWidget(self.table)

        # Boutons
        button_layout = QHBoxLayout()
        self.ok_button = QPushButton("Valider")
        self.ok_button.clicked.connect(self.accept)
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self.reject)
        button_layout.addWidget(self.ok_button)
        button_layout.addWidget(self.cancel_button)

        layout.addLayout(button_layout)
        self.setLayout(layout)

    def get_selected_field(self):
        for i in range(self.table.count()):
            item = self.table.item(i)
            if item.checkState() == Qt.Checked:
                return self.fields[i]['name']
        return None

class ImportFromFolderDialog(QDialog):
    def __init__(self, parent=None):
        super(ImportFromFolderDialog, self).__init__(parent)
        self.setWindowTitle("GBDD Import en masse depuis un dossier")
        self.setMinimumWidth(800)

        # Définir les listes de régions et départements
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

        # Initialiser l'interface
        self.setup_ui()
        self.selected_folder = None

    def setup_ui(self):
        layout = QVBoxLayout()
        self.tabs = QTabWidget()
        self.instructions_tab = QWidget()
        self.setup_instructions_tab()
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
        <h2>Module : GBDD Import en masse depuis un dossier</h2>
        <h3>Fonctionnalités :</h3>
        <p>Ce module permet d'importer un ensemble de couches/données en base PostgreSQL depuis un dossier.</p>
        <h3>Données nécessaires :</h3>
        <ul>
            <li>Dossier contenant des fichiers Shapefile (.shp), GeoPackage (.gpkg) et/ou tableurs (.csv).</li>
            <li>Login et mot de passe pour la base de données.</li>
        </ul>
        <h3>Utilisation :</h3>
        <ol>
            <li>Sélectionnez un dossier contenant les fichiers.</li>
            <li>Cochez le niveau géographique (national, régional, départemental) et sélectionnez la région ou le département si applicable.</li>
            <li>Saisissez le schéma de la base PostgreSQL.</li>
            <li>Saisissez le login et le mot de passe pour la base de données.</li>
            <li>Cochez les fichiers à importer dans la liste.</li>
            <li>Cliquez sur "Importer et allouer les droits" pour lancer le processus.</li>
        </ol>
        <h3>Règles de nommage :</h3>
        <p>Le nom de chaque couche sera transformé selon les règles suivantes :
        <code>ade_[nom]_p</code> (point), <code>ade_[nom]_l</code> (ligne), <code>ade_[nom]_s</code> (surface), <code>ade_[nom]_t</code> (tableur),
        suivi de <code>_000</code> (national), <code>_R27</code> (exemple régional), ou <code>_021</code> (exemple départemental).
        </p>
        """
        self.instructions_text.setHtml(instructions)
        layout.addWidget(self.instructions_text)
        self.instructions_tab.setLayout(layout)

    def setup_analysis_tab(self):
        layout = QVBoxLayout()

        # Bouton pour sélectionner le dossier
        self.folder_button = QPushButton("Sélectionner un dossier")
        self.folder_button.clicked.connect(self.select_folder)
        layout.addWidget(self.folder_button)

        # Label pour la liste des fichiers
        layout.addWidget(QLabel("Fichiers dans le dossier (cochez pour importer) :"))

        # Initialisation de self.file_list_widget
        self.file_list_widget = QListWidget()
        layout.addWidget(self.file_list_widget)

        # Niveaux géographiques avec checkboxes
        layout.addWidget(QLabel("Niveau géographique :"))
        self.national_check = QCheckBox("National (_000)")
        layout.addWidget(self.national_check)
        self.regional_check = QCheckBox("Régional")
        layout.addWidget(self.regional_check)
        self.region_combo = QComboBox()
        regions_list = [f"{name} {code}" for name, code in self.regions]
        self.region_combo.addItems(regions_list)
        layout.addWidget(self.region_combo)
        self.dep_check = QCheckBox("Départemental")
        layout.addWidget(self.dep_check)
        self.dep_combo = QComboBox()
        deps_list = [f"{code} {name}" for name, code in self.departments]
        self.dep_combo.addItems(deps_list)
        layout.addWidget(self.dep_combo)

        # Schéma
        self.schema_edit = QLineEdit()
        self.schema_edit.setText("r_admin_express")
        layout.addWidget(QLabel("Schéma :"))
        layout.addWidget(self.schema_edit)

        # Métadonnée
        layout.addWidget(QLabel("Métadonnée (optionnelle) :"))
        self.metadata_edit = QTextEdit()
        self.metadata_edit.setPlaceholderText("Saisissez une métadonnée pour cette importation...")
        layout.addWidget(self.metadata_edit)

        # Login
        layout.addWidget(QLabel("Login :"))
        self.login_edit = QLineEdit()
        self.login_edit.setPlaceholderText("Login")
        layout.addWidget(self.login_edit)

        # Droits
        owner_layout = QHBoxLayout()
        owner_layout.addWidget(QLabel("Création droits propriétaire :"))
        self.owner_rights_edit = QLineEdit()
        self.owner_rights_edit.setText("g_admin")
        owner_layout.addWidget(self.owner_rights_edit)
        layout.addLayout(owner_layout)

        admin_layout = QHBoxLayout()
        admin_layout.addWidget(QLabel("Création droit administrateur :"))
        self.admin_rights_edit = QLineEdit()
        self.admin_rights_edit.setText("maintenance")
        admin_layout.addWidget(self.admin_rights_edit)
        layout.addLayout(admin_layout)

        read_layout = QHBoxLayout()
        read_layout.addWidget(QLabel("Création droit consultation :"))
        self.read_rights_edit = QLineEdit()
        self.read_rights_edit.setText("g_consult")
        read_layout.addWidget(self.read_rights_edit)
        layout.addLayout(read_layout)

        # Mot de passe
        self.password_edit = QLineEdit()
        self.password_edit.setPlaceholderText("Mot de passe")
        self.password_edit.setEchoMode(QLineEdit.Password)
        self.show_password_check = QCheckBox("Afficher le mot de passe")
        self.show_password_check.stateChanged.connect(self.toggle_password_visibility)
        password_layout = QHBoxLayout()
        password_layout.addWidget(QLabel("Mot de passe :"))
        password_layout.addWidget(self.password_edit)
        password_layout.addWidget(self.show_password_check)
        layout.addLayout(password_layout)

        # Bouton d'import
        self.import_button = QPushButton("Importer et allouer les droits")
        self.import_button.clicked.connect(self.import_to_postgis)
        layout.addWidget(self.import_button)

        self.analysis_tab.setLayout(layout)

    def toggle_password_visibility(self, state):
        if state == Qt.Checked:
            self.password_edit.setEchoMode(QLineEdit.Normal)
        else:
            self.password_edit.setEchoMode(QLineEdit.Password)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Sélectionner un dossier")
        if folder:
            self.selected_folder = folder
            self.populate_file_list()

    def populate_file_list(self):
        if not hasattr(self, 'file_list_widget') or self.file_list_widget is None:
            return
        self.file_list_widget.clear()
        if not self.selected_folder:
            return
        try:
            files = [f for f in os.listdir(self.selected_folder)
                     if f.lower().endswith(('.shp', '.csv', '.gpkg'))]
            if not files:
                self.file_list_widget.addItem("Aucun fichier compatible trouvé (.shp, .csv, .gpkg)")
            for file in files:
                item = QListWidgetItem(file)
                item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
                item.setCheckState(Qt.Unchecked)
                self.file_list_widget.addItem(item)
        except Exception as e:
            QMessageBox.warning(self, "Attention", f"Impossible de lire le dossier : {e}")

    def get_checked_files(self):
        checked = []
        if not hasattr(self, 'file_list_widget') or self.file_list_widget is None:
            return checked
        for i in range(self.file_list_widget.count()):
            item = self.file_list_widget.item(i)
            if item.checkState() == Qt.Checked:
                checked.append(os.path.join(self.selected_folder, item.text()))
        return checked

    def load_last_choices(self):
        plugin_dir = os.path.dirname(__file__)
        gbdd_dir = os.path.join(plugin_dir, 'GBDD')
        if not os.path.exists(gbdd_dir):
            os.makedirs(gbdd_dir)
        csv_path = os.path.join(gbdd_dir, 'last_choices.csv')
        last_region = None
        last_dep = None
        if os.path.exists(csv_path):
            with open(csv_path, 'r') as f:
                reader = csv.reader(f)
                try:
                    row = next(reader)
                    last_region = row[0]
                    last_dep = row[1]
                except:
                    pass
        regions_list = [f"{name} {code}" for name, code in self.regions]
        if last_region and last_region in regions_list:
            regions_list = [last_region] + [r for r in regions_list if r != last_region]
        self.region_combo.clear()
        self.region_combo.addItems(regions_list)
        deps_list = [f"{code} {name}" for name, code in self.departments]
        if last_dep and last_dep in deps_list:
            deps_list = [last_dep] + [d for d in deps_list if d != last_dep]
        self.dep_combo.clear()
        self.dep_combo.addItems(deps_list)

    def save_last_choices(self):
        plugin_dir = os.path.dirname(__file__)
        gbdd_dir = os.path.join(plugin_dir, 'GBDD')
        csv_path = os.path.join(gbdd_dir, 'last_choices.csv')
        with open(csv_path, 'w', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([self.region_combo.currentText(), self.dep_combo.currentText()])

    def import_shapefile(self, file_path, schema, geo_suffix, cursor, conn, is_gpkg_layer=False, layer_name=None):
        base_name = os.path.splitext(os.path.basename(file_path if not is_gpkg_layer else layer_name))[0].lower()
        layer = QgsVectorLayer(file_path, base_name, "ogr")
        if not layer.isValid():
            QMessageBox.warning(self, "Erreur", f"La couche {base_name} est invalide.")
            return None
        try:
            geom_type_qgis = layer.geometryType()
            if geom_type_qgis == 0:  # Point
                type_suffix = "_p"
            elif geom_type_qgis == 1:  # Line
                type_suffix = "_l"
            elif geom_type_qgis == 2:  # Polygon
                type_suffix = "_s"
            else:
                type_suffix = "_t"  # Table sans géométrie
            fields = layer.fields()
            column_defs = []
            original_names = []
            sql_names = []
            field_types = []
            field_examples = []

            # Récupérer des exemples de valeurs pour chaque champ
            features = list(layer.getFeatures())
            if features:
                example_feature = features[min(9, len(features) - 1)]  # Prendre la 10ème ligne si possible

            for field in fields:
                orig_name = field.name()
                sql_name = orig_name.lower().replace('-', '_').replace(' ', '_')
                original_names.append(orig_name)
                sql_names.append(sql_name)
                ftype = field.typeName()
                field_types.append(ftype)

                # Récupérer un exemple de valeur
                example_value = example_feature[orig_name] if features else "N/A"
                field_examples.append(str(example_value) if example_value is not None else "NULL")

                # Déterminer le type SQL
                if ftype in ["Integer", "LongLong", "Integer64"]:
                    sqltype = "INTEGER"
                elif ftype in ["Real", "Double"]:
                    sqltype = "DOUBLE PRECISION"
                elif ftype == "String":
                    # Corriger VARCHAR(0) en VARCHAR(255)
                    sqltype = "VARCHAR(255)"
                elif ftype == "Date":
                    sqltype = "DATE"
                else:
                    sqltype = "TEXT"
                column_defs.append(sql.Identifier(sql_name) + sql.SQL(f" {sqltype}"))

            # Demander à l'utilisateur de sélectionner un identifiant unique
            if is_gpkg_layer:
                fields_info = [{'name': orig_name, 'type': ftype, 'example': example} for orig_name, ftype, example in zip(original_names, field_types, field_examples)]
                dialog = SelectUniqueIdDialog(fields_info, self)
                if dialog.exec_() == QDialog.Rejected:
                    return None
                unique_id_field = dialog.get_selected_field()
                if not unique_id_field:
                    QMessageBox.warning(self, "Erreur", "Vous devez sélectionner un identifiant unique.")
                    return None
            else:
                unique_id_field = "id"  # Par défaut pour les shapefiles

            if geom_type_qgis in (0, 1, 2):
                geom_def = sql.SQL(", geom GEOMETRY(GEOMETRY, 2154)")
            else:
                geom_def = sql.SQL("")
            columns_sql = sql.SQL(", ").join(column_defs) + geom_def
            new_table_name = f"ade_{base_name}{type_suffix}{geo_suffix}"

            # Création de la table
            cursor.execute(
                sql.SQL("""
                CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
                    id SERIAL PRIMARY KEY,
                    {columns}
                );
                """).format(
                    schema=sql.Identifier(schema),
                    table_name=sql.Identifier(new_table_name),
                    columns=columns_sql
                )
            )

            # Insertion des données
            for feature in layer.getFeatures():
                values = []
                for i, orig_name in enumerate(original_names):
                    value = feature[orig_name]
                    if value is None or (isinstance(value, QVariant) and value.isNull()):
                        values.append(None)
                        continue
                    ftype = field_types[i]
                    if ftype == "String":
                        values.append(str(value))
                    elif ftype in ["Integer", "LongLong", "Integer64"]:
                        try:
                            values.append(int(value))
                        except ValueError:
                            values.append(None)
                    elif ftype in ["Real", "Double"]:
                        try:
                            values.append(float(value))
                        except ValueError:
                            values.append(None)
                    elif ftype == "Date":
                        values.append(str(value))
                    else:
                        values.append(str(value))

                if geom_type_qgis in (0, 1, 2):
                    geom_wkt = feature.geometry().asWkt() if feature.geometry() else None
                    placeholders = sql.SQL(", ").join(sql.Placeholder() * len(values))
                    cursor.execute(
                        sql.SQL("""
                        INSERT INTO {schema}.{table_name} ({cols}, geom)
                        VALUES ({placeholders}, ST_GeomFromText(%s, 2154));
                        """).format(
                            schema=sql.Identifier(schema),
                            table_name=sql.Identifier(new_table_name),
                            cols=sql.SQL(", ").join([sql.Identifier(c) for c in sql_names]),
                            placeholders=placeholders
                        ),
                        values + [geom_wkt]
                    )
                else:
                    placeholders = sql.SQL(", ").join(sql.Placeholder() * len(values))
                    cursor.execute(
                        sql.SQL("""
                        INSERT INTO {schema}.{table_name} ({cols})
                        VALUES ({placeholders});
                        """).format(
                            schema=sql.Identifier(schema),
                            table_name=sql.Identifier(new_table_name),
                            cols=sql.SQL(", ").join([sql.Identifier(c) for c in sql_names]),
                            placeholders=placeholders
                        ),
                        values
                    )

            QMessageBox.information(self, "Succès", f"Table {new_table_name} importée avec succès.")
            return new_table_name
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(
                self,
                "Erreur",
                f"Erreur lors de l'import de {base_name} : {str(e)}\n\n"
                f"Types de champs détectés : {field_types}\n"
                f"Noms de champs détectés : {original_names}"
            )
            return None

    def import_geopackage(self, file_path, schema, geo_suffix, cursor, conn):
        all_layers = QgsVectorLayer(file_path, "temp", "ogr")
        if all_layers.isValid():
            sublayers = all_layers.dataProvider().subLayers()
            for sublayer in sublayers:
                layer_name = sublayer.split('!!::!!')[1] if '!!::!!' in sublayer else sublayer
                gpkg_layer = QgsVectorLayer(f"{file_path}|layername={layer_name}", layer_name, "ogr")
                if gpkg_layer.isValid():
                    self.import_shapefile(gpkg_layer.source(), schema, geo_suffix, cursor, conn, is_gpkg_layer=True, layer_name=layer_name)
        else:
            QMessageBox.warning(self, "Erreur", f"Impossible de lire les couches du GeoPackage.")

    def import_csv(self, file_path, schema, geo_suffix, cursor, conn):
        base_name = os.path.splitext(os.path.basename(file_path))[0].lower()
        type_suffix = "_t"
        new_table_name = f"ade_{base_name}{type_suffix}{geo_suffix}"
        try:
            with open(file_path, 'r', newline='', encoding='utf-8') as f:
                reader = csv.reader(f)
                header = next(reader)
                header_lower = [h.lower().replace('-', '_').replace(' ', '_') for h in header]
                column_defs = [sql.Identifier(h) + sql.SQL(" VARCHAR(255)") for h in header_lower]
                columns_sql = sql.SQL(", ").join(column_defs)
                cursor.execute(
                    sql.SQL("""
                    CREATE TABLE IF NOT EXISTS {schema}.{table_name} (
                        id SERIAL PRIMARY KEY,
                        {columns}
                    );
                    """).format(
                        schema=sql.Identifier(schema),
                        table_name=sql.Identifier(new_table_name),
                        columns=columns_sql
                    )
                )
                for row in reader:
                    cursor.execute(
                        sql.SQL("""
                        INSERT INTO {schema}.{table_name} ({cols})
                        VALUES ({placeholders});
                        """).format(
                            schema=sql.Identifier(schema),
                            table_name=sql.Identifier(new_table_name),
                            cols=sql.SQL(", ").join([sql.Identifier(c) for c in header_lower]),
                            placeholders=sql.SQL(", ").join(sql.Placeholder() * len(header_lower))
                        ),
                        row
                    )
            QMessageBox.information(self, "Succès", f"Table {new_table_name} importée avec succès.")
            return new_table_name
        except Exception as e:
            conn.rollback()
            QMessageBox.critical(self, "Erreur", f"Erreur lors de l'import de {new_table_name} : {e}")
            return None

    def import_to_postgis(self):
        selected_files = self.get_checked_files()
        if not selected_files:
            QMessageBox.warning(self, "Erreur", "Veuillez sélectionner au moins un fichier à importer.")
            return
        login = self.login_edit.text()
        password = self.password_edit.text()
        if not login or not password:
            QMessageBox.warning(self, "Erreur", "Login et mot de passe sont requis.")
            return
        schema = self.schema_edit.text()
        if not schema:
            QMessageBox.warning(self, "Erreur", "Le schéma est requis.")
            return
        suffixes = []
        if self.national_check.isChecked():
            suffixes.append("_000")
        if self.regional_check.isChecked():
            region_text = self.region_combo.currentText()
            if region_text:
                code = region_text.split()[-1]
                suffixes.append(f"_R{code}")
        if self.dep_check.isChecked():
            dep_text = self.dep_combo.currentText()
            if dep_text:
                code = dep_text.split()[0]
                if code.isdigit():
                    code = code.zfill(3)
                suffixes.append(f"_{code}")
        if len(suffixes) != 1:
            QMessageBox.warning(self, "Erreur", "Veuillez cocher exactement un niveau géographique.")
            return
        geo_suffix = suffixes[0]
        metadata = self.metadata_edit.toPlainText()

        try:
            conn = psycopg2.connect(
                dbname="gb_ddt21",
                user=login,
                password=password,
                host="10.21.8.40",
                port="5432"
            )
            cursor = conn.cursor()
        except Exception as e:
            QMessageBox.critical(self, "Erreur de connexion", f"Impossible de se connecter à la base : {e}")
            return

        for file_path in selected_files:
            if file_path.lower().endswith('.shp'):
                table_name = self.import_shapefile(file_path, schema, geo_suffix, cursor, conn)
            elif file_path.lower().endswith('.csv'):
                table_name = self.import_csv(file_path, schema, geo_suffix, cursor, conn)
            elif file_path.lower().endswith('.gpkg'):
                table_name = self.import_geopackage(file_path, schema, geo_suffix, cursor, conn)

            if table_name:
                # Allocation des droits
                owner_rights = self.owner_rights_edit.text()
                admin_rights = self.admin_rights_edit.text()
                read_rights = self.read_rights_edit.text()

                try:
                    cursor.execute(
                        sql.SQL("ALTER TABLE {schema}.{table} OWNER TO {owner};").format(
                            schema=sql.Identifier(schema),
                            table=sql.Identifier(table_name),
                            owner=sql.Identifier(owner_rights)
                        )
                    )
                    cursor.execute(
                        sql.SQL("GRANT SELECT, UPDATE, INSERT, DELETE, REFERENCES ON TABLE {schema}.{table} TO {owner};").format(
                            schema=sql.Identifier(schema),
                            table=sql.Identifier(table_name),
                            owner=sql.Identifier(owner_rights)
                        )
                    )
                    cursor.execute(
                        sql.SQL("GRANT ALL ON TABLE {schema}.{table} TO {admin};").format(
                            schema=sql.Identifier(schema),
                            table=sql.Identifier(table_name),
                            admin=sql.Identifier(admin_rights)
                        )
                    )
                    cursor.execute(
                        sql.SQL("GRANT SELECT ON TABLE {schema}.{table} TO {read};").format(
                            schema=sql.Identifier(schema),
                            table=sql.Identifier(table_name),
                            read=sql.Identifier(read_rights)
                        )
                    )
                except Exception as e:
                    QMessageBox.warning(self, "Erreur", f"Erreur lors de l'allocation des droits pour {table_name} : {e}")

                # Sauvegarde de la métadonnée
                if metadata:
                    try:
                        cursor.execute(
                            sql.SQL("""
                            INSERT INTO {schema}.metadata_import (table_name, metadata, import_date)
                            VALUES (%s, %s, NOW());
                            """).format(schema=sql.Identifier(schema)),
                            (table_name, metadata)
                        )
                    except Exception as e:
                        QMessageBox.warning(self, "Erreur", f"Erreur lors de la sauvegarde de la métadonnée : {e}")

        conn.commit()
        cursor.close()
        conn.close()
        self.save_last_choices()
