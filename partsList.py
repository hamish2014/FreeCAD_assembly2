'''
create parts list
'''
from assembly2lib import *
from PySide import QtCore

try:
    from dimensioning import getDrawingPageGUIVars, PlacementClick
    import previewDimension, table_dd #Added 12 April 2016
    from svgLib_dd import SvgTextRenderer
    #dimensioningTracker = DimensioningProcessTracker()
    d = table_dd.d
    drawing_dimensioning_installed = True
except ImportError:
    drawing_dimensioning_installed = False

class PartsList:
    def __init__(self):
        self.entries = []
        self.directoryMask = []
    def addObject(self, obj):
        try:
            index = self.entries.index(obj)
            self.entries[index].count = self.entries[index].count + 1
        except ValueError:
            self.entries.append(PartListEntry( obj ))
class PartListEntry:
    def __init__(self, obj):
        self.obj = obj
        self.count = 1
        self.sourceFile = obj.sourceFile
        self.name = os.path.basename( obj.sourceFile )
        self.parentDirectory = os.path.basename( os.path.dirname( obj.sourceFile ))
    def __eq__(self, b):
        return  self.sourceFile == b.sourceFile


def parts_list_clickHandler( x, y ):
    d.selections = [ PlacementClick( x, y) ]
    return 'createDimension:%s' % findUnusedObjectName('partsList')


class AddPartsList:
    def Activated(self):
        if not drawing_dimensioning_installed:
            QtGui.QMessageBox.critical( QtGui.qApp.activeWindow(), 'drawing dimensioning wb required', 'the parts list feature requires the drawing dimensioning wb (https://github.com/hamish2014/FreeCAD_drawing_dimensioning). Release from 12 April 2016 or later required.' )
            return
        V = getDrawingPageGUIVars() #needs to be done before dialog show, else Qt active is dialog and not freecads
        d.activate( V, dialogIconPath= ':/assembly2/icons/partsList.svg')
        P = PartsList()
        for obj in FreeCAD.ActiveDocument.Objects:
            if 'importPart' in obj.Content:
                debugPrint(3, 'adding %s to parts list' % obj.Name)
                P.addObject( PartListEntry(obj) )
        d.partsList = P
        for pref in d.preferences:
            pref.dimensioningProcess = d #required to be compadible with drawing dimensioning
        d.taskDialog =  PartsListTaskDialog()
        FreeCADGui.Control.showDialog( d.taskDialog )
        previewDimension.initializePreview( d, table_dd.table_preview, parts_list_clickHandler )
        
    def GetResources(self): 
        tip = 'create a parts list from the objects imported using the assembly 2 workbench'
        return {
            'Pixmap' : ':/assembly2/icons/partsList.svg' , 
            'MenuText': tip, 
            'ToolTip': tip
            } 
FreeCADGui.addCommand('addPartsList', AddPartsList())


