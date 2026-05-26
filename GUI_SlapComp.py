import maya.cmds as cmds
from functools import partial
import quick_composite as qc


# Call back functions for getting paths.
def get_paths_CB(TFBG, *args):
    """
    Summary:
        Opends a directory browser and updates the given textFieldButtonGrp with 
        the selected folder path.
    Parameters:
        TFBG (str):
            Name of the textFieldButtonGrp UI control to update.
    Arguments:
        TFBG (str):
            The name of the textFieldButtonGrp UI control to update.
        *args:
            Unused callback arguments passed automatically by Maya.
    Returns:
        str:
            The selected directory path, or an empty string if the user cancels.
    """
    path = cmds.fileDialog2(fileMode=2, dialogStyle=2)
    if path:
        cmds.textFieldButtonGrp(TFBG, edit=True, text=path[0])
        return path[0]
    return ''


def get_file_CB(TFBG, *args):
    """
    Summary:
        Opens a file browser and updates the given textFieldButtonGrp with the selected file path.
    Parameters:
        TFBG (str):
            Name of the textFieldButtonGrp UI control to update.
        *args:
            Extra callback parameters passed automatically by Maya.
    Arguments:
        TFBG (str):
            The UI control that will display the chosen file path.
        *args:
            Not used directly; present for Maya callback compatibility.
    Returns:
        str:
            The selected file path, or an empty string if the user cancels.
    """
    path = cmds.fileDialog2(fileMode=1, dialogStyle=2)
    if path:
        cmds.textFieldButtonGrp(TFBG, edit=True, text=path[0])
        return path[0]
    return ''


# Callback functions for resolution presets.
def res_preset_CB(*args):
    """
    Summary:
        Updates the resolution inFieldGrp based on the selected preset from the RES_PRESET_OMG 
        optionMenuGrp.
    Parameters:
        *args:
            Extra callback parameters passed automatically by Maya.
    Arguments:
        *args:
            Not used directly; present for Maya callback compatibility.
    Returns:
        None
    """
    preset = cmds.optionMenuGrp('RES_PRESET_OMG', query=True, value=True)

    if 'x' in preset:
        try:
            w, h = preset.split('x')
            cmds.intFieldGrp('RES_IFG', edit=True, value1=int(w), value2=int(h))
        except:
            pass
      

# AOVs static for now, I would like to eventually call all available AOVs including custom 
# AOVs imported into the file.
AOV_LIST = ['diffuse', 'specular', 'transmission', 'emission']

def collect_static_aovs(prefix):
    """
    Summary:
        Callects all enabled AOV checkboxes using the given prefix.
    Parameters:
        prefix (str):
            Naming prefix used to build checkbox names
            (e.g., "AOV" > "AOV_diffuse_CB).
    Arguments:
        prefix (str):
            The base name used to find AOV checkbox controls in the UI.
    Returns:
        list[str]:
            A list of AOV names that are currently enabled.
    """
    selected = []
    for aov in AOV_LIST:
        cb = '{}_{}_CB'.format(prefix, aov)
        if cmds.checkBox(cb, query=True, value=True):
            selected.append(aov)
    return selected


# Toggle the Grade / Glow UI to appear when the user selects it as an option.
def toggle_grade_UI(*args):
    """
    Summary:
        Expands or collapses the Grade Options frameLayout based on the state of the 
        GRADE_ENABLE_CB checkbox.
    Parameters:
        *args:
            Extra callback parameters passed automatically by Maya.
    Arguments:
        *args:
            Not used directly; present for Maya callback compatibility
    Returns:
        None
    """
    enabled = cmds.checkBox('GRADE_ENABLE_CB', query=True, value=True)
    cmds.frameLayout('GRADE_FL', edit=True, collapse=not enabled)


def toggle_glow_UI(*args):
    """
    Summary:
        Expands or collapses the Blow Options frameLayout based on the state of the 
        GLOW_ENABLE_CB checkbox.
    Parameters:
        *args:
            Extra callback parameters passed automatically by Maya.
    Arguments:
        *args:
            Not used directly; present for Maya callback compatibility
    Returns:
        None
    """
    enabled = cmds.checkBox('GLOW_ENABLE_CB', query=True, value=True)
    cmds.frameLayout('GLOW_FL', edit=True, collapse=not enabled)


