#from make_places.blend_in import blend_in_geometry

from math import cos
from math import sin
from math import tan
from math import sqrt
import numpy as np
import random as rm

PI = np.round(np.pi,8)

def uniq(seq):
    ret = []
    for sq in seq:
        if not sq in ret:
            ret.append(sq)
    return ret

def center_of_mass(coords):
    xs,ys,zs = zip(*coords)
    xme = np.round(np.mean(xs),8)
    yme = np.mean(ys)
    zme = np.mean(zs)
    return [xme,yme,zme]

def translate_coords(coords, vect):
    for coo in coords:
        for dx in range(3):
            coo[dx] += vect[dx]
    return coords

def scale_coords(coords, vect):
    for coo in coords:
        for dx in range(3):
            coo[dx] *= vect[dx]
    return coords

def rotate_z_coords(coords, ang_z):
    M_z = [
        [cos(ang_z), -sin(ang_z), 0], 
        [sin(ang_z), cos(ang_z), 0], 
        [0, 0, 1], 
            ]
    for coo in coords:
        rot_coo = row_major_multiply(M_z, coo)
        coo[:] = rot_coo
    return coords

def scale_vector(vect, sv):
    for dx in range(3):
        vect[dx] *= sv[dx]
    return vect

def translate_vector(vect, tv):
    for dx in range(3):
        vect[dx] += tv[dx]
    return vect

def normalize(vect):
    mag = magnitude(vect)
    return [v/mag for v in vect]

def v1_v2(v1, v2):
    v1_v2_ = [v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]]
    return v1_v2_

def point_slope(x1,x2,y1,y2):
    if x1 == x2: return None
    else: return (y2-y1)/(x2-x1)

def line_y_intersect(pt,m):
    if m is None: return None
    x = pt[0]
    y = pt[1]
    run = x*m
    return y - run

def in_range(x, rng):
    in_ = x > min(rng) and x < max(rng)
    return in_

def segments_intersect(s1,s2):
    m1 = point_slope(s1[0][0],s1[1][0],s1[0][1],s1[1][1])
    m2 = point_slope(s2[0][0],s2[1][0],s2[0][1],s2[1][1])
    if m1 == m2:
        #print('segments with same slope', m1,m2)
        return False
    b1 = line_y_intersect(s1[0],m1)
    b2 = line_y_intersect(s2[0],m2)
    if b1 is None:
        x_int = s1[0][0]
        y_int = m2*x_int + b2
    elif b2 is None:
        x_int = s2[0][0]
        y_int = m1*x_int + b1
    else:
        x_int = (b1 - b2)/(m2 - m1)
        y_int = m1*x_int + b1
    rng_chks = [
        in_range(x_int, (s1[0][0], s1[1][0])), 
        in_range(x_int, (s2[0][0], s2[1][0])), 
        in_range(y_int, (s1[0][1], s1[1][1])), 
        in_range(y_int, (s2[0][1], s2[1][1])), 
        ]
    if False in rng_chks: return False
    # are x_int,y_int within bounds of either seg?
    #print('segmentsDOintersect!',s1,s2)
    return True

def in_region(regi,pt):
    for dx in range(len(regi)):
        if not in_range(pt[dx],regi[dx]):
            return False
    return True

def midpoint(p1,p2):
    def me(x,y): return (x+y)/2.0
    return [me(x,y) for x,y in zip(p1,p2)]

def distance_xy(v1,v2):
    fakev1 = v1[:]
    fakev2 = v2[:]
    fakev1[2] = 0
    fakev2[2] = 0
    return magnitude(v1_v2(fakev1,fakev2))

def distance(v1,v2):
    return magnitude(v1_v2(v1,v2))

def magnitude(vect):
    try:quad = sum([v**2 for v in vect])
    except OverflowError:
        print('toobig',vect)
    return sqrt(quad)

def cross(v1, v2):
  return [v1[1]*v2[2]-v1[2]*v2[1], 
      v1[2]*v2[0]-v1[0]*v2[2], 
      v1[0]*v2[1]-v1[1]*v2[0]]

def dot(v1, v2):
    return sum([n*m for n, m in zip(v1, v2)])

def flip(v1):
    return [-1*v for v in v1]

