import make_places.fundamental as fu
import make_places.profiler as prf
import make_places.user_info as ui

import mp_utils as mpu
import mp_vector as cv

import xml.etree.cElementTree
import os, pdb, shutil
import numpy as np
from numpy import linalg
from numpy import matrix
from math import sin
from copy import deepcopy as dcopy
from copy import copy
import cStringIO as sio


primitive_data_path = ui.info['primitivedir']
xml_library = {}
xml_library_keys = []

def load_xml_library():
    wdir = ui.info['worlddir']
    tdir = ui.info['texturedir']
    if os.path.isdir(wdir): shutil.rmtree(wdir)
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
    xml_library_keys = xml_library.keys()
prf.measure_time('load xml library', load_xml_library)

def initialize_obj_contentdir():
    tdir = ui.info['contenttexturedir']
    if os.path.isdir(tdir): shutil.rmtree(tdir)
    if not os.path.isdir(tdir):shutil.copytree(ui.info['newtexturedir'],tdir)
prf.measure_time('reset obj content dir', initialize_obj_contentdir)

class arbitrary_primitive(fu.base):

    _scale_uvs_ = False
    def __init__(self, *args, **kwargs):
        self.coords = kwargs['verts']
        self.ncoords = kwargs['nverts']
        self.uv_coords = kwargs['uvs']
        self.faces = kwargs['faces']

        self.xml_filename = kwargs['xmlfilename']
        self.gcol_filename = self.xml_filename.replace('mesh.xml','gcol')
        self.gfxmesh_name = self.xml_filename.replace('.xml','')
        self.colmesh_name = self.gcol_filename
        
        self.obj_filename = self.xml_filename.replace('mesh.xml','mesh.obj')

        self._default_('gcol',True,**kwargs)
        self._default_('is_lod',False,**kwargs)
        self._default_('has_lod',False,**kwargs)
        
        self._default_('force_normal_calc',False,**kwargs)                   
        self._default_('prevent_normal_calc',False,**kwargs)
        self._default_('smooth_normals',False,**kwargs)                   

        self._default_('origin',None,**kwargs)
        #self._default_('materials',['gridmat','concrete1','brick2'],{})
        self._default_('materials',['gridmat'],**kwargs)
        self._default_('phys_materials',['/common/pmat/Stone'],**kwargs)
        
        fcnt = len(self.faces)
        zero = [0]*fcnt
        self._default_('phys_face_materials',zero,**kwargs)
        self._default_('face_materials',zero[:],**kwargs)

        self._default_('tag','_arb_',**kwargs)
        self.modified = False

    def consume(self, other):
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

        other_offset = len(self.coords)
        mpu.offset_faces(other.faces, other_offset)
        self.coords.extend(other.coords)
        self.ncoords.extend(other.ncoords)
        self.uv_coords.extend(other.uv_coords)
        self.faces.extend(other.faces)

        self.phys_face_materials.extend(other.phys_face_materials)
        self.face_materials.extend(other.face_materials)
        self.modified = True
        return self

    # CAN THIS BE DONE IN PLACE?
    def __add__111(self, other):
        other_offset = len(self.coords)
        org = cv.vector(0,0,0)
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

    #def has_normals(self):
    #    has = 'true' if self.ncoords else 'false'
    #    return has

    def calculate_normals(self,prevent = False,anyway = False,smooth = False):
        #if self.has_normals() == 'false' and not anyway or prevent: return
        if not anyway or prevent: return
        # must iterate over faces, for each vertex, apply new normal
        for fa in self.faces:
            v1 = self.coords[fa[0]]
            v2 = self.coords[fa[1]]
            v3 = self.coords[fa[2]]
            v1v2 = cv.v1_v2(v1,v2)
            v1v3 = cv.v1_v2(v1,v3)
            normal = v1v2.cross(v1v3).normalize()
            for vdx in fa: self.ncoords[vdx] = normal
        if smooth:
            cbins = []
            cdexs = []
            for cdx in range(len(self.coords)):
                coo = self.coords[cdx]
                if coo in cbins:
                    wdx = cbins.index(coo)
                    cdexs[wdx].append(cdx)
                else:
                    cbins.append(coo)
                    cdexs.append([cdx])

            for cd in cdexs:
                newnormal = cv.center_of_mass([self.ncoords[n] for n in cd])
                for n in cd:
                    self.ncoords[n] = newnormal

    def get_vertexes_faces_phys(self):
        mcnt = len(self.phys_materials)
        fcnt = len(self.face_materials)
        fa = {}
        for mdx in range(mcnt):
            ma = self.phys_materials[mdx]
            if ma == 'skip':continue
            fa[ma] = []
            for fmdx in range(fcnt):
                if self.phys_face_materials[fmdx] == mdx:
                    fa[ma].append(self.faces[fmdx])
        return fa

    def get_vertexes_faces(self):
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
        return fa

    def find_centroid(self):
        if len(self.coords) < 1:
            print 'i am empty inside!'
            com = None
        else:com = cv.center_of_mass(self.coords)   
        return com

    def origin_to_centroid(self):
        centroid = self.find_centroid()
        self.reset_position(centroid)

    def reset_position(self, pos):
        self.origin = pos
        if not pos is None:
            self.translate(cv.flip(pos))

    def reposition_origin(self):
        if self.origin is None:self.origin_to_centroid()
        else:self.reset_position(self.origin)
        return self.origin

    def write_as_obj(self,world_dir):
        self.calculate_normals(
            self.prevent_normal_calc, 
            self.force_normal_calc,
            self.smooth_normals)
        self.obj_representation,ofile = obj_from_primitive_data(self)

        is_new = True
        odir = os.path.join(world_dir,self.obj_filename)
        with open(odir,'w') as handle:handle.write(self.obj_representation)
        return is_new

    def write_as_xml(self,world_dir):
        if self.modified:
            self.calculate_normals(
                self.prevent_normal_calc, 
                self.force_normal_calc,
                self.smooth_normals)
            self.xml_representation,xfile = xml_from_primitive_data(self)
        else:
            xml = os.path.join(primitive_data_path,self.xml_filename)
            with open(xml, 'r') as handle:
                xlines = handle.readlines()
            self.xml_representation = '\n'.join(xlines)

        if self.xml_representation in xml_library_keys:
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
            xml_library_keys.append(self.xml_representation)
            is_new = True
            
            #print 'new xml rep!', xfile
            xdir = os.path.join(world_dir,self.xml_filename)
            with open(xdir,'w') as handle:
                handle.write(self.xml_representation)
        #return xlines, is_new
        return is_new

    def translate_x(self, dx):
        cv.translate_coords_x(self.coords, dx)
        self.modified = True
        return self

    def translate_y(self, dy):
        cv.translate_coords_y(self.coords, dy)
        self.modified = True
        return self

    def translate_z(self, dz):
        cv.translate_coords_z(self.coords, dz)
        self.modified = True
        return self

    def translate(self, vect):
        cv.translate_coords(self.coords, vect)
        self.modified = True
        return self

    def material_to_faces(self, mat, faces):
        if not mat in self.materials: self.materials.append(mat)
        mdx = self.materials.index(mat)
        for fdx in faces: self.face_materials[fdx] = mdx

    def assign_material(self, mat):
        faces = range(len(self.faces))
        self.material_to_faces(mat, faces)

    def scale_uvs(self, vect):
        unit_scale = (vect.x == 1.0 and vect.y == 1.0 and vect.z == 1.0)
        if unit_scale or not self.ncoords: return
        scaled = []
        for fdx in range(len(self.faces)):
            fdxs = self.faces[fdx]      
            rccoords = []
            rucoords = []
            rncoords = []
            for cdx in fdxs:
                rccoords.append(self.coords[cdx])
                rucoords.append(self.uv_coords[cdx])
                rncoords.append(self.ncoords[cdx])
            
            no = rncoords[0]
            b3 = no.copy().normalize()
            b1 = b3.copy().xy().rotate_z(fu.to_rad(90.0)).normalize()
            b2 = b3.cross(b1).normalize()
            proj = cv.vector(cv.dot(vect,b1),cv.dot(vect,b2),0.0)
            
            if b1.magnitude() < 0.5:
                us,vs,ns = vect.x,vect.y,1.0
            elif abs(no.x) > 0.999:
                us,vs,ns = vect.y,vect.z,1.0
            elif abs(no.y) > 0.999:
                us,vs,ns = vect.x,vect.z,1.0
            else:
                m = matrix([b1.to_list(),b2.to_list(),b3.to_list()]).transpose()
                us,vs,ns = linalg.solve(m,proj.to_list())
                us,vs,ns = abs(us),abs(vs),abs(ns)

                us,vs,ns = 1.0,1.0,1.0

            for uv in rucoords:
                if uv in scaled: continue
                else:
                    scaled.append(uv)
                    uv.x *= us
                    uv.y *= vs

    # should uv_tform be using all vector2d??
    def worldly_uvs(self, uv_ttf):
        sx = uv_ttf.scales.x
        sy = uv_ttf.scales.y
        #sx,sy,sz = uv_ttf.scales
        for uvc in self.uv_coords:
            #uvc.x *= sx
            #uvc.y *= sy
            uvc.x /= sx
            uvc.y /= sy

    def scale(self, vect):
        cv.scale_coords(self.coords, vect)
        if self._scale_uvs_: self.scale_uvs(vect)
        self.modified = True
        return self

    def scale_x(self, sx):
        cv.scale_coords_x(self.coords, sx)
        if self._scale_uvs_: self.scale_uvs(cv.vector(sx,0,0))
        self.modified = True
        return self

    def scale_y(self, sy):
        cv.scale_coords_y(self.coords, sy)
        if self._scale_uvs_: self.scale_uvs(cv.vector(0,sy,0))
        self.modified = True
        return self

    def scale_z(self, sz):
        cv.scale_coords_z(self.coords, sz)
        if self._scale_uvs_: self.scale_uvs(cv.vector(0,0,sz))
        self.modified = True
        return self

    def rotate_z(self, ang_z):
        cv.rotate_z_coords(self.coords, ang_z)
        cv.rotate_z_coords(self.ncoords, ang_z)
        self.modified = True
        return self

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
    xrep = mpu.xml_from_primitive_data(prim)
    return xrep, xfile

