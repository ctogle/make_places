import make_places.fundamental as fu

import xml.etree.ElementTree

import os


           
mpdir = os.path.join('/home', 'cogle', 
        'dev', 'forblender', 'make_places')
xml_primitive_files = {}

class arbitrary_primitive(object):

    def __init__(self, *args, **kwargs):
        self.xml_filename = kwargs['xmlfilename']
        self.position = kwargs['position']
        self.coords = kwargs['verts']
        self.ncoords = kwargs['nverts']
        self.uv_coords = kwargs['uvs']
        self.faces = kwargs['faces']
        self.materials = kwargs['materials']
        self.face_materials = kwargs['face_materials']
        self.tag = '_arb_'
        self.modified = False

    def find_centroid(self):
        com = fu.center_of_mass(self.coords)   
        return com

    def origin_to_centroid(self):
        centroid = self.find_centroid()
        self.reset_position(centroid)

    def reset_position(self, pos):
        self.position = pos
        self.translate(fu.flip(pos))

    def write_as_xml(self):
        xml = os.path.join(mpdir, 
            'primitive_data', self.xml_filename)
        with open(xml, 'r') as handle:
            xlines = handle.readlines()
        return xlines

    def translate(self, vect):
        self.coords = fu.translate_coords(self.coords, vect)
        self.modified = True

    def scale(self, vect):
        self.coords = fu.scale_coords(self.coords, vect)
        self.modified = True

    def rotate_z(self, ang_z):
        self.coords = fu.rotate_z_coords(self.coords, ang_z)
        self.modified = True

def primitive_data_from_xml(xmlfile):
    tree = xml.etree.ElementTree.parse(xmlfile)
    root = tree.getroot()
    sharedgeometry = root.find('sharedgeometry')
    if sharedgeometry == None: print('NEED SHARED GEOMETRY!')
    verts = []
    nverts = []
    uvs = []
    for vbuff in sharedgeometry.iterfind('vertexbuffer'):
        for vt in vbuff.iterfind('vertex'):
            x = float(vt.find('position').get('x'))
            y = float(vt.find('position').get('y'))
            z = float(vt.find('position').get('z'))
            verts.append([x,y,z])
            nx = float(vt.find('normal').get('x'))
            ny = float(vt.find('normal').get('y'))
            nz = float(vt.find('normal').get('z'))
            nverts.append([nx,ny,nz])
            u = float(vt.find('texcoord').get('u'))
            v = float(vt.find('texcoord').get('v'))
            uvs.append([u,1-v])
    submeshes = root.find('submeshes')
    if submeshes == None: print('NEED SUBMESHES!')
    faces = []
    materials = []
    face_materials = []
    for submesh in submeshes.iterfind('submesh'):
        mat = submesh.get('material')
        materials.append(mat)
        for xfaces in submesh.iterfind('faces'):
            for face in xfaces.iterfind('face'):
                v1 = int(face.get('v1'))
                v2 = int(face.get('v2'))
                v3 = int(face.get('v3'))
                faces.append([v1,v2,v3])
                face_materials.append(len(materials)-1)
    org = (0,0,0)
    pwargs = {
        'position' : org, 
        'verts' : verts, 
        'nverts' : nverts, 
        'uvs' : uvs, 
        'faces' : faces, 
        'materials' : materials, 
        'face_materials' : face_materials, 
        'xmlfilename' : xmlfile, 
            }
    #prim = arbitrary_primitive(verts = verts, nverts = nverts, 
    #        uvs = uvs, faces = faces, materials = materials, 
    #        face_materials = face_materials)
    return pwargs

def primitive_from_xml(xmlfile):
    pwargs = primitive_data_from_xml(xmlfile)
    return arbitrary_primitive(**pwargs)

