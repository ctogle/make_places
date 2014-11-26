from make_places.scenegraph import node
import make_places.fundamental as fu
import mp_utils as mpu
import mp_bboxes as mpbb
import make_places.primitives as pr
from make_places.stairs import ramp
from make_places.stairs import shaft
from make_places.floors import floor
from make_places.walls import wall
from make_places.walls import perimeter

import random as rm
import os

import pdb

_story_count_ = 0
class story(node):

    def get_name(self):
        global _story_count_
        nam = 'story ' + str(_story_count_)
        _story_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        self.floor_number = args[0]
        self._default_('name',self.get_name(),**kwargs)
        self._default_('add_ceiling',True,**kwargs)
        self._default_('shafts',[],**kwargs)
        self._default_('consumes_children',True,**kwargs)
        #self._default_('consumes_children',False,**kwargs)
        self._default_('grit_renderingdistance',250.0,**kwargs)
        self._default_('grit_lod_renderingdistance',1000.0,**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self._default_('uv_tform',self.def_uv_tform(*args,**kwargs),**kwargs)
        self._default_('length',20.0,**kwargs)
        self._default_('width',20.0,**kwargs)
        self._default_('floor_height',0.5,**kwargs)
        self._default_('ceiling_height',0.5,**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        self._default_('wall_height',4.0,**kwargs)
        #self._default_('ext_gaped',False,**kwargs)
        self._default_('ext_gaped',True,**kwargs)
        self._default_('rid_top_bottom_walls',True,**kwargs)
        children = self.make_children(*args, **kwargs)
        self.add_child(*children)
        self.lod_primitives = self.make_lod(*args,**kwargs)
        node.__init__(self, *args, **kwargs)

    def make_lod(self, *args, **kwargs):
        lod = pr.ucube()
        l,w = self.length,self.width
        h = self.wall_height + self.floor_height + self.ceiling_height
        #h = self.wall_height + self.floor_height
        fl = self.floor_[0]
        zrot = 0
        #pos = fl.tform.position[0]
        pos = fl.tform.position
        #pos[2] -= self.floor_height
        lod.scale([l,w,h])
        lod.rotate_z(zrot)
        lod.translate(pos)
        #lod.is_lod = True

        self.tform.children[0].owner.primitives[0].has_lod = True

        return [lod]

    def make_children(self, *args, **kwargs):
        floor_ = self.make_floor(*args, **kwargs)
        if self.add_ceiling:ceiling = self.make_ceiling(*args, **kwargs)
        else:ceiling = []
        ext_walls = self.make_exterior_walls(*args, **kwargs)
        #int_walls = self.make_interior_walls(*args, **kwargs)
        return floor_ + ceiling + ext_walls #+ int_walls

    def make_floor(self, *args, **kwargs):
        flleng = self.length
        flwidt = self.width
        gaps = []
        if self.floor_number > -1:
            for sh in self.shafts:
                gaps.extend(sh.floor_gaps)
        flpos = [0,0,0]
        flargs = {
            'uv_parent':self, 
            'position':flpos, 
            'length':flleng, 
            'width':flwidt, 
            'gaps':gaps,
            'height':self.floor_height, 
                }
        floor_ = floor(**flargs)
        #for flp in floor_.primitives:
        #    flp.remove_face('bottom')
        self.floor_ = [floor_]
        return [floor_]

    def make_ceiling(self, *args, **kwargs):
        flleng = self.length
        flwidt = self.width
        gaps = []
        if self.floor_number > -2:
            for sh in self.shafts:
                gaps.extend(sh.floor_gaps)
        czpos = self.wall_height+self.ceiling_height#+self.floor_height
        flpos = [0,0,czpos]
        flargs = {
            'uv_parent':self, 
            'position':flpos, 
            'length':flleng, 
            'width':flwidt, 
            'gaps':gaps,
            'floor_height':self.ceiling_height, 
                }
        ceil = floor(**flargs)
        #for flp in ceil.primitives:
        #    flp.remove_face('top')
        self.ceiling = [ceil]
        return [ceil]

    def make_exterior_walls(self, *args, **kwargs):
        #floor_pieces = kwargs['floor']
        floor_pieces = self.floor_
        rid = self.rid_top_bottom_walls
        peargs = [{
            #'parent':fl, 
            #'parent':self, 
            #'uv_parent':fl, 
            'rid_top_bottom_walls':rid, 
            'floor':fl, 
            'wall_offset':-self.wall_width/2.0, 
            'gaped':self.ext_gaped, 
            'wall_height':self.wall_height, 
            'wall_width':self.wall_width, 
            'wall_offset':-self.wall_width/2.0, 
                } for fl in floor_pieces]
        perims = [perimeter(**pe) for pe in peargs]
        return perims

    def make_interior_walls(self, *args, **kwargs):
        comps = []
        kwargs['gaped'] = False
        for sh in self.shafts:
            topo = sh.topology[self.floor_number]
            entry = topo[0]
            shwg = sh.wall_gaps
            kwargs['wall_gaps'] = [
                shwg[0] if entry is 'front' else [],
                shwg[1] if entry is 'right' else [],
                shwg[2] if entry is 'back' else [],
                shwg[3] if entry is 'left' else [],
                ]
            shcorns = sh.corners
            kwargs['corners'] = shcorns
            kwargs['parent'] = self
            comps.append(perimeter(**kwargs))
        return comps

class basement(story):

    def __init__(self, *args, **kwargs):
        self._default_('consumes_children',True,**kwargs)
        self._default_('wall_height',8,**kwargs)
        self._default_('ext_gaped',False,**kwargs)
        story.__init__(self, *args, **kwargs)

class roofwedge(pr.arbitrary_primitive):
    roofxml = os.path.join(pr.primitive_data_path, 'roof_angled.mesh.xml') 
    #vehicledata = pr.primitive_data_from_xml(vehiclexml)
    #offset = [0,0,0]

    def __init__(self, *args, **kwargs):
        proofdata = pr.primitive_data_from_xml(self.roofxml)
        #pvehdata = self.vehicledata
        pr.arbitrary_primitive.__init__(self, *args, **proofdata)
        self._default_('tag','_roof_',**kwargs)
        self._scale_uvs_ = True
        #self.translate(self.offset)

class wedged_roof(node):
    def __init__(self, *args, **kwargs):
        self._default_('consumes_children',True,**kwargs)
        self._default_('length',10,**kwargs)
        self._default_('width',10,**kwargs)
        self._default_('height',5,**kwargs)
        self.primitives = self.make_roof(*args, **kwargs)
        node.__init__(self, *args, **kwargs)

    def make_roof(self, *args, **kwargs):
        l,w,h = self.length,self.width,self.height
        seg1 = roofwedge()
        seg2 = roofwedge()
        flip = True if rm.random() < 0.25 else False
        seg2.rotate_z(fu.PI)
        if flip:
            seg1.rotate_z(fu.PI/2.0)
            seg2.rotate_z(fu.PI/2.0)
        seg1.scale([l,w,h])
        seg2.scale([l,w,h])
        return [seg1,seg2]

class rooftop(story):

    def __init__(self, *args, **kwargs):
        self._default_('theme','suburbs',**kwargs)
        self._default_('grit_renderingdistance',1000,**kwargs)
        self._default_('wall_height',1,{})
        def_ceiling = True if self.theme == 'suburbs' else False
        self._default_('add_ceiling',def_ceiling,**kwargs)
        self._default_('ext_gaped',False,**kwargs)
        self._default_('rid_top_bottom_walls',False,**kwargs)
        story.__init__(self, *args, **kwargs)
        veggies = self.vegetate()
        self.add_child(*veggies)
        self.assign_material('cubemat')

    def make_ceiling(self, *args, **kwargs):
        flleng = self.length/2.0
        flwidt = self.width/2.0
        flheit = rm.randrange(int(min([flleng,flwidt])),
                            int(max([flleng,flwidt])+1))

        czpos = self.wall_height#+self.ceiling_height#+self.floor_height
        rfpos = [0,0,czpos]
        rfargs = {
            'uv_parent':self, 
            'position':rfpos, 

            'length':flleng, 
            'width':flwidt, 
            'height':flheit, 
                }
        ceil = wedged_roof(**rfargs)
        self.ceiling = [ceil]
        return [ceil]

    def vegetate(self):
        vchildren = []
        #pdb.set_trace()
        return vchildren


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

_story_batch_count_ = 0
class story_batch(node):

    def get_name(self):
        global _story_batch_count_
        nam = 'story batch ' + str(_story_batch_count_)
        _story_batch_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        self._default_('name','storybatch',**kwargs)
        self._default_('consumes_children',True,**kwargs)
        self._default_('grit_renderingdistance',250,**kwargs)
        self._default_('grit_lod_renderingdistance',1000,**kwargs)
        node.__init__(self, *args, **kwargs)

_building_count_ = 0
class building(node):

    hard_min_length = 20
    hard_min_width = 20

    def get_name(self):
        global _building_count_
        nam = 'building ' + str(_building_count_)
        _building_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        self._default_('theme','suburbs',**kwargs)
        self._default_('name',self.get_name(),**kwargs)
        self._default_('grit_renderingdistance',250.0,**kwargs)
        self._default_('grit_lod_renderingdistance',1000.0,**kwargs)
        self._default_('floors',5,**kwargs)
        self._default_('length',40,**kwargs)
        self._default_('width',30,**kwargs)
        self._default_('tform',
            self.def_tform(*args,**kwargs),**kwargs)
        kwargs['uv_scales'] = [2,2,2]
        self._default_('uv_tform',
            self.def_uv_tform(*args,**kwargs),**kwargs)
        self._default_('materials',['imgtex'],**kwargs)
        self._default_('wall_height',4,**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        self._default_('floor_height',1,**kwargs)
        self._default_('ceiling_height',0.5,**kwargs)
        #self._default_('building_name','__abldg__',**kwargs)
        self._default_('roof_access',True,**kwargs)
        shafts = self.make_shafts(*args, **kwargs)
        self.shafts = shafts
        stories = self.make_floors_from_shafts(*args, **kwargs)
        foundation = self.make_foundation()
        
        story_batches = self.batch_stories(stories)
        #story_batches = self.batch_stories(foundation + stories)
        #story_batches = foundation + stories
        #story_batches = stories
        
        children = shafts + story_batches + foundation
        #children = shafts + story_batches
        self.add_child(*children)
        node.__init__(self, *args, **kwargs)
        self.assign_material('concrete')

    def make_foundation(self):
        shafts = self.shafts
        bname = self.name
        #bname = self.building_name
        bump = 0.0
        bpos = [0,0,bump]
        ww = self.wall_width
        basement_floor_height = self.floor_height
        basement_ceiling_height = self.ceiling_height
        basement_wall_height = 10
        baheight = basement_ceiling_height + basement_wall_height + basement_floor_height
        #baheight = basement_floor_height + basement_wall_height
        mpu.translate_vector(bpos,[0,0,-baheight])
        #[s.translate([0,0,-baheight]) for s in self.shafts]
        baargs = {
            #'parent':self, 
            'uv_parent':self, 
            'name':bname+'_basement_0', 
            'position':bpos, 
            'shafts':shafts, 
            'length':self.length, 
            'width':self.width, 
            'floor_height':basement_floor_height, 
            'ceiling_height':basement_ceiling_height, 
            'wall_height':basement_wall_height, 
            'wall_width':ww, 
                }
        found = [basement(-1, **baargs)]
        return found

    def batch_stories(self, stories, max_best_number = 10):
        stcnt = len(stories)
        stheight = self.wall_height + self.floor_height + self.ceiling_height
        best_number = int(((self.length+self.width)/2.0)/stheight)
        best_number = min([best_number,max_best_number])
        dex0 = 0
        batches = []
        stbargs = []
        b0_z = 0.0
        #b0_z = -stheight
        while dex0 < stcnt:

            sts_left = stcnt - dex0
            if sts_left >= best_number: 
                sts_this_round = best_number
            else: sts_this_round = sts_left % best_number
            batches.append(stories[dex0:dex0+sts_this_round])
            dex0 += sts_this_round

            b0 = batches[-1][0]
            for b in batches[-1][1:]:
                b.tform.position[2] -= b0.tform.position[2]
            b0.tform.position[2] = b0_z
            stbatpos = b0.tform.position[:]
            stbatpos[2] = b0_z
            b0_z += len(batches[-1])*stheight
            b0.tform.position[2] = 0.0

            stbargs.append({
                'name':'_storybatch_'+str(len(batches)), 
                'position':stbatpos, 
                'children':batches[-1], 
                'parent':self, 
                'uv_parent':self, 
                    })
        
        stbatches = [story_batch(**stbgs) for stbgs in stbargs]
        for stbat,bat in zip(stbatches,batches):
            for ba in bat: ba.set_parent(stbat)
        #    #for ba in bat: ba.tform.parent = stbat.tform
        return stbatches

    def terrain_points(self):
        tpts = self.find_corners()
        mpu.translate_coords(tpts,[0,0,-0.5])
        center = mpu.center_of_mass(tpts)
        mpu.translate_vector(center,[0,0,-0.5])
        #fu.translate_coords(tpts,[0,0,9])
        tpts = mpu.dice_edges(tpts, dices = 1)
        tpts.append(center)
        #tpts.append(mpu.center_of_mass(tpts))
        return tpts

    def make_shafts(self, *args, **kwargs):
        flcnt = self.floors
        if not self.roof_access: flcnt -= 1
        if flcnt == 1: return []
        shargs = [{
            #'parent':self, 
            'uv_parent':self, 
            'position':[0,0,0], 
            'rotation':[0,0,0], 
            'wall_height':self.wall_height, 
            'floor_height':self.floor_height, 
            'ceiling_height':self.ceiling_height, 
            'length':8, 
            'width':8, 
            'bottom':-1, 
            'top':'roof',
            'floors':flcnt, 
                }]
        shafts = [shaft(**sh) for sh in shargs]
        return shafts

    def get_bbox(self, *args, **kwargs):
        cornas = self.find_corners()
        bb = mpbb.bbox(corners = cornas)
        return [bb]

    def find_corners(self):
        length = self.length
        width = self.width
        pos = [0.0,0.0,0.0]
        c1, c2, c3, c4 = pos[:], pos[:], pos[:], pos[:]
        c1[0] -= length/2.0
        c1[1] -= width/2.0
        c2[0] += length/2.0
        c2[1] -= width/2.0
        c3[0] += length/2.0
        c3[1] += width/2.0
        c4[0] -= length/2.0
        c4[1] += width/2.0
        corncoords = [c1, c2, c3, c4]
        zang = self.tform.rotation[2]
        mpu.rotate_z_coords(corncoords,zang)
        mpu.translate_coords(corncoords,self.tform.position)#this doesnt need to be true()??!?!
        return [c1, c2, c3, c4]

    def make_floors_from_shafts(self, *args, **kwargs):
        shafts = self.shafts
        bname = self.name
        bpos = [0.0,0.0,0.0]
        ww = self.wall_width
        l,w = self.length,self.width

        floors = []
        flcnt = self.floors
        fllengs = [self.length]*flcnt
        flwidts = [self.width]*flcnt
        flheits = [self.floor_height]*flcnt
        clheits = [self.ceiling_height]*flcnt
        flwlhts = [self.wall_height]*flcnt
        hthresh = rm.randrange(int(flcnt/2.0),int(7.0*(flcnt+1)/8.0))
        if hthresh < 5: hthresh = 5
        lfactor = rm.choice([0.5,0.6,0.7,0.8,0.9])
        wfactor = rm.choice([0.5,0.6,0.7,0.8,0.9])
        fllengs = [l if fdx < hthresh else lfactor*l 
            #max([lfactor*l,min([l,self.hard_min_length])]) 
                for fdx,l in enumerate(fllengs)]
        flwidts = [w if fdx < hthresh else wfactor*w 
            #max([wfactor*w,min([w,self.hard_min_width])]) 
                for fdx,w in enumerate(flwidts)]
        #fllengs = [l if flcnt < flcnt/2.0 else 0.75*l for l in fllengs]
        #flwidts = [w if flcnt < flcnt/2.0 else 0.75*w for w in flwidts]
        #pdb.set_trace()
        #bump = 1.0 # what the hell is with this?
        bump = 0.0 # what the hell is with this?
        for fdx in range(flcnt):
            #stname = bname + '_story_' + str(fdx)
            fheight = flheits[fdx]
            cheight = clheits[fdx]
            wheight = flwlhts[fdx]
            fl_pos = bpos[:]
            fl_pos[2] += bump
            stheight = wheight + fheight + cheight
            bump += stheight
            stargs = {
                #'parent':self, 
                'uv_parent':self, 
                #'name':stname, 
                'position':fl_pos, 'shafts':shafts, 
                'length':fllengs[fdx], 
                'width':flwidts[fdx], 
                'floor_height':fheight, 
                'ceiling_height':cheight, 
                'wall_height':wheight, 
                'wall_width':ww, 
                'stories_below':floors, 
                    }
            floors.append(story(fdx, **stargs))

        roof_name = bname + '_roof_'
        fl_pos = bpos[:]
        #fl_pos[2] += stheight*(flcnt)
        #bump += floors[-1].ceiling_height
        fl_pos[2] += bump
        rfarg = {
            'theme':self.theme, 
            'parent':self, 
            'uv_parent':self, 
            'name':roof_name, 
            'position':fl_pos, 
            'length':fllengs[-1], 
            'width':flwidts[-1], 
            'floor_height':flheits[-1], 
            'shafts':shafts, 
            'wall_height':1, 
            'wall_width':ww, 
                }
        if self.roof_access:
            rfarg['gaps'] = []
            for sh in shafts:
                for gap in sh.floor_gaps:
                    topgap = gap[:]
                    rfarg['gaps'].append(topgap)
        roof = rooftop(flcnt, **rfarg)
        floors.append(roof)
        return floors








