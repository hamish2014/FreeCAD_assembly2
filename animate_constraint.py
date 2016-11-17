if __name__ == '__main__': #then testing library.
    import sys
    sys.path.append('/usr/lib/freecad/lib/') #path to FreeCAD library on Linux
    import FreeCADGui
    assert not hasattr(FreeCADGui, 'addCommand')
    FreeCADGui.addCommand = lambda x,y: 0

from assembly2lib import *
from PySide import QtGui, QtCore
import time, traceback

moduleVars = {}

class AnimateConstraint_Command:
    def Activated(self):
        selection = [s  for s in FreeCADGui.Selection.getSelection() if s.Document == FreeCAD.ActiveDocument ]
        assert len(selection) == 1
        constraint_to_animate = selection[0]
        if not 'ConstraintInfo' in constraint_to_animate.Content: #then mirror selected
            constraint_to_animate = FreeCAD.ActiveDocument.getObject( constraint_to_animate.ViewObject.Proxy.constraintObj_name )
            #return 
        self.taskPanel = AnimateConstraint_TaskPanel( constraint_to_animate  )
        FreeCADGui.Control.showDialog( self.taskPanel )
    def GetResources(self): 
        return {
            'MenuText': 'Animate', 
            'ToolTip':  'Animate constraint'
            } 
FreeCADGui.addCommand( 'assemly2_animate_constraint', AnimateConstraint_Command() )

class AnimateConstraint_TaskPanel:
    def __init__(self,  constraint_to_animate):
        self.constraint_to_animate = constraint_to_animate
        self.form = AnimateConstraint_Form(self)
        #self.form.setWindowIcon(QtGui.QIcon( ':/assembly2/icons/degreesOfFreedomAnimation.svg' ) )
    def getStandardButtons(self): #http://forum.freecadweb.org/viewtopic.php?f=10&t=11801
        return 0x00200000
    def reject(self): #or more correctly close, given the button settings
        if hasattr( self.form, 'constraintAnimator' ):
            self.form.constraintAnimator.stop()
            from assembly2solver import solveConstraints
            solveConstraints( FreeCAD.ActiveDocument )
        FreeCADGui.Control.closeDialog()

