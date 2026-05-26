import os
import subprocess
import maya.cmds as cmds
import mtoa.aovs as aovs


COMPRESSION_MAP = {'none': 0, 'zip': 3, 'dwab': 9}
MODULUS = 25.39999962


# AOV setup
def setup_aovs(enable_aovs):
    """
    Summary:
        Removes all existing Arnold AOVs and recreates only the AOVs specified in the 
        enable_aovs list.
    Parameters:
        enable_aovs (list[str]):
            A list of AOV names to create in the Arnold AOV interface.
    Arguments:
        enable_aovs (list[str]):
            The AOVs selected by the user in the GUI.
    Returns:
        list:
            A list of successfully created AOV objects. AOVs that fail to create are 
            skipped with a warning.
    """
    #delete current AOVs
    iface = aovs.AOVInterface()
    iface.removeAOVs(iface.getAOVs())

    created = []
    for aov in enable_aovs:
        try:
            created.append(iface.addAOV(aov))
        except:
            print('WARNING: Could not create AOV:', aov)
            
    return created


# Setup render attributes
def setup_render_attributes(data):
    """
    Summary:
        Applies render setting sin Maya based on the values provided in the data dictionary. 
        This includes frame range, file prefix, Arnold driver settings, compression, and resolution.
    Parameters:
        data (dict):
            A dictionary containing all reder-related settings such as:
            - start_frame, end_frame
            - output_name
            - image_format
            - compression
            - width, height
    Arguments:
        data (dict):
            The full GUI data dictionary passed from go_CB().
    Returns:
        None
    """
    cmds.setAttr('defaultRenderGlobals.startFrame', data['start_frame'])
    cmds.setAttr('defaultRenderGlobals.endFrame', data['end_frame'])
    cmds.setAttr('defaultRenderGlobals.imageFilePrefix', data['output_name'], type='string')

    # Arnold settings
    cmds.setAttr('defaultArnoldRenderOptions.motion_blur_enable', True)
    cmds.setAttr('defaultArnoldDriver.aiTranslator', data['image_format'], type='string')
    cmds.setAttr('defaultArnoldDriver.mergeAOVs', True)

    # Compression settings
    cmds.setAttr('defaultArnoldDriver.exrCompression', COMPRESSION_MAP[data['compression']])

    # Resolution settings
    cmds.setAttr('defaultResolution.width', data['width'])
    cmds.setAttr('defaultResolution.height', data['height'])


# Camera data extraction
def get_camera_data(camera_name, start_frame, end_frame):
    """
    Summary:
        Extracts per-frame camera animation data including translation, rotation, focal length, 
        and film aperture values. This data is later passed to Nuke for camera reconstruction.
    Parameters:
        camera_name (str:
            The name of the camera to sample.
        start_frame (int):
            First frame of the sampling range.
        end_frame (int):
            Last frame of the sampling range (non-inclusive).
    Arguments:
        camera_name (str:
            The camera selected by the user or defaulted to 'camera1'.
        start_frame (int):
            The GUI-specified start frame.
        end_frame (int):
            The GUI-specified end frame.
    Returns:
        dict:
            A dictionary containing lists of sampled camera attributes:
            - translate: [[x], [y], [z]]
            - rotate: [[rx], [ry], [rz]]
            - focal: [[focal_length]]
            - haperture: [[horizontal_aperture]]
            - vaperture: [[vertical_aperture]]            
    """
    camera_data = {'translate': [[], [], []],
                    'rotate': [[], [], []],
                    'focal': [[]],
                    'haperture': [[]],
                    'vaperture': [[]]}
    for frame in range(start_frame, end_frame):
        cmds.currentTime(frame, edit=True)

        translate = cmds.xform(camera_name, q=True, ws=True, t=True)
        rot = cmds.xform(camera_name, q=True, ws=True, ro=True)
        focal = cmds.camera(camera_name, q=True, fl=True)
        hfa = cmds.camera(camera_name, q=True, hfa=True)*MODULUS
        vfa = cmds.camera(camera_name, q=True, vfa=True)*MODULUS
        
        for i in range(len(translate)):
            camera_data['translate'][i].append(translate[i])
        for i in range(len(rot)):
            camera_data['rotate'][i].append(rot[i])
        camera_data['focal'][0].append(focal)
        camera_data['haperture'][0].append(hfa)
        camera_data['vaperture'][0].append(vfa)                              

    return camera_data


# Main composite function
def quick_composite(data):
    """
    Summary:
        Main execution function for the Quick Composite workflow.
        Handles AOV creation, render setup, camera extraction,
        Arnold rendering, Nuke script generation, and Nuke rendering.

    Parameters:
        data (dict):
            The full GUI data dictionary containing:
            - file paths
            - render settings
            - AOV selections
            - camera name
            - Nuke script paths
            - grade/glow settings (if enabled)

    Arguments:
        data (dict):
            The dictionary passed directly from the GUI's go_CB() function.

    Returns:
        None
            All results are written to disk (renders, Nuke script, logs).
    """
    print("\n==============================")
    print(" QUICK COMPOSITE — GUI INPUT")
    print("==============================")
    for k, v in data.items():
        print('{:<20} : {}'.format(k, v))
    print("==============================\n")
    
    # Create AOVs in Maya.
    setup_aovs(data['active_aovs'])

    # Set Maya render attributes.
    setup_render_attributes(data)

    # Get Camera data (camera, lens, animation) from Maya.
    camera_name = data.get('camera_name') or 'camera1'
    if not cmds.objExists(camera_name):
        print("WARNING: Camera '{}' does not exist. Using 'camera1'.".format(camera_name))
        camera_name = 'camera1'

    data['camera_data'] = get_camera_data(camera_name, data['start_frame'], data['end_frame'])

    # Render image sequence in Maya
    file_sequence_name = '{}.####.{}'.format(data['output_name'], data['image_format'])
    maya_file_sequece = os.path.join(data['maya_render_path'], file_sequence_name)
    
    print('Rendering Arnold sequence...')
    cmds.arnoldRender(width=data['width'], 
                        height=data['height'], 
                        camera=camera_name,
                        batch=True)

    # Nuke Script path
    nuke_script_name ='{}.nk'.format(data['output_name'])
    nuke_script_path = os.path.join(data['nuke_render_path'], nuke_script_name)
    nuke_file_sequence = os.path.join(data['nuke_render_path'], file_sequence_name)

    data['nuke_script_path'] = nuke_script_path
    data['input_path'] = maya_file_sequece
    data['output_path'] = nuke_file_sequence

    # Build Nuke script file
    nuke_exe = data['nuke_exe']

    print('Running Nuke script builder...')

    nuke_python = data['nuke_python_script'].replace('\\', '/')
    build_proc = subprocess.Popen([nuke_exe, 
                                    '-ti', 
                                    nuke_python, 
                                    str(data)], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE,
                                    cwd=data['nuke_render_path'])
    stdout, stderr = build_proc.communicate()
    print (stdout.decode())
    print(stderr.decode())

    # Render Nuke composite
    print('Rendering Nuke composite...')
    render_pro = subprocess.Popen([nuke_exe, 
                                    '-ti', '-x', nuke_script_path], 
                                    stdout=subprocess.PIPE, 
                                    stderr=subprocess.PIPE,
                                    cwd=data['nuke_render_path'])
    stdout, stderr = render_pro.communicate()
    print(stdout.decode())
    print(stderr.decode())

    print(r'\n=== QUICK COMPOSITE COMPLETE ===\N')


# in Maya script editor run
# import quick_composite as qc
# import importlib as il
# il.reload(qc)
# qc.main()