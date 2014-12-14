import make_places.fundamental as fu
import mp_utils as mpu
import mp_primitives as mpp
import mp_vector as cv
from make_places.fundamental import base
import make_places.profiler as prf
import make_places.user_info as ui

import xml.etree.cElementTree
#import xml.etree.ElementTree

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
        self._default_('smooth_normals',False,**kwargs)                   

        #self.origin = kwargs['position']
        self._default_('origin',None,**kwargs)
        #self.position = kwargs['position']
        
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
    def __add__(self, other):
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
            #'origin' : org, 
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

    def calculate_normals(self,anyway = False,smooth = False):
        if self.has_normals() == 'false' and not anyway: return
        # must iterate over faces, for each vertex, apply new normal
        for fa in self.faces:
            try:v1 = self.coords[fa[0]]
            except: pdb.set_trace()
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

    def get_vertexes(self):
        return mpp.vertices_from_data(self.coords,self.ncoords,self.uv_coords)

    def get_vertexes_faces_phys(self):
        #vs = self.get_vertexes()
        mcnt = len(self.phys_materials)
        fcnt = len(self.face_materials)
        fa = {}
        for mdx in range(mcnt):
            ma = self.phys_materials[mdx]
            fa[ma] = []
            for fmdx in range(fcnt):
                if self.phys_face_materials[fmdx] == mdx:
                    fa[ma].append(self.faces[fmdx])
        return fa
        #return (vs, fa)

    def get_vertexes_faces(self):
        #vs = self.get_vertexes()
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
        #return (vs, fa)

    def find_centroid(self):
        com = cv.center_of_mass(self.coords)   
        return com

    def origin_to_centroid(self):
        centroid = self.find_centroid()
        self.reset_position(centroid)

    def reset_position(self, pos):
        self.origin = pos
        self.translate(cv.flip(pos))

    def reposition_origin(self):
        if self.origin is None:self.origin_to_centroid()
        else:self.reset_position(self.origin)
        return self.origin

    def write_as_xml(self):
        if self.modified:
            self.calculate_normals(
                self.force_normal_calc,self.smooth_normals)
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

    def rotate_z(self, ang_z):
        #self.coords = mpu.rotate_z_coords(self.coords, ang_z)
        #self.ncoords = mpu.rotate_z_coords(self.ncoords, ang_z)
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
    xlines = []
    #(vertexes, faces) = prim.get_vertexes_faces()
    faces = prim.get_vertexes_faces()
    _32bitindices = prim.requires_32bit_indices()
    _normals = prim.has_normals()
    sig = 4
    doround = False

    xlines.append("<mesh>\n")
    xlines.append("    <sharedgeometry>\n")
    xlines.append("        <vertexbuffer positions=\"true\" normals=\""+_normals+"\" colours_diffuse=\""+("false")+"\" texture_coord_dimensions_0=\"float2\" texture_coords=\"1\">\n")
    #xlines.append("        <vertexbuffer positions=\"true\" normals=\"true\" colours_diffuse=\""+("false")+"\" texture_coord_dimensions_0=\"float2\" texture_coords=\"1\">\n")

    #for v in vertexes:

    coords  = prim.coords
    ncoords = prim.ncoords
    ucoords = prim.uv_coords
    vcnt = len(coords)
    for vdx in range(vcnt):
        #x = v.position.x
        #y = v.position.y
        #z = v.position.z
        #nx = v.normal.x
        #ny = v.normal.y
        #nz = v.normal.z
        #ux = v.uv.x
        #uy = v.uv.y

        p = coords[vdx]
        x,y,z = p.x,p.y,p.z
        n = ncoords[vdx]
        nx,ny,nz = n.x,n.y,n.z
        u = ucoords[vdx]
        ux,uy = u.x,u.y

        #xlines.append("            <vertex>\n")
        xlines.append(" "*12 + "<vertex>\n")
        xlines.append("                <position x=\""+str(x)+"\" y=\""+str(y)+"\" z=\""+str(z)+"\" />\n")
        #if _normals == 'true':
        xlines.append("                <normal x=\""+str(nx)+"\" y=\""+str(ny)+"\" z=\""+str(nz)+"\" />\n")
        xlines.append("                <texcoord u=\""+str(ux)+"\" v=\""+str(1.0-uy)+"\" />\n")
        xlines.append("            </vertex>\n")

    xlines.append("        </vertexbuffer>\n")
    xlines.append("    </sharedgeometry>\n")
    xlines.append("    <submeshes>\n")
    for m in faces.keys():
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

cubexml = os.path.join(primitive_data_path, 'cube.mesh.xml')
cubedata = primitive_data_from_xml(cubexml)
class unit_cube(arbitrary_primitive):
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
def ucube(*args, **kwargs):
    #pcube = dcopy(UCUBE)
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











