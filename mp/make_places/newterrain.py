
import mp_vector as cv
import mp_utils as mpu
import mp_bboxes as mpbb
import make_places.primitives as pr
import make_places.scenegraph as sg
import make_places.blueprints as mbp

import matplotlib.pyplot as plt
import numpy as np
import random as rm
from math import sqrt
import time
import pdb

# this is a reimplementation of terrain generation
#
# use a generator of the sierpenski gasket on a unit square to generate new
# triangles
#
# take as input:
#   a set of fixed pts to fit terrain to
#   a set of polygons to cut in the terrain as holes
#   a set of pts to determine where terrain should be made
#       should generate mesh to provide terrain up to a certain radius
#       from the line generated by this set of pts
#   a target length for the length of an edge of a polygon in the mesh
#       unit gaskets are scaled so that edge distance is near length (!=)
#   a target length for the edge of a piece of mesh, which represents one
#       object in grit
#   should generate lods which are properly stitched, and non lods
#       should return the kwargs to make the primitives



def some_input():
    ls = [5, 10, 15]
    ws = [2, 4, 6, 8]
    base = cv.vector(50,50,0)
    fixed_pts = []
    for sq in range(5):
        pt = base.copy().translate_x(sq*25).translate_y(sq*10)
        l,w = rm.choice(ls),rm.choice(ws)
        corners = mpu.make_corners(pt,l,w,0)
        fixed_pts.extend(corners)

    hole_corners = [pt.copy() for pt in fixed_pts]

    region_pts = []
    for lpt in range(5):
        pt = cv.zero().translate_x(lpt*100).translate_y((4*lpt-lpt**2)*100)
        region_pts.append(pt)
    region_pts.append(cv.vector(200,-100,0))
    for rpt in region_pts: print rpt

    target_polygon_edge_length = 10
    target_primitive_edge_length = 200

    theinput = {
        'fixed_pts':fixed_pts, 
        'hole_pts':hole_corners, 
        'region_pts':region_pts, 
        'polygon_edge_length':target_polygon_edge_length, 
        'primitive_edge_length':target_primitive_edge_length, 
            }
    return theinput





def find_extremes_y(pts):
    lo = pts[0]
    hi = pts[0]
    for pt in pts[1:]:
        if pt.y < lo.y: lo = pt
        if pt.y > hi.y: hi = pt
    return lo,hi

def find_extremes_x(pts):
    lo = pts[0]
    hi = pts[0]
    for pt in pts[1:]:
        if pt.x < lo.x: lo = pt
        if pt.x > hi.x: hi = pt
    return lo,hi

def sweep_search(pts,center,tangent = None):
    # this will behave oddly when `which` would
    #  be a colinear set
    offset = center.copy().flip()
    cv.translate_coords(pts,offset)
    if not tangent is None:
        tangent_rot = cv.angle_from_xaxis_xy(tangent)
        cv.rotate_z_coords(pts,-tangent_rot)
    which = center
    pang = 2*np.pi
    pcnt = len(pts)
    for adx in range(pcnt):
        pt = pts[adx]
        if pt is center: continue
        tpang = cv.angle_from_xaxis_xy(pt)
        if tpang < pang:
            pang = tpang
            which = pt
    if not tangent is None:
        cv.rotate_z_coords(pts,tangent_rot)
    cv.translate_coords(pts,offset.flip())
    return which

def pts_to_convex_xy(pts):
    # return the corners of the polygon, a subset of pts
    # it could be that pts is all one point or is colinear
    new = find_extremes_x(pts)[1]
    tang = None
    shape = []
    while not new in shape:
        shape.append(new)
        if len(shape) > 1:
            tang = cv.v1_v2(shape[-2],shape[-1])
        new = sweep_search(pts,new,tang)
    return shape

def inflate(convex, radius):
    enorms = mpbb.get_norms(convex)
    for cdx in range(len(convex)):
        lead = enorms[cdx]
        rear = enorms[cdx-1]
        norm = cv.midpoint(lead,rear).normalize()
        convex[cdx].translate(norm.scale_u(radius))
    return convex