class PartsListTaskDialog:
    def __init__(self):
        from assembly2lib import __dir__
        self.form = FreeCADGui.PySideUic.loadUi( ':/assembly2/ui/partsList.ui' )
        self.form.setWindowIcon(QtGui.QIcon( ':/assembly2/icons/partsList.svg' ) )
        self.setIntialValues()
        self.getValues()
        for groupBox in self.form.children():
            for w in groupBox.children():
                if hasattr(w, 'valueChanged'):
                    w.valueChanged.connect( self.getValues )
                if isinstance(w, QtGui.QLineEdit):
                    w.textChanged.connect( self.getValues ) 
        self.form.pushButton_set_as_default.clicked.connect( self.setDefaults )

    def setIntialValues(self):
        parms = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2/partsList")
        form = self.form
        form.doubleSpinBox_column_part_width.setValue(         parms.GetFloat('column_part_width', 20) )
        form.doubleSpinBox_column_sourceFile_width.setValue(   parms.GetFloat('column_sourceFile_width', 80) )
        form.doubleSpinBox_column_quantity_width.setValue(     parms.GetFloat('column_quantity_width', 40)  )
        form.lineEdit_column_part_label.setText(               parms.GetString('column_part_label', 'part #'))
        form.lineEdit_column_sourceFile_label.setText(         parms.GetString('column_sourceFile_label', 'source file'))
        form.lineEdit_column_quantity_label.setText(           parms.GetString('column_quantity_label', 'quantity'))
        form.doubleSpinBox_lineWidth.setValue(                 parms.GetFloat('lineWidth', 0.4) )
        form.doubleSpinBox_fontSize.setValue(                  parms.GetFloat('fontSize', 4.0) )
        form.lineEdit_fontColor.setText(                       parms.GetString('fontColor','rgb(0,0,0)') )
        form.doubleSpinBox_padding.setValue(                   parms.GetFloat('padding', 1.5))
        filtersAdded = []
        for entry in d.partsList.entries:
            if not entry.parentDirectory in filtersAdded:
                item = QtGui.QListWidgetItem('%s' % entry.parentDirectory, form.listWidget_directoryFilter)
                item.setCheckState( QtCore.Qt.CheckState.Checked )
                filtersAdded.append( entry.parentDirectory )
        d.partsList.directoryMask = filtersAdded
        form.listWidget_directoryFilter.itemChanged.connect( self.update_directoryFilter )  

    def setDefaults(self):
        parms = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2/partsList")
        form = self.form        
        parms.SetFloat('column_part_width',       form.doubleSpinBox_column_part_width.value()       )
        parms.SetFloat('column_sourceFile_width', form.doubleSpinBox_column_sourceFile_width.value() )
        parms.SetFloat('column_quantity_width',   form.doubleSpinBox_column_quantity_width.value()   )
        parms.SetString('column_part_label',      form.lineEdit_column_part_label.text()             )
        parms.SetString('column_sourceFile_label',form.lineEdit_column_sourceFile_label.text()       ) 
        parms.SetString('column_quantity_label',  form.lineEdit_column_quantity_label.text()         )
        parms.SetFloat('lineWidth',               form.doubleSpinBox_lineWidth.value()               )
        parms.SetFloat('fontSize',                form.doubleSpinBox_fontSize.value()                )
        parms.SetString('fontColor',              form.lineEdit_fontColor.text()                     )
        parms.SetFloat('padding',                 form.doubleSpinBox_padding.setValue()              )


    def getValues(self, notUsed=None):
        form = self.form
        contents = [
            form.lineEdit_column_part_label.text(),
            form.lineEdit_column_sourceFile_label.text(),
            form.lineEdit_column_quantity_label.text()
            ]
        partsList = d.partsList
        entries = [ e for e in partsList.entries if e.parentDirectory in partsList.directoryMask ]
        for ind, entry in enumerate(entries):
            contents.extend([
                str(ind+1),
                os.path.basename(entry.sourceFile).replace('.fcstd',''),
                str(entry.count)
                ])
        d.dimensionConstructorKWs = dict(
            column_widths = [
                form.doubleSpinBox_column_part_width.value(),
                form.doubleSpinBox_column_sourceFile_width.value(),
                form.doubleSpinBox_column_quantity_width.value()
                ],
            contents = contents,
            row_heights = [
                form.doubleSpinBox_fontSize.value() + 2*form.doubleSpinBox_padding.value()
                ],
            border_width = form.doubleSpinBox_lineWidth.value(),
            border_color='rgb(0,0,0)',
            padding_x = form.doubleSpinBox_padding.value(), 
            padding_y = form.doubleSpinBox_padding.value(), 
            extra_rows= 0,
            textRenderer_table = SvgTextRenderer(
                u'inherit', 
                u'%1.2f pt' % form.doubleSpinBox_fontSize.value(), 
                form.lineEdit_fontColor.text() 
                )
            )
    
    def update_directoryFilter(self, *args):
        try:
            del d.partsList.directoryMask[:]
            listWidget = self.form.listWidget_directoryFilter
            for index in range(listWidget.count()):
                item = listWidget.item(index)
                if item.checkState() ==  QtCore.Qt.CheckState.Checked:
                    d.partsList.directoryMask.append( item.text() )
            self.getValues()
        except:
            import traceback
            FreeCAD.Console.PrintError(traceback.format_exc())

    def reject(self):
        previewDimension.removePreviewGraphicItems( recomputeActiveDocument = True )
        FreeCADGui.Control.closeDialog()
        
    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00400000

