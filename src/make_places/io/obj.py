import make_places.fundamental as fu
import make_places.scenegraph as sg
import make_places.materials as mpm
import make_places.user_info as ui

import mp_utils as mpu
import mp_vector as cv

import cStringIO as sio

import sys,os,pdb


world_dir = ui.info['contentdir']
last_origin = None

#########################################################################
### materials
#########################################################################

matstring = sio.StringIO()

# initialize the materials script
def reset_materials_script():
    matfile = os.path.join(world_dir, 'materials.mtl')
    matstring.write('\n')
    write_default_materials_mtl(matstring)
    matstring.write('\n')
    with open(matfile, 'w') as handle:
        handle.write(matstring.getvalue())

def write_default_materials_mtl(msio):
    cubemat = material('cubemat',diffuseMap = 'textures/generic/orangeboxtex.png')
    sidewalk1 = material('sidewalk1',diffuseMap = 'textures/concrete/sidewalk1.jpg')
    asphalt = material('asphalt',diffuseMap = 'textures/concrete/asphalt.jpg')
    roadline_y = material('roadline_y',diffuseMap = 'textures/concrete/roadline.png')
    roadline_y_cont = material('roadline_y_cont',diffuseMap = 'textures/concrete/roadline_w_continuous.png')
    roadline_w_cont = material('roadline_w_cont',diffuseMap = 'textures/concrete/roadline_w_continuous.png')
    def_mats = [cubemat,sidewalk1,asphalt,roadline_y,roadline_y_cont,roadline_w_cont]

    mcount = len(def_mats)
    msio.write('# Material Count: ')
    msio.write(str(mcount))
    msio.write('\n')
    for dm in def_mats: dm._write(msio)

class material(fu.base):

    def _write_path_property(self,msio,prop,val):
        if val is None:return
        msio.write(prop)
        msio.write(' ')
        msio.write(val)
        msio.write('\n')

    def _write(self,msio):
        msio.write('\nnewmtl ')
        msio.write(self.name)
        msio.write('\n')
        msio.write('Ka 1.000 1.000 1.000\n')
        msio.write('Kd 1.000 1.000 1.000\n')
        msio.write('Ks 0.000 0.000 0.000\n')
        msio.write('d 1.0\n')
        msio.write('illum 2\n')
        self._write_properties(msio)
        msio.write('\n')

    def _write_properties(self,msio):
        self._write_diffuse_properties(msio)

    def _write_diffuse_properties(self,msio):
        #self._write_vector_property(msio,'diffuseColour',self.diffuseColour)
        #self._write_path_property(msio,'diffuseMap',self.diffuseMap)
        #self._write_bool_property(msio,'vertexDiffuse',self.vertexDiffuse)
        self._write_path_property(msio,'map_Kd',self.diffuseMap)

    def __init__(self,name,**kwargs):
        self.name = name
        self._default_('diffuseMap',None,**kwargs)

'''#
newmtl Textured
   Ka 1.000 1.000 1.000
   Kd 1.000 1.000 1.000
   Ks 0.000 0.000 0.000
   d 1.0
   illum 2
   map_Ka lenna.tga           # the ambient texture map
   map_Kd lenna.tga           # the diffuse texture map (most of the time, it will
                              # be the same as the ambient texture map)
   map_Ks lenna.tga           # specular color texture map
   map_Ns lenna_spec.tga      # specular highlight component
   map_d lenna_alpha.tga      # the alpha texture map
   map_bump lenna_bump.tga    # some implementations use 'map_bump' instead of 'bump' below
'''#

#########################################################################
#########################################################################

# create scengraphs in an obj world by providing top level nodes
def create_element(*args):
    for ag in args:
        if not type(ag) is type([]): create_elem(ag)
        else: [create_elem(e) for e in ag]

# create one node and its children in an obj world
def create_elem(elem, center = True):
    sgr = sg.sgraph(nodes = [elem])
    objgeo = sys.modules[__name__]
    sgr.make_scene(objgeo,center = center)
    #print 'creating node\n', elem

# create primitives as obj files
def create_primitive(*args, **kwargs):
    for ag in args:
        if not type(ag) is type([]): create_prim(ag, **kwargs)
        elif ag is None: return
        else: [create_prim(p, **kwargs) for p in ag if not p is None]
    
# create one primitive as one obj file
def create_prim(prim, name = None, center = False, 
        world_rotation = None, rdist = 200, 
                lodrdist = 2000, **kwargs):

    # this should take one primitive and create one obj/mtl file in a content directory

    global last_origin
    if world_rotation is None:
        world_rotation = cv.vector(0,0,0)

    if prim.is_lod:
        prim.origin = last_origin
        last_origin = prim.reposition_origin()
    else:last_origin = prim.reposition_origin()

    if last_origin is None:
        print 'must skip empty primitive creation!'
        return

    w_position = prim.origin
    w_rotation = world_rotation

    is_new = prim.write_as_obj(world_dir)

#########################################################################
#########################################################################










