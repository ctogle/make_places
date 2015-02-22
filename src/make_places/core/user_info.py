
import os

game = 'solemn'

grit_dir = os.path.join('/home','athyra','dev','gritengine')
#grit_dir = os.path.join('/home','athyra','dev','grit')
game_dir = os.path.join(grit_dir,'grit_core','media',game)
world_dir = os.path.join(game_dir,'newworld')
texture_dir = os.path.join(game_dir,'textures')

make_places_dir = os.path.join('/home','athyra','dev','make_places','src')
mp_dir = os.path.join(make_places_dir,'make_places')

obj_world_dir = os.path.join('/home','athyra','dev','mpcontent')
obj_texture_dir = os.path.join(obj_world_dir,'textures')

resource_dir = os.path.join(make_places_dir,'resources')
new_world_dir = os.path.join(resource_dir,'newworld')
new_texture_dir = os.path.join(resource_dir,'textures')
prim_data_dir = os.path.join(resource_dir,'primitive_data')

info = {
    #'exporter':'obj',
    'exporter':'grit',

    'game':game, 
    'mpdir':mp_dir, 
    'gritdir':grit_dir, 
    'gamedir':game_dir, 
    'worlddir':world_dir, 
    'newworlddir':new_world_dir, 
    'texturedir':texture_dir, 
    'newtexturedir':new_texture_dir, 
    'primitivedir':prim_data_dir, 

    'contentdir':obj_world_dir, 
    'contenttexturedir':obj_texture_dir, 
        }
