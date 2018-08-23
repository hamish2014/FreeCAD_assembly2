from assembly2.core import *
from assembly2.lib3D import *
from assembly2.selection import *
from objectProxy import ConstraintObjectProxy
from viewProviderProxy import ConstraintViewProviderProxy, repair_tree_view
from pivy import coin
from PySide import QtGui

__dir2__ = os.path.dirname(__file__)
GuiPath = os.path.expanduser ("~") #GuiPath = os.path.join( __dir2__, 'Gui' )


def recordConstraints( doc, s1, s2 ):
    constraintFile = os.path.join( GuiPath , 'constraintFile.txt')
    with open(constraintFile, 'w') as outfile:
         outfile.write(make_string(s1.ObjectName)+'\n'+str(s1.Object.Placement.Base)+'\n'+str(s1.Object.Placement.Rotation)+'\n')
         outfile.write(make_string(s2.ObjectName)+'\n'+str(s2.Object.Placement.Base)+'\n'+str(s2.Object.Placement.Rotation)+'\n')
    constraints = [ obj for obj in FreeCAD.ActiveDocument.Objects if 'ConstraintInfo' in obj.Content ]
    #print constraints
    if len(constraints) > 0:
         constraintFile = os.path.join( GuiPath , 'constraintFile.txt')
         if os.path.exists(constraintFile):
             with open(constraintFile, 'a') as outfile:
                 lastConstraintAdded = constraints[-1]
                 outfile.write(make_string(lastConstraintAdded.Name)+'\n')
