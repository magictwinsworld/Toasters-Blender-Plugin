# MIT License

import os
import bpy
import shutil
import pathlib

import bpy.utils.previews
from bpy.utils.previews import ImagePreviewCollection
import typing

from . import common as Common
from . import settings as Settings
from .. import globs
from ..tools.register import register_wrap
from .translations import t

# global variables
preview_collections: typing.Type[ImagePreviewCollection] = {}
reloading = False

main_dir = pathlib.Path(os.path.dirname(__file__)).parent.resolve()
resources_dir = os.path.join(str(main_dir), "resources")

def load_other_icons():
    # Note that preview collections returned by bpy.utils.previews
    # are regular py objects - you can use them to store custom data.
    pcoll: typing.Type[ImagePreviewCollection] = bpy.utils.previews.new()

    # path to the folder where the icon is
    # the path is calculated relative to this py file inside the addon folder
    icons_dir = os.path.join(resources_dir, "icons")
    icons_other_dir = os.path.join(icons_dir, "other")

    pcoll.load('heart1', os.path.join(icons_other_dir, 'heart1.png'), 'IMAGE')
    pcoll.load('discord1', os.path.join(icons_other_dir, 'discord1.png'), 'IMAGE')
    pcoll.load('help1', os.path.join(icons_other_dir, 'help1.png'), 'IMAGE')
    pcoll.load('cats1', os.path.join(icons_other_dir, 'toaster1.png'), 'IMAGE')
    pcoll.load('toaster1', os.path.join(icons_other_dir, 'toaster1.png'), 'IMAGE')
    pcoll.load('empty', os.path.join(icons_other_dir, 'empty.png'), 'IMAGE')
    pcoll.load('mesh', os.path.join(icons_other_dir, 'mesh.png'), 'IMAGE')
    pcoll.load('UP_ARROW', os.path.join(icons_other_dir, 'blender_up_arrow.png'), 'IMAGE')
    pcoll.load('Resonite', os.path.join(icons_other_dir, 'rsn_logo128.png'), 'IMAGE')

    # Automatically load all PNG icons from resources/icons/menu
    icons_menu_dir = os.path.join(icons_dir, "menu")
    if os.path.exists(icons_menu_dir):
        for file_name in os.listdir(icons_menu_dir):
            if file_name.lower().endswith('.png'):
                icon_key = os.path.splitext(file_name)[0]
                icon_path = os.path.join(icons_menu_dir, file_name)
                pcoll.load(icon_key, icon_path, 'IMAGE')

    preview_collections['custom_icons'] = pcoll


def unload_icons():
    print('UNLOADING ICONS!')
    for pcoll in preview_collections.values():
        bpy.utils.previews.remove(pcoll)
    preview_collections.clear()
    print('DONE!')
    