# MIT License

import bpy
from .. import globs
from ..tools import common as Common
from ..tools import iconloader as Iconloader
from ..tools.register import register_wrap
from ..tools.translations import t

class ToolPanel(object):
    bl_label = t('ToolPanel.label')
    bl_idname = '3D_VIEW_TS_vrc'
    bl_category = t('ToolPanel.category')
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'


class SearchMenuOperatorBase(object):
    """Base class for search menu operators that set scene properties."""
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}
    bl_property = "my_enum"
    scene_property = None  # Override in subclass
    
    def execute(self, context):
        if self.scene_property:
            setattr(context.scene, self.scene_property, self.my_enum)
        return {'FINISHED'}
    
    def invoke(self, context, event):
        wm = context.window_manager
        wm.invoke_search_popup(self)
        return {'FINISHED'}


def layout_split(layout, factor=0.0, align=False):
    return layout.split(factor=factor, align=align)


def add_button_with_small_button(layout, button_1_idname, button_1_icon, button_2_idname, button_2_icon, scale=1):
    row = layout.row(align=True)
    row.scale_y = scale
    subcol = layout_split(row, factor=0, align=True)
    subcol.operator(button_1_idname, icon=button_1_icon)
    subcol = layout_split(row, factor=0, align=True)
    subcol.operator(button_2_idname, text="", icon=button_2_icon)


def draw_section_card(layout, title=None, icon=None, align=True):
    """Draw a Zen UV-style card container with an optional section header."""
    box = layout.box()
    col = box.column(align=align)
    if title:
        header_row = col.row(align=True)
        header_row.scale_y = 0.85
        if icon:
            header_row.label(text=title, icon=icon)
        else:
            header_row.label(text=title)
        col.separator()
    return box, col


def draw_warning_box(layout, messages, icon='INFO'):
    """Draw a warning/info box with consistent styling"""
    if isinstance(messages, str):
        messages = [messages]
    
    box = layout.box()
    col = box.column(align=True)
    col.scale_y = 0.8
    
    for i, msg in enumerate(messages):
        row = col.row(align=True)
        if i == 0:
            if icon in ('ERROR', 'WARNING'):
                row.alert = True
            row.label(text=msg, icon=icon if i == 0 else 'BLANK1')
        else:
            row.label(text=msg, icon='BLANK1')
    
    return box


def draw_error_box(layout, messages):
    """Draw an error box with alert styling"""
    return draw_warning_box(layout, messages, icon='ERROR')


def draw_info_box(layout, messages):
    """Draw an info box"""
    return draw_warning_box(layout, messages, icon='INFO')


class PanelWrapper:
    """Wrapper to safely invoke Panel.draw() methods without Blender RNA struct instantiation errors."""
    def __init__(self, panel_cls, layout):
        self.layout = layout
        self.panel_cls = panel_cls

    def __getattr__(self, attr):
        val = getattr(self.panel_cls, attr)
        if callable(val):
            return val.__get__(self, self.panel_cls)
        return val


def draw_subpanel(panel_cls, layout, context):
    wrapper = PanelWrapper(panel_cls, layout)
    panel_cls.draw(wrapper, context)


@register_wrap
class TOASTERS_OT_set_tab(bpy.types.Operator):
    bl_idname = "toasters.set_tab"
    bl_label = "Switch Tab"
    bl_description = "Switch active tab in Toasters Blender Plugin"
    bl_options = {'INTERNAL'}

    tab: bpy.props.StringProperty()

    def execute(self, context):
        context.scene.toasters_active_tab = self.tab
        return {'FINISHED'}


