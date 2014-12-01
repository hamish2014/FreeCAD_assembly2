import numpy, os
import FreeCAD
import FreeCADGui
from PySide import QtGui

__dir__ = os.path.dirname(__file__)
wb_globals = {}

def debugPrint( level, msg ):
    if level <= debugPrint.level:
        FreeCAD.Console.PrintMessage(msg + '\n')
debugPrint.level = 3

class ConstraintSelectionObserver:
     def __init__(self, selectionGate, parseSelectionFunction):
          self.selections = []
          self.parseSelectionFunction = parseSelectionFunction
          FreeCADGui.Selection.addObserver(self)  
          FreeCADGui.Selection.removeSelectionGate()
          FreeCADGui.Selection.addSelectionGate( selectionGate )
     def addSelection( self, docName, objName, sub, pnt ):
         debugPrint(4,'addSelection: docName,objName,sub = %s,%s,%s' % (docName, objName, sub))
         obj = FreeCAD.ActiveDocument.getObject(objName)
         self.selections.append( SelectionRecord( docName, objName, sub ))
         if len(self.selections) == 2:
             self.stopSelectionObservation()
             self.parseSelectionFunction( self.selections)
     def stopSelectionObservation(self):
         FreeCADGui.Selection.removeObserver(self) 
         del wb_globals['selectionObserver']
         FreeCADGui.Selection.removeSelectionGate()



class SelectionRecord:
    def __init__(self, docName, objName, sub):
        self.Document = FreeCAD.getDocument(docName)
        self.ObjectName = objName
        self.Object = self.Document.getObject(objName)
        self.SubElementNames = [sub]


def findUnusedObjectName(base, counterStart=1, fmt='%02i'):
    i = counterStart
    objName = '%s%s' % (base, fmt%i)
    while hasattr(FreeCAD.ActiveDocument, objName):
        i = i + 1
        objName = '%s%s' % (base, fmt%i)
    return objName

class ConstraintPrototype:
    def __init__( self, doc, constraintObj, variableManager):
        '''
        assembly2 constraints are stored under App::FeaturePython object (constraintObj)

        cName = findUnusedObjectName('axialConstraint')
        c = FreeCAD.ActiveDocument.addObject("App::FeaturePython", cName)
        c.addProperty("App::PropertyString","Type","ConstraintInfo","Object 1").Type = '...'
       
        see http://www.freecadweb.org/wiki/index.php?title=Scripted_objects#Available_properties for more information
        '''
        self.doc = doc
        self.constraintObj = constraintObj
        self.variableManager = variableManager
        self.registerVariables()

    def registerVariables( self ):
        raise RuntimeError, "ConstraintPrototype class not supposed to used directly"

    def errors( self ):
        'returns a list of errors, which the solver tries to reduce to 0'
        raise RuntimeError, "ConstraintPrototype class not supposed to used directly"
    
    def satisfied( self, eps=10**-3 ):
        return all( numpy.array(self.errors()) < eps )

    def objectNames( self):
        'for the general case...'
        return [self.constraintObj.Object1, self.constraintObj.Object2 ]


class ConstraintObjectProxy:
    def execute(self, obj):
        self.callSolveConstraints()
        obj.touch()
    def callSolveConstraints(self):
        from assembly2solver import solveConstraints
        solveConstraints( FreeCAD.ActiveDocument )