# Go button callback.
def go_CB(*args):
    """
    Summary:
        Gathers all GUI input values, builds a data dictionary, prints it for debugging, 
        and sends it to qc.quick_composite().
    Parameters:
        *args:
            Extra callback parameters passed automatically by Maya.
    Arguments:
        *args:
            Not used directly; present for Maya callback compatibility
    Returns:
        None
    """
    grade_enabled = cmds.checkBox('GRADE_ENABLE_CB', query=True, value=True)
    glow_enabled = cmds.checkBox('GLOW_ENABLE_CB', query=True, value=True)

    data = {'nuke_exe': cmds.textFieldButtonGrp('NUKE_EXE_TFBG', query=True, text=True),
            'output_name': cmds.textFieldGrp('OUTPUT_TFG', query=True, text=True),
            'camera_name': cmds.textFieldGrp('CAMERA_TFG', query=True, text=True),
            'maya_render_path': cmds.textFieldButtonGrp('MAYA_RENDER_PATH_TFBG', 
                                                          query=True, 
                                                          text=True),
            'nuke_render_path': cmds.textFieldButtonGrp('NUKE_RENDER_PATH_TFBG', 
                                                        query=True, 
                                                        text=True),
            'nuke_python_script': cmds.textFieldButtonGrp('NUKE_PY_TFBG', query=True, text=True),
            'background_image': cmds.textFieldButtonGrp('BG_TFBG', query=True, text=True),
            
            'active_aovs': collect_static_aovs('AOV'),

            'start_frame':cmds.intFieldGrp('FRAME_RANGE_IFG', query=True, value1=True),
            'end_frame': cmds.intFieldGrp('FRAME_RANGE_IFG', query=True, value2=True),
            'width': cmds.intFieldGrp('RES_IFG', query=True, value1=True),
            'height': cmds.intFieldGrp('RES_IFG', query=True, value2=True),

            'image_format': cmds.optionMenuGrp('IMG_FMT_OMG', query=True, value=True),
            'compression': cmds.optionMenuGrp('COMP_OMG', query=True, value=True),
            'merge_operation': cmds.optionMenuGrp('MERGE_OP_OMG', query=True, value=True),

            'grade_enabled': grade_enabled,
            'grade_settings': {'h': cmds.floatSliderGrp('GRADE_H_FSG', query=True, value=True),
                               's': cmds.floatSliderGrp('GRADE_S_FSG', query=True, value=True),
                               'l': cmds.floatSliderGrp('GRADE_L_FSG', query=True, value=True),
                               'gain': cmds.floatSliderGrp('GRADE_GAIN_FSG', 
                                                           query=True, 
                                                           value=True),
                               'gamma': cmds.floatSliderGrp('GRADE_GAMMA_FSG', 
                                                            query=True, 
                                                            value=True),
                               'lift': cmds.floatSliderGrp('GRADE_LIFT_FSG', 
                                                           query=True, 
                                                           value=True),} 
                                                           if grade_enabled else {},
            'glow_enabled': glow_enabled,
            'glow_settings': {'h': cmds.floatSliderGrp('GLOW_H_FSG', query=True, value=True),
                              's': cmds.floatSliderGrp('GLOW_S_FSG', query=True, value=True),
                              'l': cmds.floatSliderGrp('GLOW_L_FSG', query=True, value=True),
                              'size': cmds.floatSliderGrp('GLOW_SIZE_FSG', query=True, value=True),
                              'brightness': cmds.floatSliderGrp('GLOW_BRIGHT_FSG', 
                                                                query=True, 
                                                                value=True),} 
                                                                if glow_enabled else{},}

    print('GUI DATA:', data)
    qc.quick_composite(data)


# Window defaults

