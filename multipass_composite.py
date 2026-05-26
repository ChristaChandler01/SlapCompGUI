import nuke
import sys
import os
import subprocess
import ast


def multipass_composite(input_path, 
                        output_path, 
                        active_aovs, 
                        camera_data, 
                        width, 
                        height,  
                        start_frame, 
                        end_frame,
                        background_image,
                        merge_operation='plus',
                        grade_enabled=False,
                        grade_settings=None,
                        glow_enabled=False,
                        glow_settings=None):
    """
    Summary:
        Builds a full Nuke composite script using Arnold AOVs, optional
        grade and glow effects, a background sphere, and animated camera
        data. Writes the final composite to disk and prepares the script
        for rendering.

    Parameters:
        input_path (str):
            File path to the rendered Arnold EXR sequence.
        output_path (str):
            File path for the final Nuke-rendered output sequence.
        active_aovs (list[str]):
            List of AOV layer names to shuffle and merge.
        camera_data (dict):
            Per-frame camera animation data extracted from Maya.
        width (int):
            Output resolution width.
        height (int):
            Output resolution height.
        start_frame (int):
            First frame of the composite range.
        end_frame (int):
            Last frame of the composite range.
        background_image (str):
            File path to the background image used on the sphere.
        merge_operation (str):
            Nuke Merge operation (e.g., "plus", "over").
        grade_enabled (bool):
            Whether to apply a Grade node to the base AOV.
        grade_settings (dict):
            Grade parameters: gain, lift, gamma (HSL tint).
        glow_enabled (bool):
            Whether to apply a Glow node to the emission AOV.
        glow_settings (dict):
            Glow parameters: tint (HSL), brightness, size.

    Arguments:
        All arguments are passed from quick_composite() after being
        collected from the Maya GUI.

    Returns:
        None
            The function builds nodes directly inside Nuke and writes
            the composite to disk.
    """
    
    if grade_settings is None:
        grade_settings = {}
    if glow_settings is None:
        glow_settings = {}
    
    # Root settings
    nuke.addFormat('{} {} ccCustom'.format(width, height))
    nuke.root()['first_frame'].setValue(start_frame)
    nuke.root()['last_frame'].setValue(end_frame)

    # Read Render
    nRead = nuke.nodes.Read(file=input_path,
                            first=start_frame,
                            last=end_frame)
    
    # Suffle and Merge AOVs
    aovs = active_aovs[:]
    base = aovs.pop(0)

    # Base AOV
    connect_from = nuke.nodes.Shuffle2(label=base, inputs=[nRead])
    connect_from['in1'].setValue(base)
    connect_from.forceValidate()

    # Optional Grade on base (usually diffuse)
        # Optional Grade node
    if grade_enabled and base == 'diffuse':
        grade = nuke.nodes.Grade(inputs=[connect_from])
        grade['white'].setValue(grade_settings['gain'])
        grade['black'].setValue(grade_settings['lift'])
        # HSL tint mapped from GUI, alpha left at 1.
        grade['gamma'].setValue([grade_settings['h'],
                                 grade_settings['s'],
                                 grade_settings['l'],
                                 1.0])
        connect_from = grade

    # Remaining AOVs
    for aov in aovs:
        nLayer = nuke.nodes.Shuffle2(label=aov, inputs=[nRead])
        nLayer['in1'].setValue(aov)
        nLayer.forceValidate()

        # Optional glow for emission
        if glow_enabled and aov == 'emission':
            glow = nuke.nodes.Glow(inputs=[nLayer])
            glow['tint'].setValue([glow_settings['h'], glow_settings['s'], glow_settings['l']])
            glow['brightness'].setValue(glow_settings['brightness'])
            glow['size'].setValue(glow_settings['size'])
            nLayer = glow  

        # Merge AOV
        nMerge = nuke.nodes.Merge(operation=merge_operation)
        nMerge.setInput(0, connect_from)
        nMerge.setInput(1, nLayer)
        connect_from = nMerge

    # Camera
    nCam = nuke.nodes.Camera()
    load_camera_data(nCam, camera_data)

    # Background sphere
    nBG = nuke.nodes.Read(file=background_image)

    nReformat = nuke.nodes.Reformat()
    nReformat.setInput(0, nBG)

    nSphere = nuke.nodes.Sphere()
    nSphere.setInput(0, nReformat)
    nSphere['scaling'].setValue(10000)
    nSphere['rotate'].setValue(0, 100, 0)

    nScan = nuke.nodes.ScanlineRender()
    nScan.setInput(1, nSphere)
    nScan.setInput(2, nCam)

    # Alpha 
    nAlpha = nuke.nodes.Shuffle2()
    nAlpha.setInput(0, nRead)
    nAlpha['in1'].setValue('alpha')
    nAlpha['out1'].setValue('alpha')

    # Final merge
    final_merge = nuke.nodes.Merge(operation='over')
    final_merge.setInput(0, nScan)
    final_merge.setInput(1, connect_from)
    final_merge.setInput(2, nAlpha)

    # rLAB is not loading for me today, I have downloaded the OCIO folders from Shark Tacos' 
    # Git but no matter which one I try my OCIO settings still do not match the schools and 
    # causes display errors. So I'm adding Detect OCIO availabilty for at home testing purposes 
    # to just get this turned in today.
    ocio_available = 'OCIO' in os.environ and os.paht.exists(os.environ['OCIO'])

    # Write
    nWrite = nuke.nodes.Write(file=output_path,
                              first=start_frame,
                              last=end_frame)
    nWrite.setInput(0, final_merge)

    if ocio_available:
        if 'ocioColorspace' in nWrite.knobs():
            nWrite['ocioColorspace'].setValue('scene_linear')
        if 'display' in nWrite.knobs():
            nWrite['display'].setValue('default')
        if 'view' in nWrite.knobs():
            nWrite['view'].setValue('sRGB')
    else:
        # Bypass OCIO on home PC
        if 'ocioColorspace' in nWrite.knobs():
            nWrite['ocioColorspace'].setValue('')
        if 'display' in nWrite.knobs():
            nWrite['display'].setValue('')
        if 'view' in nWrite.knobs():
            nWrite['view'].setValue('')                  

