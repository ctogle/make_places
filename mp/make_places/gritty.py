




import pdb, os, subprocess

'''#
create_primitive should make an xml mesh, write the class def, 
add the necessary materials, and place the object in the world

unmodified meshes can be placed in a dict and recycled
'''#

def create_primitive(*args):
    for ag in args:
        if not type(ag) is type([]): create_prim(ag)
        else: [create_prim(p) for p in ag]
    
world_dir = os.path.join(
    'C:\\', 'Users', 'bartl_000', 
    'Desktop', 'gritengine', 'grit_core', 
    'media', 'solemn', 'world')
#textdir = os.path.join(
#    'C:\\', 'Users', 'bartl_000', 
#    'Desktop', 'gritengine', 'grit_core', 
#    'media', 'solemn', 'textures')
textdir = '/solemn/textures'
def create_prim(prim):
    prim.origin_to_centroid()
    create_grit_mesh(prim)
    create_gcol(prim)
    oname = prim.tag + get_grit_number()
    mname = prim.gfxmesh_name
    cname = prim.colmesh_name
    add_to_classes(oname, mname, cname)
    add_to_map(oname, tuple(prim.position), oname)
    add_to_materials(prim.materials)

grit_numbers = [0]
def get_grit_number():
    num = grit_numbers.pop(0)
    nex = num + 1
    grit_numbers.append(nex)
    return str(num)

materials = {
    'cubemat' : ('animgtex', 'cubetex.png'), 
    'octagonmat' : ('animgtex', 'octagontex.png'), 
        }
def read_material_name(matline):
    if matline.startswith('material'):
        st = matline.find('"') + 1
        matline = matline.replace('"','@',1)
        en = matline.find('"')
        matname = matline[st:en]
        return matname

def add_to_materials(mats):
    matfile = os.path.join(world_dir, 'materials.lua')
    #texfiles = ['.'.join([ma,'png']) for ma in mats]
    texfiles = [materials[ma][1] for ma in mats]
    with open(matfile, 'r') as handle:
        matlines = handle.readlines()
    used_mats = [read_material_name(li) for li in matlines]
    used_mats = [um for um in used_mats if not um is None]
    for tf, ma in zip(texfiles, mats):
        if not ma in used_mats:
            margs = (ma,tf,)
            newmatlines = write_material(*margs)
            matlines += newmatlines
    with open(matfile, 'w') as handle:
        [handle.write(li) for li in matlines]

def write_material(matname, textfile):
    lines = ['\nmaterial "' + matname + '" {diffuseMap = "' + textdir + '/' + textfile + '"}\n']
    return lines

def read_class_name(cline):
    if cline.startswith('class'):
        st = cline.find('"') + 1
        cline = cline.replace('"','@',1)
        en = cline.find('"')
        cname = cline[st:en]
        return cname

def add_to_classes(clname,gmesh,cmesh):
    classfile = os.path.join(world_dir, 'classes.lua')
    with open(classfile, 'r') as handle:
        classlines = handle.readlines()
    used_classes = [read_class_name(li) for li in classlines]
    used_classes = [cl for cl in used_classes if not cl is None]
    if not clname in used_classes:
        clargs = (clname,gmesh,cmesh,)
        newclasslines = write_class(*clargs)
        classlines += newclasslines
    with open(classfile, 'w') as handle:
        [handle.write(li) for li in classlines]

def write_class(clname, gmesh, cmesh):
    rd = 1000.0
    lines = [
        '\nclass "' + clname + '" (ColClass) {\n', 
        '    gfxMesh = \'/solemn/world/' + gmesh + '\';\n'
        '    colMesh = \'/solemn/world/' + cmesh + '\';\n'
        '    renderingDistance = '+str(rd)+';\n', 
        '    castShadows = true;\n',  
        '    receiveShadows = true;\n',  
        '    placementZOffset = false;\n',  
        '    placementRandomRotation = false;\n', 
        '}\n']
    return lines

def add_to_map(obj,loc,name):
    mapfile = os.path.join(world_dir, 'map.lua')
    with open(mapfile, 'r') as handle:
        maplines = handle.readlines()
    mapargs = (obj,loc,name,)
    newmaplines = write_map_lines(*mapargs)
    maplines += newmaplines
    with open(mapfile, 'w') as handle:
        [handle.write(li) for li in maplines]

def write_map_lines(obj, location, name):
    lines = ['\nobject "' + obj + '" ' + location.__repr__() + ' { rot=quat(1.0, 0.0, 0.0, 0.0), name="' + name + '" }\n']
    return lines

executable_suffix = '.exe'
def create_grit_mesh(prim, tangents = False, 
            use_ogre_xml_converter = True):
    xml = prim.write_as_xml()
    xdir = os.path.join(world_dir, prim.xml_filename)
    with open(xdir,'w') as handle:
        [handle.write(li) for li in xml]
    if use_ogre_xml_converter:
        converterpath = os.path.join(world_dir, 
            'OgreXMLConverter' + executable_suffix)
        args = [converterpath, "-e"]
        if tangents:
            args.append("-t")
            args.append("-ts")
            args.append("4")
        args.append(xdir)
        subprocess.call(args)

def create_gcol(prim):
    filename = os.path.join(world_dir, prim.gcol_filename)
    #for c in obj.children:
    #    if c.type == 'EMPTY':
    #        print(
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
    (vertexes, faces) = prim.get_vertexes_faces_phys()
    glines += 'trimesh {\n'
    glines += '\tvertexes {\n'
    for v in vertexes:
        glines += '\t\t'+\
            ' '.join([str(v.pos[0]),str(v.pos[1]),str(v.pos[2])])+\
            ';\n'
    glines += '\t}\n'
    glines += '\tfaces {\n'
    for m in faces.keys():
        for f in faces[m]:
            glines += '\t\t'+\
                ' '.join([str(f[0]),str(f[1]),str(f[2])])+\
                ' \"'+m+'\";\n'
    glines += '\t}\n'
    glines += '}\n'

    #glines += children_lines
    gfile = os.path.join(world_dir,filename)
    with open(gfile,'w') as handle:
        [handle.write(gli) for gli in glines]

def create_element(*args):
    for ag in args:
        if not type(ag) is type([]): create_elem(ag)
        else: [create_elem(e) for e in ag]

def create_elem(elem):
    eelems = elem.children
    eprims = elem.primitives
    pos = elem.position
    scl = elem.scales
    rot = elem.rotation
    for ee in eelems:
        ee.scale(scl)
        ee.rotate_z(rot)
        ee.translate(pos)
        create_elem(ee)
    for ep in eprims:
        ep.scale(scl)
        ep.rotate_z(rot[2])
        ep.translate(pos)
        create_prim(ep)








