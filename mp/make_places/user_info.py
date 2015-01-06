
import os

game = 'solemn'

grit_dir = os.path.join('/home','athyra','dev','gritengine')
#grit_dir = os.path.join('/home','athyra','dev','grit')
game_dir = os.path.join(grit_dir,'grit_core','media',game)
world_dir = os.path.join(game_dir,'newworld')
texture_dir = os.path.join(game_dir,'textures')

make_places_dir = os.path.join('/home','athyra','dev','make_places','mp')
mp_dir = os.path.join(make_places_dir, 'make_places')

resource_dir = os.path.join(make_places_dir,'resources')
new_world_dir = os.path.join(resource_dir,'newworld')
new_texture_dir = os.path.join(resource_dir,'textures')
prim_data_dir = os.path.join(resource_dir,'primitive_data')

info = {
    'game':game, 
    'mpdir':mp_dir, 
    'gritdir':grit_dir, 
    'gamedir':game_dir, 
    'worlddir':world_dir, 
    'newworlddir':new_world_dir, 
    'texturedir':texture_dir, 
    'newtexturedir':new_texture_dir, 
    'primitivedir':prim_data_dir, 
        }

