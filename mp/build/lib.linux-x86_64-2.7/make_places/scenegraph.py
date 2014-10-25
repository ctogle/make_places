import make_places.fundamental as fu
import make_places.primitives as pr
import make_places.blend_in as blgeo
import make_places.gritty as gritgeo

from copy import deepcopy as dcopy
import numpy as np





class base(object):
    def _default_(self, *args, **kwargs):
        key = args[0]
        init = args[1]
        if key in kwargs.keys():init = kwargs[key]
        if not key in self.__dict__.keys():
            self.__dict__[key] = init

class tform(base):
    def true(self):
        if self.parent:
            tpar = self.parent.true()
            self.position = fu.rotate_z_coords(
                [self.position], tpar.rotation[2])[0]
            return tpar + self
        else: return self

    def __init__(self, *args, **kwargs):
        self._default_('position',[0,0,0],**kwargs)
        self._default_('rotation',[0,0,0],**kwargs)
        self._default_('scales',[1,1,1],**kwargs)
        self._default_('parent',None,**kwargs)
        self._default_('children',[],**kwargs)

    def __str__(self):
        strr = 'tform\n\tpos:\t'
        strr += str(self.position)
        strr += '\n\trot:\t'
        strr += str(self.rotation)
        strr += '\n\tscl:\t'
        strr += str(self.scales)
        strr += '\n'
        return strr

    def __add__(self, other):
        np = fu.translate_vector(self.position[:],other.position)
        nr = fu.translate_vector(self.rotation[:],other.rotation)
        ns = fu.scale_vector(self.scales[:],other.scales)
        new = tform(parent = self.parent, children = self.children, 
            position = np, rotation = nr, scales = ns)
        return new

class sgraph(base):
    def __init__(self, *args, **kwargs):
        self._default_('nodes',[],**kwargs)

    def add_node(self, nd):
        self.nodes.append(nd)

    def make_scene_b(self, center = False):
        for nd in self.nodes:
            nd.make_b(center = center)

    def make_scene_g(self, center = False):
        for nd in self.nodes:
            nd.make_g(center = center)

class node(base):
    def translate(self, v):
        fu.translate_vector(self.tform.position, v)

    def rotate(self, v):
        fu.translate_vector(self.tform.rotation, v)

    def def_tform(self,*args,**kwargs):
        def _def(ke,de):
            if ke in kwargs.keys(): return kwargs[ke]
            else: return de
        pos = _def('position',[0,0,0])
        rot = _def('rotation',[0,0,0])
        scl = _def('scales',[1,1,1])
        if 'parent' in kwargs.keys():
            tpar = kwargs['parent'].tform
        else: tpar = None
        chi = _def('children',[])
        return tform(parent = tpar, position = pos, 
            rotation = rot, scales = scl)

    def add_child(self, *chil):
        for ch in chil:
            ch.tform.parent = self.tform
            self.children.append(ch)

    def __init__(self, *args, **kwargs):
        self._default_('children',[],**kwargs)
        self._default_('primitives',[],**kwargs)
        self._default_('tform',self.def_tform(*args,**kwargs),**kwargs)

    def make_b(self, *args, **kwargs):
        ttf = self.tform.true()
        for pm in self.primitives:
            tpm = dcopy(pm)
            tpm.scale(ttf.scales)
            tpm.rotate_z(ttf.rotation[2])
            tpm.translate(ttf.position)
            blgeo.create_primitive(tpm, **kwargs)
        for ch in self.children:
            ch.make_b(*args, **kwargs)

    def make_g(self, *args, **kwargs):
        ttf = self.tform.true()
        for pm in self.primitives:
            tpm = dcopy(pm)
            tpm.scale(ttf.scales)
            tpm.rotate_z(ttf.rotation[2])
            tpm.translate(ttf.position)
            gritgeo.create_primitive(tpm, **kwargs)
        for ch in self.children:
            ch.make_g(*args, **kwargs)