def angle_between_xy(v1, v2):
    alpha1 = angle_from_xaxis_xy(v1)
    alpha2 = angle_from_xaxis_xy(v2)
    if alpha2 - alpha1 > PI/2:
    #if alpha2 - alpha1 > np.pi/2:
        print('arpha', v1, v2, alpha1, alpha2)
    return alpha2 - alpha1

def angle_between(v1, v2):
    alpha1 = angle_from_xaxis(v1)
    alpha2 = angle_from_xaxis(v2)
    return alpha2 - alpha1

def angle_from_xaxis_xy(v1):
    fakev1 = v1[:]
    fakev1[2] = 0
    return angle_from_xaxis(fakev1)

def angle_from_xaxis(v1):
    v1 = normalize(v1)
    length = magnitude(v1)
    x_hat = [1,0,0]
    x_proj = dot(v1, x_hat)
    sign = -1 if v1[1] < 0 else 1
    if x_proj == 0:ang = sign*np.pi/2.0
    elif x_proj < length and x_proj > -length:
        ang = sign*np.arccos(x_proj)
    elif x_proj < 0:ang = np.pi
    else:ang = 0.0
    return ang    

def to_rad(deg):
    return (np.pi/180.0)*deg

def to_deg(rad):
    return (180.0/np.pi)*rad

def row_major_multiply(M, coo):
    rcoox = dot(M[0],coo)
    rcooy = dot(M[1],coo)
    rcooz = dot(M[2],coo)
    return [rcoox, rcooy, rcooz]

def find_corners(pos, length, width):
    c1, c2, c3, c4 = pos[:], pos[:], pos[:], pos[:]
    c2[0] += length
    c3[0] += length
    c3[1] += width
    c4[1] += width
    return [c1, c2, c3, c4]

def offset_faces(faces, offset):
    for fa in faces:
        for fx in range(len(fa)):
            fa[fx] += offset
    return faces

class element(object):

    def _default_(self, *args, **kwargs):
        key = args[0]
        init = args[1]
        if key in kwargs.keys():init = kwargs[key]
        if not key in self.__dict__.keys():
            self.__dict__[key] = init

    def __init__(self, *args, **kwargs):
        self._default_('position',[0,0,0],**kwargs)
        self._default_('scales',[1,1,1],**kwargs)
        self._default_('rotation',[0,0,0],**kwargs)
        self._default_('name','__element__',**kwargs)
        self._default_('primitives',[],**kwargs)
        self._default_('children',[],**kwargs)
        self._default_('materials',[],**kwargs)

    def scale(self, vect):
        for sdx in range(3):
            self.scales[sdx] *= vect[sdx]

    def rotate_z(self, vect):
        translate_vector(self.rotation, vect)

    def translate(self, vect):
        translate_vector(self.position, vect)







    def set_world_coords(self, trans = None, 
                  scls = None, rots = None):
        def add_coords(coords, faces):
            faces_offset = len(world_coords)
            world_coords.extend(
                translate_coords(
                    rotate_z_coords(
                        scale_coords(
                            coords,scales),rot_z),translation))
            world_faces.extend(
                offset_faces(faces, faces_offset))
        world_coords = []
        world_faces = []
        texfaces = []
        if trans is None: translation = self.position
        else: translation = trans
        if scls is None: scales = self.scales
        else: scales = scls
        if rots is None: rot_z = self.rotation[2]
        else: rot_z = rots[2]
        for prim in self.primitives:
            prim_coords = prim.model_coords
            prim_faces = prim.model_faces
            add_coords(prim_coords, prim_faces)
            texfaces.extend(prim.texfaces)
        for elem in self.children:
            elem.set_world_coords()
            elem_world_coords = elem.world_coords
            elem_world_faces = elem.world_faces
            elem_texfaces = elem.texfaces
            add_coords(elem_world_coords, elem_world_faces)
            texfaces.extend(elem_texfaces)
            self.materials.extend(elem.materials)
        self.world_coords = world_coords
        self.world_faces = world_faces
        self.texfaces = texfaces

    def get_bbox(self):
        corners = [[0,0,0],[1,0,0],[1,1,0],[0,1,0]]
        scale_coords(corners,self.scales)
        rotate_z_coords(corners,self.rotation[2])
        translate_coords(corners,self.position)
        bbox_ = bbox(position = self.position,
            corners = corners, parent = self)
        return bbox_