class unit_cube(arbitrary_primitive):
    cubexml = os.path.join('/home', 'cogle', 
        'dev', 'forblender', 'make_places',
        'primitive_data', 'cube.mesh.xml')

    def __init__(self, *args, **kwargs):
        pcubedata = primitive_data_from_xml(self.cubexml)
        arbitrary_primitive.__init__(self, *args, **pcubedata)
        self.coords_by_face = self.find_faces()
        self.tag = '_cube_'

    def find_faces(self):
        fronts = [v for v in self.coords if v[1] < 0.0]
        backs = [v for v in self.coords if v[1] > 0.0]
        lefts = [v for v in self.coords if v[0] < 0.0]
        rights = [v for v in self.coords if v[0] > 0.0]
        bottoms = [v for v in self.coords if v[2] <= 0.0]
        tops = [v for v in self.coords if v[2] > 0.0]
        facedict = {
            'front':fronts, 
            'back':backs, 
            'left':lefts,                                        
            'right':rights, 
            'top':tops, 
            'bottom':bottoms, 
                }
        return facedict

    def translate_face(self, vect, face = 'top'):
        cfaces = self.coords_by_face
        face_coords = cfaces[face]
        fu.translate_coords(face_coords, vect)
        self.modified = True

    def rotate_z_face(self, ang_z, face = 'top'):
        cfaces = self.coords_by_face
        face_coords = cfaces[face]
        foff = fu.center_of_mass(face_coords)
        fu.translate_coords(face_coords, fu.flip(foff))
        fu.rotate_z_coords(face_coords, ang_z)
        fu.translate_coords(face_coords, foff)
        self.modified = True

def ucube():
    pcube = unit_cube()
    return pcube

def uoctagon():
    octaxml = os.path.join('/home', 'cogle', 
        'dev', 'forblender', 'make_places',
        'primitive_data', 'octagon.mesh.xml')
    poct = primitive_from_xml(octaxml)
    return poct






class primitive(object):

    def __init__(self, *args, **kwargs):
        self.model_coords = kwargs['model_coords']
        self.model_faces = kwargs['model_faces']
        try: self.texfaces = kwargs['texfaces']
        except KeyError: self.texfaces = []

    def translate(self, vect):
        self.model_coords = fu.translate_coords(self.model_coords, vect)

    def scale(self, vect):
        self.model_coords = fu.scale_coords(self.model_coords, vect)

    def rotate_z(self, ang_z):
        self.model_coords = fu.rotate_z_coords(self.model_coords, ang_z)







class _____unit_cube(primitive):
    def __init__(self):
        coords = [
            [0.0, 0.0, 0.0], 
            [1.0, 0.0, 0.0], 
            [1.0, 1.0, 0.0], 
            [0.0, 1.0, 0.0], 
            [0.0, 0.0, 1.0], 
            [1.0, 0.0, 1.0], 
            [1.0, 1.0, 1.0], 
            [0.0, 1.0, 1.0], 
                ]
        faces = [
            [0,3,2,1], [3,0,4,7], 
            [0,1,5,4], [1,2,6,5], 
            [2,3,7,6], [4,5,6,7], 
                ]                                      
        bottom = [[0.25,0.0], [0.5,0.0], [0.5,0.33], [0.25,0.33]]
        left = [[0.0,0.33], [0.25,0.33], [0.25,0.66], [0.0,0.66]]
        front = [[0.25,0.33], [0.5,0.33], [0.5,0.66], [0.25,0.66]]
        right = [[0.5,0.33], [0.75,0.33], [0.75,0.66], [0.5,0.66]]
        back = [[0.75,0.33], [1.0,0.33], [1.0,0.66], [0.75,0.66]]
        top = [[0.25,0.66], [0.5,0.66], [0.5,1.0], [0.25,1.0]]
        texfaces = [bottom, left, front, right, back, top]
        self.bottom = faces[0]
        self.top = faces[5]
        self.front = faces[2]
        self.back = faces[4]
        self.left = faces[1]
        self.right = faces[3]
        primitive.__init__(self, model_coords = coords, 
            model_faces = faces, texfaces = texfaces)

    def translate_face(self, vect,  face = 'top'):
        co = self.model_coords
        face_coords = [co[dx] for dx in self.__dict__[face]]
        fu.translate_coords(face_coords, vect)






