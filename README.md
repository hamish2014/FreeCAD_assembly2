FreeCAD_assembly2
=================

Assembly workbench for FreeCAD v0.15 with support for importing parts from external files.
Please note that the Assembly 2 workbench is a work under progress and still contains bugs.

Intended work-flow:
  * each part in the assembly is designed in its own FreeCAD file
  * a separate assembly FreeCAD file is created
  * parts are imported to this assembly file using the Assembly 2 workbench
  * spacial constraints are then added to assemble the imported parts

Features
  * circular edge constraint
  * axial constraint
  * plane constraint
  * part importing 
  * updating of parts already imported

Limitations
  * Poor constraint solver which may fail or take excessively long for complicated assemblies
  * undo and other similar features not supported


Linux Installation Instructions
-------------------------------

To use this workbench clone this git repository under your FreeCAD MyScripts directory, and install the pyside and numpy python libraries.
On a Linux Debian based system such as Ubuntu, installation can be done through BASH as follows

```bash
  $ sudo apt-get install git python-numpy python-pyside
  $ mkdir ~/.FreeCAD/Mod
  $ cd ~/.FreeCAD/Mod
  $ git clone https://github.com/hamish2014/FreeCAD_assembly2.git
```

FreeCAD you will now have a new workbench-entry called "Assembly 2".
Once installed, use git to upgrade to the latest version through BASH as follows
```bash
  $ cd ~/.FreeCAD/Mod/FreeCAD_assembly2
  $ git pull
  $ rm *.pyc
```

Alternatilvely, on an *Ubuntu* system the freecad-community PPA can be used:

  1.  Add **ppa:freecad-community/ppa** to your software sources ([What are PPAs and how do I use them?](http://askubuntu.com/questions/4983/what-are-ppas-and-how-do-i-use-them/5102#5102%29))
  2.  sudo apt-get update
  3.  sudo apt-get install freecad-extras-assembly2


Windows Installation Instructions
---------------------------------

  * download the git repository as ZIP
  * assuming FreeCAD is installed in "C:\PortableApps\FreeCAD 0_15",  go to "C:\PortableApps\FreeCAD 0_15\Mod" within Windows Explorer
  * create new directory named "assembly2"
  * unzip downloaded repository in "C:\PortableApps\FreeCAD 0_15\Mod\assembly2"
  
FreeCAD will now have a new workbench-entry called "Assembly 2".

*Pyside and Numpy are integrated in the FreeCAD 0.15 dev-Snapshots, so these Python packages do not need to be installed individually*

To update to the latest version, delete the assembly2 folder and redownload the git repository.

Bugs
----

Please report bugs at https://github.com/hamish2014/FreeCAD_assembly2/issues