import make_places.fundamental as fu
import mp_utils as mpu
import mp_bboxes as mpbb
import mp_terrain as mpt
from make_places.scenegraph import node
from make_places.primitives import arbitrary_primitive
import make_places.profiler as prf
import make_places.veg as veg

from math import sqrt
from copy import deepcopy as dcopy
import numpy as np
import random as rm
import pdb, time







terrain_numbers = [0]
def get_terrain_number______(repeat = False):
    if repeat: return str(terrain_numbers[0] - 1)
    num = terrain_numbers.pop(0)
    nex = num + 1
    terrain_numbers.append(nex)
    return str(num)

class terrain_point_____(fu.base):

    def __init__(self, *args, **kwargs):
        self._default_('position',[0,0,0],**kwargs)
        self._default_('neighbors',None,**kwargs)
        self._default_('weights',[1,1,1],**kwargs)
        self._str = str((self.position[0],self.position[1]))

    def __add__adfkjlkd(self, other):
        newpos = mpu.midpoint(self.position,other.position)
        newneighbors = self.neighbors + other.neighbors
        newweights = mpu.scale_vector(self.weights[:],other.weights)
        new = terrain_point(
            position = newpos, 
            neighbors = newneighbors, 
            weights = newweights)
        return new

    def relax(self,xstr = 1.0,ystr = 1.0,zstr = 1.0):
        #global howmany
        #if not len(self.neighbors) in [4,6,2]:
        #    howmany += 1
        #    print('howmany', howmany, len(self.neighbors), self.position)
        #    #pdb.set_trace()
        centroid = mpu.center_of_mass([v.position for v in self.neighbors])
        wx,wy,wz = self.weights[0],self.weights[1],self.weights[2]
        move = mpu.scale_vector(
            mpu.v1_v2(self.position,centroid), 
            [xstr*wx,ystr*wy,zstr*wz])
        mpu.translate_vector(self.position, move)
        return mpu.magnitude(move)

