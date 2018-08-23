'''
The solvers for assembly2 constraint systems are accessed here.
'''

from assembly2.core import *
from assembly2.constraints import updateOldStyleConstraintProperties
import common 
from common import constraintsObjectsAllExist
from dof_reduction_solver import solveConstraints as solveConstraints_dof_reduction_solver

_default =  "_assembly2_preference_"
    
def solveConstraints(
        doc,
        solver_name = _default,
        showFailureErrorDialog = True,
        printErrors = True,
        use_cache = _default,
):
    if solver_name == _default or use_cache == _default:
        preferences = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/Assembly2")
        if solver_name == _default:
            solver_name = preferences.GetString('solver_to_use', 'dof_reduction_solver')
        if use_cache == _default:
            use_cache = preferences.GetBool('useCache', False)
    if not constraintsObjectsAllExist(doc):
        return
    updateOldStyleConstraintProperties(doc)
    if solver_name == 'dof_reduction_solver':
        return solveConstraints_dof_reduction_solver( doc, showFailureErrorDialog, printErrors, use_cache )
    else:
        raise NotImplementedError( '%s solver interface not added yet' % solver_name )
        
    

class Assembly2SolveConstraintsCommand:
    def Activated(self):
        solveConstraints( FreeCAD.ActiveDocument )
    def GetResources(self):
        return {
            'Pixmap' : ':/assembly2/icons/assembly2SolveConstraints.svg',
            'MenuText': 'Solve Assembly 2 constraints',
            'ToolTip': 'Solve Assembly 2 constraints'
            }

FreeCADGui.addCommand('assembly2_solveConstraints', Assembly2SolveConstraintsCommand())


