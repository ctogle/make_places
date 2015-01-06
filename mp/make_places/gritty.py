import make_places.fundamental as fu
import mp_utils as mpu
import mp_vector as cv
import make_places.user_info as ui





import pdb, os, subprocess

from math import cos
from math import sin
from math import tan

def create_primitive(*args, **kwargs):
    for ag in args:
        if not type(ag) is type([]): create_prim(ag, **kwargs)
        elif ag is None: return
        else: [create_prim(p, **kwargs) for p in ag if not p is None]
    
world_dir = ui.info['worlddir']
textdir = '/solemn/textures'
last_origin = None
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

    xml, is_new = prim.write_as_xml()
    if is_new:
        xdir = os.path.join(world_dir, prim.xml_filename)
        with open(xdir,'w') as handle:
            [handle.write(li) for li in xml]
        create_gcol(prim)

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
    add_to_materials(prim.materials)

grit_numbers = [0]
def get_grit_number(repeat = False):
    if repeat: return str(grit_numbers[0] - 1)
    num = grit_numbers.pop(0)
    nex = num + 1
    grit_numbers.append(nex)
    return str(num)

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
    
    #'grass2' : ('animgtex', 'grass.dds'), 
    'road' : ('animgtex', 'road.png'), 
    
    'roof' : ('animgtex', 'rubber.png'), 
    #material "Road" {vertexDiffuse=true, diffuseMap="textures/road.dds", normalMap="textures/road_N.dds", glossMap="textures/road_S.tga"  }
        }
def read_material_name(matline):
    if matline.startswith('material'):
        st = matline.find('`') + 1
        matline = matline.replace('`','@',1)
        en = matline.find('`')
        matname = matline[st:en]
        return matname

matlines = []
used_mats = {}
def add_to_materials(mats):
    global matlines
    texfiles = []
    for ma in mats:
        if ma in materials.keys(): texfiles.append(ma)
        else:
            texfiles.append(None)
            #print('material is assumed already present',ma)

    #texfiles = ['.'.join([ma,'png']) for ma in mats]
    #with open(matfile, 'r') as handle:
    #    matlines = handle.readlines()
    #used_mats = [read_material_name(li) for li in matlines]
    #used_mats = [um for um in used_mats if not um is None]
    for tf, ma in zip(texfiles, mats):
        if tf is None: continue
        if not ma in used_mats.keys():
            margs = (ma,tf,)
            newmatlines = write_material(*margs)
            matlines += newmatlines
            used_mats[ma] = newmatlines
    #with open(matfile, 'w') as handle:
    #    [handle.write(li) for li in matlines]

def output_mats():
    matfile = os.path.join(world_dir, 'materials.lua')
    with open(matfile, 'w') as handle:
        handle.write(''.join(matlines))

def write_material(matname, textfile):
    #lines = ['\nmaterial "' + matname + '" {diffuseMap = "' + textdir + '/' + textfile + '"}\n']
    lines = ['\nmaterial `' + matname + '` {diffuseMap = `' + textfile + '`}\n']
    return lines

classlines = []
used_classes = {}
def add_to_classes(clname,gmesh,cmesh,rd,
        is_lod = False,has_lod = False):
    global classlines
    if clname in used_classes.keys() and not is_lod:
        #clname += get_grit_number()
        print('clname should be made unique:', clname)
    clargs = (clname,gmesh,cmesh,rd,has_lod)
    if is_lod: newclasslines = write_lod_class(*clargs)
    else: newclasslines = write_class(*clargs)
    classlines += newclasslines
    used_classes[clname] = newclasslines
    #else: print 'clname in used classes already:', clname

def output_classes():
    classfile = os.path.join(world_dir, 'classes.lua')
    with open(classfile, 'w') as handle:
        handle.write(''.join(classlines))

