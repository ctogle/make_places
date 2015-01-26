import make_places.fundamental as fu
import make_places.materials as mpm
import make_places.user_info as ui

import mp_utils as mpu
import mp_vector as cv

import cStringIO as sio
import os, subprocess

from math import cos
from math import sin
from math import tan

import pdb



# create a gcol file for a primitive
def create_gcol(prim):
    lindamp = 1.0
    angdamp = 1.0
    linsleepthresh = 1.0
    angsleepthresh = 1.0
    faces = prim.get_vertexes_faces_phys()
    filename = os.path.join(world_dir, prim.gcol_filename)

    sioio = sio.StringIO()
    siowrite = sioio.write

    siowrite('TCOL1.0\n\n')
    siowrite('attributes {\n')
    siowrite('\tstatic;\n')
    siowrite('\tlinear_damping ')
    siowrite(str(lindamp))
    siowrite(';\n')
    siowrite('\tangular_damping ' + str(angdamp) + ';\n')
    siowrite('\tlinear_sleep_threshold ' + str(linsleepthresh) + ';\n')
    siowrite('\tangular_sleep_threshold ' + str(angsleepthresh) + ';\n')
    siowrite('}\n\n')
    siowrite('compound {\n')
    siowrite('}\n')

    siowrite('trimesh {\n')
    siowrite('\tvertexes {\n')

    coords = prim.coords
    for vdx in range(len(coords)):
        p = coords[vdx]
        x,y,z = str(p.x),str(p.y),str(p.z)
        siowrite('\t\t')
        siowrite(x)
        siowrite(' ')
        siowrite(y)
        siowrite(' ')
        siowrite(z)
        siowrite(';\n')

    siowrite('\t}\n')
    siowrite('\tfaces {\n')
    for m in faces.keys():
        for f in faces[m]:
            siowrite('\t\t')
            siowrite(' '.join([str(f[0]),str(f[1]),str(f[2])]))
            siowrite(' \"')
            siowrite(m)
            siowrite('\";\n')
    siowrite('\t}\n}\n')

    with open(filename,'w') as handle:handle.write(sioio.getvalue())

#####################################################################################
### everything to do with the lua scripts for the grit world
#####################################################################################

# initialize the grit world as empty
def reset_world_scripts():
    reset_map_script()
    reset_classes_script()
    reset_materials_script()

# dump the grit world into lua scripts
def output_world_scripts():
    output_classes()
    output_map()
    output_mats()

#####################################################################################
### functions for writing the map script
#####################################################################################

maplines = []

# initialize the map script
def reset_map_script():
    global maplines
    world_start = [
        '\ninclude `materials_constant.lua`\n', 
        'include `materials.lua`\n', 
        'include `classes.lua`\n\n']
    maplines = world_start
    mapfile = os.path.join(world_dir, 'map.lua')
    with open(mapfile, 'w') as handle:
        [handle.write(li) for li in world_start]

# add object to map for new grit world
def add_to_map(obj,loc,rot,name):
    global maplines
    mapargs = (obj,loc,rot,name,)
    newmaplines = write_map_lines(*mapargs)
    maplines += newmaplines

# add an object to the map script lines
def write_map_lines(obj, location, rotation, name):
    zang = rotation[2]
    quat = (cos(zang/2.0),0,0,sin(zang/2.0))
    lines = ['\nobject `' + obj + '` ' + location.__repr__() + ' { rot=quat' + quat.__repr__() + ', name="' + name + '" }\n']
    return lines

# generate the map script
def output_map():
    mapfile = os.path.join(world_dir, 'map.lua')
    with open(mapfile, 'w') as handle:
        handle.write(''.join(maplines))

#####################################################################################
#####################################################################################

#####################################################################################
### functions for writing the classes script
#####################################################################################

classlines = []
used_classes = {}

