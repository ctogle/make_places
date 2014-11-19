import make_places.fundamental as fu
#from make_places.fundamental import element
from make_places.scenegraph import node
from make_places.primitives import unit_cube

_floor_count_ = 0
class floor(node):

    def get_name(self):
        global _floor_count_
        nam = 'floor ' + str(_floor_count_)
        _floor_count_ += 1
        return nam

    def __init__(self, *args, **kwargs):
        self.seg_numbers = [str(x) for x in range(10)]  
        self._default_('name',self.get_name(),**kwargs)
        #self._default_('position',[0,0,0],**kwargs)
        #self._default_('tform',tform(),**kwargs)
        self._default_('length',20,**kwargs)
        self._default_('width',20,**kwargs)
        self._default_('floor_height',0.5,**kwargs)
        self._default_('gaps',[],**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)
        self.primitives = self.make_primitives([0,0,0],
            self.length,self.width,self.floor_height,self.gaps)
        node.__init__(self, *args, **kwargs)

    def find_corners(self, pos, length, width):
        x = length/2.0
        y = width/2.0
        c1 = fu.translate_vector(pos[:],[-x,-y,0])
        c2 = fu.translate_vector(pos[:],[x,-y,0])
        c3 = fu.translate_vector(pos[:],[x,y,0])
        c4 = fu.translate_vector(pos[:],[-x,y,0])
        corners = [c1, c2, c3, c4]
        ttf = self.tform
        #ttf = self.tform.true()
        fu.rotate_z_coords(corners, ttf.rotation[2])
        fu.translate_coords(corners, ttf.position)
        return corners

    def make_primitives(self, pos, length, width, flheight, gaps = []):
        self.corners = self.find_corners(pos, length, width)
        if len(gaps) == 0:
            self.gapped = False
            return self.make_floor_segment(pos, length, width, flheight)
        elif len(gaps) == 1:
            self.gapped = True
            gap = gaps[0]
            segments = []
            args = self.segment_single_projection_x(
                pos, length, width, flheight, gap)
            for ag in args:
                segments.extend(self.make_floor_segment(*ag))
            return segments
        else: print('failed to make a floor!!')

    def segment_single_projection_x(self, p, l, w, h, g):
        sargs = []
        c1x = p[0]
        c1y = p[1]
        c1z = p[2]
        c2x = g[0][0]
        c2y = g[0][1]
        c2z = g[0][2]
        lg = g[1]
        wg = g[2]
        s1l = l/2.0 + c2x - c1x - lg/2.0
        s1x = c1x - l/2.0 + s1l/2.0
        s1y = c1y
        s1z = c1z
        s2l = l - lg - s1l
        s2x = c2x + lg/2.0 + s2l/2.0
        s2y = c1y
        s2z = c1z
        s1 = ([s1x,s1y,s1z],s1l,w,h)
        s2 = ([s2x,s2y,s2z],s2l,w,h)
        s3w = w/2.0 + c2y - c1y - wg/2.0
        s3x = c2x
        s3y = c1y - w/2.0 + s3w/2.0
        s3z = c1z
        s4w = w - wg - s3w
        s4x = c2x
        s4y = c1y + wg/2.0 + s3w/2.0
        s4z = c1z
        s3 = ([s3x,s3y,s3z],lg,s3w,h)
        s4 = ([s4x,s4y,s4z],lg,s4w,h)
        #segposs = [s1[0],s2[0],s3[0],s4[0]]
        #print 'seggggg', segposs
        #fu.rotate_z_coords(segposs, self.tform.rotation[2])
        #print 'seggggg', segposs
        return [s1,s2,s3,s4]

    def seg_number(self):
        if self.seg_numbers:return self.seg_numbers.pop(0)

    def make_floor_segment(self, pos, length, width, flheight):
        segnum = self.seg_number()
        if segnum is None:
            print 'floor has too many segments!'
            return []
        fl = unit_cube(tag = '_floor_seg_' + segnum)
        fl.scale([length, width, flheight])
        fl.translate([pos[0],pos[1],pos[2]-flheight])
        return [fl]









