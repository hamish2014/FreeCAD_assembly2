import assembly2 #QtCore.QResource.registerResource happens here
import FreeCAD

class Assembly2Workbench (Workbench): 
    MenuText = 'Assembly 2'
    def Initialize(self):
        commandslist = [
            'assembly2_importPart', 
            'assembly2_updateImportedPartsCommand', 
            'assembly2_movePart', 
            'assembly2_addCircularEdgeConstraint', 
            'assembly2_addPlaneConstraint', 
            'assembly2_addAxialConstraint', 
            'assembly2_addAngleConstraint', 
            'assembly2_addSphericalSurfaceConstraint',
            #'assembly2_undoConstraint', not ready yet
            'assembly2_degreesOfFreedomAnimation', 
            'assembly2_solveConstraints',
            'assembly2_muxAssembly',
            'assembly2_muxAssemblyRefresh',
            'assembly2_addPartsList',
            'assembly2_checkAssembly'
            ]
        self.appendToolbar('Assembly 2', commandslist)
        shortcut_commandslist = [
            'assembly2_flipLastConstraintsDirection',
            'assembly2_lockLastConstraintsRotation',
            'assembly2_boltMultipleCircularEdges',
            ]
        self.appendToolbar('Assembly 2 shortcuts', shortcut_commandslist )
        self.treecmdList = [
            'assembly2_importPart',
            'assembly2_updateImportedPartsCommand'
        ]
        FreeCADGui.addIconPath( ':/assembly2/icons' )
        FreeCADGui.addPreferencePage( ':/assembly2/ui/assembly2_prefs.ui','Assembly2' )
        self.appendMenu('Assembly 2', commandslist)

    def Activated(self):
        from assembly2.constraints import updateOldStyleConstraintProperties
        import os
        doc = FreeCAD.activeDocument()
        if hasattr(doc, 'Objects'):
            updateOldStyleConstraintProperties(doc)
        GuiPath = os.path.expanduser ("~")
        constraintFile = os.path.join( GuiPath , 'constraintFile.txt')
        if os.path.exists(constraintFile):
            os.remove(constraintFile)

    def ContextMenu(self, recipient):
        selection = [s  for s in FreeCADGui.Selection.getSelection() if s.Document == FreeCAD.ActiveDocument ]
        if len(selection) == 1:
            obj = selection[0]
            if hasattr(obj,'Content'):
                if 'ConstraintInfo' in obj.Content or 'ConstraintNfo' in obj.Content:
                    redefineCmd = {
                        'plane':'assembly2_redefinePlaneConstraint',
                        'angle_between_planes':'assembly2_redefineAngleConstraint',
                        'axial': 'assembly2_redefineAxialConstraint',
                        'circularEdge' : 'assembly2_redefineCircularEdgeConstraint',
                        'sphericalSurface' : 'assembly2_redefineSphericalSurfaceConstraint'
                        }[ obj.Type ]
                    self.appendContextMenu( "Assembly2", [
                            'assembly2_animate_constraint',
                            redefineCmd,
                            'assembly2_selectConstraintObjects',
                            'assembly2_selectConstraintElements'
                    ])
            if 'sourceFile' in  obj.Content:
                self.appendContextMenu( 
                    "Assembly2", 
                    [ 'assembly2_movePart',
                      'assembly2_duplicatePart',
                      'assembly2_editImportedPart',
                      'assembly2_forkImportedPart',
                      'assembly2_deletePartsConstraints',
                      'assembly2_randomColorAll']
                    )

    Icon = ':/assembly2/icons/workBenchIcon.svg'

Gui.addWorkbench( Assembly2Workbench() )