def set_window_defaults():
    """
    Summary:
        Initializes all GUI fields with default values based on the current Maya workspace, 
        playback range, and platform-specific Nnuke paths.
    Parameters:
        None
    Arguments:
        None
    Returns:
        None
    """
    root_dir = cmds.workspace(query=True, rootDirectory=True)

    cmds.textFieldButtonGrp('MAYA_RENDER_PATH_TFBG', edit=True, text='{}images'.format(root_dir))
    cmds.textFieldButtonGrp('NUKE_RENDER_PATH_TFBG', edit=True, text='{}comp'.format(root_dir))
    cmds.textFieldButtonGrp('NUKE_PY_TFBG', 
                            edit=True, 
                            text='{}.nuke/multipass_composite.py'.format(root_dir))
    cmds.textFieldButtonGrp('BG_TFBG', edit=True, text='{}sourceimages'.format(root_dir))

    try:
        import path_utilities as pu
        default_nuke = pu.get_alias_path('nuke')
    except:
        if cmds.about(nt=True):
            default_nuke = r'C:\Program Files\Nuke16.0v7\Nuke16.0.exe'
        elif cmds.about(macOS=True):
            default_nuke = '/Applications/Nuke16.0v7/Nuke16.0v7.app/Contents/MacOS/Nuke16.0v7'
        else:
            default_nuke = ''

    cmds.textFieldButtonGrp('NUKE_EXE_TFBG', edit=True, text=default_nuke)

    cmds.textFieldGrp('OUTPUT_TFG', edit=True, text='test')

    start = int(cmds.playbackOptions(query=True, minTime=True))
    end = int(cmds.playbackOptions(query=True, maxTime=True))
    cmds.intFieldGrp('FRAME_RANGE_IFG', edit=True, value1=start, value2=end)

    cmds.intFieldGrp('RES_IFG', edit=True, value1=1920, value2=1080)
    cmds.optionMenuGrp('RES_PRESET_OMG', edit=True, value='1920x1080')

    cmds.optionMenuGrp('IMG_FMT_OMG', edit=True, value='exr')
    cmds.optionMenuGrp('COMP_OMG', edit=True, value='zip')
    cmds.optionMenuGrp('MERGE_OP_OMG', edit=True, value='plus')

    cmds.checkBox('GRADE_ENABLE_CB', edit=True, value=False)
    cmds.frameLayout('GRADE_FL', edit=True, collapse=True)

    cmds.checkBox('GLOW_ENABLE_CB', edit=True, value=False)
    cmds.frameLayout('GLOW_FL', edit=True, collapse=True)

