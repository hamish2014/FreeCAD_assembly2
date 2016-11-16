FreeCAD_assembly2
=================

Assembly workbench for FreeCAD v0.16 with support for importing parts from external files.
Although the original programmer of the workbench (hamish) is no longer active
this workbench is still maintained as good as possible.
Feel free to post issues and pull requests.


Linux Installation Instructions
-------------------------------

For Ubuntu (Linux Mint) we recommend to add the community ppa to your systems software
resources and install via the sysnaptic package manager the addon of your liking.
Refer to here for more information:
https://launchpad.net/~freecad-community/+archive/ubuntu/ppa

On other Linux distros you may try to install manually via BASH and git:

```bash
$ sudo apt-get install git python-numpy python-pyside
$ mkdir ~/.FreeCAD/Mod
$ cd ~/.FreeCAD/Mod
$ git clone https://github.com/hamish2014/FreeCAD_drawing_dimensioning.git
```

Once installed, use git to easily update to the latest version:

```bash
$ cd ~/.FreeCAD/Mod/FreeCAD_drawing_dimensioning
$ git pull
$ rm *.pyc
```

Windows Installation Instructions
---------------------------------

Please use the FreeCAD-Addons-Installer provided here:
https://github.com/FreeCAD/FreeCAD-addons

For more in-depth information refer to the corresponding tutorial on the FreeCAD-Homepage:
http://www.freecadweb.org/wiki/index.php?title=How_to_install_additional_workbenches

Mac Installation Instructions
-----------------------------

Copy or unzip the drawing dimensioning folder to the directory *FreeCAD.app*/Contents/Mod
where *FreeCAD.app* is the folder where FreeCAD is installed. (thanks PLChris)

For more in-depth information refer to the corresponding tutorial on the FreeCAD-Homepage:
http://www.freecadweb.org/wiki/index.php?title=How_to_install_additional_workbenches

Wiki
----

For instructions on usage of the workbench refer to the wiki (link on top of the page)
[https://github.com/hamish2014/FreeCAD_assembly2/wiki]