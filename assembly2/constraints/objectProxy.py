from assembly2.core import *

class ConstraintObjectProxy:
    
    def execute(self, obj):
        preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
        if preferences.GetBool('autoSolveConstraintAttributesChanged', True):
            self.callSolveConstraints()
            #obj.touch()
            
    def onChanged(self, obj, prop):
        if hasattr(self, 'mirror_name'):
            cMirror = obj.Document.getObject( self.mirror_name )
            if cMirror.Proxy == None:
                return #this occurs during document loading ...
            if obj.getGroupOfProperty( prop ) == 'ConstraintInfo':
                cMirror.Proxy.disable_onChanged = True
                setattr( cMirror, prop, getattr( obj, prop) )
                cMirror.Proxy.disable_onChanged = False

    def reduceDirectionChoices( self, obj, value):
        if hasattr(self, 'mirror_name'):
            cMirror = obj.Document.getObject( self.mirror_name )
            cMirror.directionConstraint = ["aligned","opposed"] #value should be updated in onChanged call due to assignment in 2 lines
        obj.directionConstraint = ["aligned","opposed"]
        obj.directionConstraint = value
        
    def callSolveConstraints(self):
        from assembly2.solvers import solveConstraints
        solveConstraints( FreeCAD.ActiveDocument )

class ConstraintMirrorObjectProxy:
    def __init__(self, obj, constraintObj ):
        self.constraintObj_name = constraintObj.Name
        constraintObj.Proxy.mirror_name = obj.Name
        self.disable_onChanged = False
        obj.Proxy = self

    def execute(self, obj):
        return #no work required in onChanged causes touched in original constraint ...

    def onChanged(self, obj, prop):
        '''
        is triggered by Python code!
        And on document loading...
        '''
        #FreeCAD.Console.PrintMessage("%s.%s property changed\n" % (obj.Name, prop))
        if getattr( self, 'disable_onChanged', True):
            return
        if obj.getGroupOfProperty( prop ) == 'ConstraintNfo':
            if hasattr( self, 'constraintObj_name' ):
                constraintObj = obj.Document.getObject( self.constraintObj_name )
                try:
                    if getattr(constraintObj, prop) != getattr( obj, prop):
                        setattr( constraintObj, prop, getattr( obj, prop) )
                except AttributeError as e:
                    pass #loading issues...