class AnimateConstraint_Form( QtGui.QWidget):
    def __init__(self, taskDialog ):
        super(AnimateConstraint_Form, self).__init__()
        self.taskDialog = taskDialog
        self.initUI()
    def initUI(self):
        vbox = QtGui.QVBoxLayout()
        hbox = QtGui.QHBoxLayout()
        #hbox2.addStretch(1)
        self.playStopButton = QtGui.QPushButton() #QtGui.QToolButton()
        self.playStopButton.setIcon( QtGui.QIcon(':/assembly2/icons/play.svg') )
        self.playStopButton.clicked.connect( self.playStopButton_clicked )
        self.playStopButton.setFlat( True )
        self.playStopButton.setMaximumWidth( 20 )
        self.playStopButton.setEnabled( False )
        #self.stopButton.setIcon( QtGui.QIcon(':/haas_mill/icons/stop.svg') )
        self.animationSlider = QtGui.QSlider( QtCore.Qt.Orientation.Horizontal )
        self.animationSlider.setMaximum(160)
        self.animationSlider.sliderMoved.connect( self.slider_moved )
        self.animationSlider.setEnabled( False )
        #self.animationSlider.sliderMoved.connect( self.slider_moved )
        hbox.addWidget( self.animationSlider )
        hbox.addWidget( self.playStopButton )
        vbox.addLayout( hbox )
        #operation parameters
        self.parameterDict = {}
        constraint_to_animate = self.taskDialog.constraint_to_animate
        for widgetManager in animation_parameters: #or widgetConstructors or widgetMangers or ...
            w = widgetManager.generateWidget( self.parameterDict, constraint_to_animate )
            if isinstance(w, QtGui.QLayout):
                vbox.addLayout( w )
            else:
                vbox.addWidget( w )
        self.button_generate_animiation =  QtGui.QPushButton('Generate')
        self.button_generate_animiation.clicked.connect( self.generate_animation )
        vbox.addWidget( self.button_generate_animiation )
        self.setLayout(vbox)  
          
    def generate_animation( self ):
        preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
        org_auto_solve = preferences.GetBool('autoSolveConstraintAttributesChanged', True)
        preferences.SetBool('autoSolveConstraintAttributesChanged', False)
        try:
            if hasattr( self, 'constraintAnimator' ):
                 self.constraintAnimator.stop()
            from assembly2solver import solveConstraints
            P = {}
            for p in animation_parameters:
                if hasattr(p,'getValue'):
                    p.add_property_to_freecad_object()
                    P[p.name] = p.getValue()
            debugPrint(3, 'generate_animation parms %s' % P )
            constraint_to_animate = self.taskDialog.constraint_to_animate
            self.original_expressions = constraint_to_animate.ExpressionEngine #[('angle', '12')]
            self.X = []
            if not hasattr(constraint_to_animate, 'a'):
                constraint_to_animate.addProperty(
                    {'angle_between_planes':'App::PropertyAngle', 'plane':'App::PropertyDistance', 'circularEdge':'App::PropertyDistance'}[ constraint_to_animate.Type ], 
                    'a', 
                    "animationParameters"
                    )
                constraint_to_animate.setEditorMode( 'a', 2)
            attr_to_animate = {'angle_between_planes':'angle', 'plane':'offset', 'circularEdge':'offset'}[ constraint_to_animate.Type ]
            attr_org_value = getattr( constraint_to_animate, attr_to_animate)
            constraint_to_animate.setExpression( attr_to_animate, P['animation_exp'] )

            moduleVars['progressDialog'] = QtGui.QProgressDialog("Generating Animation", "Cancel", 0, P['a_n'])
            p = moduleVars['progressDialog']
            p.setWindowModality(QtCore.Qt.WindowModal)
            p.forceShow()
            A = numpy.linspace(P['a_0'],P['a_1'],P['a_n'])
            for count, a in enumerate(A):
                if not p.wasCanceled():
                    p.setLabelText( 'solving %i/%i' % (count+1, P['a_n']) )
                    p.setValue(count)
                    debugPrint(3, 'solving constraint system for a=%1.1f' % a )
                    constraint_to_animate.a = a
                    FreeCAD.ActiveDocument.recompute() #update other expersions
                    constraint_sys = solveConstraints( FreeCAD.ActiveDocument )
                    self.X.append( constraint_sys.variableManager.X.copy() )
                    #variableManager.updateFreeCADValues( constraintSystem.variableManager.X )
            set_exp_to_none = True
            for ent in self.original_expressions:
                if ent[0] == attr_to_animate:
                    constraint_to_animate.setExpression( attr_to_animate,ent[1] )
                    set_exp_to_none = False
            if set_exp_to_none:
                constraint_to_animate.setExpression( attr_to_animate, None )
            setattr( constraint_to_animate, attr_to_animate, attr_org_value )
            if not p.wasCanceled():
                p.setValue(P['a_n']) #hopefully this will close the progress dialog
                if P['interp_method'] == 'none':
                    pass
                elif P['interp_method'] == 'linear':
                    self.X = linear_interp( self.X, A , P['n_interp'] )
                elif P['interp_method'] == 'Cubic_Hermite_spline':
                    self.X = spline_interp( self.X, A , P['n_interp'] )
                else:
                    raise NotImplemented

                self.playStopButton.setEnabled( True )
                self.constraintAnimator = ConstraintAnimator( self.X, constraint_sys.variableManager)
                if P['play_after_generate']:
                    self.playStopButton_clicked()
        except:
            FreeCAD.Console.PrintError( traceback.format_exc() )
        preferences.SetBool('autoSolveConstraintAttributesChanged',org_auto_solve)
        debugPrint(3, 'done generating constraint animation' )

    def playStopButton_clicked( self ):
        try:
            if not self.constraintAnimator.playing():
                self.playStopButton.setIcon( QtGui.QIcon(':/assembly2/icons/stop.svg') )
                self.constraintAnimator.update_ms_per_frame( [ p for p in animation_parameters if p.name == 'timer_ms'][0].spinbox.value() )
                self.constraintAnimator.loop = [ p for p in animation_parameters if p.name == 'loop'][0].checkbox.isChecked()
                p = 1.0 * self.animationSlider.sliderPosition() / self.animationSlider.maximum()
                self.constraintAnimator.play( 1, self.playRenderFrameHook )
                self.constraintAnimator.jumpTo( p*self.constraintAnimator.runningTime  )
            else:
                self.playStopButton.setIcon( QtGui.QIcon(':/assembly2/icons/play.svg') )
                self.constraintAnimator.stop()
        except:
            FreeCAD.Console.PrintError(traceback.format_exc())
    def playRenderFrameHook( self, time ):
        dt = self.constraintAnimator.runningTime
        p = time / dt
        sliderPos = int( p* self.animationSlider.maximum() )
        if p < 1:
            self.animationSlider.setSliderPosition(  sliderPos )
        else:
            self.playStopButton.setIcon( QtGui.QIcon(':/assembly2/icons/play.svg') )
            self.animationSlider.setSliderPosition( 0 )
    def slider_moved( self, position ):
        try:
            dt = self.constraintAnimator.runningTime
            p = 1.0 * position / self.animationSlider.maximum() 
            if not self.constraintAnimator.playing():
                self.constraintAnimator.showAt( p*dt )
            else:
                self.constraintAnimator.jumpTo( p*dt )
        except:
            FreeCAD.Console.PrintError(traceback.format_exc())