@register_wrap
class MainToastersPanel(ToolPanel, bpy.types.Panel):
    bl_idname = 'VIEW3D_PT_toasters_main_v3'
    bl_label = 'Toasters Blender Plugin'

    def draw(self, context):
        layout = self.layout
        col = layout.column(align=True)

        # Validate armature selection
        Common.validate_armature_selection()

        # --- 1. TOP BAR (Quick Access Header) ---
        from .quickaccess import QuickAccessPanel
        top_box = col.box()
        top_col = top_box.column(align=True)
        draw_subpanel(QuickAccessPanel, top_col, context)

        col.separator()

        # --- 2. UNDERNEATH: LEFT ICON SIDEBAR + RIGHT ACTIVE TAB CONTENT ---
        main_row = col.row(align=True)

        # Left Icon Sidebar
        sidebar = main_row.column(align=True)
        sidebar.scale_x = 1.15

        # Get loaded custom icons dictionary
        custom_icons = Iconloader.preview_collections.get("custom_icons", {})

        # Tab definitions: (tab_id, translation_label, menu_icon_key, fallback_builtin_icon)
        tabs = [
            ('CUSTOM', t('CustomPanel.label'), 'custom', 'MODIFIER'),
            ('OPTIMIZATION', t('OptimizePanel.label'), 'optimization', 'MATERIAL'),
            ('EYE_TRACKING', t('EyeTrackingPanel.label'), 'eye_tracking', 'HIDE_OFF'),
            ('VISEMES', t('VisemePanel.label'), 'visemes', 'SPEAKER'),
            ('BONES', t('BoneRootPanel.label'), 'bones', 'BONE_DATA'),
            ('SCALE', t('ScalingPanel.label'), 'scale', 'FULLSCREEN_ENTER'),
            ('MMD', t('MMDOptions.label'), 'mmd', 'COMMUNITY'),
            ('OTHER', t('OtherOptionsPanel.label'), 'other', 'PREFERENCES'),
            ('SETTINGS', t('UpdaterPanel.label'), 'settings', 'SETTINGS'),
            ('CREDITS', t('CreditsPanel.label'), 'credits', 'INFO'),
        ]

        active_tab = getattr(context.scene, 'toasters_active_tab', 'CUSTOM')

        # Draw left vertical icon sidebar using custom menu icons
        for tab_id, tab_label, icon_key, fallback_icon in tabs:
            is_active = (active_tab == tab_id)
            btn_row = sidebar.row(align=True)
            btn_row.scale_y = 1.4

            if icon_key in custom_icons:
                op = btn_row.operator(
                    "toasters.set_tab",
                    text="",
                    icon_value=custom_icons[icon_key].icon_id,
                    depress=is_active
                )
            else:
                op = btn_row.operator(
                    "toasters.set_tab",
                    text="",
                    icon=fallback_icon,
                    depress=is_active
                )
            op.tab = tab_id

        # Right Active Tab Content Column
        content_box = main_row.box()
        content_col = content_box.column(align=True)

        # Find current active tab label and icon for header display
        active_label = ""
        active_icon_key = ""
        active_fallback = "INFO"
        for t_id, t_lbl, t_key, t_ico in tabs:
            if t_id == active_tab:
                active_label = t_lbl
                active_icon_key = t_key
                active_fallback = t_ico
                break

        # Render Header with the name and icon of the opened tab
        hdr_row = content_col.row(align=True)
        hdr_row.scale_y = 1.0
        if active_icon_key in custom_icons:
            hdr_row.label(text=active_label, icon_value=custom_icons[active_icon_key].icon_id)
        else:
            hdr_row.label(text=active_label, icon=active_fallback)
        content_col.separator()

        # Render Active Tab Content
        if active_tab == 'CUSTOM':
            from .custom import CustomPanel
            draw_subpanel(CustomPanel, content_col, context)

        elif active_tab == 'OPTIMIZATION':
            from .optimization import OptimizePanel
            draw_subpanel(OptimizePanel, content_col, context)

        elif active_tab == 'MMD':
            from .mmdoptions import MMDOptions
            draw_subpanel(MMDOptions, content_col, context)

        elif active_tab == 'EYE_TRACKING':
            from .eye_tracking import EyeTrackingPanel
            draw_subpanel(EyeTrackingPanel, content_col, context)

        elif active_tab == 'VISEMES':
            from .visemes import VisemePanel
            draw_subpanel(VisemePanel, content_col, context)

        elif active_tab == 'BONES':
            from .bone_root import BoneRootPanel
            draw_subpanel(BoneRootPanel, content_col, context)

        elif active_tab == 'SCALE':
            from .scale import ScalingPanel
            draw_subpanel(ScalingPanel, content_col, context)

        elif active_tab == 'OTHER':
            from .otheroptions import OtherOptionsPanel
            draw_subpanel(OtherOptionsPanel, content_col, context)

        elif active_tab == 'SETTINGS':
            from .settings_updates import UpdaterPanel
            draw_subpanel(UpdaterPanel, content_col, context)

        elif active_tab == 'CREDITS':
            from .credits import CreditsPanel
            draw_subpanel(CreditsPanel, content_col, context)


# Export commonly used classes and functions for easy import
__all__ = [
    'ToolPanel',
    'SearchMenuOperatorBase',
    'layout_split',
    'add_button_with_small_button',
    'draw_section_card',
    'draw_warning_box',
    'draw_error_box',
    'draw_info_box',
    'draw_subpanel',
    'MainToastersPanel',
]