howmany = 0
class terrain_triangle____(fu.base):

    def __init__(self, *args, **kwargs):
        self._default_('verts',None,**kwargs)
        self._default_('children',None,**kwargs)
        self._default_('splits',0,**kwargs)
        self.set_center(*args, **kwargs)

    def __str__(self):
        _str = '\n'.join([' v'+str(dx)+' :\t'+\
            str(self.verts[dx].position) for dx in range(3)])
        return _str

    def set_center(self, *args, **kwargs):
        vposs = [v.position for v in self.verts]
        self._default_('center',mpu.center_of_mass(vposs),**kwargs)
        self.com_vects = [mpu.v1_v2(v,self.center) for v in vposs]
        self.com_vects = [mpu.normalize(v) for v in self.com_vects]

    def bisect_all(self, vcnt, controls, control_count):
        t1,t2,t3 = self.verts
        newt1 = bisect(t1,t2,vcnt,controls,control_count)
        newt2 = bisect(t2,t3,vcnt,controls,control_count)
        newt3 = bisect(t3,t1,vcnt,controls,control_count)
        newt1.neighbors.extend([newt2,newt3])
        newt2.neighbors.extend([newt3,newt1])
        newt3.neighbors.extend([newt1,newt2])
        return newt1,newt2,newt3

    def fix_topology(self, locs = {}, lockeys = None):
        if lockeys is None: tempkeys = locs.keys()
        else: tempkeys = lockeys
        if not self.children:
            vcnt = len(self.verts)
            for vdx in range(vcnt):
            #for vdx,v in enumerate(self.verts):
                v = self.verts[vdx]
                str_v = v._str
                if not str_v in tempkeys:
                    locs[str_v] = v
                    tempkeys.append(str_v)
                else:
                    keep = locs[str_v]
                    locnes = [n._str for n in keep.neighbors]
                    [keep.neighbors.append(n) for n in 
                        v.neighbors if not n._str in locnes]
                    self.verts[vdx] = keep
        else:
            for ch in self.children:
                locs, tempkeys = ch.fix_topology(
                    locs = locs, lockeys = tempkeys)
        return locs, tempkeys

    def split(self, vcnt, controls, control_count, locs = None):
        if locs is None: locs = {}
        self.splits += 1
        if self.children:
            #[ch.split(vcnt, controls) for ch in self.children[1:]]
            [ch.split(vcnt, controls, control_count, locs) for ch in self.children]
            #prf.measure_time('fix topology of terrain', 
            #            self.fix_topology, locs = locs)
        else:
            t1,t2,t3 = self.verts
            newt1,newt2,newt3 = self.bisect_all(
                    vcnt, controls, control_count)
            self.children = [
                terrain_triangle(verts = [newt1,newt2,newt3]), 
                terrain_triangle(verts = [t1,newt1,newt3]), 
                terrain_triangle(verts = [t2,newt2,newt1]), 
                terrain_triangle(verts = [t3,newt3,newt2])]
            #prf.measure_time('fix topology of terrain', 
            #            self.fix_topology, locs = locs)
            self.fix_topology(locs = locs)

    def inside(self, pt):
        corners = [mpu.translate_vector(v.position[:],tv) 
            for v,tv in zip(self.verts,self.com_vects)]
        return mpu.inside(pt, corners)

    def fix_closest(self, pts, locs):
        if not pts: return
        all_verts = locs.values()
        verts = [v.position for v in all_verts]
        vcnt = len(verts)
        for pt in pts:
            if not self.inside(pt): continue
            #nearest,neardis,neardex = mpu.find_closest_xy(pt,verts,vcnt)
            neardex = mpu.find_closest_xy(pt,verts,vcnt,5.0)
            nearest = verts[neardex]
            #neardis = mpu.distance_xy(nearest,pt)
            closest = all_verts[neardex]
            q2 = pt[2] - closest.position[2]
            closest.position[2] += q2
            newwt = [0.0,0.0,0.0]
            all_verts[neardex].weights = newwt

    def on_boundary(self, v):
        corners = self.verts
        s1 = [corners[0].position,corners[1].position]
        s2 = [corners[1].position,corners[2].position]
        s3 = [corners[2].position,corners[0].position]
        if mpu.pt_on_segment(v.position,s1): return True
        elif mpu.pt_on_segment(v.position,s2): return True
        elif mpu.pt_on_segment(v.position,s3): return True
        else: return False

    def fix_bounds(self, locs):
        all_verts = locs.values()
        bpts = 0
        self.boundary_points = []
        for uqvt in all_verts:
            if not self.inside(uqvt.position):
                uqvt.weights = [0,0,uqvt.weights[2]]
                self.boundary_points.append(uqvt)
                bpts += 1
        print('found',bpts,'boundary points in',len(all_verts),'points')

    def smooth(self, icnt, locs):
        tpoints = locs.values()
        movement = 0.0
        for idx in range(icnt):
            for tp in tpoints:
                movement += tp.relax()
        return movement

    def meshes(self, lod = False):
        if lod:
            lod_meshes = []

            #lod_meshes = [self.mesh(depth = 0,max_depth = self.splits-3)]

            #for ch in self.children:
            #    for subch in ch.children:
            #        lod_meshes.append(subch.mesh(depth = 0, 
            #                max_depth = self.splits - 3))

            for ch in self.children:
                for subch in ch.children:
                    for subsubch in subch.children:
                        lod_meshes.append(subsubch.mesh(
                            depth = 0, max_depth = self.splits - 3))
                            
            #for ch in self.children:
            #    for subch in ch.children:
            #        for subsubch in subch.children:
            #            for subsubsubch in subsubch.children:
            #                lod_meshes.append(subsubsubch.mesh(
            #                    depth = 0, max_depth = self.splits - 3))
            
            #lod_meshes = [
            #    ch.mesh(depth = 0, max_depth = self.splits - 3) 
            #        for ch in self.children]
            
            for lod in lod_meshes: lod.is_lod = True
            return lod_meshes
        else:
            meshes = []
            
            #for ch in self.children:
            #    for subch in ch.children:
            #        meshes.append(subch.mesh())

            for ch in self.children:
                for subch in ch.children:
                    for subsubch in subch.children:
                        meshes.append(subsubch.mesh())

            #for ch in self.children:
            #    for subch in ch.children:
            #        for subsubch in subch.children:
            #            for subsubsubch in subsubch.children:
            #                meshes.append(subsubsubch.mesh())
            
            #meshes = [ch.mesh() for ch in self.children]
            #meshes = [self.mesh()]
            for nonlod in meshes: nonlod.has_lod = True
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
            #newverts = [dcopy(f.position) for f in fdat]
            newverts = [f.position[:] for f in fdat]
            v1v2 = mpu.v1_v2(newverts[0],newverts[1])
            v1v3 = mpu.v1_v2(newverts[0],newverts[2])
            newnorml = [mpu.normalize(mpu.cross(v1v2,v1v3)) for f in fdat]
            newuvs = [[0,0],[1,0],[0,1]]
            verts.extend(newverts)
            nverts.extend(newnorml)
            uvs.extend(newuvs)
            faces.append([3*fdx+x for x in range(3)])
            face_materials.append(materials[0])
        xmlfile = '.'.join(['terrain',
            str(get_terrain_number()),'mesh','xml'])
        pwargs = {
            'position' : [0,0,0], 
            'verts' : verts, 
            'nverts' : nverts, 
            'uvs' : uvs, 
            'faces' : faces, 
            'materials' : materials, 
            'face_materials' : face_materials, 
            'xmlfilename' : xmlfile, 
            'force_normal_calc' : True, 
                }
        new = arbitrary_primitive(**pwargs)
        new.phys_materials = ['/common/pmat/Grass']
        #new.phys_materials = ['/common/pmat/Stone']
        new.modified = True
        return new

    def count_vertices(self):
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