class ConstraintAnimator:
    def __init__( self, X, variableManager, ms_per_frame=25, loop=False ):
        self.X = X
        self.variableManager = variableManager
        self.timer =  QtCore.QTimer()
        self.timer.timeout.connect( self.renderFrame )
        self.update_ms_per_frame( ms_per_frame )
        self.loop = loop

    def update_ms_per_frame( self, ms_per_frame ):
        self.timer_tick = ms_per_frame
        self.runningTime = ms_per_frame * len(self.X) / 1000.0

    def showAt( self, time ):
        frame = int(numpy.floor( 1000* time / self.timer_tick )) % len(self.X)
        self.variableManager.updateFreeCADValues( self.X[frame] )
        return frame

    def play( self, speed, renderFrameHook=None, tick = 20 ):
        self.timer_speed = speed 
        self.timer_t_start = time.time()
        self.renderFrameHook = renderFrameHook
        self.timer.start( tick )

    def playing( self ):
        return self.timer.isActive()

    def stop( self ):
        self.timer.stop()
        
    def jumpTo( self, t ):
        self.timer_t_start = time.time() - t/self.timer_speed

    def renderFrame( self ):
        try:
            dt = ( time.time() - self.timer_t_start ) * self.timer_speed
            frame = self.showAt( dt  )
            if dt > self.runningTime:
                if not self.loop:
                    self.stop()
                else:
                    self.timer_t_start = time.time()
                    dt = 0
            if self.renderFrameHook <> None:
                self.renderFrameHook( dt )
        except:
            FreeCAD.Console.PrintError(traceback.format_exc())


#
# animation parameters
#

animation_paratmeters = []

def Qt_label_widget( label, inputWidget, info_button_text=None ):
    hbox = QtGui.QHBoxLayout()
    hbox.addWidget( QtGui.QLabel(label) )
    hbox.addStretch(1)
    if inputWidget <> None:
        hbox.addWidget(inputWidget)
    if info_button_text:
        hbox.addWidget( InfoButton(info_button_text) )
    return hbox
class InfoButton( QtGui.QPushButton ):
    def __init__( self, infoText ):
        QtGui.QPushButton.__init__( self )
        self.setIcon( QtGui.QIcon(':/assembly2/icons/help.svg') )
        self.info_text = infoText
        self.setFlat( True )
        self.setMaximumWidth( 12 )
        self.clicked.connect( self.clickFun )
    def clickFun( self ):
        QtGui.QMessageBox.information( QtGui.qApp.activeWindow(), 'Info', self.info_text ) 