# Build GUI
def build_win():
    """
    Summary:
        Builds the full Quick Composite GUI window, including file paths, resolution settings, 
        AOVs, grade options, glow options, and the Go button.
    Parameters:
        None
    Arguments:
        None
    Returns:
        None
    """
    if cmds.window('COMP_WIN', exists=True):
        cmds.deleteUI('COMP_WIN')

    cmds.window('COMP_WIN', title='Quick Composite', sizeable=True)
    cmds.columnLayout(adjustableColumn=True)

    # File Paths
    cmds.textFieldButtonGrp('NUKE_EXE_TFBG', 
                            label='Nuke Application', 
                            buttonLabel='Set', 
                            buttonCommand=partial(get_file_CB, 'NUKE_EXE_TFBG'))

    cmds.textFieldButtonGrp('MAYA_RENDER_PATH_TFBG', 
                            label='Maya Render Path', 
                            buttonLabel='Set', 
                            buttonCommand=partial(get_paths_CB, 'MAYA_RENDER_PATH_TFBG'))
    
    cmds.textFieldButtonGrp('NUKE_RENDER_PATH_TFBG', 
                            label='Nuke Render Path', 
                            buttonLabel='Set', 
                            buttonCommand=partial(get_paths_CB, 'NUKE_RENDER_PATH_TFBG'))

    cmds.textFieldButtonGrp('NUKE_PY_TFBG', 
                            label='Nuke Python Script', 
                            buttonLabel='Set', 
                            buttonCommand=partial(get_file_CB, 'NUKE_PY_TFBG'))

    cmds.textFieldButtonGrp('BG_TFBG', 
                            label='Background Image', 
                            buttonLabel='Set', 
                            buttonCommand=partial(get_file_CB, 'BG_TFBG'))

    cmds.separator(h=9, style='in')

    # Output
    cmds.textFieldGrp('OUTPUT_TFG', label='Output Name', text='test')

    cmds.textFieldGrp('CAMERA_TFG', label='Camera', text='camera1')

    cmds.intFieldGrp('FRAME_RANGE_IFG', 
                     numberOfFields=2, 
                     label='Frame Range', 
                     value1=1, 
                     value2=100)

    cmds.separator(h=9, style='in')

    # Resolution
    cmds.optionMenuGrp('RES_PRESET_OMG', label='Resolution Preset', changeCommand=res_preset_CB)

    cmds.menuItem(label='320x240')
    cmds.menuItem(label='640x480')
    cmds.menuItem(label='720x486')
    cmds.menuItem(label='720x576')
    cmds.menuItem(label='1280x720')
    cmds.menuItem(label='1920x1080')
    cmds.menuItem(label='2048x2048')
    cmds.menuItem(label='2048x1080')
    cmds.menuItem(label='4096x4096')
    cmds.menuItem(label='4096x2160')
    cmds.menuItem(label='Custom/Scene')

    cmds.intFieldGrp('RES_IFG', 
                    numberOfFields=2, 
                    label='Resolution(W x H)', 
                    value1=1920, 
                    value2=1080)

    cmds.separator(h=9, style='in')

    # Image format
    cmds.optionMenuGrp('IMG_FMT_OMG', label='Image Format')
    cmds.menuItem(label='exr')
    cmds.menuItem(label='png')
    cmds.menuItem(label='jpeg')

    cmds.optionMenuGrp('COMP_OMG', label='Compression')
    cmds.menuItem(label='zip')
    cmds.menuItem(label='dwab')
    cmds.menuItem(label='none')

    # Merge Operation
    cmds.optionMenuGrp('MERGE_OP_OMG', label='Merge Operation')
    cmds.menuItem(label='plus')
    cmds.menuItem(label='over')

    cmds.separator(h=9, style='in')

    # AOVs
    cmds.text(label='AOVs', align = 'left')
    cmds.columnLayout(adjustableColumn=True)
    for aov in AOV_LIST:
        cmds.checkBox('AOV_{}_CB'.format(aov), label=aov, value=True)
    cmds.setParent('..')

    cmds.separator(h=9, style='in')
    

    # Grade options
    cmds.checkBox('GRADE_ENABLE_CB', 
                  label='Enable Grade Node', 
                  value=False, 
                  changeCommand=toggle_grade_UI)
    
    cmds.frameLayout('GRADE_FL', label='Grade Options', collapsable=True, collapse=True)
    cmds.columnLayout(adjustableColumn=True)

    cmds.text(label='Grade Tint (HSL)', align='left')
    cmds.floatSliderGrp('GRADE_H_FSG', 
                        label='Hue', 
                        field=True, 
                        minValue=0.0, 
                        maxValue=1.0, 
                        value=0.0)
    cmds.floatSliderGrp('GRADE_S_FSG', 
                        label='Saturation', 
                        field=True, 
                        minValue=0.0, 
                        maxValue=1.0)
    cmds.floatSliderGrp('GRADE_L_FSG', 
                        label='Lightness', 
                        field=True, 
                        minValue=0.0, 
                        maxValue=1.0, 
                        value=0.5)

    cmds.floatSliderGrp('GRADE_GAIN_FSG', 
                        label='Gain', 
                        field=True, 
                        minValue=0.0, 
                        maxValue=5.0, 
                        value=1.0)
    cmds.floatSliderGrp('GRADE_GAMMA_FSG', 
                        label='Gamma', 
                        field=True, 
                        minValue=0.1, 
                        maxValue=5.0, 
                        value=1.0)
    cmds.floatSliderGrp('GRADE_LIFT_FSG', 
                        label='Lift', 
                        field=True, 
                        minValue=-1.0, 
                        maxValue=1.0, 
                        value=0.0)

    cmds.setParent('..') # exit Grade column
    cmds.setParent('..') # exit Grade frame
    cmds.separator(h=9, style='in')

    # Glow options
    cmds.checkBox('GLOW_ENABLE_CB', label='Enable Glow', value=False, changeCommand=toggle_glow_UI)

    cmds.frameLayout('GLOW_FL', label='Glow Options', collapsable=True, collapse=True)
    cmds.columnLayout(adjustableColumn=True)

    cmds.text(label='Glow Tint (HSL)', align='left')
    cmds.floatSliderGrp('GLOW_H_FSG', 
                        label='Hue', 
                        field=True, 
                        minValue=0.0, 
                        maxValue=1.0, 
                        value=0.793)
    cmds.floatSliderGrp('GLOW_S_FSG', 
                        label='Saturation', 
                        field=True, 
                        minValue=0.0, 
                        maxValue=1.0, 
                        value=0.875)
    cmds.floatSliderGrp('GLOW_L_FSG', 
                        label='Lightness', 
                        field=True, 
                        minValue=0.0, 
                        maxValue=1.0, 
                        value=0.48)

    cmds.floatSliderGrp('GLOW_SIZE_FSG', 
                        label='Glow Size', 
                        field=True, 
                        minValue=0.0, 
                        maxValue=200.0, 
                        value=30)
    cmds.floatSliderGrp('GLOW_BRIGHT_FSG', 
                        label='Glow Brightness', 
                        field=True, 
                        minValue=0.0, 
                        maxValue=20.0, 
                        value=9.0)

    cmds.setParent('..')
    cmds.setParent('..')

    cmds.separator(h=9, style='in')

    # Go! button
    cmds.button(label='Go!', height=40, command=go_CB)

    cmds.showWindow('COMP_WIN')


# Main function
def main():
    """
    Summary:
        Entry point for launching the Quick Composite GUI. Guilds the window and applies all default settings.
    Parameters:
        None
    Arguments:
        None
    Returns:
        None
    """
    build_win()
    set_window_defaults()


# Shelf button script for SlapComp GUI
# import GUI_SlapComp as sc
# import importlib as il
# il.reload(sc)
# sc.main()