def pick_zoff_____(dist,vcnt):
    zoff = (rm.random()*2.0 - 1.0)*(dist**(1.0/2.0))/(vcnt**(1.0/2.0))
    return zoff

def bisect____(tv1,tv2,vcnt,controls,control_count,
            tolerance = 25,big_tolerance = 250):
    if tv1 in tv2.neighbors and tv2 in tv1.neighbors:
        newpos = mpu.midpoint(tv1.position,tv2.position)
        if controls:
            #nearest,dist,ndex = mpu.find_closest_xy(
            ndex = mpu.find_closest_xy(
                newpos,controls,control_count,10.0)
            nearest = controls[ndex]
            dist = mpu.distance_xy(nearest,newpos)
            zdiff = nearest[2] - newpos[2]
            if dist < tolerance: zoff = zdiff
            elif dist < big_tolerance:
                zoff = pick_zoff(dist,vcnt)
                #zoff = rm.choice([-1,0,1])*(dist**(1.0/2.0)/vcnt)
            else: zoff = pick_zoff(250**2,vcnt)
            #else: zoff = rm.choice([-1,0,1])*(250.0/vcnt)
        else: zoff = pick_zoff(1000**2,vcnt)
        #else: zoff = rm.choice([-1,0,1])*(1000.0/vcnt)
        newpos[2] += zoff
        newtv = terrain_point(position = newpos)
        newtv.neighbors = [tv1,tv2]
        tv1.neighbors.append(newtv)
        tv2.neighbors.append(newtv)
        tv1.neighbors.remove(tv2)
        tv2.neighbors.remove(tv1)
    else: newtv = [n for n in tv1.neighbors if n in tv2.neighbors][0]
    return newtv

def filter____(pts,tri):
    good = []
    for pt in pts:
        if pt in good: continue
        elif mpu.inside(pt,tri): good.append(pt)
    return good