def region_pts_to_boundary(rpts, radius = 100):
    convex = pts_to_convex_xy(rpts)
    inflate(convex,radius)
    return convex

def triangle_cover(boundary,side_length):
    side_length = float(side_length)
    perp_side_length = sqrt(3)*side_length/2.0
    bproj_x = mpbb.project(boundary,cv.xhat)
    bproj_y = mpbb.project(boundary,cv.yhat)
    xrng = bproj_x.y - bproj_x.x
    yrng = bproj_y.y - bproj_y.x
    total_offset = cv.vector(
        bproj_x.x - side_length,
        bproj_y.x - perp_side_length,0)

    xtcnt = int(xrng/side_length+0.5) + 3
    ytcnt = int(yrng/perp_side_length+0.5) + 3

    broffset = cv.vector(side_length/2.0,perp_side_length,0)
    corners = []
    xs = [x*side_length for x in range(xtcnt)]
    bottomrow = [cv.vector(x,0,0).translate(total_offset) for x in xs]
    toprow = [b.copy().translate(broffset) for b in bottomrow]
    
    def next_rows(bottom,top,even):
        sign = -1 if even else 1
        broffset.translate_x(sign*side_length)
        newtop = [t.copy().translate(broffset) for t in top]
        newbottom = [t.copy() for t in top]
        return newbottom,newtop

    for rdx in range(ytcnt):
        even = rdx % 2 == 0

        for vdx in range(1,len(bottomrow)):
            c1 = bottomrow[vdx-1]
            c2 = bottomrow[vdx]
            c3 = toprow[vdx-1]
            c4 = toprow[vdx]
            if even:
                corners.append([c1,c2,c3])
                corners.append([c3,c2,c4])
            else:
                corners.append([c1,c2,c4])
                corners.append([c3,c1,c4])

        if not rdx == ytcnt - 1:
            bottomrow,toprow = next_rows(bottomrow,toprow,even)
    
    return corners

def intersects_xy(polys,bounds):
    keep = []
    bounds = inflate([b.copy() for b in bounds],2)
    bndbox = mpbb.bbox(corners = bounds)
    for poly in polys:
        plybox = mpbb.bbox(corners = poly)
        if mpbb.intersects([plybox],[bndbox]):
            keep.append(poly)
    return keep

def relax(tpt):
    if tpt.neighbors:
        centroidz = np.mean([v.position.z for v in tpt.neighbors])
        move = (centroidz - tpt.position.z) * tpt.weights.z
        tpt.position.translate_z(move)

class terrain_point:
    def __init__(self,position):
        self.position = position
        self.weights = cv.one().scale_u(0.05)
        self.neighbors = []
        self.owners = []
        self.owner_count = 0
        self.boundary = False
        self.hole_boundary = False
        self.is_corner = False
    
    def set_neighbor_count(self):
        if self.boundary:
            if self.owner_count == 1:
                self.neighbor_count = 4
            elif self.is_corner == True:
                self.neighbor_count = 6
            else: self.neighbor_count = 6
        else: self.neighbor_count = 6

    def calculate_smooth_normal(self):
        spos = self.position
        nposs = self.neighbor_positions()
        nnorms = []
        #for ndx in range(self.neighbor_count):
        for ndx in range(len(self.neighbors)):
            n1 = self.neighbors[ndx-1].position
            n2 = self.neighbors[ndx].position

            #if near_xy(n1,n2):pdb.set_trace()

            vn1 = cv.v1_v2(spos,n1)
            vn2 = cv.v1_v2(spos,n2)
            nnorm = vn1.cross(vn2)
            if nnorm.z < 0.0: nnorm.flip().normalize()
            nnorms.append(nnorm)

        ncom = cv.center_of_mass(nnorms)
        ncom.normalize()
        return ncom

    def neighbor_positions(self):
        return [n.position for n in self.neighbors]

    def reneighbors(self, pts, dthresh = 50):
        renew = []
        dt2 = dthresh**2
        spos = self.position

        target_ncnt = self.neighbor_count
        for npt in self.neighbors:
            tpos = npt.position
            ndist = cv.distance_xy(tpos,spos)
            if ndist < dthresh:
                renew.append(npt)

        rdx = len(renew)
        if rdx < target_ncnt:
            for tp in pts:
                tpos = tp.position
                dx2 = (tpos.x - spos.x)**2
                if dx2 > dt2: continue
                dy2 = (tpos.y - spos.y)**2
                if dy2 > dt2: continue
                if tp in renew: continue
                if tp is self: continue
                if dx2 + dy2 < dt2:
                    renew.append(tp)
                    rdx += 1
                    if rdx == target_ncnt: break
        #else: print 'already reneighbored'
        self.neighbors = renew

