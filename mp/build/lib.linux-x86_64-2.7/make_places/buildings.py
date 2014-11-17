#from make_places.fundamental import element
from make_places.scenegraph import node
import make_places.fundamental as fu
import make_places.primitives as pr
from make_places.stairs import ramp
from make_places.stairs import shaft
from make_places.floors import floor
from make_places.walls import wall
from make_places.walls import perimeter

import random as rm

import pdb

class story(node):

    def __init__(self, *args, **kwargs):
        self.floor_number = args[0]
        self._default_('add_ceiling',True,**kwargs)
        self._default_('shafts',[],**kwargs)
        #self._default_('consumes_children',True,**kwargs)
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
        self._default_('ext_gaped',True,**kwargs)
        self.children = self.make_children(*args, **kwargs)
        self.lod_primitives = []
        #self.lod_primitives = self.make_lod(*args, **kwargs)
        node.__init__(self, *args, **kwargs)

    def make_lod(self, *args, **kwargs):
        lod = pr.ucube()
        l,w = self.length,self.width
        #h = self.wall_height + self.floor_height + self.ceiling_height
        h = self.wall_height + self.floor_height
        fl = self.floor_[0]
        zrot = 0
        #pos = fl.tform.position[0]
        pos = fl.tform.position
        #pos[2] -= self.floor_height
        lod.scale([l,w,h])
        lod.rotate_z(zrot)
        lod.translate(pos)
        #lod.is_lod = True

        self.children[0].primitives[0].has_lod = True

        return [lod]

    def make_children(self, *args, **kwargs):
        floor_ = self.make_floor(*args, **kwargs)
        if self.add_ceiling:ceiling = self.make_ceiling(*args, **kwargs)
        else:ceiling = []
        #ceiling = []
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
            'position':flpos, 
            'length':flleng, 
            'width':flwidt, 
            'gaps':gaps,
            'height':self.floor_height, 
            'parent':self, 
                }
        floor_ = floor(**flargs)
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
            'position':flpos, 
            'length':flleng, 
            'width':flwidt, 
            'gaps':gaps,
            'floor_height':self.ceiling_height, 
            'parent':self, 
                }
        ceil = floor(**flargs)
        self.ceiling = [ceil]
        return [ceil]

    def make_exterior_walls(self, *args, **kwargs):
        #floor_pieces = kwargs['floor']
        floor_pieces = self.floor_
        peargs = [{
            'parent':fl, 
            #'parent':self, 
            'floor':fl, 
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
        #self._default_('consumes_children',True,**kwargs)
        self._default_('wall_height',8,**kwargs)
        self._default_('ext_gaped',False,**kwargs)
        story.__init__(self, *args, **kwargs)

class rooftop(story):

    def __init__(self, *args, **kwargs):
        self._default_('wall_height',1,{})
        self._default_('add_ceiling',False,**kwargs)
        self._default_('ext_gaped',False,**kwargs)
        story.__init__(self, *args, **kwargs)

class story_batch(node):

    def __init__(self, *args, **kwargs):
        self._default_('name','storybatch',**kwargs)
        self._default_('consumes_children',True,**kwargs)
        self._default_('grit_renderingdistance',100,**kwargs)
        self._default_('grit_lod_renderingdistance',1000,**kwargs)
        node.__init__(self, *args, **kwargs)

class building(node):

    def __init__(self, *args, **kwargs):
        self._default_('floors',5,**kwargs)
        self._default_('length',40,**kwargs)
        self._default_('width',30,**kwargs)
        self._default_('tform',
            self.def_tform(*args,**kwargs),**kwargs)
        kwargs['uv_scales'] = [8,8,8]
        self._default_('uv_tform',
            self.def_uv_tform(*args,**kwargs),**kwargs)
        self._default_('materials',['imgtex'],**kwargs)
        self._default_('wall_height',4,**kwargs)
        self._default_('wall_width',0.4,**kwargs)
        self._default_('floor_height',1,**kwargs)
        self._default_('ceiling_height',0.5,**kwargs)
        self._default_('building_name','__abldg__',**kwargs)
        self._default_('roof_access',True,**kwargs)
        shafts = self.make_shafts(*args, **kwargs)
        self.shafts = shafts
        stories = self.make_floors_from_shafts(*args, **kwargs)
        foundation = self.make_foundation()
        
        #story_batches = self.batch_stories(foundation+stories)
        story_batches = foundation + stories
        #story_batches = stories
        
        self.children = shafts + story_batches
        node.__init__(self, *args, **kwargs)
        self.assign_material('concrete')

    def make_foundation(self):
        shafts = self.shafts
        bname = self.building_name
        bump = 1.0 # what the hell is with this as well?
        bump = 0.0 # what the hell is with this as well?
        bpos = [0,0,bump]
        ww = self.wall_width
        basement_floor_height = self.floor_height
        basement_ceiling_height = self.ceiling_height
        basement_wall_height = 10
        #baheight = basement_ceiling_height + basement_wall_height + basement_floor_height
        baheight = basement_floor_height + basement_wall_height
        fu.translate_vector(bpos,[0,0,-baheight])
        baargs = {
            'parent':self, 
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
        stheight = self.wall_height + self.floor_height
        best_number = int(((self.length+self.width)/2.0)/stheight)
        best_number = min([best_number,max_best_number])
        dex0 = 0
        batches = []
        stbargs = []
        #b0_z = 0.0
        b0_z = -stheight
        while dex0 < stcnt:
            sts_left = stcnt - dex0
            if sts_left >= best_number: 
                sts_this_round = best_number
            else: sts_this_round = sts_left % best_number
            batches.append(stories[dex0:dex0+sts_this_round])
            b0 = batches[-1][0]
            for b in batches[-1][1:]:
                b.tform.position[2] -= b0.tform.position[2]
            b0.tform.position[2] = b0_z
            stbatpos = b0.tform.position[:]
            stbatpos[2] = b0_z
            b0_z += len(batches[-1])*stheight
            stbargs.append({
                'name':'_storybatch_'+str(len(batches)), 
                'position':stbatpos, 
                'children':batches[-1], 
                'parent':self, 
                'uv_parent':self, 
                    })
            b0.tform.position[2] = 0.0
            dex0 += sts_this_round
        
        stbatches = [story_batch(**stbgs) for stbgs in stbargs]
        for stbat,bat in zip(stbatches,batches):
            for ba in bat: ba.tform.parent = stbat.tform
        return stbatches

    def terrain_points(self):
        tpts = self.find_corners()
        fu.translate_coords(tpts,[0,0,-0.5])
        #fu.translate_coords(tpts,[0,0,9])
        tpts = fu.dice_edges(tpts, dices = 1)
        tpts.append(fu.center_of_mass(tpts))
        return tpts

    def make_shafts(self, *args, **kwargs):
        flcnt = self.floors
        if not self.roof_access: flcnt -= 1
        if flcnt == 1: return []
        shargs = [{
            'parent':self, 
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
        bb = fu.bbox(corners = cornas)
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
        #corncoords = fu.rotate_z_coords(corncoords,zang)
        fu.rotate_z_coords(corncoords,zang)
        fu.translate_coords(corncoords,self.tform.position)#this doesnt need to be true()??!?!
        #fu.translate_coords(corncoords,self.tform.true().position)#this doesnt need to be true()??!?!
        return [c1, c2, c3, c4]

    def make_floors_from_shafts(self, *args, **kwargs):
        shafts = self.shafts
        bname = self.building_name
        bpos = [0.0,0.0,0.0]
        #stheight = self.wall_height + self.floor_height
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
        lfactor = rm.choice([0.5,0.6,0.7,0.8,0.9])
        wfactor = rm.choice([0.5,0.6,0.7,0.8,0.9])
        fllengs = [l if fdx < hthresh else lfactor*l 
                    for fdx,l in enumerate(fllengs)]
        flwidts = [w if fdx < hthresh else wfactor*w 
                    for fdx,w in enumerate(flwidts)]
        #fllengs = [l if flcnt < flcnt/2.0 else 0.75*l for l in fllengs]
        #flwidts = [w if flcnt < flcnt/2.0 else 0.75*w for w in flwidts]
        #pdb.set_trace()
        #bump = 1.0 # what the hell is with this?
        bump = 0.0 # what the hell is with this?
        for fdx in range(flcnt):
            stname = bname + '_story_' + str(fdx)
            fheight = flheits[fdx]
            cheight = clheits[fdx]
            wheight = flwlhts[fdx]
            fl_pos = bpos[:]
            fl_pos[2] += bump
            stheight = wheight + fheight
            bump += stheight
            stargs = {
                'parent':self, 
                'uv_parent':self, 
                'name':stname, 
                'position':fl_pos, 
                'shafts':shafts, 
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








