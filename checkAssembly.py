from assembly2lib import *
from assembly2lib import __dir__
from PySide import QtGui, QtCore
import time

moduleVars = {}

class CheckAssemblyCommand:
    def Activated(self):
        debugPrint(2, 'Conducting Assembly Part Overlap Check for: %s' % FreeCAD.ActiveDocument.Label)
        objects = [obj for obj in FreeCAD.ActiveDocument.Objects if hasattr(obj, 'Shape') and obj.Name <> 'muxedAssembly']
        n = len(objects)
        no_of_checks = 0.5*(n-1)*(n)
        moduleVars['progressDialog'] = QtGui.QProgressDialog("Waiting one minute", "Cancel", 0, no_of_checks, QtGui.qApp.activeWindow())
        p = moduleVars['progressDialog']
        #p.setWindowModality(QtCore.WindowModal)
        count = 0
        errorMsgs = []
        for i in range(0, len(objects)-1):
            for j in range(i+1, len(objects)):
                if p.wasCanceled():
                    break
                msg = 'overlap check between:   "%s"  &  "%s"' % (objects[i].Label, objects[j].Label)
                debugPrint(3, '  ' + msg)
                p.setLabelText(msg)
                overlap = objects[i].Shape.common( objects[j].Shape )
                if overlap.Volume > 0:
                    errorMsgs.append('%s  &  %s' % (objects[i].Label, objects[j].Label) )
                count = count + 1
                p.setValue(count)
        p.setValue(no_of_checks)
        if len(errorMsgs) > 0:
            #flags |= QtGui.QMessageBox.Ignore
            message = "Overlap detected between:\n  - %s" % "  \n  - ".join(errorMsgs)
            response = QtGui.QMessageBox.critical(QtGui.qApp.activeWindow(), "Assebly Check", message)#, flags)
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
