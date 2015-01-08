'''
create parts list
'''
from assembly2lib import *
from assembly2lib import __dir__
try:
    from dimensioning import getDrawingPageGUIVars, DimensioningProcessTracker
    import previewDimension
    dimensioning = DimensioningProcessTracker()
    drawing_dimensioning_installed = True
except ImportError:
    drawing_dimensioning_installed = False

strokeWidth = 0.4

fontSize = 4.0
fontColor = 'rgb(0,0,0)'
fontPadding = 1.6
rowHeight = fontSize + 2*fontPadding


class PartsList:
    def __init__(self):
        self.entries = []
    def addObject(self, obj):
        try:
            index = self.entries.index(obj)
            self.entries[index].count = self.entries[index].count + 1
        except ValueError:
            self.entries.append(PartListEntry( obj ))
    def svg(self, x, y, svgTag='g', svgParms=''):
        XML_body = []
        def addLine(x1,y1,x2,y2):
            XML_body.append('<line x1="%f" y1="%f" x2="%f" y2="%f" style="stroke:rgb(0,0,0);stroke-width:%1.2f" />' % (x1, y1, x2, y2, strokeWidth))
        #building table body
        width = sum( c.width for c in columns )
        for i in range(len(self.entries) +2):
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
            for j, entry in enumerate(self.entries):
                addText( j+1, i,  c.entryFor(j, entry))

        XML = '''<%s  %s > %s </%s> ''' % ( svgTag, svgParms, '\n'.join(XML_body), svgTag )
        debugPrint(4, 'partList.XML %s' % XML)
        return XML


class PartListEntry:
    def __init__(self, obj):
        self.obj = obj
        self.count = 1
        self.sourceFile = obj.sourceFile
        self.name = os.path.basename( obj.sourceFile )
    def __eq__(self, b):
        return  self.sourceFile == b.sourceFile

class PartListColumn:
    def __init__(self, heading, width, entryFor):
        self.heading = heading
        self.width = width
        self.entryFor = entryFor

columns = [
    PartListColumn('part', 20, lambda ind,entry: '%i' % (ind+1)),
    PartListColumn('sourceFile', 80, lambda ind,entry: '%s' % os.path.basename(entry.sourceFile).replace('.fcstd','')),
    PartListColumn('quantity', 40, lambda ind,entry: '%i' % entry.count),
    ]
        

def clickEvent( x, y):
    viewName = findUnusedObjectName('dimPartsList')
    XML = dimensioning.partsList.svg(x,y)
    return viewName, XML

def hoverEvent( x, y):
    return dimensioning.partsList.svg( x, y,svgTag=dimensioning.svg_preview_KWs['svgTag'], svgParms=dimensioning.svg_preview_KWs['svgParms'] )

class AddPartsList:
    def Activated(self):
        if not drawing_dimensioning_installed:
            QtGui.QMessageBox.critical( QtGui.qApp.activeWindow(), 'drawing dimensioning wb required', 'the parts list feature requires the drawing dimensioning wb (https://github.com/hamish2014/FreeCAD_drawing_dimensioning/network)' )
            return
        V = getDrawingPageGUIVars() #needs to be done before dialog show, else Qt active is dialog and not freecads
        dimensioning.activate( V )
        P = PartsList()
        for obj in FreeCAD.ActiveDocument.Objects:
            if 'importPart' in obj.Content:
                debugPrint(3, 'adding %s to parts list' % obj.Name)
                P.addObject(obj)
        dimensioning.partsList = P
        P.svg(0,0) #calling here as once inside previewRect, error trapping difficult...
        previewDimension.initializePreview( V, clickEvent, hoverEvent )
        
    def GetResources(self): 
        tip = 'create a parts list from the objects imported using the assembly 2 workbench'
        return {
            'Pixmap' : os.path.join( __dir__ , 'partsList.svg' ) , 
            'MenuText': tip, 
            'ToolTip': tip
            } 
FreeCADGui.addCommand('addPartsList', AddPartsList())


