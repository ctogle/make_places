#imports
# cython: profile=True,nonecheck=False
#cimport cython

import mp_utils as mpu
import mp_vector as cv
cimport mp_vector as cv

from libc.math cimport sqrt

import time
import random as rm

stuff = 'hi'

#global loccnt
cdef int loccnt
cdef terrain_point add_loc(terrain_point loc,list locs,list locs_str):
    global loccnt
    cdef terrain_point n
    #cdef loccnt = len(locs)
    cdef int ldx
    cdef int ndx
    cdef str loc_str = loc._str
    cdef list keep_str
    for ldx in range(loccnt):
        if <str>locs_str[ldx] == loc_str:
            keep = <terrain_point>locs[ldx]

            kncnt = len(keep.neighbors)
            keep_str = []
            for ndx in range(kncnt):
                keep_str.append(<str>keep.neighbors[ndx]._str)
            #keep_str = [n._str for n in keep.neighbors]

            pncnt = len(loc.neighbors)
            for ndx in range(pncnt):
                #n = loc.neighbors[ndx]
                n = <terrain_point>loc.neighbors[ndx]
                if not n._str in keep_str:
                    keep.neighbors.append(n)
                    keep_str.append(n._str)

            return keep

    locs_str.append(loc_str)
    locs.append(loc)
    loccnt += 1
    return loc

cdef float relax(terrain_point tpt):
    cdef cv.vector centroid
    cdef cv.vector move
    cdef cv.vector weights = tpt.weights
    centroid = cv.com([v.position for v in tpt.neighbors])
    move = cv.v1_v2_c(tpt.position,centroid)
    move.scale(weights)
    tpt.position.translate(move)
    return move.magnitude()

cdef class terrain_point:

    #def __cinit__(self,x,y,z):
    def __cinit__(self,position):
        #self.position = cv.vector(x,y,z)
        self.position = position
        self.weights = cv.one()
        x,y = self.position.x,self.position.y
        self._str = str((x,y))
        self.neighbors = []

terrain_numbers = [0]
def get_terrain_number(repeat = False):
    if repeat: return str(terrain_numbers[0] - 1)
    num = terrain_numbers.pop(0)
    nex = num + 1
    terrain_numbers.append(nex)
    return str(num)