def near_xy(p1,p2):
    dx = (p2.x - p1.x)
    dx2 = dx*dx
    if dx2 > 0.5: return False
    dy = (p2.y - p1.y)
    dy2 = dy*dy
    if dy2 > 0.5: return False
    return True

def new_neighbors(tp1,tp2):
    # fix the first guy with the second guys neighbors added
    for n2 in tp2.neighbors:
        found = None
        for n1 in tp1.neighbors:
            if near_xy(n1.position,n2.position):
                found = n1
                #print 'found neighbor preexisting'
                break
        if found is None:
            #print 'didnt find neighbor so added'
            tp1.neighbors.append(n2)

class terrain_triangle:
    def __init__(self,parent,tpts):
        self.parent = parent
        self.local_points = tpts
        self.children = []
        self.set_bbox()

    def set_bbox(self):
        tpts = self.local_points
        tposs = []
        for t in tpts:
                tpos = t.position
                if not tpos in tposs:
                    tposs.append(tpos)
        #tposs = [t.position for t in tpts]
        if len(tpts) > 3:
            tposs = mpu.pts_to_convex_xy(tposs)
        if len(tposs) < 3: self.bbox = None
        else: self.bbox = mpbb.bbox(corners = tposs)

    '''#
    def set_bbox(self):
        tpts = self.local_points
        if len(tpts) > 3:
            tposs = [t.position for t in tpts]
            tposs = mpu.pts_to_convex_xy(tposs)
        else: tposs = [t.position for t in tpts]
        if len(tposs) < 3: self.bbox = None
        else:
            for p in tposs: print p
            self.bbox = mpbb.bbox(corners = tposs)
    '''#

    def split(self, isolated = False):
        if self.children:
            [ch.split(isolated) for ch in self.children]
        else:
            t1,t2,t3 = self.local_points

            nt1 = terrain_point(cv.midpoint(t1.position,t2.position))
            nt2 = terrain_point(cv.midpoint(t2.position,t3.position))
            nt3 = terrain_point(cv.midpoint(t3.position,t1.position))
            nt1.neighbors.append(nt2)
            nt1.neighbors.append(nt3)
            nt2.neighbors.append(nt3)
            nt2.neighbors.append(nt1)
            nt3.neighbors.append(nt1)
            nt3.neighbors.append(nt2)

            nt1 = self.parent.add_point(nt1, certainly_new = isolated)
            nt2 = self.parent.add_point(nt2, certainly_new = isolated)
            nt3 = self.parent.add_point(nt3, certainly_new = isolated)

            self.children = [
                terrain_triangle(self.parent,[nt1,nt2,nt3]), 
                terrain_triangle(self.parent,[ t1,nt1,nt3]), 
                terrain_triangle(self.parent,[ t2,nt2,nt1]), 
                terrain_triangle(self.parent,[ t3,nt3,nt2])]
    
    def cut_self(self,in1,in2,in3,bboxes):

        '''#
        lposs = [tp.position for tp in self.local_points]
        mbp.plot(lposs,marker = '*',color = 'green')
        for mc in must_check:
            mbp.plot(mc.corners,marker = 's',color = 'red')
        plt.show()
        '''#

        ins = [in1,in2,in3]
        incnt = ins.count(True)
        if incnt == 3:
            for tpt in self.local_points:
                if self in tpt.owners:
                    tpt.owners.remove(self)
                for n in tpt.neighbors:
                    if tpt in n.neighbors:
                        n.neighbors.remove(tpt)
                        n.hole_boundary = True
            self.local_points = []
        elif incnt == 2:
            for tpt in self.local_points:
                if self in tpt.owners:
                    tpt.owners.remove(self)
                for n in tpt.neighbors:
                    if tpt in n.neighbors:
                        n.neighbors.remove(tpt)
                        n.hole_boundary = True
            self.local_points = []

            '''#
            outwhich = ins.index(False)
            shared = self.local_points[outwhich]

            # find intersection from shared and the other 2 local points
            fanmembers = self.local_points[:]
            fanmembers.pop(outwhich)
            for fm in fanmembers:
                if not fm is shared:
                    etang = cv.v1_v2(fm.position,shared.position)
                    fm.position.translate(etang.scale_u(0.9))
            fanmembers.insert(0,shared)

            for fm in fanmembers:
                for ow in fm.owners:
                    ow.set_bbox()

            self.local_points = []
            tcnt = len(fanmembers) - 2
            for trdx in range(tcnt):
                c2dx = trdx+1
                c3dx = trdx+2
                if c3dx == tcnt + 1: c3dx = 1
                c1 = fanmembers[0]
                c2 = fanmembers[c2dx]
                c3 = fanmembers[c3dx]
                c1.weights = cv.zero()
                c2.weights = cv.zero()
                c3.weights = cv.zero()
                self.local_points.extend([c1,c2,c3])
            self.set_bbox()
            # for any vertex whose position changes, recalc the bbox for
            # that vertex's owner triangle
            '''#
        elif incnt == 1:
            for tpt in self.local_points:
                if self in tpt.owners:
                    tpt.owners.remove(self)
                for n in tpt.neighbors:
                    if tpt in n.neighbors:
                        n.neighbors.remove(tpt)
                        n.hole_boundary = True
            self.local_points = []

    def cut_holes(self, holes):
        bb = self.bbox
        must_check = []
        for ho in holes:
            if mpbb.intersect_xy(bb,ho):
                must_check.append(ho)
        
        if must_check:
            if self.children:
                for ch in self.children:
                    ch.cut_holes(holes)
            else:
                lp1,lp2,lp3 = self.local_points

                # must_check is now a list of bboxes
                inside1 = False
                inside2 = False
                inside3 = False
                for mc in must_check:
                    p1in = cv.inside(lp1.position,mc.corners)
                    if p1in: inside1 = True
                    p2in = cv.inside(lp2.position,mc.corners)
                    if p2in: inside2 = True
                    p3in = cv.inside(lp3.position,mc.corners)
                    if p3in: inside3 = True
                self.cut_self(inside1,inside2,inside3,must_check)


    def face_data(self, depth = None, max_depth = None):
        data = []
        if not depth is None:
            if depth == max_depth:
                data.append(self.local_points)
                return data
            else: depth += 1
        if self.children:
            [data.extend(ch.face_data(depth,max_depth)) 
                for ch in self.children]
        else: data.append(self.local_points)
        return data

