
from assembly2lib import *
from assembly2lib import __dir__
from PySide import QtGui, QtCore

moduleVars = {}

class animateCommand:
    def Activated(self):
        from assembly2solver import solveConstraints
        constraintSystem = solveConstraints(FreeCAD.ActiveDocument)
        if len(constraintSystem.degreesOfFreedom) > 0:
            moduleVars['animation'] = AnimateDOF(constraintSystem)#required to protect the QTimer from the garbage collector
        else:
            FreeCAD.Console.PrintError('Aborting Animation! Constraint system has no degrees of freedom.')
    def GetResources(self): 
        msg = 'animate degrees of freedom'
        return {
            'Pixmap' : os.path.join( __dir__ , 'degreesOfFreedomAnimation.svg' ) , 
            'MenuText': msg, 
            'ToolTip':  msg
            } 

FreeCADGui.addCommand('degreesOfFreedomAnimation', animateCommand())


class AnimateDOF(object):
    'based on http://freecad-tutorial.blogspot.com/2014/06/piston-conrod-animation.html'
    def __init__(self, constraintSystem, tick=50, framesPerDOF=40 ):
        self.constraintSystem = constraintSystem
        self.Y0 = numpy.array([ d.value for d in constraintSystem.degreesOfFreedom ])
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
        debugPrint(5,'timer loop running')
        self.count = self.count + 1
        if self.count > self.framesPerDOF: #placed here so that if is error timer still exits
            self.count = 0
            self.dof_count = self.dof_count + 1
            if self.dof_count + 1 > len( self.constraintSystem.degreesOfFreedom ):
                self.timer.stop()
                return
            self.updateAmplitude()


        D = self.constraintSystem.degreesOfFreedom
        if self.count == 1: debugPrint(3,'animating %s' % D[self.dof_count])
        debugPrint(4,'dof %i, dof frame %i' % (self.dof_count, self.count))
        Y = self.Y0.copy()
        r = 2*numpy.pi*( 1.0*self.count/self.framesPerDOF)
        Y[self.dof_count] = self.Y0[self.dof_count] + self.amplitude * numpy.sin(r)
        debugPrint(5,'Y frame %s, sin(r) %1.2f' % (Y,numpy.sin(r)))
        try:
            for d,y in zip( D, Y):
                d.setValue(y)
                self.constraintSystem.update()
            X = self.constraintSystem.getX2()
            self.constraintSystem.variableManager.updateFreeCADValues( X )
            debugPrint(5,'updated assembly')
        except:
            FreeCAD.Console.PrintError('AnimateDegreeOfFreedom (dof %i, dof frame %i) unable to update constraint system'  % (self.dof_count, self.count))

        debugPrint(5,'finished timer loop')