cdef class terrain_triangle:

    cdef public list verts
    cdef public list corners
    cdef public list boundary_points
    cdef public list children
    cdef list com_vects
    cdef public cv.vector center
    cdef public int splits

    def __cinit__(self,list verts,list children,list locs,list locs_str):
        #self.verts = verts
        self.set_verts(verts,locs,locs_str)
        self.children = children
        self.splits = 0

    cdef set_verts(self, list verts, list locs, list locs_str):
        cdef list vposs = [v.position for v in verts]
        cdef cv.vector center = cv.com(vposs)
        cdef int vdx
        for vdx in range(3):
            vkeep = add_loc(verts[vdx],locs,locs_str)
            verts[vdx] = vkeep

        self.center = center
        self.verts = verts
        self.com_vects = [cv.v1_v2_c(v,center) for v in vposs]
        [cvt.normalize() for cvt in self.com_vects]
        self.corners = [cv.vector(v.x,v.y,v.z) for v in vposs]
        [c.translate(tv) for c,tv in zip(self.corners,self.com_vects)]
    
    cdef float pick_zoff(self, float dist,int vcnt):
        cdef float rand = rm.random()*2.0 - 1.0
        cdef float zoff
        vcnt = 10000 if vcnt > 10000 else vcnt
        zoff = rand*dist/(float(vcnt)**(1.0/2.0))
        return zoff

    cdef terrain_point bisect(self,
            terrain_point tv1,terrain_point tv2,int vcnt,list controls,int control_count,
            list locs,list locs_str,int tolerance = 25,int big_tolerance = 250):

        cdef terrain_point newtv
        cdef cv.vector newpos
        cdef cv.vector nearest
        cdef float zoff
        cdef float zdiff
        cdef float dist

        newpos = cv.midpoint_c(tv1.position,tv2.position)
        #newtv = terrain_point(newpos.x,newpos.y,newpos.z)
        newtv = terrain_point(newpos)
        #newtv = terrain_point(newpos.copy())????
        #newtv.position = newpos
        newtv.neighbors = [tv1,tv2]

        if not newtv._str in locs_str:
            if control_count == 0:zoff = self.pick_zoff(100,vcnt)
            else:
                ndex = cv.find_closest_xy_c(newpos,controls,control_count,20.0)
                nearest = <cv.vector>controls[ndex]
                dist = cv.distance_xy_c(nearest,newpos)
                zdiff = nearest.z - newpos.z
        
                if dist < tolerance: zoff = zdiff
                elif dist < big_tolerance: zoff = self.pick_zoff(dist,vcnt)
                else: zoff = self.pick_zoff(100,vcnt)
            newtv.position.z += zoff

            tv1_nstr = [n._str for n in tv1.neighbors]
            tv2_nstr = [n._str for n in tv2.neighbors]

            if not newtv._str in tv1_nstr:
                tv1.neighbors.append(newtv)
            if not newtv._str in tv2_nstr:
                tv2.neighbors.append(newtv)

            if tv2._str in tv1_nstr:
                ndx = tv1_nstr.index(tv2._str)
                tv1.neighbors.pop(ndx)
            if tv1._str in tv2_nstr:
                ndx = tv2_nstr.index(tv1._str)
                tv2.neighbors.pop(ndx)
        return newtv

    cpdef bisect_all(self, int vcnt, list controls, 
            int control_count, list locs, list locs_str):
        cdef terrain_point newt1
        cdef terrain_point newt2
        cdef terrain_point newt3
        cdef terrain_point t1
        cdef terrain_point t2
        cdef terrain_point t3
        t1,t2,t3 = self.verts
        newt1 = self.bisect(t1,t2,vcnt,controls,control_count,locs,locs_str)
        newt2 = self.bisect(t2,t3,vcnt,controls,control_count,locs,locs_str)
        newt3 = self.bisect(t3,t1,vcnt,controls,control_count,locs,locs_str)
        newt1.neighbors.extend([newt2,newt3])
        newt2.neighbors.extend([newt3,newt1])
        newt3.neighbors.extend([newt1,newt2])
        return newt1,newt2,newt3

    cpdef split(self, vcnt, controls, control_count, locs, locs_str):
        self.splits += 1
        if self.children:
            [ch.split(vcnt, controls, control_count, 
                locs, locs_str) for ch in self.children]
        else:
            t1,t2,t3 = self.verts
            newt1,newt2,newt3 = self.bisect_all(
                    vcnt, controls, control_count, locs, locs_str)
            self.children = [
                terrain_triangle([newt1,newt2,newt3],[],locs,locs_str), 
                terrain_triangle([t1,newt1,newt3],[],locs,locs_str), 
                terrain_triangle([t2,newt2,newt1],[],locs,locs_str), 
                terrain_triangle([t3,newt3,newt2],[],locs,locs_str)]

    cpdef bint inside(self, cv.vector pt):
        return cv.inside(pt, self.corners)

    cpdef fix_closest(self, pts, locs, locs_str):
        all_verts = locs
        verts = [v.position for v in all_verts]
        vcnt = len(verts)
        for pt in pts:
            if not self.inside(pt): continue
            neardex = cv.find_closest_xy_c(pt,verts,vcnt,5.0)
            nearest = verts[neardex]
            #neardis = mpu.distance_xy(nearest,pt)
            closest = all_verts[neardex]
            q2 = pt.z - closest.position.z
            closest.position.z += q2
            newwt = all_verts[neardex].weights
            newwt.x = 0.0
            newwt.y = 0.0
            newwt.z = 0.0

    cpdef fix_bounds(self, locs, locs_str, sea_level):
        cdef list all_verts = locs
        cdef int bpts = 0
        cdef terrain_point uqvt

        self.boundary_points = []
        for uqvt in all_verts:
            if not self.inside(uqvt.position):
                uqvt.weights.x = 0.0
                uqvt.weights.y = 0.0
                #uqvt.weights.z = 0.0
                #uqvt.position.z = sea_level
                self.boundary_points.append(uqvt)
                bpts += 1
        print 'found',bpts,'boundary points in',len(all_verts),'points'

    cpdef smooth(self, int icnt, list locs):
        cdef float movement = 0.0
        cdef int idx
        print 'smoothing', len(locs), 'verts', icnt, 'times'
        for idx in range(icnt):
            for tp in locs:
                movement += relax(tp)
                #movement += tp.relax()
        return movement

    def meshes(self, lod = False):
        if lod:
            lod_meshes = []
            for ch in self.children:
                for subch in ch.children:
                    for subsubch in subch.children:
                        lod_meshes.append(subsubch.mesh(
                            depth = 0, max_depth = self.splits - 4))
            for lod in lod_meshes: lod['is_lod'] = True
            return lod_meshes
        else:
            meshes = []
            for ch in self.children:
                for subch in ch.children:
                    for subsubch in subch.children:
                        meshes.append(subsubch.mesh())
            for nonlod in meshes: nonlod['has_lod'] = True
            return meshes

    def mesh(self, depth = None, max_depth = None):
        verts = []
        nverts = []
        faces = []
        face_materials = []
        uvs = []
        #materials = ['ground']
        #materials = ['grass']
        materials = ['grass2']
        data = self.face_data(depth, max_depth)
        for fdx,fdat in enumerate(data):
            newverts = [f.position.copy() for f in fdat]
            v1v2 = cv.v1_v2(newverts[0],newverts[1])
            v1v3 = cv.v1_v2(newverts[0],newverts[2])
            newnorml = [cv.cross(v1v2,v1v3).normalize() for f in fdat]
            newuvs = [cv.vector2d(0,0),cv.vector2d(1,0),cv.vector2d(0,1)]
            newuvs = [cv.vector2d(0,0),cv.vector2d(1,0),cv.vector2d(0,1)]
            verts.extend(newverts)
            nverts.extend(newnorml)
            uvs.extend(newuvs)
            faces.append([3*fdx+x for x in range(3)])
            face_materials.append(materials[0])
        xmlfile = '.'.join(['terrain',
            str(get_terrain_number()),'mesh','xml'])
        pwargs = {
            #'origin' : cv.zero(), 
            'verts' : verts, 
            'nverts' : nverts, 
            'uvs' : uvs, 
            'faces' : faces, 
            'materials' : materials, 
            'face_materials' : face_materials, 
            'phys_materials' : ['/common/pmat/Grass'], 
            'xmlfilename' : xmlfile, 
            'force_normal_calc' : True, 
            'smooth_normals' : True, 
                }
        return pwargs

    cdef int count_vertices(self):
        return 3**(self.splits+1)

    def face_data(self, depth = None, max_depth = None):
        data = []
        if not depth is None:
            if depth == max_depth:
                data.append(self.verts)
                return data
            else: depth += 1
        if self.children:
            [data.extend(ch.face_data(depth,max_depth)) 
                for ch in self.children]
        else: data.append(self.verts)
        return data

