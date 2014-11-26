FreeCAD_assembly2
=================

Assembly workbench for FreeCAD v0.15 with support for importing parts from external files.
Please note that the Assembly 2 workbench is a work under progress and still contains bugs.

Intended work-flow:
  * each part in the assembly is designed in its own FreeCAD file.
  * a separate assembly FreeCAD file is created
  * parts are imported to this assembly file using the Assembly 2 workbench
  * spacial constraints are then added to assemble the imported parts

Features
  * circular edge constraint
  * axial constraint
  * plane constraint
  * part importing
  * an update imported part button for updating parts imported using the assembly 2 workbench

Limitations
  * Poor constraint solver which may fail or take excessively long for complicated assemblies
  * undo and other similar features not supported


Installation Instructions
-------------------------

To use this workbench clone this git repository under your FreeCAD MyScripts directory, and install the scipy and numpy python libraries.
On a Linux Debian based system such as Ubuntu, installation can be done through BASH as follows

  $ sudo apt-get install git python-scipy python-numpy

  $ mkdir .FreeCAD/Mod

  $ cd .FreeCAD/Mod

  $ git clone git@github.com:hamish2014/FreeCAD_assembly2.git


Updating to the latest version
------------------------------

  $ cd ~/.FreeCAD/Mod/FreeCAD_assembly2
  $ git pull


Bugs
----

Please report bugs on FreeCAD_assembly2 git page at https://github.com/hamish2014/FreeCAD_assembly2