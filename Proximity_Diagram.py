# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Proximity_Diagram
                                 A QGIS plugin
 Create Proximity Diagram
 Generated by Plugin Builder: http://g-sherman.github.io/Qgis-Plugin-Builder/
                              -------------------
        begin                : 2021-05-27
        git sha              : $Format:%H$
        copyright            : (C) 2021 by Anna Bodnarchuk
        email                : bodnarchukania12@gmail.com
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""
from qgis.PyQt.QtCore import QSettings, QTranslator, QCoreApplication
from qgis.PyQt.QtGui import QIcon
from qgis.PyQt.QtWidgets import QAction
from qgis.core import QgsProject
from qgis.core import QgsProcessing
from qgis.core import QgsMapLayer,QgsWkbTypes
from qgis.core import QgsProcessingParameters
from qgis.core import QgsProcessingException
from qgis.core import QgsProcessingParameterBoolean
from qgis.core import QgsProcessingParameterDistance
from qgis.core import QgsProcessingParameterEnum
from qgis.core import QgsProcessingParameterPoint
from qgis.core import QgsProcessingParameterField
from qgis.core import QgsProcessingParameterNumber
from qgis.core import QgsProcessingParameterString
from qgis.core import QgsProcessingParameterFeatureSource
from qgis.core import QgsProcessingParameterFeatureSink
from qgis.core import QgsProcessingParameterDefinition
from qgis.core import QgsProcessingAlgorithm
from qgis.gui import QgsMessageBar
from PyQt5.QtWidgets import QAction,QMessageBox,QTableWidgetItem, QApplication,QSizePolicy,QGridLayout,QDialogButtonBox,QFileDialog,QProgressBar,QColorDialog,QToolBar
import processing
from processing.tools import dataobjects
from processing.algs.qgis.QgisAlgorithm import QgisAlgorithm
from qgis.core import QgsProcessingFeedback, Qgis, QgsProcessingMultiStepFeedback
from PyQt5.QtGui import *
from PyQt5.QtWidgets import QAction, QMessageBox, QTableWidgetItem, QApplication, QToolBar, QColorDialog, QFileDialog
from qgis.core import QgsFillSymbol
from qgis.core import QgsRenderContext
from qgis.core import QgsGradientColorRamp
from qgis.core import QgsRendererRangeLabelFormat
from qgis.core import QgsGraduatedSymbolRenderer
from qgis.core import QgsLayerTreeLayer
from qgis.utils import iface
from qgis.core import QgsPalLayerSettings
from qgis.core import QgsTextFormat
import psycopg2


# Initialize Qt resources from file resources.py
from .resources import *
# Import the code for the dialog
from .Proximity_Diagram_dialog import Proximity_DiagramDialog
import os.path

Versio_modul="V_Q3.211111"