def primitive_data_from_xml(xmlfile):
    tree = xml.etree.cElementTree.parse(xmlfile)
    #tree = xml.etree.ElementTree.parse(xmlfile)
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
                verts.append(cv.vector(x,y,z))
                nx = float(vt.find('normal').get('x'))
                ny = float(vt.find('normal').get('y'))
                nz = float(vt.find('normal').get('z'))
                nverts.append(cv.vector(nx,ny,nz))
                u = float(vt.find('texcoord').get('u'))
                v = float(vt.find('texcoord').get('v'))
                uvs.append(cv.vector2d(u,1-v))

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

    #org = cv.vector(0,0,0)
    sep = xmlfile.rfind(os.path.sep)
    xmlfile = xmlfile[sep+1:]
    xml_file_names.append(xmlfile)
    pwargs = {
        #'origin' : org, 
        'verts' : verts, 
        'nverts' : nverts, 
        'uvs' : uvs, 
        'faces' : faces, 
        'materials' : materials, 
        'face_materials' : face_materials, 
        'xmlfilename' : xmlfile, 
            }
    return pwargs

def primitive_from_xml(xmlfile):
    pwargs = primitive_data_from_xml(xmlfile)
    return arbitrary_primitive(**pwargs)

obj_file_names = []
def make_obj_name_unique(ofile):
    ob = ofile[:ofile.rfind('mesh.obj')]
    onum = len(obj_file_names) + 1
    om += '.'.join([str(onum),'mesh','obj'])
    return om

