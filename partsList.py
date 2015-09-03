'''
create parts list
'''
from assembly2lib import *
from PySide import QtCore

try:
    from dimensioning import getDrawingPageGUIVars, DimensioningProcessTracker
    import previewDimension
    dimensioningTracker = DimensioningProcessTracker()
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
    def svg(self, x, y, columns,
            strokeWidth = 0.4,
            fontSize = 4.0,
            fontColor = 'rgb(0,0,0)',
            fontPadding = 1.6,
            ):
        entries = [ e for e in self.entries if e.parentDirectory in self.directoryMask ]
        rowHeight = fontSize + 2*fontPadding
        XML_body = []
        def addLine(x1,y1,x2,y2):
            XML_body.append('<line x1="%f" y1="%f" x2="%f" y2="%f" style="stroke:rgb(0,0,0);stroke-width:%1.2f" />' % (x1, y1, x2, y2, strokeWidth))
        #building table body
        width = sum( c.width for c in columns )
        for i in range(len(entries) +2):
            addLine( x, y + i*rowHeight, x+width, y + i*rowHeight )
        y_bottom = y + i*rowHeight
        addLine( x, y, x, y_bottom )
        columnOffsets = [0]
        for c in columns:
            columnOffsets.append( columnOffsets[-1] + c.width )
            addLine( x+columnOffsets[-1], y, x+columnOffsets[-1], y_bottom )
        def addText(row,col,text):
            x1 = x + columnOffsets[col] + fontPadding
            y1 = y + (row+1)*rowHeight - fontPadding
            XML_body.append('<text x="%f" y="%f" fill="%s" style="font-size:%i">%s</text>' % (x1,y1,fontColor,fontSize,text))
        for i,c in enumerate(columns):
            addText(0,i,c.heading)
            for j, entry in enumerate(entries):
                addText( j+1, i,  c.entryFor(j, entry))

        XML = '''<g> %s </g>''' % ('\n'.join(XML_body) )
        debugPrint(4, 'partList.XML %s' % XML)
        return XML


class PartListEntry:
    def __init__(self, obj):
        self.obj = obj
        self.count = 1
        self.sourceFile = obj.sourceFile
        self.name = os.path.basename( obj.sourceFile )
        self.parentDirectory = os.path.basename( os.path.dirname( obj.sourceFile ))
    def __eq__(self, b):
        return  self.sourceFile == b.sourceFile

class PartListColumn:
    def __init__(self, heading, width, entryFor):
        self.heading = heading
        self.width = width
        self.entryFor = entryFor

def partsListSvg(x,y):
    d = dimensioningTracker
    columns = [
        PartListColumn(d.column_part_label,       d.column_part_width,       lambda ind,entry: '%i' % (ind+1)),
        PartListColumn(d.column_sourceFile_label, d.column_sourceFile_width, lambda ind,entry: '%s' % os.path.basename(entry.sourceFile).replace('.fcstd','')),
        PartListColumn(d.column_quantity_label,   d.column_quantity_width,   lambda ind,entry: '%i' % entry.count),
        ]
    return dimensioningTracker.partsList.svg( 
        x, y,
        columns,
        strokeWidth = d.strokeWidth,
        fontSize = d.fontSize,
        fontColor = d.fontColor,
        fontPadding = d.fontPadding
        )

def clickHandler( x, y):
    FreeCADGui.Control.closeDialog()
    return 'createDimension:%s' % findUnusedObjectName('dimPartsList')

class AddPartsList:
    def Activated(self):
        if not drawing_dimensioning_installed:
            QtGui.QMessageBox.critical( QtGui.qApp.activeWindow(), 'drawing dimensioning wb required', 'the parts list feature requires the drawing dimensioning wb (https://github.com/hamish2014/FreeCAD_drawing_dimensioning)' )
            return
        V = getDrawingPageGUIVars() #needs to be done before dialog show, else Qt active is dialog and not freecads
        dimensioningTracker.activate( V )
        P = PartsList()
        for obj in FreeCAD.ActiveDocument.Objects:
            if 'importPart' in obj.Content:
                debugPrint(3, 'adding %s to parts list' % obj.Name)
                P.addObject(obj)
        dimensioningTracker.partsList = P
        
        dimensioningTracker.taskPanelDialog =  PartsListTaskDialog()
        FreeCADGui.Control.showDialog( dimensioningTracker.taskPanelDialog )
        previewDimension.initializePreview( dimensioningTracker, partsListSvg, clickHandler )
        
    def GetResources(self): 
        tip = 'create a parts list from the objects imported using the assembly 2 workbench'
        from assembly2lib import __dir__
        return {
            'Pixmap' : os.path.join( __dir__ , 'partsList.svg' ) , 
            'MenuText': tip, 
            'ToolTip': tip
            } 
FreeCADGui.addCommand('addPartsList', AddPartsList())


class PartsListTaskDialog:
    def __init__(self):
        from assembly2lib import __dir__
        self.form = FreeCADGui.PySideUic.loadUi( os.path.join(__dir__, 'partsList.ui') )
        self.form.setWindowIcon(QtGui.QIcon( os.path.join( __dir__, 'partsList.svg' ) ) )
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
        for entry in dimensioningTracker.partsList.entries:
            if not entry.parentDirectory in filtersAdded:
                item = QtGui.QListWidgetItem('%s' % entry.parentDirectory, form.listWidget_directoryFilter)
                item.setCheckState( QtCore.Qt.CheckState.Checked )
                filtersAdded.append( entry.parentDirectory )
        dimensioningTracker.partsList.directoryMask = filtersAdded
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
        d = dimensioningTracker
        form = self.form
        d.column_part_width =       form.doubleSpinBox_column_part_width.value()
        d.column_sourceFile_width = form.doubleSpinBox_column_sourceFile_width.value()
        d.column_quantity_width =   form.doubleSpinBox_column_quantity_width.value()

        d.column_part_label =       form.lineEdit_column_part_label.text()
        d.column_sourceFile_label = form.lineEdit_column_sourceFile_label.text()
        d.column_quantity_label =   form.lineEdit_column_quantity_label.text()

        d.fontSize = form.doubleSpinBox_fontSize.value()
        d.fontColor = form.lineEdit_fontColor.text()

        d.fontPadding = form.doubleSpinBox_padding.value()
        d.strokeWidth =  form.doubleSpinBox_lineWidth.value()
    
    def update_directoryFilter(self, *args):
        try:
            del dimensioningTracker.partsList.directoryMask[:]
            listWidget = self.form.listWidget_directoryFilter
            for index in range(listWidget.count()):
                item = listWidget.item(index)
                if item.checkState() ==  QtCore.Qt.CheckState.Checked:
                    dimensioningTracker.partsList.directoryMask.append( item.text() )
        except:
            import traceback
            FreeCAD.Console.PrintError(traceback.format_exc())


    def reject(self):
        previewDimension.removePreviewGraphicItems( recomputeActiveDocument = True )
        FreeCADGui.Control.closeDialog()
        
    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00400000

