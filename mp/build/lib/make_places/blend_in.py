import make_places.fundamental as fu

import os

try:
    import bpy
    from bpy_extras.io_utils import unpack_list
    from bpy_extras.io_utils import unpack_face_list
except ImportError:
    print('bpy is not available!')
    bpy = None
    unpack_list = None
    unpack_face_list = None





def object_to_scene(obj, make_active = True):
    bpy.context.scene.objects.link(obj)
    if make_active: bpy.context.scene.objects.active = obj

def object_from_mesh(name, mesh, obj_loc = (0,0,0), mats = None):
    obj = bpy.data.objects.new(name, mesh)
    obj.location = obj_loc
    if not mats is None:
        mats = [materials[mat] for mat in mats]
        [obj.data.materials.append(ma) for ma in mats]
    return obj

def mesh_from_data(name, coords, uvs, faces, face_mats, mats):
    mesh = bpy.data.meshes.new(name)
    if not mats is None:
        [mesh.materials.append(materials[ma]) for ma in mats]

    mesh.vertices.add(len(coords))
    mesh.vertices.foreach_set('co', unpack_list(coords))

    mesh.tessfaces.add(len(faces))
    mesh.tessfaces.foreach_set('vertices_raw', unpack_face_list(faces))
    mesh.tessfaces.foreach_set('material_index', face_mats)

    mesh.tessface_uv_textures.new()
    for fdx in range(len(faces)):
        fa = faces[fdx]
        mesh.tessface_uv_textures[0].data[fdx].uv1 = uvs[fa[0]]
        mesh.tessface_uv_textures[0].data[fdx].uv2 = uvs[fa[1]]
        mesh.tessface_uv_textures[0].data[fdx].uv3 = uvs[fa[2]]

    mesh.update()
    return mesh

def create_primitive(*args, **kwargs):
    for ag in args:
        if not type(ag) is type([]): create_prim(ag, **kwargs)
        else: [create_prim(p, **kwargs) for p in ag]
    
def create_prim(prim, center = False, **kwargs):
    oname = prim.tag + '.000'
    mname = '.'.join([oname, 'mesh'])
    coords = prim.coords
    uvs = prim.uv_coords
    faces = prim.faces
    face_mats = prim.face_materials
    mats = prim.materials
    if center: prim.origin_to_centroid()
    loc = prim.position

    mesh = mesh_from_data(mname, coords, uvs, faces, face_mats, mats)
    obj = object_from_mesh(oname, mesh, loc, mats)
    object_to_scene(obj)

def create_element(*args, **kwargs):
    for ag in args:
        if not type(ag) is type([]): create_elem(ag,**kwargs)
        else: [create_elem(e,**kwargs) for e in ag]

def create_elem(elem, center = True):
    import make_places.scenegraph as sg
    sgr = sg.sgraph(nodes = [elem])
    sgr.make_scene_b(center = center)


    return
    eelems = elem.children
    eprims = elem.primitives
    pos = elem.position
    scl = elem.scales
    rot = elem.rotation
    for ee in eelems:
        ee.scale(scl)
        ee.rotate_z(rot[2])
        ee.translate(pos)
        create_elem(ee)
    for ep in eprims:
        ep.scale(scl)
        ep.rotate_z(rot[2])
        ep.translate(pos)
        create_prim(ep, center)

texture_directory = os.path.join(
    '/home', 'cogle', 'dev', 'forblender',
    'make_places', 'mp', 'make_places', 'textures')
def create_material_image(name, texture):
    mat = bpy.data.materials.new(name)
    imgpath = os.path.join(texture_directory,texture)
    tex = bpy.data.textures.new(name, type = 'IMAGE')
    tex.image = bpy.data.images.load(imgpath)
    tex.use_alpha = True

    mat.use_shadeless = True
    mtex = mat.texture_slots.add()
    mtex.texture = tex
    mtex.texture_coords = 'UV'
    mtex.use_map_color_diffuse = True
    return mat

def create_material_solid(name, diffuse, specular, alpha):
    mat = bpy.data.materials.new(name)

    mat.diffuse_color = diffuse
    mat.diffuse_shader = 'LAMBERT'
    mat.diffuse_intensity = 1.0
    mat.specular_color = specular
    mat.specular_shader = 'COOKTORR'
    mat.specular_intensity = 0.5
    mat.alpha = alpha
    mat.ambient = 1
    return mat

if bpy:
    materials = {
        #'acolor' : create_material_solid('amat', (0.5, 0.5, 0.0), (0.5,0.5,0), 1.0), 
        #'imgtex' : create_material_image('animgtex', 'cubetexture.png'), 
        'cubemat' : create_material_image('animgtex', 'cubetex.png'), 
        'octagonmat' : create_material_image('animgtex', 'octagontex.png'), 
            }
else:
    materials = {
        #'acolor' : create_material_solid('amat', (0.5, 0.5, 0.0), (0.5,0.5,0), 1.0), 
        #'imgtex' : create_material_image('animgtex', 'cubetexture.png'), 
        'cubemat' : ('animgtex', 'cubetex.png'), 
        'octagonmat' : ('animgtex', 'octagontex.png'), 
            }

def flatten(unflat):
    flat = [item for sublist in unflat for item in sublist]
    return flat

def create_texture_layer(name, mesh, texfaces):
    uvtex = mesh.uv_textures.new()
    uvtex.name = name
    texfaces = flatten(texfaces)
    for f in mesh.polygons:
        for i in f.loop_indices:
            tf = texfaces[i]
            l = mesh.loops[i]
            uvl = mesh.uv_layers[0]
            uvl.data[l.index].uv.x = tf[0]
            uvl.data[l.index].uv.y = tf[1]
    return uvtex

def create_object(name, coords, faces, 
        texfaces = None, mats = None):
    mesh = bpy.data.meshes.new(name)
    obj = bpy.data.objects.new(name, mesh)
    if not mats is None:
        mats = [materials[mat] for mat in mats]
        [obj.data.materials.append(ma) for ma in mats]
    bpy.context.scene.objects.link(obj)
    bpy.context.scene.objects.active = obj
    mesh.from_pydata(coords,[],faces)
    mesh.update(calc_edges = True)
    if not texfaces is None:
        uv_main = create_texture_layer('uvmain', mesh, texfaces)
    else:
        bpy.ops.mesh.uv_texture_add()
        uvs = mesh.uv_textures.active
        uvs.name = 'uvmain'
        bpy.ops.object.mode_set(mode = 'EDIT')
        bpy.ops.uv.cube_project()
        bpy.ops.object.mode_set(mode = 'OBJECT')

    mesh.uv_textures['uvmain'].active = True
    mesh.uv_textures['uvmain'].active_render = True

def blend_in_geometry(names, coords, faces, texfaces, mats, coo_cnt):
    for stdx in range(coo_cnt):
        stcoords = coords[stdx]
        stfaces = faces[stdx]
        sttexfaces = texfaces[stdx]
        stmats = mats[stdx]
        stname = names[stdx]
        create_object(stname, stcoords, stfaces, 
            texfaces = sttexfaces, mats = stmats)






