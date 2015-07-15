from assembly2lib import *
from assembly2lib import __dir__
from PySide import QtGui, QtCore
import time
from FreeCAD import Base

moduleVars = {}

class CheckAssemblyCommand:
    def Activated(self):
        debugPrint(2, 'Conducting Assembly Part Overlap Check for: %s' % FreeCAD.ActiveDocument.Label)
        objects = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj, 'Shape') and obj.Name <> 'muxedAssembly']
        n = len(objects)
        no_of_checks = 0.5*(n-1)*(n)
        moduleVars['progressDialog'] = QtGui.QProgressDialog("Checking assembly", "Cancel", 0, no_of_checks)#, QtGui.qApp.activeWindow()) with parent cancel does not work for some reason
        p = moduleVars['progressDialog']
        p.setWindowModality(QtCore.Qt.WindowModal)
        p.forceShow()
        count = 0
        t_start = time.time()
        errorMsgs = []
        for i in range(0, len(objects)-1):
            for j in range(i+1, len(objects)):
                if not p.wasCanceled():
                    msg = 'overlap check between:   "%s"  &  "%s"' % (objects[i].Label, objects[j].Label)
                    debugPrint(3, '  ' + msg)
                    p.setLabelText(msg)
                    if boundBoxesOverlap(objects[i].Shape, objects[j].Shape ): #first do a rough check, to speed up checks, on the test case used, time reduce from 11s ->10s ...
                        overlap = objects[i].Shape.common( objects[j].Shape )
                        overlap_ratio = overlap.Volume / min( objects[j].Shape.Volume, objects[i].Shape.Volume )
                        if overlap.Volume > 0:
                            errorMsgs.append('%s  &  %s : %3.3f%%*' % (objects[i].Label, objects[j].Label, 100*overlap_ratio ))
                    count = count + 1
                    p.setValue(count)
                else:            
                    break
        debugPrint(3, 'ProgressDialog canceled %s' % p.wasCanceled())
        if not p.wasCanceled():
            debugPrint(2, 'Assembly overlap check duration:    %3.1fs' % (time.time() - t_start) )
            #p.setValue(no_of_checks)
            if len(errorMsgs) > 0:
                #flags |= QtGui.QMessageBox.Ignore
                message = "Overlap detected between:\n  - %s" % "  \n  - ".join(errorMsgs)
                message = message + '\n\n*overlap.Volume / min( shape1.Volume, shape2.Volume )'
                FreeCAD.Console.PrintError( message + '\n' )
                response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Assembly Check", message)#, flags)
            else:
                QtGui.QMessageBox.information(  QtGui.qApp.activeWindow(), "Assembly Check", "Passed:\n  - No overlap/interferance dectected.")
    def GetResources(self): 
        msg = 'Check assembly for part overlap/interferance'
        return {
            'Pixmap' : os.path.join( __dir__ , 'checkAssembly.svg' ) , 
            'MenuText': msg, 
            'ToolTip':  msg
            } 
FreeCADGui.addCommand('assembly2_checkAssembly', CheckAssemblyCommand())


def boundBoxesOverlap( shape1, shape2 ):
    bb1 = shape1.BoundBox
    box1 = Part.makeBox( bb1.XLength, bb1.YLength, bb1.ZLength, Base.Vector( bb1.XMin, bb1.YMin, bb1.ZMin ))
    bb2 = shape2.BoundBox
    box2 = Part.makeBox( bb2.XLength, bb2.YLength, bb2.ZLength, Base.Vector( bb2.XMin, bb2.YMin, bb2.ZMin ))
    return box1.common(box2).Volume > 0
