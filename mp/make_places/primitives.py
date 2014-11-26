import make_places.fundamental as fu
import mp_utils as mpu
from make_places.fundamental import base
import make_places.profiler as prf
import make_places.user_info as ui

import xml.etree.ElementTree

import os, pdb, shutil
import numpy as np
from numpy import linalg
from numpy import matrix
from math import sin
from copy import deepcopy as dcopy
from copy import copy


primitive_data_path = ui.info['primitivedir']
xml_library = {}

def load_xml_library():
    wdir = ui.info['worlddir']
    tdir = ui.info['texturedir']
    if not os.path.isdir(wdir):shutil.copytree(ui.info['newworlddir'],wdir)
    if not os.path.isdir(tdir):shutil.copytree(ui.info['newtexturedir'],tdir)

    for xfi in os.listdir(wdir):
        if not xfi.endswith('.xml'): continue
        else:
            xpa = os.path.join(wdir,xfi)
            with open(xpa, 'r') as handle:
                xlines = handle.readlines()
            xml_rep = '\n'.join(xlines)
            gcol = xfi.replace('mesh.xml','gcol')
            gfx = xfi.replace('.xml','')
            col = gcol
            xml_library[xml_rep] = (xfi,gcol,gfx,col)
prf.measure_time('load xml library', load_xml_library)

