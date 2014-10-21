




'''#
create_primitive should make an xml mesh, write the class def, 
add the necessary materials, and place the object in the world

unmodified meshes can be placed in a dict and recycled
'''#

def create_primitive(*args):
    for ag in args:
        if not type(ag) is type([]): create_prim(ag)
        else: [create_prim(p) for p in ag]
    
world_dir = ''
def create_prim(prim):
    xml = prim.write_as_xml()
    xdir = os.path.join(world_dir, prim.xml_filename)
    with open(xdir,'w') as handle:
        [handle.write(li) for li in xml]

    pdb.set_trace()

    return
    oname = prim.tag + '.000'
    mname = '.'.join([oname, 'mesh'])
    coords = prim.coords
    uvs = prim.uv_coords
    faces = prim.faces
    face_mats = prim.face_materials
    mats = prim.materials

    #mesh = mesh_from_data(mname, coords, uvs, faces, face_mats, mats)
    #obj = object_from_mesh(oname, mesh, mats)
    object_to_scene(obj)

def create_gcol(filename):
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
    #    'compound {\n', 
            ]

    (vertexes, faces) = get_vertexes_faces(scene, mesh, True, "/common/Stone", obj.scale)

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
                '\"'+m+'\";\n'
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