def obj_from_primitive_data(prim):
    ofile = prim.obj_filename
    if ofile in obj_file_names:
        ofile = make_obj_name_unique(ofile)
    obj_file_names.append(ofile)

    faces = prim.get_vertexes_faces()
    mats = faces.keys()
    mcnt = len(mats)

    sioio = sio.StringIO()
    sioio.write('mtllib materials.mtl\n')
    for vdx in range(len(prim.coords)):
        pvert = prim.coords[vdx]
        nvert = prim.ncoords[vdx]
        uvert = prim.uv_coords[vdx]
        sioio.write( 'v %f %f %f\n' % (pvert.x, pvert.y, pvert.z) )
        sioio.write( 'vn %f %f %f\n' % (nvert.x, nvert.y, nvert.z) )
        sioio.write( 'vt %f %f\n' % (uvert.x, uvert.y) )
    #for vert in prim.coords: sioio.write( 'v %f %f %f\n' % (vert.x, vert.y, vert.z) )
        
    for mdx in range(mcnt):
        m = mats[mdx]
        mfaces = faces[m]
        fcnt = len(mfaces)
        sioio.write('usemtl ')
        sioio.write(m)
        sioio.write('\n')
        sioio.write('s off\n')
        for fdx in range(fcnt):
            f = mfaces[fdx]
            f1 = f[0] + 1
            f2 = f[1] + 1
            f3 = f[2] + 1
            sioio.write('f')
            sioio.write( ' %i/%i/%i' % (f1,f1,f1) )
            sioio.write( ' %i/%i/%i' % (f2,f2,f2) )
            sioio.write( ' %i/%i/%i' % (f3,f3,f3) )
            sioio.write('\n')

    '''#
    sioio.write('usemtl Material\n')
    sioio.write('s off\n')
    for face in prim.faces:
        sioio.write('f')
        for vert in face:
            vi = vert + 1
            sioio.write( ' %i/%i/%i' % (vi,vi,vi) )
        sioio.write('\n')
    '''#

    orep = sioio.getvalue()
    return orep,ofile