terrain_number = 0
class terrain_piece:
    def filter_fixed(self,fixed):
        relevant = []
        for fx in fixed:
            if cv.inside(fx,self.corners):
                relevant.append(fx)
        return relevant

    def __init__(self,verts,fixed_pts,
            primitive_edge_length,poly_edge_length,
            global_points,global_bounding_points):
        self.set_corners(verts)
        self.fixed_pts = self.filter_fixed(fixed_pts)
        self.fixed_count = len(self.fixed_pts)
        self.children = []
        self.splits = 0
        self.parent = None
        self.global_points = global_points
        self.global_bounding_points = global_bounding_points
        self.bounding_points = []
        self.local_points = []
        self.poly_size = poly_edge_length
        self.primitive_size = primitive_edge_length

    def set_bbox(self):
        tpts = self.local_points
        tposs = []
        for t in tpts:
                tpos = t.position
                if not tpos in tposs:
                    tposs.append(tpos)
        #tposs = [t.position for t in tpts]
        if len(tpts) > 3:
            tposs = mpu.pts_to_convex_xy(tposs)
        if len(tposs) < 3: self.bbox = None
        else: self.bbox = mpbb.bbox(corners = tposs)

    def get_terrain_number(self):
        global terrain_number
        num = str(terrain_number)
        terrain_number += 1
        return num

    def count_vertices(self):
        #return 3**(self.splits+1)
        return len(self.local_points)

    def set_corners(self, verts):
        self.center = cv.center_of_mass(verts)
        self.corners = []
        self.tight_corners = []
        for v in verts:
            self.corners.append(v)
            cvt = cv.v1_v2(v,self.center).normalize()
            self.tight_corners.append(v.copy().translate(cvt))

    def on_boundary(self, pos):
        if not cv.inside(pos,self.tight_corners): return True
        else: return False

    def pick_zoff(self, tpt, zero_tolerance = 20, partial_tolerance = 200):
        def free_find():
            mdist = cv.distance(
                tpt.neighbors[0].position,
                tpt.neighbors[1].position)/2.0
            return offset(mdist)

        def offset(dist, powa = 0.25):
            vcnt = self.count_vertices()
            rand = rm.random()*2.0 - 1.0
            zoff = rand*dist/((vcnt + 1.0)**powa)
            return zoff

        if not self.fixed_pts: zoff = free_find()
        else:
            ndex = cv.find_closest_xy(tpt.position,
                self.fixed_pts,self.fixed_count,2.0)
            nearest = self.fixed_pts[ndex]
            dist = cv.distance_xy(nearest,tpt.position)
            zdiff = nearest.z - tpt.position.z
            if dist < zero_tolerance:
                zoff = zdiff
                tpt.weights.z = 0
            elif dist < partial_tolerance:
                zoff = zdiff * (1 - (dist/(partial_tolerance)))# * offset(1)
            else: zoff = free_find()
        return zoff

    def add_point(self, tpt, certainly_new = False):
        if self.on_boundary(tpt.position):
            if not certainly_new:
                for gpt in self.global_bounding_points:
                    if near_xy(tpt.position,gpt.position):
                        if self.splits == self.final_splits:
                            new_neighbors(gpt,tpt)
                        self.local_points.append(gpt)
                        self.bounding_points.append(gpt)
                        gpt.owners.append(self)
                        gpt.owner_count += 1
                        return gpt

            tpt.position.z += self.pick_zoff(tpt)

            self.global_points.append(tpt)
            self.global_bounding_points.append(tpt)
            self.local_points.append(tpt)
            self.bounding_points.append(tpt)
            tpt.owners.append(self)
            tpt.owner_count += 1
            tpt.boundary = True
            return tpt
        else:
            #if not certainly_new:
            for lpt in self.local_points:
                if near_xy(tpt.position,lpt.position):
                    if self.splits == self.final_splits:
                        new_neighbors(lpt,tpt)
                    self.local_points.append(lpt)
                    lpt.owners.append(self)
                    lpt.owner_count += 1
                    return lpt

            tpt.position.z += self.pick_zoff(tpt)

            self.global_points.append(tpt)
            self.local_points.append(tpt)
            tpt.owners.append(self)
            tpt.owner_count += 1
            return tpt

    def split(self, isolated = False):
        if self.children:
            [ch.split(isolated) for ch in self.children]
        else:
            t1,t2,t3 = self.local_points

            nt1 = terrain_point(cv.midpoint(t1.position,t2.position))
            nt2 = terrain_point(cv.midpoint(t2.position,t3.position))
            nt3 = terrain_point(cv.midpoint(t3.position,t1.position))

            nt1.neighbors.append(nt2)
            nt1.neighbors.append(nt3)
            nt2.neighbors.append(nt3)
            nt2.neighbors.append(nt1)
            nt3.neighbors.append(nt1)
            nt3.neighbors.append(nt2)

            nt1 = self.add_point(nt1, certainly_new = isolated)
            nt2 = self.add_point(nt2, certainly_new = isolated)
            nt3 = self.add_point(nt3, certainly_new = isolated)

            self.children = [
                terrain_triangle(self,[nt1,nt2,nt3]), 
                terrain_triangle(self,[ t1,nt1,nt3]), 
                terrain_triangle(self,[ t2,nt2,nt1]), 
                terrain_triangle(self,[ t3,nt3,nt2])]

    def smooth(self, icnt):
        print 'smoothing verts', icnt, 'times'
        for idx in range(icnt):
            for tp in self.local_points:
                relax(tp)

    def set_local_points(self):
        nt1 = terrain_point(self.corners[0])
        nt2 = terrain_point(self.corners[1])
        nt3 = terrain_point(self.corners[2])

        nt1.neighbors.append(nt2)
        nt1.neighbors.append(nt3)
        nt2.neighbors.append(nt3)
        nt2.neighbors.append(nt1)
        nt3.neighbors.append(nt1)
        nt3.neighbors.append(nt2)
        
        nt1 = self.add_point(nt1)
        nt2 = self.add_point(nt2)
        nt3 = self.add_point(nt3)

        nt1.is_corner = True
        nt2.is_corner = True
        nt3.is_corner = True

    def subdivide(self, splits = None, max_splits = 20, isolated = False):
        if splits is None:
            side_length = self.primitive_size
            poly_length = self.poly_size
            poly_table = [side_length/(2.0**n) for n in range(max_splits)]
            for dx in range(max_splits):
                if poly_length > poly_table[dx]:
                    splits = dx
                    break

        self.final_splits = splits
        self.set_local_points()
        for sdx in range(splits):
            self.splits += 1
            self.split(isolated)

    def cut_holes(self, holes):
        for ch in self.children:
            ch.cut_holes(holes)

    def mesh(self, lod = False):
        verts = []
        nverts = []
        uvs = []
        faces = []
        face_materials = []
        materials = ['grass2']

        depth = None
        max_depth = None
        if lod:
            depth = 0
            max_depth = self.splits - 1
        data = self.face_data(depth, max_depth)

        bump = 0
        for fdx,fdat in enumerate(data):
            if not fdat: bump += 1
            #if len(fdat) == 3:
            if len(fdat) > 0:
                newverts = [f.position.copy() for f in fdat]
                newnorml = [f.calculate_smooth_normal() for f in fdat]
                newuvs = [cv.vector2d(0,0),cv.vector2d(1,0),cv.vector2d(0,1)]
                verts.extend(newverts)
                nverts.extend(newnorml)

                newfcnt = len(fdat)/3
                if not newfcnt == 1: pdb.set_trace()
                for d in range(newfcnt):
                    uvs.extend([u.copy() for u in newuvs])
                    if d > 0: bump += 1
                    faces.append([3*(fdx-bump)+x for x in range(3)])
                    face_materials.append(0)

                #faces.append([3*(fdx-bump)+x for x in range(3)])
                #face_materials.append(0)
        
        xmlfile = '.'.join(['terrain',
            self.get_terrain_number(),'mesh','xml'])
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
            'force_normal_calc' : False, 
            'prevent_normal_calc' : True, 
            'smooth_normals' : True, 
            'is_lod' : lod, 
            'has_lod' : not lod, 
                }
        mesh = pr.arbitrary_primitive(**pwargs)
        return mesh

    def face_data(self, depth = None, max_depth = None):
        data = []
        if not depth is None:
            if depth == max_depth:
                data.append(self.local_points)
                return data
            else: depth += 1
        if self.children:
            [data.extend(ch.face_data(depth,max_depth)) 
                for ch in self.children]
        else: data.append(self.local_points)
        return data

