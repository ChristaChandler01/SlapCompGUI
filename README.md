# SlapCompGUI
A GUI for Maya that allows the user to choose render paths, Nuke path, AOVs, grade and glow nodes to generate a Nuke script with AOV passes and render CG over a background as a slap comp.

Please place the GUI_SlapComp.py and quick_composite.py scripts in your Maya's scripts folder. 
If you have not set up your Maya environment to pull scripts from a specific location, you should locate where your Maya folder is for your current version of Maya and locate the scripts folder within there.
This Python script was created for Maya 2026, so that is the suggested location to place in the scripts folder. 
For example Z:\Documents\maya\2026\scripts
You could save it in your main Maya scripts folder for every version of Maya to use but as features change the code may need to be updated for future versions.

Please save the multipass_composite.py script into your .nuke folder. 
For example: Z:\.nuke

Open Maya's script editor, choose a python tab and type paste the following:

import GUI_SlapComp
importlib.reload(GUI_SlapComp)

GUI_SlapComp.main()

Choose your file paths and settings within the GUI then click Go!
It will start to render what ever scene you have open.
If you like what this does, you can save the above text to a custom shelf in Maya by highlighting the text and middle mouse dragging it to the shelf, it will create a button on the shelf. Right click to give it a name or icon then click save all shelves.
You can reuse this as many times as you like with several scenes to create quick slap comps.