def empty_primitive():
    xmlfile = 'empty.mesh.xml'
    pwargs = {
        'verts':[],'nverts':[], 
        'uvs' :[],'faces':[], 
        'materials':[],'face_materials':[], 
        'xmlfilename':xmlfile, 
            }
    return arbitrary_primitive(**pwargs)

cubexml = os.path.join(primitive_data_path, 'cube.mesh.xml')
cubedata = primitive_data_from_xml(cubexml)
class unit_cube___________(arbitrary_primitive):
    cubexml = os.path.join(primitive_data_path, 'cube.mesh.xml')

    def __init__(self, *args, **kwargs):
        #pcubedata = dcopy(cubedata)
        pcubedata = primitive_data_from_xml(self.cubexml)
        self._default_('tag','_cube_',**kwargs)
        arbitrary_primitive.__init__(self, *args, **pcubedata)
        self.find_faces()
        self._scale_uvs_ = True

    def find_faces(self):
        fronts = []
        backs = []
        lefts = []
        rights = []
        tops = []
        bottoms = []
        for vdx in range(len(self.coords)):
            cc = self.coords[vdx]
            if cc.y < 0.0: fronts.append(cc)
            if cc.y > 0.0: backs.append(cc)
            if cc.x < 0.0: lefts.append(cc)
            if cc.x > 0.0: rights.append(cc)
            if cc.z > 0.0: tops.append(cc)
            if cc.z <= 0.0: bottoms.append(cc)

        cfacedict = {
            'front':fronts, 
            'back':backs, 
            'left':lefts,                                        
            'right':rights, 
            'top':tops, 
            'bottom':bottoms, 
                }

        def find_face_indices(side):
            found = []
            fcnt = len(self.faces)
            for fdx in range(fcnt):
                face = self.faces[fdx]
                relevcoords = [self.coords[f] for f in face]
                if mpu.subset(cfacedict[side],relevcoords):
                    found.append(fdx)
            return found

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
        self.coords_by_face = cfacedict

    def align_face(self, parent_uvs):
        pdb.set_trace()

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
        cv.translate_coords(face_coords, vect)
        self.calculate_normals()
        self.modified = True

    def rotate_z_face(self, ang_z, face = 'top'):
        cfaces = self.coords_by_face
        face_coords = cfaces[face]
        foff = cv.center_of_mass(face_coords)
        cv.translate_coords(face_coords, cv.flip(foff))
        cv.rotate_z_coords(face_coords, ang_z)
        cv.translate_coords(face_coords, foff)
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
        self.find_faces()
        #self.coords_by_face = self.find_faces()
        self._scale_uvs_ = True

    def find_faces(self):
        #fronts = [v for v in self.coords if v[1] < 0.0]
        #backs = [v for v in self.coords if v[1] > 0.0]
        #lefts = [v for v in self.coords if v[0] < 0.0]
        #rights = [v for v in self.coords if v[0] > 0.0]
        bottoms = [v for v in self.coords if v.z <= 0.0]
        tops = [v for v in self.coords if v.z > 0.0]
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
        cv.translate_coords(face_coords, vect)
        self.calculate_normals()
        self.modified = True

    def rotate_z_face(self, ang_z, face = 'top'):
        cfaces = self.coords_by_face
        face_coords = cfaces[face]
        foff = cv.center_of_mass(face_coords)
        cv.translate_coords(face_coords, cv.flip(foff))
        cv.rotate_z_coords(face_coords, ang_z)
        cv.translate_coords(face_coords, foff)
        self.calculate_normals()
        self.modified = True

#UCUBE = unit_cube()
def ucube____(*args, **kwargs):
    #pcube = dcopy(UCUBE)
    #pcube = unit_cube(*args, **kwargs)
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
            final_prim.consume(prim)
            #final_prim += prim
    return final_prim