class arbitrary_primitive(base):

    _scale_uvs_ = False
    def __init__(self, *args, **kwargs):
        self.xml_filename = kwargs['xmlfilename']
        self.gcol_filename = self.xml_filename.replace('mesh.xml','gcol')
        self.gfxmesh_name = self.xml_filename.replace('.xml','')
        self.colmesh_name = self.gcol_filename
        
        self._default_('is_lod',False,**kwargs)
        self._default_('has_lod',False,**kwargs)
        
        self._default_('force_normal_calc',False,**kwargs)

        self.position = kwargs['position']
        self.coords = kwargs['verts']
        self.ncoords = kwargs['nverts']
        self.uv_coords = kwargs['uvs']
        self.faces = kwargs['faces']

        fcnt = len(self.faces)
        zero = [0]*fcnt
        self._default_('materials',['cubemat'],**kwargs)
        self._default_('phys_materials',['/common/pmat/Stone'],**kwargs)
        self._default_('phys_face_materials',zero,**kwargs)
        self._default_('face_materials',zero[:],**kwargs)
        #self.face_materials = kwargs['face_materials']

        self._default_('tag','_arb_',**kwargs)
        self.modified = False

    def __add__(self, other):
        other_offset = len(self.coords)
        org = [0,0,0]
        verts = self.coords + other.coords
        nverts = self.ncoords + other.ncoords
        uvs = self.uv_coords + other.uv_coords
        mpu.offset_faces(other.faces, other_offset)
        faces = self.faces + other.faces

        ofmats = other.face_materials
        ofacnt = len(ofmats)
        for dx in range(len(other.materials)):
            omat = other.materials[dx]
            if not omat in self.materials:
                self.materials.append(omat)
                mdx = len(self.materials) - 1
                for fdx in range(ofacnt):
                    if ofmats[fdx] == dx:
                        ofmats[fdx] = mdx
            else:
                mdx = self.materials.index(omat)
                if not mdx == dx:
                    for fdx in range(ofacnt):
                        if ofmats[fdx] == dx:
                            ofmats[fdx] = mdx

        materials = self.materials[:]
        face_materials = self.face_materials + other.face_materials
        xmlfile = self.xml_filename
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
        new = arbitrary_primitive(**pwargs)
        new.modified = True
        new.has_lod = self.has_lod
        return new

    def requires_32bit_indices(self):
        vcnt = len(self.coords)
        _32bitindices = True if vcnt > 65000 else False
        _32bitindices = 'true' if _32bitindices else 'false'
        return _32bitindices

    def has_normals(self):
        has = 'true' if self.ncoords else 'false'
        return has

    def calculate_normals(self,anyway = False):
        if self.has_normals() == 'false' and not anyway: return
        # must iterate over faces, for each vertex, apply new normal
        for fa in self.faces:
            try:fcoords = [self.coords[f] for f in fa]
            except: pdb.set_trace()
            v1 = self.coords[fa[0]]
            v2 = self.coords[fa[1]]
            v3 = self.coords[fa[2]]
            v1v2 = mpu.v1_v2(v1,v2)
            v1v3 = mpu.v1_v2(v1,v3)
            normal = mpu.normalize(mpu.cross(v1v2,v1v3))
            #com = self.find_centroid()
            #comf = mpu.center_of_mass(fcoords)
            #if not fu.angle_between(fu.v1_v2(comf,com),normal)>fu.PI/2.0:
            #    normal = mpu.flip(normal)
            for vdx in fa: self.ncoords[vdx] = normal

    def get_vertexes(self):
        vargs = zip(self.coords,self.ncoords,self.uv_coords)
        vs = [fu.vertex(*va) for va in vargs]
        return vs

    def get_vertexes_faces_phys(self):
        vs = self.get_vertexes()
        mcnt = len(self.phys_materials)
        fcnt = len(self.face_materials)
        #self.phys_face_materials = [0]*fcnt
        fa = {}
        for mdx in range(mcnt):
            ma = self.phys_materials[mdx]
            fa[ma] = []
            for fmdx in range(fcnt):
                if self.phys_face_materials[fmdx] == mdx:
                    fa[ma].append(self.faces[fmdx])
        return (vs, fa)

    def get_vertexes_faces(self):
        vargs = zip(self.coords,self.ncoords,self.uv_coords)
        vs = [fu.vertex(*va) for va in vargs]
        mcnt = len(self.materials)
        fcnt = len(self.face_materials)
        fa = {}
        for mdx in range(mcnt):
            ma = self.materials[mdx]
            fa[ma] = []
            for fmdx in range(fcnt):
                if self.face_materials[fmdx] == mdx:
                    fa[ma].append(self.faces[fmdx])
            if not fa[ma]: del fa[ma]
        return (vs, fa)

    def find_centroid(self):
        com = mpu.center_of_mass(self.coords)   
        return com

    def origin_to_centroid(self):
        centroid = self.find_centroid()
        self.reset_position(centroid)

    def reset_position(self, pos):
        self.position = pos
        self.translate(mpu.flip(pos))

    def write_as_xml(self):
        if self.modified:
            self.calculate_normals(self.force_normal_calc)
            xlines, xfile = xml_from_primitive_data(self)
            self.xml_representation = '\n'.join(xlines)
        else:
            #xml = os.path.join(mpdir, 
            #    'primitive_data', self.xml_filename)
            xml = os.path.join(primitive_data_path,self.xml_filename)
            with open(xml, 'r') as handle:
                xlines = handle.readlines()
            self.xml_representation = '\n'.join(xlines)

        if self.xml_representation in xml_library.keys():
            xfile,gcol,gfx,col = xml_library[self.xml_representation]
            self.xml_filename = xfile
            self.gcol_filename = gcol
            self.gfxmesh_name = gfx
            self.colmesh_name = col
            is_new = False
            #print 'reusing an xml rep!', xfile

        else:
            #xlines, xfile = xml_from_primitive_data(self)
            self.xml_filename = xfile
            gcol = self.xml_filename.replace('mesh.xml','gcol')
            self.gcol_filename = gcol
            gfx = self.xml_filename.replace('.xml','')
            self.gfxmesh_name = gfx
            col = self.gcol_filename
            self.colmesh_name = col
            xml_library[self.xml_representation] = (xfile,gcol,gfx,col)
            is_new = True
            #print 'new xml rep!', xfile
        return xlines, is_new

    def translate(self, vect):
        mpu.translate_coords(self.coords, vect)
        #self.coords = mpu.translate_coords(self.coords, vect)
        self.modified = True

    def material_to_faces(self, mat, faces):
        if not mat in self.materials: self.materials.append(mat)
        mdx = self.materials.index(mat)
        for fdx in faces: self.face_materials[fdx] = mdx

    def assign_material(self, mat):
        faces = range(len(self.faces))
        self.material_to_faces(mat, faces)

    def scale_uvs(self, vect):
        x_hat = [1,0,0]
        y_hat = [0,1,0]
        z_hat = [0,0,1]
        hats = [x_hat,y_hat,z_hat]
        if vect == [1,1,1]: return
        for vdx in range(len(self.coords)):
            uv = self.uv_coords[vdx]
            no = self.ncoords[vdx]
            alpha = fu.angle_between(no, vect)
            fact = mpu.magnitude(vect)*sin(alpha)
            proj = mpu.cross(no,mpu.normalize(mpu.cross(vect,no)))
            mpu.scale_vector(proj,[fact,fact,fact])
            b1 = mpu.normalize(mpu.rotate_z_coords(
                [[no[0],no[1],0]], fu.PI/2.0)[0])
            if mpu.magnitude(b1) == 0: us,vs = vect[0],vect[1]
            else:
                b3 = mpu.normalize(no[:])
                b2 = mpu.normalize(mpu.cross(b3,b1))
                m = matrix([b1,b2,b3]).transpose()
                us,vs,ns = linalg.solve(m,proj)
                us,vs,ns = abs(us),abs(vs),abs(ns)
            uv[0] *= us
            uv[1] *= vs

    def worldly_uvs(self, uv_ttf):
        sx,sy,sz = uv_ttf.scales
        for uvc in self.uv_coords:
            uvc[0] /= sx
            uvc[1] /= sy

    def scale(self, vect):
        self.coords = mpu.scale_coords(self.coords, vect)
        if self._scale_uvs_: self.scale_uvs(vect)
        self.modified = True

    def rotate_z(self, ang_z):
        self.coords = mpu.rotate_z_coords(self.coords, ang_z)
        self.ncoords = mpu.rotate_z_coords(self.ncoords, ang_z)
        self.modified = True