class bbox(object):
    def __init__(self, *args, **kwargs):
        try: self.corners = kwargs['corners']
        except KeyError:
            x = args[0]
            y = args[1]
            z = args[2]
            self.xbox = x
            self.ybox = y
            self.zbox = z
            self.corners = []
        #print('bbcorners',self.corners)
        try: self.position = kwargs['position']
        except KeyError: self.position = [0,0,0]
        try: self.rotation = kwargs['rotation']
        except KeyError: self.rotation = [0,0,0]
        try: self.parent = kwargs['parent']
        except KeyError: self.parent = None

    def intersects(self,boxes,box):
        if not type(box) is type([]):box = [box]
        check = separating_axis
        for bo in box:
            for ibox in boxes:
                if check(ibox,bo):
                    return True
        return False

def fall_inside(rng,x):
    return rng[0] < x and rng[1] > x

def no_overlaps(rng1,rng2):
    if rng1[1] < rng2[0]: return True
    elif rng1[0] > rng2[1]: return True
    else: return False

def check_norot(ibox,box):
    overs = []
    for key in ['xbox','ybox']:#,'zbox']:
        iboxv = ibox.get_world_axbox(key)
        boxv = box.__dict__[key]
        if not no_overlaps(iboxv, boxv):overs.append(key)
    return len(overs) == 2

def segments_intersect2(s1,s2):
    def determ(v1,v2):
        return v1[0]*v2[1] - v1[1]*v2[0]
    a,b = s1
    c,d = s2
    det = determ(v1_v2(a,b),v1_v2(d,c))
    if det == 0.0: return False,None
    t = determ(v1_v2(a,c),v1_v2(d,c)) / det
    u = determ(v1_v2(a,b),v1_v2(a,c)) / det
    if (t < 0 or u < 0 or t > 1 or u > 1):
        return False,None
    p = [n*(1-t) for n in a]
    q = [n*t for n in b]
    pt = [n+m for n,m in zip(p,q)]
    return True,pt

def check_corners(ibox,box):
    icorns = ibox.corners
    corns = box.corners
    icorncnt = len(icorns)
    corncnt = len(corns)
    edges = [[corns[edx-1],corns[edx]] for edx in range(1,corncnt)]
    iedges = [[icorns[edx-1],icorns[edx]] for edx in range(1,icorncnt)]
    for edge in edges:
        for iedge in iedges:
            bad,pt = segments_intersect2(edge,iedge)
            if bad:
                print('found isect',pt,icorns,corns)
                return True
    return False

def get_norms(verts):
    norms = []
    for vdx in range(1, len(verts)):
        v1,v2 = verts[vdx-1],verts[vdx]
        if v1 == v2:
            print('wtf vs', verts)
        v1_v2_ = v1_v2(v1,v2)
        zhat = [0,0,1]
        #norm = normalize(cross(v1_v2_,zhat))
        norm = normalize(cross(normalize(v1_v2_),zhat))
        norms.append(norm)
    return norms

def project(verts, axis):
    min_ = dot(verts[0],axis)
    max_ = min_
    for v in verts[1:]:
        val = dot(v,axis)
        if val < min_: min_ = val
        if val > max_: max_ = val
    return [min_,max_]
    
def overlap(rng1,rng2):
    if max(rng1) < min(rng2): return False
    elif max(rng2) < min(rng1): return False
    else: return True

def separating_axis(bb1,bb2):
    ns1 = get_norms(bb1.corners)
    ns2 = get_norms(bb2.corners)
    edgenorms = ns1 + ns2
    for edgenorm in edgenorms:
        proj1 = project(bb1.corners,edgenorm)
        proj2 = project(bb2.corners,edgenorm)
        if not overlap(proj1,proj2):
            return False
    return True

def break_elements(elements):
    def prep(elem):
        elms = [elem.transform(child) for child in elem.children]
        return elms
    elements = [prep(el) for el in elements]
    return [item for sublist in elements for item in sublist]

#def create_elements(elements):
#    [el.set_world_coords() for el in elements]
#    all_coords = [el.world_coords for el in elements]
#    all_faces = [el.world_faces for el in elements]
#    all_texfaces = [el.texfaces for el in elements]
#    all_mats = [el.materials for el in elements]
#    all_names = [el.name for el in elements]
#    #   if this is possible...
#    # build global verts from all_coords, 
#    #  and change all_faces to references to this
#    #  if the user specifies....
#    blend_in_geometry(all_names, all_coords, 
#        all_faces, all_texfaces, all_mats, 
#            len(elements))