cpdef list filter(pts,tri):
    cdef list good = []
    cdef cv.vector vpt
    #cdef list vtri = [cv.vector(*t) for t in tri]

    #com = cv.com(tri)
    #vns = [cv.v1_v2(com,v).normalize() for v in tri]
    #tri = [v.translate(vn) for v,vn in zip(tri,vns)]

    for pt in pts:
        if pt in good: continue
        else:
            if type(pt) == type([]):
                vpt = cv.vector(*pt)
            else: vpt = pt
            if cv.inside(vpt,tri):
                good.append(vpt)
    return good

def make_terrain(initial_tps,splits = 2,smooths = 25,
        pts_of_interest = [[250,250,25],[500,250,-25]], sea_level = 0.0):

    global loccnt
    loccnt = 0

    pts_of_interest = filter(pts_of_interest,list(initial_tps))
    poi_count = len(pts_of_interest)
    
    cdef terrain_point t1
    cdef terrain_point t2
    cdef terrain_point t3
    #t1 = terrain_point
    #t2 = terrain_point
    #t3 = terrain_point
    #t1.position = cv.vector(*initial_tps[0])
    #t2.position = cv.vector(*initial_tps[1])
    #t3.position = cv.vector(*initial_tps[2])
    #t1 = terrain_point(*initial_tps[0])
    #t2 = terrain_point(*initial_tps[1])
    #t3 = terrain_point(*initial_tps[2])
    t1 = terrain_point(initial_tps[0])
    t2 = terrain_point(initial_tps[1])
    t3 = terrain_point(initial_tps[2])
    print 'making terrain with'
    print t1.position
    print t2.position
    print t3.position

    #locs_str = [t1._str,t2._str,t3._str]
    #locs = [t1,t2,t3]
    locs_str = []
    locs = []

    t1.neighbors = [t2,t3]
    t2.neighbors = [t3,t1]
    t3.neighbors = [t1,t2]
    init_verts = [t1,t2,t3]
    terra = terrain_triangle(init_verts,[],locs,locs_str)

    for sp in range(splits):
        vcnt = terra.count_vertices()
        terra.split(vcnt, pts_of_interest, poi_count, locs, locs_str)
        print 'ldat', len(locs), len(locs_str)
    terra.fix_bounds(locs, locs_str, sea_level)
    terra.fix_closest(pts_of_interest, locs, locs_str)
    terra.smooth(smooths, locs)
    print 'made terrain!'
    return terra, locs, locs_str