def load_camera_data(camera, camera_data):
    """
    Summary:
        Applies animated camera attributes to a Nuke Camera node using
        the per-frame data exported from Maya.

    Parameters:
        camera (nuke.Node):
            The Nuke Camera node to receive animation.
        camera_data (dict):
            Dictionary containing lists of animated values for:
            - translate
            - rotate
            - focal
            - haperture
            - vaperture

    Arguments:
        camera (nuke.Node):
            The Camera node created inside multipass_composite().
        camera_data (dict):
            The animation data generated by get_camera_data() in Maya.

    Returns:
        None
            The function sets keyframes directly on the Nuke Camera node.
    """
    first = int(nuke.root()['first_frame'].value())

    for attribute in camera_data.keys():
        camera.knob(attribute).setAnimated()
        for index in range(len(camera_data[attribute])):
            for frame in range(len(camera_data[attribute][index])):
                camera.knob(attribute).setValueAt(camera_data[attribute][index][frame], 
                                                  first + frame, 
                                                  index)

# only execute in the main context.
if __name__ == '__main__':
    # Summary:
    #     Entry point when the script is executed directly by Nuke.
    #     Parses the incoming data dictionary, normalizes paths, and
    #     calls multipass_composite() with all required arguments.
    data = ast.literal_eval(sys.argv[1])

    # Normalize paths
    for key in ['input_path', 'output_path', 'nuke_script_path', 'background_image']:
        if key in data:
            data[key] = data[key].replace('\\', '/')
    
    multipass_composite(data['input_path'], 
                        data['output_path'], 
                        data['active_aovs'],
                        data['camera_data'],
                        data['width'],
                        data['height'],
                        data['start_frame'], 
                        data['end_frame'],
                        data['background_image'],
                        merge_operation=data.get('merge_operation', 'plus'),
                        grade_enabled=data.get('grade_enabled', False),
                        grade_settings=data.get('grade_settings', {}),
                        glow_enabled=data.get('glow_enabled', False),
                        glow_settings=data.get('glow_settings', {}))    
    
    nuke.scriptSave(data['nuke_script_path'])

# In the script editor in Nuke you can import this script by pasting the following code into the 
# script editor and running it:
# import multipass_composite as mc
# mc.multipass_composite