class Proximity_Diagram:
    """QGIS Plugin Implementation."""

    def __init__(self, iface):
        """Constructor.

        :param iface: An interface instance that will be passed to this class
            which provides the hook by which you can manipulate the QGIS
            application at run time.
        :type iface: QgsInterface
        """
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value('locale/userLocale')[0:2]
        locale_path = os.path.join(
            self.plugin_dir,
            'i18n',
            'Proximity_Diagram_{}.qm'.format(locale))

        if os.path.exists(locale_path):
            self.translator = QTranslator()
            self.translator.load(locale_path)
            QCoreApplication.installTranslator(self.translator)

        '''
        Connexio dels botons amb les funcions que han de realitzar
        '''

        self.dlg = Proximity_DiagramDialog()
        self.dlg.bt_sortir.clicked.connect(self.on_click_Sortir)
        self.dlg.comboConnexio.currentIndexChanged.connect(self.on_Change_ComboConn)
        self.dlg.combo_punts.currentIndexChanged.connect(self.on_Change_ComboPunts)
        self.dlg.combo_polygons.currentIndexChanged.connect(self.on_Change_ComboPolygons)
        self.dlg.bt_inici.clicked.connect(self.on_click_Inici)
        self.dlg.bt_ReloadLeyenda.clicked.connect(self.cerca_elements_Leyenda)

        # Declare instance attributes
        self.actions = []
        self.menu = self.tr('&CCU')
        # Check if plugin was started the first time in current QGIS session
        # Must be set in initGui() to survive plugin reloads
        self.first_start = None

        trobat = False
        for x in iface.mainWindow().findChildren(QToolBar, 'CCU'):
            self.toolbar = x
            trobat = True

        if not trobat:
            self.toolbar = self.iface.addToolBar('CCU')
            self.toolbar.setObjectName('CCU')

        self.bar = QgsMessageBar()
        self.bar.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        self.dlg.setLayout(QGridLayout())
        self.dlg.layout().setContentsMargins(0, 0, 0, 0)
        self.dlg.buttonbox = QDialogButtonBox(QDialogButtonBox.Ok)
        self.dlg.buttonbox.accepted.connect(self.run)
        self.dlg.buttonbox.setVisible(False)
        self.dlg.layout().addWidget(self.dlg.buttonbox, 0, 0, 2, 1)
        self.dlg.layout().addWidget(self.bar, 0, 0, 1, 1)

    # noinspection PyMethodMayBeStatic
    def tr(self, message):
        """Get the translation for a string using Qt translation API.

        We implement this ourselves since we do not inherit QObject.

        :param message: String for translation.
        :type message: str, QString

        :returns: Translated version of message.
        :rtype: QString
        """
        # noinspection PyTypeChecker,PyArgumentList,PyCallByClass
        return QCoreApplication.translate('Proximity_Diagram', message)


    def add_action(
        self,
        icon_path,
        text,
        callback,
        enabled_flag=True,
        add_to_menu=True,
        add_to_toolbar=True,
        status_tip=None,
        whats_this=None,
        parent=None):
        """Add a toolbar icon to the toolbar.

        :param icon_path: Path to the icon for this action. Can be a resource
            path (e.g. ':/plugins/foo/bar.png') or a normal file system path.
        :type icon_path: str

        :param text: Text that should be shown in menu items for this action.
        :type text: str

        :param callback: Function to be called when the action is triggered.
        :type callback: function

        :param enabled_flag: A flag indicating if the action should be enabled
            by default. Defaults to True.
        :type enabled_flag: bool

        :param add_to_menu: Flag indicating whether the action should also
            be added to the menu. Defaults to True.
        :type add_to_menu: bool

        :param add_to_toolbar: Flag indicating whether the action should also
            be added to the toolbar. Defaults to True.
        :type add_to_toolbar: bool

        :param status_tip: Optional text to show in a popup when mouse pointer
            hovers over the action.
        :type status_tip: str

        :param parent: Parent widget for the new action. Defaults None.
        :type parent: QWidget

        :param whats_this: Optional text to show in the status bar when the
            mouse pointer hovers over the action.

        :returns: The action that was created. Note that the action is also
            added to self.actions list.
        :rtype: QAction
        """

        icon = QIcon(icon_path)
        action = QAction(icon, text, parent)
        action.triggered.connect(callback)
        action.setEnabled(enabled_flag)

        if status_tip is not None:
            action.setStatusTip(status_tip)

        if whats_this is not None:
            action.setWhatsThis(whats_this)

        if add_to_toolbar:
            self.toolbar.addAction(action)

        if add_to_menu:
            self.iface.addPluginToMenu(
                self.menu,
                action)

        self.actions.append(action)

        return action

    def initGui(self):
        """Create the menu entries and toolbar icons inside the QGIS GUI."""

        icon_path = ':/plugins/Proximity_Diagram/icon.png'
        self.add_action(
            icon_path,
            text=self.tr(u'Proximity_Diagram'),
            callback=self.run,
            parent=self.iface.mainWindow())

        # will be set False in run()
        self.first_start = True


    def unload(self):
        """Removes the plugin menu item and icon from QGIS GUI."""
        for action in self.actions:
            self.iface.removePluginMenu(
                self.tr('&CCU'),
                action)
            self.toolbar.removeAction(action)

    def on_click_ColorArea(self):
        """Aquesta funció obra un dialeg per poder triar el color de l'area que volem pintar. """
        global micolorArea
        aux = QColorDialog.getColor()
        if aux.isValid():
            micolorArea = aux
        # estilo='border:1px solid #000000; background-color: '+ micolorArea.name().decode('utf8')
        estilo = 'border:1px solid #000000; background-color: ' + micolorArea.name()
        self.dlg.colorArea.setStyleSheet(estilo)
        self.dlg.colorArea.setAutoFillBackground(True)
        pep = self.dlg.colorArea.palette().color(1)
        pass

    def on_click_Sortir(self):
        '''
        Tanca la finestra del plugin
        '''
        self.EstatInicial()
        self.dlg.close()

    def controlErrors(self):
        """Aquesta funció controla que tots els camps siguin correctes abans de fer el càlcul"""
        errors = []
        if self.dlg.comboConnexio.currentText() == 'Choose connection' and self.dlg.tabWidget_Destino.currentIndex() == 0:
            errors.append('Connection not selected')
        if self.dlg.tabWidget_Destino.currentIndex() == 0:
            if self.dlg.combo_punts.currentText() == 'Choose an entity' or self.dlg.combo_punts.currentText() == '':
                errors.append('Entitiy not selected')
            if self.dlg.combo_polygons.currentText() == 'Choose an entity' or self.dlg.combo_polygons.currentText() == '':
                errors.append('Polygon layer not selected')
        else:
            if self.dlg.combo_punts_2.currentText() == 'Choose an entity' or self.dlg.combo_punts_2.currentText() == '':
                errors.append('Entity layer not selected')
            if self.dlg.combo_polygons_2.currentText() == 'Choose an entity' or self.dlg.combo_polygons_2.currentText() == '':
                errors.append('Polygon layer not selected')

        '''try:
            numero = int(float(self.dlg.txt_iteracions.text()))
            if numero < 0:
                errors.append("El número d'iteracions no pot ser negatiu")
        except:
            errors.append("El número d'iteracions no és vàlid")'''


        return errors

    def puntsValid(self, taula):
        '''Aquesta funcio comprova si la taula de la capa de punts té els camps necessaris per fer els càlculs'''
        global cur
        global conn
        campNPlaces = False
        sql = "select exists (select * from information_schema.columns where table_schema = 'public' and table_name = '" + taula + "' and column_name = 'NPlaces');"
        cur.execute(sql)
        campNPlaces = cur.fetchall()
        campRadiInicial = True
        sql = "select exists (select * from information_schema.columns where table_schema = 'public' and table_name = '" + taula + "' and column_name = 'RadiInicial');"
        cur.execute(sql)
        campRadiInicial = cur.fetchall()
        campID = True
        sql = "select exists (select * from information_schema.columns where table_schema = 'public' and table_name = '" + taula + "' and column_name = 'id');"
        cur.execute(sql)
        campID = cur.fetchall()
        return campNPlaces[0][0] and campRadiInicial[0][0] and campID[0][0]

    def getConnections(self):
        """Aquesta funcio retorna les connexions que estan guardades en el projecte."""
        s = QSettings()
        s.beginGroup("PostgreSQL/connections")
        currentConnections = s.childGroups()
        s.endGroup()
        return currentConnections

    def populateComboBox(self, combo, list, predef, sort):
        """Procediment per omplir el combo especificat amb la llista suministrada"""
        combo.blockSignals(True)
        combo.clear()
        model = QStandardItemModel(combo)
        predefInList = None
        for elem in list:
            try:
                item = QStandardItem(unicode(elem))
            except TypeError:
                item = QStandardItem(str(elem))
            model.appendRow(item)
            if elem == predef:
                predefInList = elem
        if sort:
            model.sort(0)
        combo.setModel(model)
        if predef != "":
            if predefInList:
                combo.setCurrentIndex(combo.findText(predefInList))
            else:
                combo.insertItem(0, predef)
                combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def ompleCombos(self, combo, llista, predef, sort):
        """Aquesta funció omple els combos que li passem per paràmetres"""
        combo.blockSignals(True)
        combo.clear()
        model = QStandardItemModel(combo)
        predefInList = None
        for elem in llista:
            try:
                if isinstance(elem, tuple):
                    item = QStandardItem(unicode(elem[0]))
                else:
                    item = QStandardItem(str(elem))
            except TypeError:
                item = QStandardItem(str(elem[0]))
            model.appendRow(item)
            if elem == predef:
                predefInList = elem
        combo.setModel(model)
        if predef != "":
            if predefInList:
                combo.setCurrentIndex(combo.findText(predefInList))
            else:
                combo.insertItem(0, predef)
                combo.setCurrentIndex(0)
        combo.blockSignals(False)

    def EstatInicial(self):
        """Aquesta funció posa tots els elements de la interficie en el seu estat inicial."""
        global Versio_modul
        global micolor
        global micolorArea
        global TEMPORARY_PATH

        self.barraEstat_noConnectat()
        self.dlg.progressBar.setValue(0)
        self.dlg.progressBar.setVisible(False)
        self.dlg.progressBar.setMaximum(100)
        self.dlg.versio.setText(Versio_modul)
        self.dlg.tabWidget_Destino.setCurrentIndex(0)
        self.dlg.combo_punts.clear()
        self.dlg.combo_punts_2.clear()
        self.dlg.combo_polygons.clear()
        self.dlg.combo_polygons_2.clear()
        self.dlg.drop_fields.setVisible(False)

        self.dlg.setEnabled(True)
        if (os.name == 'nt'):
            TEMPORARY_PATH = os.environ['TMP']
        else:
            TEMPORARY_PATH = os.environ['TMPDIR']

        self.cerca_elements_Leyenda()
        QApplication.processEvents()

        # Processing feedback

    def progress_changed(self, progress):
        # print(progress)
        self.dlg.progressBar.setValue(progress)
        QApplication.processEvents()

        #      *****************************************************************************************************************
        #               INICI Proximity Diagram
        #      *****************************************************************************************************************

    def cerca_elements_Leyenda(self):
        try:  # Accedir als elements de la llegenda que siguin de tipus punt.
            punts = []
            polygons = []

            layers = QgsProject.instance().mapLayers().values()
            for layer in layers:
                # print(layer.type())
                if layer.type() == QgsMapLayer.VectorLayer:
                    if layer.wkbType() == QgsWkbTypes.Point or layer.wkbType() == QgsWkbTypes.MultiPoint:
                        punts.append(layer.name())
                    elif layer.wkbType() == QgsWkbTypes.Polygon or layer.wkbType() == QgsWkbTypes.MultiPolygon:
                        polygons.append(layer.name())

            self.ompleCombos(self.dlg.combo_punts_2, punts, 'Choose an entity', True)
            self.ompleCombos(self.dlg.combo_polygons_2, polygons, 'Choose an entity', True)
        except Exception as ex:
            missatge = "Error adding legend elements"
            print(missatge)
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)
            QMessageBox.information(None, "Error", missatge)
            return

    def on_click_Inici(self):

        self.progress_changed(10)
        self.dlg.progressBar.setVisible(True)
        self.dlg.setEnabled(False)
        QApplication.processEvents()

        f0 = QgsProcessingFeedback()
        f = QgsProcessingMultiStepFeedback(12, f0)
        f.progressChanged.connect(self.progress_changed)

        errors = self.controlErrors()
        if len(errors) > 0:
            llista = "Error list:\n\n"
            for i in range(0, len(errors)):
                llista += ("- " + errors[i] + '\n')

            QMessageBox.information(None, "Error", llista)
            self.dlg.setEnabled(True)
            self.dlg.progressBar.setVisible(False)
            self.dlg.setEnabled(True)
            return

        if self.dlg.tabWidget_Destino.currentIndex() == 0:
            point_layer = self.dlg.combo_punts.currentText()

            parameters = {
                'DATABASE': self.dlg.comboConnexio.currentText(),
                'SQL': 'SELECT *\nFROM \"' + point_layer + '\"',
                'ID_FIELD': 'id',
                'OUTPUT': 'memory:'
            }
            postgis_execute_and_load_sql_out = processing.run('qgis:postgisexecuteandloadsql', parameters, feedback=f)
            result = postgis_execute_and_load_sql_out['OUTPUT']
        else:
            result = self.loadLayerFromLegend(self.dlg.combo_punts_2.currentText())

        # Transform geometry from multipart to monopart
        parameters = {
            'INPUT': result,
            'OUTPUT': 'memory:'
        }
        geometry_mono = processing.run('native:multiparttosingleparts', parameters, feedback=f)
        
        # Add geometry attributes to IES

        parameters = {
            'INPUT': geometry_mono['OUTPUT'],
            'CALC_METHOD': 0,
            'OUTPUT': 'memory:'
        }
        geometry_attributes_out = processing.run('qgis:exportaddgeometrycolumns', parameters, feedback=f)

        #QgsProject.instance().addMapLayer(geometry_mono['OUTPUT'])

        # Buffer, we use the output from 'Add geometry attributes'

        parameters = {
            'INPUT': geometry_attributes_out['OUTPUT'],
            'DISTANCE': 3000,
            'SEGMENTS': 5,
            'END_CAP_STYLE': 0,
            'JOIN_STYLE': 0,
            'MITER_LIMIT': 2,
            'DISSOLVE': False,
            'OUTPUT': 'memory:'
        }
        buffer_out = processing.run('native:buffer', parameters, feedback=f)

        # QgsProject.instance().addMapLayer(buffer_out['OUTPUT'])
        if self.dlg.tabWidget_Destino.currentIndex() == 0:
            polygon_layer = self.dlg.combo_polygons.currentText()

            parameters = {
                'DATABASE': self.dlg.comboConnexio.currentText(),
                'SQL': 'SELECT *\nFROM \"' + polygon_layer + '\"',
                'ID_FIELD': 'id',
                'OUTPUT': 'memory:'
            }
            postgis_execute_and_load_sql_out1 = processing.run('qgis:postgisexecuteandloadsql', parameters, feedback=f)
            result = postgis_execute_and_load_sql_out1['OUTPUT']
        else:
            result = self.loadLayerFromLegend(self.dlg.combo_polygons_2.currentText())

        # Transform geometry from multipart to monopart
        parameters = {
            'INPUT': result,
            'OUTPUT': 'memory:'
        }
        geometry_mono = processing.run('native:multiparttosingleparts', parameters, feedback=f)

        # Field calculator for ILLES/IES

        parameters = {
            'INPUT': geometry_mono['OUTPUT'],
            'FIELD_NAME': 'UNIC',
            'FIELD_TYPE': 2,
            'FIELD_LENGTH': 99,
            'FIELD_PRECISION': 4,
            'FORMULA': ' uuid() ',
            'OUTPUT': 'memory:'
        }
        field_calculator_out = processing.run('qgis:fieldcalculator', parameters, feedback=f)

        # QgsProject.instance().addMapLayer(field_calculator_out['OUTPUT'])

        # Field calculator 1 for ILLES/IES

        parameters = {
            'INPUT': field_calculator_out['OUTPUT'],
            'FIELD_NAME': 'Xc',
            'FIELD_TYPE': 0,
            'FIELD_LENGTH': 99,
            'FIELD_PRECISION': 4,
            'FORMULA': ' x( centroid( $geometry))',
            'OUTPUT': 'memory:'
        }
        field_calculator_1_out = processing.run('qgis:fieldcalculator', parameters, feedback=f)

        # QgsProject.instance().addMapLayer(field_calculator_1_out['OUTPUT'])

        # Field calculator 2 for ILLES/IES

        parameters = {
            'INPUT': field_calculator_1_out['OUTPUT'],
            'FIELD_NAME': 'Yc',
            'FIELD_TYPE': 0,
            'FIELD_LENGTH': 99,
            'FIELD_PRECISION': 4,
            'FORMULA': ' y( centroid( $geometry))',
            'OUTPUT': 'memory:'
        }
        field_calculator_2_out = processing.run('qgis:fieldcalculator', parameters, feedback=f)

        # QgsProject.instance().addMapLayer(field_calculator_2_out['OUTPUT'])

        # Join attributes by location, we use the output from Field calculator 2 and Buffer

        parameters = {
            'INPUT': field_calculator_2_out['OUTPUT'],
            'JOIN': buffer_out['OUTPUT'],
            'PREDICATE': [0],
            'JOIN_FIELDS': ['Nom', 'xcoord', 'ycoord'],
            'METHOD': 0,
            'DISCARD_NONMATCHING': [True],
            'PREFIX': '',
            'OUTPUT': 'memory:'
        }
        join_attributes_by_location_out = processing.run('qgis:joinattributesbylocation', parameters, feedback=f)

        # QgsProject.instance().addMapLayer(join_attributes_by_location_out['OUTPUT'])

        # Field calculator 3, we use the output from Join attributes by location

        parameters = {
            'INPUT': join_attributes_by_location_out['OUTPUT'],
            'FIELD_NAME': 'DIST',
            'FIELD_TYPE': 0,
            'FIELD_LENGTH': 99,
            'FIELD_PRECISION': 4,
            'FORMULA': 'sqrt(( ycoord - Yc ) ^ 2 + ( xcoord - Xc ) ^ 2)',
            'OUTPUT': 'memory:'
        }
        field_calculator_3_out = processing.run('qgis:fieldcalculator', parameters, feedback=f)

        # QgsProject.instance().addMapLayer(field_calculator_3_out['OUTPUT'])

        # Field calculator 4, we use the output from Field calculator 3

        parameters = {
            'INPUT': field_calculator_3_out['OUTPUT'],
            'FIELD_NAME': 'dst',
            'FIELD_TYPE': 0,
            'FIELD_LENGTH': 99,
            'FIELD_PRECISION': 4,
            'FORMULA': 'minimum( DIST,group_by:="UNIC" )',
            'OUTPUT': 'memory:'
        }
        field_calculator_4_out = processing.run('qgis:fieldcalculator', parameters, feedback=f)

        # QgsProject.instance().addMapLayer(field_calculator_4_out['OUTPUT'])

        # Extact by expression we use the output from Field calculator 4

        parameters = {
            'INPUT': field_calculator_4_out['OUTPUT'],
            'EXPRESSION': ' \"DIST\" = \"dst\" ',
            'OUTPUT': 'memory:',
            'FAIL_OUTPUT': 'memory:'
        }
        extact_by_expression_out = processing.run('native:extractbyexpression', parameters, feedback=f)

        # QgsProject.instance().addMapLayer(extact_by_expression_out['OUTPUT'])

        if self.dlg.drop_fields.isChecked():
            self.dlg.progressBar.setVisible(False)
            return self.showTematic(extact_by_expression_out['OUTPUT'])
        else:
            # Drop fields from Extact by expression

            parameters = {
                'INPUT': extact_by_expression_out['OUTPUT'],
                'COLUMN': ['Xc', 'Yc', 'UNIC', 'xcoord', 'ycoord', 'dst'],
                'OUTPUT': 'memory:'
            }
            drop_fields_out = processing.run('qgis:deletecolumn', parameters, feedback=f)

            # QgsProject.instance().addMapLayer(drop_fields_out['OUTPUT'])
            self.dlg.progressBar.setVisible(False)
            self.dlg.setEnabled(True)

            return self.showTematic(drop_fields_out['OUTPUT'])

    def loadLayerFromLegend(self, comboText):
        result = None
        layers = QgsProject.instance().mapLayers().values()
        if layers != None:
            for layer in layers:
                if layer.name() == comboText:
                    result = layer
                    break
        return result

    def showTematic(self, vlayer):
        global micolorTag
        global TEMPORARY_PATH
        # try:
        QApplication.processEvents()
        if vlayer.isValid():
            QApplication.processEvents()
            """Es carrega el Shape a l'entorn del QGIS"""
            symbols = vlayer.renderer().symbols(QgsRenderContext())
            symbol = symbols[0]

            fieldname = "DIST"

            template = "%1 - %2 "

            numberOfClasses = int(float(self.dlg.LE_rang.value()))
            myRangeList = []
            mysymbol = QgsFillSymbol()

            if (self.dlg.ColorDegradat.currentText() == 'Gray'):
                colorRamp = QgsGradientColorRamp(QColor(255, 255, 255), QColor(0, 0, 0))
            elif (self.dlg.ColorDegradat.currentText() == 'Red'):
                colorRamp = QgsGradientColorRamp(QColor(255, 255, 255), QColor(255, 0, 0))
            elif (self.dlg.ColorDegradat.currentText() == 'Yellow'):
                colorRamp = QgsGradientColorRamp(QColor(255, 255, 255), QColor(255, 255, 0))
            elif (self.dlg.ColorDegradat.currentText() == 'Blue'):
                colorRamp = QgsGradientColorRamp(QColor(255, 255, 255), QColor(0, 0, 255))
            elif (self.dlg.ColorDegradat.currentText() == 'Green'):
                colorRamp = QgsGradientColorRamp(QColor(255, 255, 255), QColor(0, 255, 0))

            format = QgsRendererRangeLabelFormat()

            precision = 3

            format.setFormat(template)
            format.setPrecision(precision)
            format.setTrimTrailingZeroes(False)
            '''
            if (self.dlg.combo_Tipus.currentText() == 'Quantil'):
                renderer = QgsGraduatedSymbolRenderer.createRenderer(vlayer, fieldname, numberOfClasses,
                                                                     QgsGraduatedSymbolRenderer.Quantile,
                                                                     mysymbol, colorRamp)
            elif (self.dlg.combo_Tipus.currentText() == 'Interval igual'):
                renderer = QgsGraduatedSymbolRenderer.createRenderer(vlayer, fieldname, numberOfClasses,
                                                                     QgsGraduatedSymbolRenderer.EqualInterval,
                                                                     mysymbol, colorRamp)
            elif (self.dlg.combo_Tipus.currentText() == 'Ruptures naturals'):
                renderer = QgsGraduatedSymbolRenderer.createRenderer(vlayer, fieldname, numberOfClasses,
                                                                     QgsGraduatedSymbolRenderer.Jenks, mysymbol,
                                                                     colorRamp)
            elif (self.dlg.combo_Tipus.currentText() == 'Desviació estandard'):
                renderer = QgsGraduatedSymbolRenderer.createRenderer(vlayer, fieldname, numberOfClasses,
                                                                     QgsGraduatedSymbolRenderer.StdDev,
                                                                     mysymbol, colorRamp)
            elif (self.dlg.combo_Tipus.currentText() == 'Pretty breaks'):
                renderer = QgsGraduatedSymbolRenderer.createRenderer(vlayer, fieldname, numberOfClasses,
                                                                     QgsGraduatedSymbolRenderer.Pretty,
                                                                     mysymbol, colorRamp)

            '''
            renderer = QgsGraduatedSymbolRenderer.createRenderer(vlayer, fieldname, numberOfClasses,
                                                                 QgsGraduatedSymbolRenderer.Quantile,
                                                                 mysymbol, colorRamp)

            renderer.setLabelFormat(format, True)
            # vlayer.setOpacity(self.dlg.Transparencia.value() / 100)
            vlayer.setRenderer(renderer)
            QApplication.processEvents()

            QApplication.processEvents()
            QgsProject.instance().addMapLayer(vlayer, False)
            root = QgsProject.instance().layerTreeRoot()
            myLayerNode = QgsLayerTreeLayer(vlayer)
            root.insertChildNode(0, myLayerNode)
            myLayerNode.setCustomProperty("showFeatureCount", True)
            iface.mapCanvas().refresh()

            for layer in QgsProject.instance().mapLayers().values():
                if layer.id() == vlayer.id():
                    layer.setName("Distant ranges in meters")
                    break

        else:
            print("Error vector layer")
        QApplication.processEvents()
        '''except Exception as ex:
            print("Error a la connexio")
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)
            #self.progress_changed(0)
            self.dlg.setEnabled(True)
            #self.barraEstat_connectat()
            QMessageBox.information(None, "Error",
                                    "Error mostrant el vlayer per pantalla.")
'''

    def on_click_MarcarIlles(self, clicked):
        """Aquesta funció controla l'aparença del botó Illes """
        if clicked:
            self.dlg.bt_ILLES.setStyleSheet('background-color: #7fff7f')
            self.dlg.bt_Parcel.setChecked(False)
            self.dlg.bt_Portals.setChecked(False)
            self.dlg.color.setStyleSheet('border:1px solid #000000; background-color: #ff0000')
            micolor = QColor(255, 0, 0, 255)
        else:
            self.dlg.bt_ILLES.setChecked(False)
            self.dlg.bt_ILLES.setStyleSheet('background-color: rgb(227, 227, 227)')

    def on_click_MarcarParcel(self, clicked):
        """Aquesta funció controla l'aparença del botó Parceles """
        if clicked:
            self.dlg.bt_Parcel.setStyleSheet('background-color: #7fff7f')
            self.dlg.bt_ILLES.setChecked(False)
            self.dlg.bt_Portals.setChecked(False)
            self.dlg.color.setStyleSheet('border:1px solid #000000; background-color: #0000ff')
            micolor = QColor(0, 0, 255, 255)
        else:
            self.dlg.bt_Parcel.setChecked(False)
            self.dlg.bt_Parcel.setStyleSheet('background-color: rgb(227, 227, 227)')

    def on_Change_ComboConn(self):
        """
        En el moment en que es modifica la opcio escollida
        del combo o desplegable de les connexions,
        automàticament comprova si es pot establir
        connexió amb la bbdd seleccionada.
        """
        global nomBD1
        global contra1
        global host1
        global port1
        global usuari1
        global schema
        global cur
        global conn
        s = QSettings()
        self.dlg.combo_punts.clear()
        # self.dlg.comboLeyenda.clear()
        select = 'Selecciona connexió'
        nom_conn = self.dlg.comboConnexio.currentText()
        if nom_conn != select:
            s.beginGroup("PostgreSQL/connections/" + nom_conn)
            currentKeys = s.childKeys()

            nomBD1 = s.value("database", "")
            contra1 = s.value("password", "")
            host1 = s.value("host", "")
            port1 = s.value("port", "")
            usuari1 = s.value("username", "")
            schema = 'public'

            self.dlg.lblEstatConn.setStyleSheet('border:1px solid #000000; background-color: #ffff7f')
            self.dlg.lblEstatConn.setText('Connecting...')
            self.dlg.lblEstatConn.setAutoFillBackground(True)
            QApplication.processEvents()

            # Connexio
            nomBD = nomBD1.encode('ascii', 'ignore')
            usuari = usuari1.encode('ascii', 'ignore')
            servidor = host1.encode('ascii', 'ignore')
            contrasenya = contra1.encode('ascii', 'ignore')
            try:
                estructura = "dbname='" + nomBD.decode("utf-8") + "' user='" + usuari.decode(
                    "utf-8") + "' host='" + servidor.decode("utf-8") + "' password='" + contrasenya.decode(
                    "utf-8") + "'"  # schema='"+schema+"'"
                print("1")
                conn = psycopg2.connect(estructura)
                print("2")
                self.barraEstat_connectat()
                cur = conn.cursor()
                sql = "select f_table_name from geometry_columns where type = 'POINT' and f_table_schema ='public' order by 1"
                cur.execute(sql)
                llista = cur.fetchall()
                print("3")
                self.ompleCombos(self.dlg.combo_punts, llista, 'Choose an entity', True)

                sql = "select f_table_name from geometry_columns where (type = 'MULTIPOLYGON' or type = 'POLYGON') and f_table_schema ='public' order by 1"
                cur.execute(sql)
                llista = cur.fetchall()
                print("3")
                self.ompleCombos(self.dlg.combo_polygons, llista, 'Choose an entity', True)
            except Exception as ex:
                self.dlg.setEnabled(True)
                print("Error connecting")
                template = "An exception of type {0} occurred. Arguments:\n{1!r}"
                message = template.format(type(ex).__name__, ex.args)
                print(message)
                self.barraEstat_Error()
                QMessageBox.information(None, "Error", "Error connecting")
                self.dlg.lblEstatConn.setStyleSheet('border:1px solid #000000; background-color: #ff7f7f')
                self.dlg.lblEstatConn.setText('Error: There''s an invalid field.')
                print("I am unable to connect to the database")

                return

            # self.DropTemporalTables()
        else:
            self.barraEstat_noConnectat()

    def on_Change_ComboPunts(self, state):
        """
        En el moment en que es modifica la opcio escollida
        del combo o desplegable de la capa de punts,
        automàticament comprova els camps de la taula escollida.
        """
        try:
            capa = self.dlg.combo_punts.currentText()
        except Exception as ex:
            self.dlg.setEnabled(True)
            print("Error Change_ComboPunts")
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)
            self.barraEstat_Error()
            QMessageBox.information(None, "Error", "Change_ComboPunts")
            return

    def on_Change_ComboPolygons(self, state):
        """
        En el moment en que es modifica la opcio escollida
        del combo o desplegable de la capa de punts,
        automàticament comprova els camps de la taula escollida.
        """
        try:
            capa = self.dlg.combo_polygons.currentText()
        except Exception as ex:
            self.dlg.setEnabled(True)
            print("Error Change_ComboPunts")
            template = "An exception of type {0} occurred. Arguments:\n{1!r}"
            message = template.format(type(ex).__name__, ex.args)
            print(message)
            self.barraEstat_Error()
            QMessageBox.information(None, "Error", "Change_ComboPolygons")
            return

    def barraEstat_llegint(self):
        self.dlg.lblEstatConn.setStyleSheet('border:1px solid #000000; background-color: rgb(255, 170, 142)')
        self.dlg.lblEstatConn.setText("Reading...")

    def barraEstat_processant(self):
        self.dlg.lblEstatConn.setStyleSheet('border:1px solid #000000; background-color: rgb(255, 125, 155)')
        self.dlg.lblEstatConn.setText("Processing...")

    def barraEstat_noConnectat(self):
        self.dlg.lblEstatConn.setStyleSheet('border:1px solid #000000; background-color: #FFFFFF')
        self.dlg.lblEstatConn.setText('Not connected')

    def barraEstat_Error(self):
        self.dlg.lblEstatConn.setStyleSheet('border:1px solid #000000; background-color: #FF0000')
        self.dlg.lblEstatConn.setText('Error')

    def barraEstat_connectat(self):
        self.dlg.lblEstatConn.setStyleSheet('border:1px solid #000000; background-color: #7fff7f')
        self.dlg.lblEstatConn.setText('Connected')

    def run(self):
        """Run method that performs all the real work"""

        # Create the dialog with elements (after translation) and keep reference
        # Only create GUI ONCE in callback, so that it will only load when the plugin is started
        self.EstatInicial()
        # show the dialog
        self.dlg.show()
        conn = self.getConnections()
        # Run the dialog event loop
        # Run the dialog event loop
        self.populateComboBox(self.dlg.comboConnexio, conn, 'Choose connection', True)
        # Run the dialog event loop
        result = self.dlg.exec_()
        # See if OK was pressed
        if result:
            # Do something useful here - delete the line containing pass and
            # substitute with your code.
            pass

    def arxiusExisteixen(self, path):
            '''Aquesta funcio s'encarrega de comprovar que els arxius necessaris per a cada execució estiguin a la carpeta seleccio'''
            if self.dlg.bt_ILLES.isChecked():
                if (os.path.exists(path + "/tr_illes.csv")):
                    return True
                else:
                    QMessageBox.information(None, "ERROR 0: READING ILLES", "ILLES file not found.")
                    return False
            elif (self.dlg.bt_Parcel.isChecked()):
                if (os.path.exists(path + "/tr_parceles.csv") and os.path.exists(path + "/tr_illes.csv")):
                    return True
                else:
                    QMessageBox.information(None, "ERROR 1: READING PARCELES", "ILLES and PARCELES files not found.")
                    return False
            else:
                if (os.path.exists(path + "/tr_npolicia.csv") and os.path.exists(path + "/tr_illes.csv")):
                    return True
                else:
                    QMessageBox.information(None, "ERROR 2: READING NUMEROS DE POLICIA", "NUMEROS DE POLICIA file not found.")
                    return False