# initialize the classes script
def reset_classes_script():
    global classlines, used_classes
    used_classes = {}

    class_start = ['\n', '\n']
    classlines = class_start
    classfile = os.path.join(world_dir, 'classes.lua')
    with open(classfile, 'w') as handle:
        [handle.write(li) for li in class_start]

# generate the classes script file
def output_classes():
    classfile = os.path.join(world_dir, 'classes.lua')
    with open(classfile, 'w') as handle:
        handle.write(''.join(classlines))

# add a class to the classes script
def add_to_classes(clname,gmesh,cmesh,rd,
        is_lod = False,has_lod = False):
    global classlines

    if clname in used_classes.keys() and not is_lod:
        print 'clname should be made unique:', clname
        pdb.set_trace()

    clargs = (clname,gmesh,cmesh,rd,has_lod)
    if is_lod: newclasslines = write_lod_class(*clargs)
    else: newclasslines = write_class(*clargs)
    classlines += newclasslines
    used_classes[clname] = newclasslines
    #else: print 'clname in used classes already:', clname

# write a single class
def write_class(clname, gmesh, cmesh, rd, lod):
    lod = 'true' if lod else 'false'
    lines = [
        '\nclass `' + clname + '` (ColClass) {\n', 
        '    gfxMesh = `' + gmesh + '`;\n'
        '    colMesh = `' + cmesh + '`;\n'
        '    renderingDistance = ' + str(rd) + ';\n', 
        '    castShadows = true;\n',  
        '    lod = ' + lod + ';\n',  
        '    receiveShadows = true;\n',  
        '    placementZOffset = false;\n',  
        '    placementRandomRotation = false;\n', 
        '}\n']
    return lines

# write a single lod class
def write_lod_class(clname, gmesh, cmesh, rd, lod):
    lodclname = 'lod_' + clname
    lines = [
        '\nclass `'+ lodclname + '` (BaseClass) {\n',
        '    gfxMesh = `' + gmesh + '`;\n'
        '    castShadows = false;\n', 
        '    renderingDistance = ' + str(rd) + ';\n',
        '}\n']
    return lines

#####################################################################################
#####################################################################################

#####################################################################################
### functions for writing the materials script
#####################################################################################

materials = {
    'cubemat' : ('animgtex', 'cubetex.png'), 
    'octagonmat' : ('animgtex', 'octagontex.png'), 
    'ground' : ('animgtex', 'green.png'), 
    'grass' : ('animgtex', 'grass.png'), 
    'concrete' : ('animgtex', 'concrete.png'), 
    
    'rubber' : ('animgtex', 'rubber.png'), 
    #'bumper' : ('animgtex', 'bumper.png'), 
    'bumper' : ('animgtex', 'rubber.png'), 
    'light' : ('animgtex', 'light.png'), 
    'glass' : ('animgtex', 'glass.png'), 
    'metal' : ('animgtex', 'metal.png'), 
    #'metal2' : ('animgtex', 'metal2.png'), 
    'metal2' : ('animgtex', 'metal.png'), 

    'asphalt' : ('animgtex', 'asphalt.jpg'), 
    'brick' : ('animgtex', 'brick.jpg'), 
    'hokie' : ('animgtex', 'hokiestone.jpg'), 
    
    #'grass2' : ('animgtex', 'grass.dds'), 
    'road' : ('animgtex', 'road.png'), 
    
    'roof' : ('animgtex', 'rubber.png'), 
    #material "Road" {vertexDiffuse=true, diffuseMap="textures/road.dds", normalMap="textures/road_N.dds", glossMap="textures/road_S.tga"  }
        }
#used_mats = {}
#matlines = []

matstring = sio.StringIO()