xml_file_names = []
def make_xml_name_unique(xfile):
    xm = xfile[:xfile.rfind('mesh.xml')]
    xnum = len(xml_file_names) + 1
    xm += '.'.join([str(xnum),'mesh','xml'])
    return xm

def xml_from_primitive_data(prim):
    xfile = prim.xml_filename
    if xfile in xml_file_names:
        xfile = make_xml_name_unique(xfile)
    xml_file_names.append(xfile)
    xlines = []
    (vertexes, faces) = prim.get_vertexes_faces()# THIS NEEDS TO RETURN PROPER FACES DICT FOR MATERIALS TO WORK!!!
    _32bitindices = prim.requires_32bit_indices()
    _normals = prim.has_normals()
    sig = 4
    doround = False

    xlines.append("<mesh>\n")
    xlines.append("    <sharedgeometry>\n")
    xlines.append("        <vertexbuffer positions=\"true\" normals=\""+_normals+"\" colours_diffuse=\""+("false")+"\" texture_coord_dimensions_0=\"float2\" texture_coords=\"1\">\n")
    #xlines.append("        <vertexbuffer positions=\"true\" normals=\"true\" colours_diffuse=\""+("false")+"\" texture_coord_dimensions_0=\"float2\" texture_coords=\"1\">\n")
    for v in vertexes:
        x,y,z = v.pos
        nx,ny,nz = v.normal
        ux,uy = v.uv
        xlines.append("            <vertex>\n")
        if doround:
            xlines.append("                <position x=\""+str(np.round(v.pos[0],sig))+"\" y=\""+str(np.round(v.pos[1],sig))+"\" z=\""+str(np.round(v.pos[2],sig))+"\" />\n")
            if _normals == 'true':
                xlines.append("                <normal x=\""+str(np.round(v.normal[0],sig))+"\" y=\""+str(np.round(v.normal[1],sig))+"\" z=\""+str(np.round(v.normal[2],sig))+"\" />\n")
            xlines.append("                <texcoord u=\""+str(np.round(v.uv[0],sig))+"\" v=\""+str(np.round(1-v.uv[1],sig))+"\" />\n")
        else:
            xlines.append("                <position x=\""+str(x)+"\" y=\""+str(y)+"\" z=\""+str(z)+"\" />\n")
            if _normals == 'true':
                xlines.append("                <normal x=\""+str(nx)+"\" y=\""+str(ny)+"\" z=\""+str(nz)+"\" />\n")
            xlines.append("                <texcoord u=\""+str(ux)+"\" v=\""+str(1.0-uy)+"\" />\n")
        xlines.append("            </vertex>\n")
    xlines.append("        </vertexbuffer>\n")
    xlines.append("    </sharedgeometry>\n")

    xlines.append("    <submeshes>\n")
    for m in faces.keys():
        #xlines.append("        <submesh material=\""+m+"\" usesharedvertices=\"true\" use32bitindexes=\"false\" operationtype=\"triangle_list\">\n")
        xlines.append("        <submesh material=\""+m+"\" usesharedvertices=\"true\" use32bitindexes=\""+_32bitindices+"\" operationtype=\"triangle_list\">\n")
        xlines.append("            <faces>\n")
        for f in faces[m]:
            xlines.append("                <face v1=\""+str(f[0])+"\" v2=\""+str(f[1])+"\" v3=\""+str(f[2])+"\" />\n")
        xlines.append("            </faces>\n")
        xlines.append("        </submesh>\n")
    xlines.append("    </submeshes>\n")
    xlines.append("</mesh>\n")
    return xlines, xfile

