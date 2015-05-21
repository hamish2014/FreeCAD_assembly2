
from assembly2lib import *
from assembly2lib import __dir__
from PySide import QtGui, QtCore
import traceback
import degreesOfFreedom

moduleVars = {}

class AnimateCommand:
    def Activated(self):
        from assembly2solver import solveConstraints
        constraintSystem = solveConstraints(FreeCAD.ActiveDocument)
        self.taskPanel = AnimateDegreesOfFreedomTaskPanel( constraintSystem )
        FreeCADGui.Control.showDialog( self.taskPanel )
    def GetResources(self): 
        msg = 'animate degrees of freedom'
        return {
            'Pixmap' : os.path.join( __dir__ , 'degreesOfFreedomAnimation.svg' ) , 
            'MenuText': msg, 
            'ToolTip':  msg
            } 
animateCommand = AnimateCommand()
FreeCADGui.addCommand('degreesOfFreedomAnimation', animateCommand)


class AnimateDegreesOfFreedomTaskPanel:
    def __init__(self, constraintSystem):
        self.constraintSystem = constraintSystem
        self.original_degrees_of_freedom =  constraintSystem.degreesOfFreedom
        self.form = FreeCADGui.PySideUic.loadUi( os.path.join(__dir__,"degreesOfFreedomAnimation.ui") )
        self.form.setWindowIcon(QtGui.QIcon( os.path.join( __dir__ , 'degreesOfFreedomAnimation.svg' ) ) )
        self.form.groupBox_DOF.setTitle('%i Degrees-of-freedom:' % len(constraintSystem.degreesOfFreedom))
        for i, d in enumerate(constraintSystem.degreesOfFreedom):
            QtGui.QListWidgetItem('%i. %s' % (i+1, str(d)[1:-1].replace('DegreeOfFreedom ','')), self.form.listWidget_DOF)
        self.form.pushButton_animateSelected.clicked.connect(self.animateSelected)

    def _startAnimation(self, D):
        frames_per_DOF =  self.form.spinBox_frames_per_DOF.value()
        ms_per_frame = self.form.spinBox_ms_per_frame.value()
        self.constraintSystem.degreesOfFreedom = D
        if len(self.constraintSystem.degreesOfFreedom) > 0:
            moduleVars['animation'] = AnimateDOF(self.constraintSystem, ms_per_frame, frames_per_DOF)#required to protect the QTimer from the garbage collector
        else:
            FreeCAD.Console.PrintError('Aborting Animation! Constraint system has no degrees of freedom.')
            FreeCADGui.Control.closeDialog()

    def accept(self):
        self._startAnimation( self.original_degrees_of_freedom )
        
    def animateSelected(self):
        debugPrint(4,'pushButton_animateSelected has been clicked')
        D_to_animate = []
        for index, d in enumerate( self.original_degrees_of_freedom ):
            #debugPrint(4,'getting item at index %i' % index)
            item = self.form.listWidget_DOF.item(index)
            #debugPrint(4,'checking if %s is selected' % d.str())
            if item.isSelected():
                D_to_animate.append( d )
        if len(D_to_animate) > 0:
            self._startAnimation( D_to_animate )

    def reject(self):
        moduleVars['animation'].timer.stop()
        self.constraintSystem.variableManager.updateFreeCADValues(moduleVars['animation'].X_before_animation)
        FreeCADGui.Control.closeDialog()



class AnimateDOF(object):
    'based on http://freecad-tutorial.blogspot.com/2014/06/piston-conrod-animation.html'
    def __init__(self, constraintSystem, tick=50, framesPerDOF=40 ):
        self.constraintSystem = constraintSystem
        self.Y0 = numpy.array([ d.getValue() for d in constraintSystem.degreesOfFreedom ])
        self.X_before_animation = constraintSystem.variableManager.X.copy()
        self.framesPerDOF = framesPerDOF
        debugPrint(2,'beginning degrees of freedom animation')
        self.count = 0
        self.dof_count = 0
        self.updateAmplitude()
        self.timer = QtCore.QTimer()
        QtCore.QObject.connect(self.timer, QtCore.SIGNAL("timeout()"), self.renderFrame)
        self.timer.start( tick )

    def updateAmplitude( self) :
        D = self.constraintSystem.degreesOfFreedom
        if D[self.dof_count].rotational():
            self.amplitude = 1.0
        else:
            obj = FreeCAD.ActiveDocument.getObject( D[self.dof_count].objName )
            self.amplitude = obj.Shape.BoundBox.DiagonalLength / 2

    def renderFrame(self):
        try:
            debugPrint(5,'timer loop running')
            self.count = self.count + 1
            D = self.constraintSystem.degreesOfFreedom
            if self.count > self.framesPerDOF: #placed here so that if is error timer still exits
                self.count = 0
                self.dof_count = self.dof_count + 1
                if base_rotation_dof( D[self.dof_count-1] ):
                    self.dof_count = self.dof_count + 2
                if self.dof_count + 1 > len( self.constraintSystem.degreesOfFreedom ):
                    self.timer.stop()
                    self.constraintSystem.variableManager.updateFreeCADValues(self.X_before_animation)
                    return
                self.updateAmplitude()
                
            if self.count == 1: debugPrint(3,'animating %s' % D[self.dof_count])
            debugPrint(4,'dof %i, dof frame %i' % (self.dof_count, self.count))
            Y = self.Y0.copy()
            r = 2*numpy.pi*( 1.0*self.count/self.framesPerDOF)
            Y[self.dof_count] = self.Y0[self.dof_count] + self.amplitude * numpy.sin(r)
            if self.dof_count + 2 < len(self.constraintSystem.degreesOfFreedom):
                if base_rotation_dof( D[self.dof_count] ) and base_rotation_dof( D[self.dof_count+1] ) and base_rotation_dof( D[self.dof_count+2] ): #then also adjust other base rotation degrees of freedom so that rotation is always visible
                    Y[self.dof_count+1] = self.Y0[self.dof_count+1] +self.amplitude*numpy.sin(r)
                    Y[self.dof_count+2] = self.Y0[self.dof_count+2] +self.amplitude*numpy.sin(r)
            debugPrint(5,'Y frame %s, sin(r) %1.2f' % (Y,numpy.sin(r)))
        except:
            self.timer.stop()
            App.Console.PrintError(traceback.format_exc())
            App.Console.PrintError('Aborting animation')
        try:
            for d,y in zip( D, Y):
                d.setValue(y)
                self.constraintSystem.update()
            self.constraintSystem.variableManager.updateFreeCADValues( self.constraintSystem.variableManager.X )
            debugPrint(5,'updated assembly')
        except:
            FreeCAD.Console.PrintError('AnimateDegreeOfFreedom (dof %i, dof frame %i) unable to update constraint system\n'  % (self.dof_count, self.count))
            FreeCAD.Console.PrintError(traceback.format_exc())
        debugPrint(5,'finished timer loop')

def base_rotation_dof(d):
    if isinstance(d,degreesOfFreedom.PlacementDegreeOfFreedom) and  hasattr(d, 'ind'):
        return d.ind % 6 > 2
    return False