class RealParemeter:
    def __init__(self, name, defaultValue, label=None, info_button_text=None, **extraKWs):
        self.name = name
        self.defaultValue = defaultValue
        self.label = label if label <> None else name
        self.info_button_text = info_button_text
        self.process_extraKWs(**extraKWs)
        self.initExtra()
    def process_extraKWs(self):
        pass
    def initExtra(self):
        pass
    def process_extraKWs(self, increment=1.0, min=0.0, max=1000.0, decimalPlaces=3):
        self.spinBox_increment = increment
        self.spinBox_min = min
        self.spinBox_max = max
        self.spinBox_decimalPlaces = decimalPlaces

    def generateWidget( self, parameterDict, constraint_to_animate ):
        self.parameterDict = parameterDict
        self.constraint_to_animate = constraint_to_animate
        spinbox = QtGui.QDoubleSpinBox()
        default = self.getDefaultValue()
        spinbox.setMinimum( self.spinBox_min )
        spinbox.setMaximum( self.spinBox_max )
        spinbox.setSingleStep( self.spinBox_increment )
        spinbox.setDecimals( self.spinBox_decimalPlaces )
        spinbox.setValue( default )
        #spinbox.valueChanged.connect( self.valueChanged )
        #self.valueChanged(default)
        self.spinbox = spinbox
        return  Qt_label_widget( self.label, spinbox, self.info_button_text )

    def getDefaultValue(self ):
        return getattr(  self.constraint_to_animate, self.name+'_animatation', self.defaultValue )

    def add_property_to_freecad_object( self ):
        featurePython = self.constraint_to_animate
        if not hasattr(featurePython, self.name+'_animatation'):
            featurePython.addProperty("App::PropertyFloat", self.name+'_animatation', "animationParameters")
            featurePython.setEditorMode( self.name+'_animatation', 2)
        setattr( featurePython, self.name+'_animatation', self.spinbox.value() )
    def getValue( self ):
        return  getattr(  self.constraint_to_animate, self.name+'_animatation')


class TextParemeter( RealParemeter ):
    def process_extraKWs(self):
        pass
    def generateWidget( self, parameterDict, constraint_to_animate ):
        self.parameterDict = parameterDict
        self.constraint_to_animate = constraint_to_animate
        textbox = QtGui.QLineEdit()
        textbox.setText( self.getDefaultValue() )
        self.textbox = textbox
        return  Qt_label_widget( self.label, textbox, self.info_button_text )
    def add_property_to_freecad_object( self ):
        featurePython = self.constraint_to_animate
        if not hasattr(featurePython, self.name+'_animatation'):
            featurePython.addProperty("App::PropertyString", self.name+'_animatation', "animationParameters")
            featurePython.setEditorMode( self.name+'_animatation', 2)
        setattr( featurePython, self.name+'_animatation', self.textbox.text())

class BooleanParemeter( TextParemeter ):
    def generateWidget( self, parameterDict, constraint_to_animate ):
        self.parameterDict = parameterDict
        self.constraint_to_animate = constraint_to_animate
        self.checkbox = QtGui.QCheckBox(self.label)
        self.checkbox.setChecked( self.getDefaultValue() )
        return self.checkbox
    def add_property_to_freecad_object( self ):
        featurePython = self.constraint_to_animate
        if not hasattr(featurePython, self.name+'_animatation'):
            featurePython.addProperty("App::PropertyBool", self.name+'_animatation', "animationParameters")
            featurePython.setEditorMode( self.name+'_animatation', 2)
        setattr( featurePython, self.name+'_animatation', self.checkbox.isChecked())
#self.parameterDict[ self.name ] = self.checkbox.isChecked()

class ChoiceParemeter( TextParemeter ):
    def getDefaultValue(self ):
        return getattr(  self.constraint_to_animate, self.name+'_animatation', self.defaultValue[0] )
    def generateWidget( self, parameterDict, constraint_to_animate ):
        self.parameterDict = parameterDict
        self.constraint_to_animate = constraint_to_animate
        combobox = QtGui.QComboBox()
        for i in self.defaultValue:
            combobox.addItem(i)
        try:
            combobox.setCurrentIndex( self.defaultValue.index(self.getDefaultValue()) )
        except IndexError:
            pass
        self.combobox = combobox
        return Qt_label_widget( self.label, combobox )
    def add_property_to_freecad_object( self ):
        featurePython = self.constraint_to_animate
        if not hasattr(featurePython, self.name+'_animatation'):
            featurePython.addProperty("App::PropertyString", self.name+'_animatation', "animationParameters")
            featurePython.setEditorMode( self.name+'_animatation', 2)
        setattr( featurePython, self.name+'_animatation', self.combobox.currentText())




class ParameterHeading:
    def __init__(self, text, bold=True):
        self.name = None
        self.text = text
        self.bold = bold
    def generateWidget( self, parameterDict, constraint_to_animate ):
        return QtGui.QLabel('<b> %s </b>' % self.text if self.bold else self.text)

