import numpy, os, sys
import FreeCAD
import FreeCADGui
import Part
from PySide import QtGui, QtCore

path_assembly2 = os.path.dirname( os.path.dirname(__file__) )
#path_assembly2_icons =  os.path.join( path_assembly2, 'Resources', 'icons')
#path_assembly2_ui =  os.path.join( path_assembly2, 'Resources', 'ui')
path_assembly2_resources = os.path.join( path_assembly2, 'Gui', 'Resources', 'resources.rcc')
resourcesLoaded = QtCore.QResource.registerResource(path_assembly2_resources)
assert resourcesLoaded
#update resources file using 
# $rcc -binary  Gui/Resources/resources.qrc -o Gui/Resources/resources.rcc 

__dir__ = path_assembly2
wb_globals = {}
__dir2__ = os.path.dirname(__file__)
GuiPath = os.path.expanduser ("~") #GuiPath = os.path.join( __dir2__, 'Gui' )

def make_string(input):
    if (sys.version_info > (3, 0)):  #py3
        if isinstance(input, str):
            return input
        else:
            input =  input.encode('utf-8')
            return input
    else:  #py2
        if type(input) == unicode:
            input =  input.encode('utf-8')
            return input
        else:
            return input

def debugPrint( level, msg ):
    if level <= debugPrint.level:
        FreeCAD.Console.PrintMessage(msg + '\n')
debugPrint.level = 4 if hasattr(os,'uname') and os.uname()[1].startswith('antoine') else 2
#debugPrint.level = 4 #maui to debug

def formatDictionary( d, indent):
    return '%s{' % indent + '\n'.join(['%s%s:%s' % (indent,k,d[k]) for k in sorted(d.keys())]) + '}'

def findUnusedObjectName(base, counterStart=1, fmt='%02i', document=None):
    i = counterStart
    objName = '%s%s' % (base, fmt%i)
    if document == None:
        document = FreeCAD.ActiveDocument
    usedNames = [ obj.Name for obj in document.Objects ]    
    while objName in usedNames:
        i = i + 1
        objName = '%s%s' % (base, fmt%i)
    return objName

def findUnusedLabel(base, counterStart=1, fmt='%02i', document=None):
    i = counterStart
    label = '%s%s' % (base, fmt%i)
    if document == None:
        document = FreeCAD.ActiveDocument
    usedLabels = [ obj.Label for obj in document.Objects ]
    while label in usedLabels:
        i = i + 1
        label = '%s%s' % (base, fmt%i)
    return label