def primitive_data_from_xml(xmlfile):
    tree = xml.etree.ElementTree.parse(xmlfile)
    root = tree.getroot()
    sharedgeometry = root.find('sharedgeometry')
    if sharedgeometry == None: print('NEED SHARED GEOMETRY!')
    verts = []
    nverts = []
    uvs = []
    sig = 4
    doround = False
    for vbuff in sharedgeometry.iterfind('vertexbuffer'):
        for vt in vbuff.iterfind('vertex'):
            if doround:
                x = np.round(float(vt.find('position').get('x')), sig)
                y = np.round(float(vt.find('position').get('y')), sig)
                z = np.round(float(vt.find('position').get('z')), sig)
                verts.append([x,y,z])
                nx = np.round(float(vt.find('normal').get('x')), sig)
                ny = np.round(float(vt.find('normal').get('y')), sig)
                nz = np.round(float(vt.find('normal').get('z')), sig)
                nverts.append([nx,ny,nz])
                u = np.round(float(vt.find('texcoord').get('u')), sig)
                v = np.round(float(vt.find('texcoord').get('v')), sig)
                uvs.append([u,1-v])
            else:
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
    org = [0,0,0]
    sep = xmlfile.rfind(os.path.sep)
    xmlfile = xmlfile[sep+1:]
    xml_file_names.append(xmlfile)
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

