from assembly2.core import *
from random import random, choice

class RandomColorAllCommand:
    def Activated(self):
        randomcolors=(0.1,0.18,0.33,0.50,0.67,0.78,0.9)
        for objs in FreeCAD.ActiveDocument.Objects:
            if 'importPart' in objs.Content: 
                FreeCADGui.ActiveDocument.getObject(objs.Name).ShapeColor=(choice(randomcolors),choice(randomcolors),choice(randomcolors))

    def GetResources(self):
        return {
            'MenuText': 'Apply a random color to all imported objects',
            'ToolTip': 'Apply a random color to all imported objects'
        }

FreeCADGui.addCommand('assembly2_randomColorAll', RandomColorAllCommand())