def make_terrain____(initial_tps,splits = 2,smooths = 25, 
        pts_of_interest = [[250,250,25],[500,250,-25]],locs = None):
    pts_of_interest = filter(pts_of_interest,initial_tps)
    #pts_of_interest = fu.uniq(pts_of_interest)
    poi_count = len(pts_of_interest)
    t1 = terrain_point(position = initial_tps[0])
    t2 = terrain_point(position = initial_tps[1])
    t3 = terrain_point(position = initial_tps[2])
    t1.neighbors = [t2,t3]
    t2.neighbors = [t3,t1]
    t3.neighbors = [t1,t2]
    init_verts = [t1,t2,t3]
    terra = terrain_triangle(verts = init_verts)
    if locs is None: locs = {}
    for ivt in init_verts: locs[ivt._str] = ivt
    for sp in range(splits):
        vcnt = terra.count_vertices()
        prf.measure_time('split terrain', terra.split, vcnt, 
            pts_of_interest, poi_count, locs)
    prf.measure_time('fix bounds', terra.fix_bounds, locs)
    prf.measure_time('fix closest', terra.fix_closest, pts_of_interest, locs)
    prf.measure_time('smooth terrain', terra.smooth, smooths, locs)
    return terra, locs

class terrain(node):
    def __init__(self, *args, **kwargs):
        kwargs['uv_scales'] = [0.1,0.1,0.1]
        self._default_('sea_level',0.0,**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)
        self._default_('grit_renderingdistance',500,**kwargs)
        self._default_('grit_lod_renderingdistance',2000,**kwargs)
        self._default_('pts_of_interest',[],**kwargs)
        self._default_('splits',3,**kwargs)
        self._default_('smooths',25,**kwargs)
        self._default_('region_bounds',[(0,1000),(0,1000)],**kwargs)
        self._default_('bboxes',[],**kwargs)
    
        rb = self.region_bounds
        t1 = [rb[0][0],rb[1][0],0]
        t2 = [rb[0][1],rb[1][0],0]
        t3 = [rb[0][0],rb[1][1],0]
        t4 = [rb[0][1],rb[1][1],0]

        use_mpt = False
    
        hexagonal = True
        #hexagonal = False
        if hexagonal:
            xrng,yrng = rb[0][1]-rb[0][0],rb[1][1]-rb[1][0]
            mrng = max([xrng,yrng])
            hrad = mrng
            center = mpu.center_of_mass([t1,t2,t3,t4])
            hverts = []
            for ang in [0,60,120,180,240,300]:
                pt = [hrad,0,0]
                mpu.rotate_z_coords([pt],fu.to_rad(ang))
                hverts.append(pt)
            mpu.translate_coords(hverts,center)
            hverts.insert(0,center)
            pieces = []
            ptlocs = []
            bounds = []
            for trdx in range(6):
                c2dx = trdx+1
                c3dx = trdx+2
                if c3dx == 7: c3dx = 1
                c1 = hverts[0]
                c2 = hverts[c2dx]
                c3 = hverts[c3dx]
                #terr,locs = make_terrain((c1,c2,c3),
                terr,locs,locs_str = mpt.make_terrain((c1,c2,c3),
                    self.splits,self.smooths,self.pts_of_interest,
                    self.sea_level)
                use_mpt = True
                #pdb.set_trace()
                #use_mpt = False
                #bounds.extend(terr.boundary_points)
                self.pts_of_interest.extend(
                    [v.position for v in terr.boundary_points])
                pieces.append(terr)
                ptlocs.append(locs)
        
            self.use_mpt = use_mpt
            self.primitives, self.lod_primitives = self.stitch(pieces,ptlocs)

        else:
            #r = 1000
            #t1 = [-r,0,0]
            #t3 = [r,0,0]
            #y = (4*r)/sqrt(3)
            #t2 = [0,-y,0]
            #fu.translate_coords([t1,t2,t3],[250,250,0])
            mpu.translate_coords([t1],[-50,-50,0])
            mpu.translate_coords([t2],[ 50,-50,0])
            mpu.translate_coords([t3],[ 50, 50,0])
            mpu.translate_coords([t4],[-50, 50,0])
            terr1,locs1,locs1str = mpt.make_terrain((t1,t2,t3),self.splits,
                        self.smooths,self.pts_of_interest,self.sea_level)
            terr2,locs2,locs2str = mpt.make_terrain((t2,t4,t3),self.splits,
                        self.smooths,self.pts_of_interest,self.sea_level)
            #terr1,locs1 = make_terrain((t1,t2,t3),self.splits,self.smooths,self.pts_of_interest)
            #terr2,locs2 = make_terrain((t2,t4,t3),self.splits,self.smooths,self.pts_of_interest)
            pieces = [terr1,terr2]
            ptlocs = [locs1,locs2]
            
            self.use_mpt = use_mpt
            self.use_mpt = True
            self.primitives, self.lod_primitives = self.stitch(pieces,ptlocs)

        #vegetate = True
        vegetate = False
        if vegetate:
            children = prf.measure_time('vegetate',self.vegetate,pieces)
            self.add_child(*children)
        node.__init__(self, *args, **kwargs)
        self.assign_material('grass2', propagate = False)
        #self.assign_material('ground')

    def vegetate(self, terras):
        vchildren = []
        bboxes = self.bboxes
        for ter in terras:
            fdat = ter.face_data()
            vcargs = []
            fcnt = len(fdat)
            for fdx in range(fcnt):
                if rm.choice([0,1,1,1]):
                    verts = [v.position for v in fdat[fdx]]
                    vegbox = mpbb.bbox(corners = verts)
                    if not mpbb.intersects(bboxes, vegbox):
                    #if not vegbox.intersects(bboxes, vegbox):
                        nvcarg = (verts,None,[fdx])
                        vcargs.append(nvcarg)

            # stitch the nvcargs together based on how contiguous they are
            dx = 0
            vccnt = len(vcargs)
            vcmax = 4
            fewer = []
            while dx < vccnt:
                left = vccnt - dx
                if left >= vcmax: vc_this_round = vcmax
                else: vc_this_round = left % vcmax
                relev = vcargs[dx:dx+vc_this_round]
                reverts = [r[0] for r in relev]
                refaces = range(vc_this_round)
                fewer.append((reverts,[],refaces))
                dx += vc_this_round

            for varg in fewer:
                vchild = veg.vegetate(*varg)
                vchildren.append(vchild)

        return vchildren

    def stitch(self, pieces, locs):
        if len(pieces) == 6:
            p1,p2,p3,p4,p5,p6 = pieces
            pairs = [(p1,p2),(p2,p3),(p3,p4),(p4,p5),(p5,p6),(p6,p1)]
        elif len(pieces) == 2:
            p1,p2 = pieces
            pairs = [(p1,p2),(p2,p1)]

        all_pieces = []
        for p1,p2 in pairs:
            print('stitching')#,p1,p2)
            b1,b2 = p1.boundary_points,p2.boundary_points
            for bp1 in b1:
                for bp2 in b2:
                    if bp1._str == bp2._str:
                        if not self.use_mpt:
                            midz = (bp1.position[2]+bp2.position[2])/2.0
                            bp1.position[2] = midz
                            bp2.position[2] = midz
                            bp1.weights[2] = 0.0
                            bp2.weights[2] = 0.0
                        else:
                            midz = (bp1.position.z+bp2.position.z)/2.0
                            bp1.position.z = midz
                            bp2.position.z = midz
                            bp1.weights.z = 0.0
                            bp2.weights.z = 0.0
            pieces = [p1,p2]
            [pc.smooth(5,lc) for pc,lc in zip(pieces,locs)]
            all_pieces.append(pieces[0])

        meshpieces = []
        lod_meshpieces = []
        [meshpieces.extend(p.meshes()) for p in all_pieces]
        [lod_meshpieces.extend(p.meshes(lod = True)) for p in all_pieces]

        if self.use_mpt:
            meshpieces = [arbitrary_primitive(**pwg) for pwg in meshpieces]
            lod_meshpieces = [arbitrary_primitive(**lpwg) for lpwg in lod_meshpieces]

        return meshpieces, lod_meshpieces
    