def write_class(clname, gmesh, cmesh, rd, lod):
    lod = 'true' if lod else 'false'
    lines = [
        '\nclass `' + clname + '` (ColClass) {\n', 
        #'    gfxMesh = \'/solemn/world/' + gmesh + '\';\n'
        #'    colMesh = \'/solemn/world/' + cmesh + '\';\n'
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

def write_lod_class(clname, gmesh, cmesh, rd, lod):
    lodclname = 'lod_' + clname
    lines = [
        '\nclass `'+ lodclname + '` (BaseClass) {\n',
        #'    gfxMesh = \'/solemn/world/' + gmesh + '\';\n'
        '    gfxMesh = `' + gmesh + '`;\n'
        '    castShadows = false;\n', 
        '    renderingDistance = ' + str(rd) + ';\n',
        '}\n']
    return lines

maplines = []
def add_to_map(obj,loc,rot,name):
    global maplines
    mapargs = (obj,loc,rot,name,)
    newmaplines = write_map_lines(*mapargs)
    maplines += newmaplines

def output_map():
    mapfile = os.path.join(world_dir, 'map.lua')
    with open(mapfile, 'w') as handle:
        handle.write(''.join(maplines))

def write_map_lines(obj, location, rotation, name):
    zang = rotation[2]
    quat = (cos(zang/2.0),0,0,sin(zang/2.0))
    lines = ['\nobject `' + obj + '` ' + location.__repr__() + ' { rot=quat' + quat.__repr__() + ', name="' + name + '" }\n']
    return lines

def create_grit_meshes():
    gdir = os.path.join(world_dir, 'convert.sh')
    subprocess.call([gdir, world_dir], shell = True)
    #subprocess.call('./convert.sh', shell = True)

executable_suffix = '.exe'
executable_suffix = ''
converterpath = 'OgreXMLConverter'
def create_grit_mesh(prim, tangents = False, 
            use_ogre_xml_converter = True):
    xml, is_new = prim.write_as_xml()
    if is_new:
        xdir = os.path.join(world_dir, prim.xml_filename)
        with open(xdir,'w') as handle:
            [handle.write(li) for li in xml]
        if use_ogre_xml_converter:
            args = [converterpath, "-e"]
            args.append("-q")
            if tangents:
                args.append("-t")
                args.append("-ts")
                args.append("4")
            args.append(xdir)
            p_op = subprocess.Popen(args, bufsize = 4096)
            #p_op.wait()
            #subprocess.call(args)
    return is_new

def create_gcol(prim):
    lindamp = 1.0
    angdamp = 1.0
    linsleepthresh = 1.0
    angsleepthresh = 1.0
    faces = prim.get_vertexes_faces_phys()

    filename = os.path.join(world_dir, prim.gcol_filename)
    with open(filename,'w') as handle:
        handle.write('TCOL1.0\n\n')
        handle.write('attributes {\n')
        handle.write('\tstatic;\n')
        handle.write('\tlinear_damping ' + str(lindamp) + ';\n')
        handle.write('\tangular_damping ' + str(angdamp) + ';\n')
        handle.write('\tlinear_sleep_threshold ' + str(linsleepthresh) + ';\n')
        handle.write('\tangular_sleep_threshold ' + str(angsleepthresh) + ';\n')
        handle.write('}\n\n')
        handle.write('compound {\n')
        handle.write('}\n')

        handle.write('trimesh {\n')
        handle.write('\tvertexes {\n')
        coords = prim.coords
        for vdx in range(len(coords)):
            p = coords[vdx]
            x,y,z = p.x,p.y,p.z
            handle.write('\t\t' + ' '.join([str(x),str(y),str(z)]) + ';\n')
        handle.write('\t}\n')
        handle.write('\tfaces {\n')
        for m in faces.keys():
            for f in faces[m]:
                handle.write('\t\t'+\
                    ' '.join([str(f[0]),str(f[1]),str(f[2])])+\
                    ' \"'+m+'\";\n')
        handle.write('\t}\n}\n')

    '''#
    lindamp = 1.0
    angdamp = 1.0
    linsleepthresh = 1.0
    angsleepthresh = 1.0
    glines = [
        'TCOL1.0\n\n', 
        'attributes {\n', 
        '\tstatic;\n', 
        '\tlinear_damping ' + str(lindamp) + ';\n', 
        '\tangular_damping ' + str(angdamp) + ';\n', 
        '\tlinear_sleep_threshold ' + str(linsleepthresh) + ';\n', 
        '\tangular_sleep_threshold ' + str(angsleepthresh) + ';\n', 
        '}\n\n', 
        'compound {\n', 
            ]
    # handle children if necessary
    glines.append('}\n')
    faces = prim.get_vertexes_faces_phys()
    #(vertexes, faces) = prim.get_vertexes_faces_phys()
    glines += 'trimesh {\n'
    glines += '\tvertexes {\n'
    #for v in vertexes:
    coords = prim.coords
    for vdx in range(len(coords)):
        p = coords[vdx]
        x,y,z = p.x,p.y,p.z
        #x = v.position.x
        #y = v.position.y
        #z = v.position.z
        #' '.join([str(v.pos[0]),str(v.pos[1]),str(v.pos[2])])+\
        glines += '\t\t' + ' '.join([str(x),str(y),str(z)]) + ';\n'
    glines += '\t}\n'
    glines += '\tfaces {\n'
    for m in faces.keys():
        for f in faces[m]:
            glines += '\t\t'+\
                ' '.join([str(f[0]),str(f[1]),str(f[2])])+\
                ' \"'+m+'\";\n'
    glines += '\t}\n}\n'

    gfile = os.path.join(world_dir,filename)
    with open(gfile,'w') as handle:
        [handle.write(gli) for gli in glines]
    '''#

def reset_world_scripts():
    global classlines, used_classes, maplines, used_mats, matlines
    used_classes = {}
    used_mats = {}

    world_start = [
        #'\ninclude "materials_constant.lua"\n', 
        #'include "materials.lua"\n', 
        #'include "classes.lua"\n\n']
        '\ninclude `materials_constant.lua`\n', 
        'include `materials.lua`\n', 
        'include `classes.lua`\n\n']
    maplines = world_start

    mapfile = os.path.join(world_dir, 'map.lua')
    with open(mapfile, 'w') as handle:
        [handle.write(li) for li in world_start]

    class_start = ['\n', '\n']
    classlines = class_start
    classfile = os.path.join(world_dir, 'classes.lua')
    with open(classfile, 'w') as handle:
        [handle.write(li) for li in class_start]

    matfile = os.path.join(world_dir, 'materials.lua')
    mats_start = ['\n']
    with open(matfile, 'r') as handle:
        for li in handle.readlines():
            if not li.strip == '':
                newmat = read_material_name(li)
                if not newmat in used_mats.keys():
                    used_mats[newmat] = li.replace('\n','')
                    mats_start.append(li)
    mats_start.append('\n')
    matlines = mats_start
    with open(matfile, 'w') as handle:
        [handle.write(li) for li in mats_start]

def output_world_scripts():
    output_classes()
    output_map()
    output_mats()
    #create_grit_meshes()

def create_element(*args):
    for ag in args:
        if not type(ag) is type([]): create_elem(ag)
        else: [create_elem(e) for e in ag]

def create_elem(elem, center = True):
    import make_places.scenegraph as sg
    sgr = sg.sgraph(nodes = [elem])
    sgr.make_scene_g(center = center)
    #print 'creating node\n', elem