cubexml = os.path.join(primitive_data_path, 'cube.mesh.xml')
cubedata = primitive_data_from_xml(cubexml)
class unit_cube(arbitrary_primitive):
    cubexml = os.path.join(primitive_data_path, 'cube.mesh.xml')

    def __init__(self, *args, **kwargs):
        pcubedata = dcopy(cubedata)
        #pcubedata = primitive_data_from_xml(self.cubexml)
        self._default_('tag','_cube_',**kwargs)
        arbitrary_primitive.__init__(self, *args, **pcubedata)
        self.coords_by_face = self.find_faces()
        self._scale_uvs_ = True

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

        def subset(super, sub):
            for su in sub:
                if not su in super:
                    return False
            return True

        def find_face_indices(side):
            found = []
            for fdx in range(fcnt):
                face = self.faces[fdx]
                relevcoords = [self.coords[f] for f in face]
                if subset(facedict[side],relevcoords):
                    found.append(fdx)
            return found

        fcnt = len(self.faces)
        fs = self.faces
        top_faces = find_face_indices('top')
        bottom_faces = find_face_indices('bottom')
        left_faces = find_face_indices('left')
        right_faces = find_face_indices('right')
        front_faces = find_face_indices('front')
        back_faces = find_face_indices('back')
        truefacedict = {
            'top':top_faces, 
            'bottom':bottom_faces, 
            'left':left_faces, 
            'right':right_faces, 
            'front':front_faces, 
            'back':back_faces, 
                }
        self.face_dict = truefacedict
        return facedict

    def remove_face(self, *args):# calling this more than once will ruin geometry
        fdxs = [self.face_dict[face] for face in args]
        fdxs = fu.flatten(fdxs)
        fdxs = sorted(fdxs)
        fdxs.reverse()
        for fx in fdxs:
            self.faces.pop(fx)
            self.face_materials.pop(fx)
            self.phys_face_materials.pop(fx)

    def translate_face(self, vect, face = 'top'):
        cfaces = self.coords_by_face
        face_coords = cfaces[face]
        mpu.translate_coords(face_coords, vect)
        self.calculate_normals()
        self.modified = True

    def rotate_z_face(self, ang_z, face = 'top'):
        cfaces = self.coords_by_face
        face_coords = cfaces[face]
        foff = mpu.center_of_mass(face_coords)
        mpu.translate_coords(face_coords, mpu.flip(foff))
        mpu.rotate_z_coords(face_coords, ang_z)
        mpu.translate_coords(face_coords, foff)
        self.calculate_normals()
        self.modified = True

#cubexml = os.path.join(primitive_data_path, 'cube.mesh.xml')
octaxml = os.path.join(primitive_data_path, 'octagon.mesh.xml')
#cubedata = primitive_data_from_xml(cubexml)
class unit_octagon(arbitrary_primitive):
    #cubexml = os.path.join(primitive_data_path, 'cube.mesh.xml')
    octaxml = os.path.join(primitive_data_path, 'octagon.mesh.xml')

    def __init__(self, *args, **kwargs):
        #pcubedata = dcopy(cubedata)
        poctadata = primitive_data_from_xml(self.octaxml)
        self._default_('tag','_octagon_',**kwargs)
        arbitrary_primitive.__init__(self, *args, **poctadata)
        self.coords_by_face = self.find_faces()
        self._scale_uvs_ = True

    def find_faces(self):
        #fronts = [v for v in self.coords if v[1] < 0.0]
        #backs = [v for v in self.coords if v[1] > 0.0]
        #lefts = [v for v in self.coords if v[0] < 0.0]
        #rights = [v for v in self.coords if v[0] > 0.0]
        bottoms = [v for v in self.coords if v[2] <= 0.0]
        tops = [v for v in self.coords if v[2] > 0.0]
        facedict = {
        #    'front':fronts, 
        #    'back':backs, 
        #    'left':lefts,                                        
        #    'right':rights, 
            'top':tops, 
            'bottom':bottoms, 
                }
        return facedict

    def translate_face(self, vect, face = 'top'):
        cfaces = self.coords_by_face
        face_coords = cfaces[face]
        mpu.translate_coords(face_coords, vect)
        self.calculate_normals()
        self.modified = True

    def rotate_z_face(self, ang_z, face = 'top'):
        cfaces = self.coords_by_face
        face_coords = cfaces[face]
        foff = mpu.center_of_mass(face_coords)
        mpu.translate_coords(face_coords, mpu.flip(foff))
        mpu.rotate_z_coords(face_coords, ang_z)
        mpu.translate_coords(face_coords, foff)
        self.calculate_normals()
        self.modified = True

def ucube(*args, **kwargs):
    pcube = unit_cube(*args, **kwargs)
    return pcube

def uoctagon(*args, **kwargs):
    octaxml = os.path.join(primitive_data_path, 'octagon.mesh.xml')
    poct = primitive_from_xml(octaxml)
    #poct = unit_octagon(*args, **kwargs)
    return poct

def sum_primitives(prims):
    final_prim = prims[0]
    if len(prims) > 1:
        for prim in prims[1:]:
            final_prim += prim
    return final_prim