animation_parameters = [
    ParameterHeading('Animation variable (a)'),
    RealParemeter( 'a_0', 0, decimalPlaces=1 ),
    RealParemeter( 'a_1', 180, decimalPlaces=1 ),
    RealParemeter( 'a_n', 42, decimalPlaces=0 ),
    TextParemeter( 'animation_exp', 'a',info_button_text= r'''for a in numpy.linspace(a_0, a_1, a_n):
    constraint.value = exp(a)
''' ),

    ParameterHeading('Interpolation'),
    ChoiceParemeter( 'interp_method', ['none', 'linear','Cubic_Hermite_spline'], label='method'),
    RealParemeter( 'n_interp', 6, min=3, decimalPlaces=0, label='no. per segment' ),

    ParameterHeading('Timer'),
    RealParemeter( 'timer_ms', 25, decimalPlaces=0, min=10, max=100 ),
    BooleanParemeter( 'loop', True ),
    BooleanParemeter( 'play_after_generate', False ),
    ]








def linear_interp( P, X, n_per_seg ):
    P = numpy.array(P)
    n = len(P)
    n_dim = len(P[0])
    assert n > 1
    assert n_per_seg > 2
    t_int = numpy.linspace( X[0], X[-1], (n-1)*n_per_seg )
    P_int = numpy.zeros( ((n-1)*n_per_seg, n_dim ) )
    for j in range(n_dim):
        P_int[:,j] = numpy.interp( t_int, X, P[:,j])
    return P_int



def spline_interp( P, X, n_per_seg ):
    '''
    https://en.wikipedia.org/wiki/Cubic_Hermite_spline
    implemented here to assembly2 independent from SciPy

    p ( x ) = h_00 ( t ) p_k + h_10 ( t ) ( x_{k+1} - x_k ) m_k + h_01 ( t ) p_{k + 1} + h_11 ( t ) ( x_{k+1} - x_k ) m_{k+1} . 

    with 
       m = the tangent
       t = ( x - x k ) / ( x k + 1 - x k )
       h_00 =   2 t**3 - 3 t**2       + 1
       h_10 =     t**3 - 2 t**2 + t
       h_01 = - 2 t**3 + 3 t**2 
       h_11 =     t**3 -   t**2 

    natural spline 0,1st, and 2nd order continous, with 2 derivative being 0 and ends
    
    Catmull-Rom spline is obtained, being a special case of a cardinal spline. This assumes uniform parameter spacing.
        m k = ( p_{k+1} - p_{k-1} )/ (t_{k+1} - t_{k-1} )
    '''
    n = len(P)
    n_dim = len(P[0])
    assert n > 3
    assert n_per_seg > 2
    t_int = numpy.linspace( 0, 1, n_per_seg )
    P_int = numpy.zeros( ((n-1)*n_per_seg, n_dim ) )
    dx = X[1]-X[0]
    for j in range(n_dim):
        m = numpy.zeros(n)
        p_int = []
        for k in range(1,n-1):
            m[k] = ( P[k+1][j] - P[k-1][j] ) / (X[k+1]-X[k-1] )
        for k in range(n-1):
            for t in t_int:
                h_00 =   2*t**3 - 3*t**2       + 1
                h_10 =     t**3 - 2*t**2 + t
                h_01 =  -2*t**3 + 3*t**2 
                h_11 =     t**3 -   t**2 
                p_int.append( h_00*P[k][j] + h_10*dx*m[k] + h_01*P[k+1][j] + h_11*dx*m[k+1])
        P_int[:,j] = p_int
    return P_int


if __name__ == "__main__":
    print('Testing interpolation')
    P = [
        [ 0, 0],
        [ 1, -1],
        [ 1, -4],
        [ 0, -5],
        [ 4, -6],
        [10, -4],
        [8, -4],
        [6, -5],
        [3, -2]
        ]
    A = numpy.arange( len(P) ) * 4.2
    P_spline = spline_interp( P, A, 16 )
    P_linear = linear_interp( P, A, 16 )
    from matplotlib import pyplot
    pyplot.figure()
    pyplot.plot( P_spline[:,0], P_spline[:,1], '-bx' )
    pyplot.plot( P_linear[:,0], P_linear[:,1], '--g' )
    pyplot.plot( [p[0] for p in P], [p[1] for p in P], 'go' )
    pyplot.show()
    