def test():
    someinput = some_input()
    boundary = region_pts_to_boundary(someinput['region_pts'])
    fixed = someinput['fixed_pts']

    mesh_corners = triangle_cover(boundary,someinput['primitive_edge_length'])
    mesh_corners = intersects_xy(mesh_corners,boundary)

    map_curves = [(mc,'green',None,0.75) for mc in mesh_corners]
    map_curves.append((boundary,'black','o',1.5))
    make_map(map_curves)

def plot_tpts(tpts):
    curves = []
    for tp in tpts:
        if tp.is_corner: col = 'red'
        elif tp.boundary: col = 'green'
        elif tp.hole_boundary: col = 'red'
        else: col = 'blue'
        if tp.neighbor_count == 4: mark = 'o'
        elif tp.neighbor_count == 6: mark = 'x'
        else: mark = '+'
        curves.append(([tp.position],col,mark,1.0))
    make_map(curves)

def make_map(curves):
    def add_curve(x,y,curd):
        for c in curd:
            x.append(c.x)
            y.append(c.y)
        x.append(curd[0].x)
        y.append(curd[0].y)
        return x,y

    for cur in curves:
        curd = cur[0]
        colr = cur[1]
        mark = cur[2]
        linw = cur[3]
        x,y = [],[]
        if hasattr(curd[0],'__iter__'):
            for subcurd in curd:
                x,y = add_curve(x,y,subcurd)
                plt.plot(x,y,color = colr,
                    marker = mark,linewidth = linw)
        else:
            x,y = add_curve(x,y,curd)
            plt.plot(x,y,color = colr,
                marker = mark,linewidth = linw)

    plt.show()