# initialize the materials script
def reset_materials_script():
    global used_mats, matlines
    used_mats = {}

    matfile = os.path.join(world_dir, 'materials.lua')
    #mats_start = sio.StringIO()
    matstring.write('\n')
    #mats_start = ['\n']

    mpm.write_default_materials(matstring)

    #with open(matfile, 'r') as handle:
    #    for li in handle.readlines():
    #        if not li.strip == '':
    #            newmat = read_material_name(li)
    #            if not newmat in used_mats.keys():
    #                used_mats[newmat] = li.replace('\n','')
    #                mats_start.append(li)

    #mats_start.append('\n')
    matstring.write('\n')
    #matlines = mats_start
    with open(matfile, 'w') as handle:
        handle.write(matstring.getvalue())
        #[handle.write(li) for li in mats_start]

# read the name of a material
def read_material_name____(matline):
    if matline.startswith('material'):
        st = matline.find('`') + 1
        matline = matline.replace('`','@',1)
        en = matline.find('`')
        matname = matline[st:en]
        return matname

# adds a material to the materials script
def add_to_materials___(mats):
    #global matlines

    print 'called add to mats', mats

    texfiles = []
    for ma in mats:
        if ma in materials.keys(): texfiles.append(ma)
        else:texfiles.append(None)
    
    for tf, ma in zip(texfiles, mats):
        if tf is None: continue
        if not ma in used_mats.keys():
            margs = (ma,tf,)
            newmatlines = write_material(*margs)
            #matlines += newmatlines
            used_mats[ma] = newmatlines

# generate the materials script file
def output_mats():
    matfile = os.path.join(world_dir, 'materials.lua')
    #mats_start = sio.StringIO()
    with open(matfile, 'w') as handle:
        #handle.write(''.join(matlines))
        handle.write(matstring.getvalue())

# write the lua code defining a new material
def write_material(matname, textfile):

    print 'write mat', matname, textfile

    #lines = ['\nmaterial "' + matname + '" {diffuseMap = "' + textdir + '/' + textfile + '"}\n']
    lines = ['\nmaterial `' + matname + '` {diffuseMap = `' + textfile + '`}\n']
    return lines

#####################################################################################
#####################################################################################

#####################################################################################
### functions for creating scenegraph nodes in the grit world
#####################################################################################

world_dir = ui.info['worlddir']
textdir = '/solemn/textures'
last_origin = None
grit_number = 0

# get a grit world id number shared by lods
def get_grit_number(repeat = False):
    global grit_number
    if repeat: return str(grit_number - 1)
    num = grit_number
    nex = num + 1
    grit_number = nex
    return str(num)

# create scengraphs in the grit world by providing top level nodes
def create_element(*args):
    for ag in args:
        if not type(ag) is type([]): create_elem(ag)
        else: [create_elem(e) for e in ag]

# create one node and its children in the grit world
def create_elem(elem, center = True):
    import make_places.scenegraph as sg
    sgr = sg.sgraph(nodes = [elem])
    sgr.make_scene(center = center)
    #print 'creating node\n', elem

# create primitives in the grit world
def create_primitive(*args, **kwargs):
    for ag in args:
        if not type(ag) is type([]): create_prim(ag, **kwargs)
        elif ag is None: return
        else: [create_prim(p, **kwargs) for p in ag if not p is None]
    
# create one primitive in the grit world
def create_prim(prim, name = None, center = False, 
        world_rotation = None, rdist = 200, 
                lodrdist = 2000, **kwargs):
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
    # rotate coords backwards by world_rotation?

    is_new = prim.write_as_xml(world_dir)
    if is_new and prim.gcol:create_gcol(prim)

    gnum = get_grit_number(repeat = prim.is_lod)
    if name is None: oname = prim.tag + gnum
    else: oname = name + gnum
    mname = prim.gfxmesh_name
    cname = prim.colmesh_name
    if prim.is_lod:
        rdist = lodrdist
    else:
        add_to_map(oname,w_position.to_tuple(),
            w_rotation.to_tuple(),oname)
    add_to_classes(oname, mname, cname, rdist, 
        has_lod = prim.has_lod, is_lod = prim.is_lod)
    #mpm.add_materials(prim.materials)
    #add_to_materials(prim.materials)