def make_terrain(**someinput):
    poly_length = someinput['polygon_edge_length']
    prim_length = someinput['primitive_edge_length']

    boundary = region_pts_to_boundary(someinput['region_pts'])
    fixed = someinput['fixed_pts']

    mesh_corners = triangle_cover(boundary,someinput['primitive_edge_length'])
    mesh_corners = intersects_xy(mesh_corners,boundary)

    global_points = []
    global_bounding_points = []
    pieces = [terrain_piece(
        corners,fixed,prim_length,poly_length,
        global_points,global_bounding_points) 
            for corners in mesh_corners]

    tpiececount = len(pieces)
    for pdx in range(tpiececount):
        p = pieces[pdx]
        p.subdivide(isolated = False)
        print 'terrain piece',pdx + 1,'of',tpiececount,'split',p.splits,'times'
    '''#
    for pdx in range(tpiececount):
        if pdx % 2 == 0:
            p = pieces[pdx]
            p.subdivide(isolated = True)
            print 'terrain piece',pdx + 1,'of',tpiececount,'split',p.splits,'times'
    for pdx in range(tpiececount):
        if pdx % 2 != 0:
            p = pieces[pdx]
            p.subdivide(isolated = False)
            print 'terrain piece',pdx + 1,'of',tpiececount,'split',p.splits,'times'
    '''#

    reneightime = time.time()
    print 'reneighboring...'
    for pt in global_points:
        pt.set_neighbor_count()
        for pwn in pt.owners:
            ownerpts = pwn.local_points
            pt.reneighbors(ownerpts,poly_length+1)
    print 'reneighbored!', time.time() - reneightime

    holes = []
    for hdx in range(len(someinput['hole_pts'])):
        hpts = someinput['hole_pts'][hdx]
        holes.append(mpbb.bbox(corners = hpts))

    #for pdx in range(tpiececount):
    #    p = pieces[pdx]
    #    p.cut_holes(holes)
    #    print 'terrain piece',pdx + 1,'of',tpiececount,'cut holes'

    reneightime = time.time()
    print 'reneighboring...'
    for pt in global_points:
        pt.set_neighbor_count()
        for pwn in pt.owners:
            ownerpts = pwn.local_points
            pt.reneighbors(ownerpts,poly_length+1)
    print 'reneighbored!', time.time() - reneightime

    #plot_tpts(global_points)
    #plot_tpts(global_bounding_points)
    
    #smooths = 0
    smooths = 100
    for sdx in range(smooths):
        print 'smoothing global points', sdx
        #for pt in global_bounding_points:
        for pt in global_points:
            relax(pt)

    tprimitives = [p.mesh() for p in pieces]
    tlodprimitives = [p.mesh(lod = True) for p in pieces]
    
    terrain_node = sg.node(
        grit_renderingdistance = prim_length, 
        grit_lod_renderingdistance = 5000, 
        primitives = tprimitives, 
        lod_primitives = tlodprimitives)
    return terrain_node

if __name__ == '__main__':
    test()












