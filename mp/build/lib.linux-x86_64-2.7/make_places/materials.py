import make_places.fundamental as fu

import mp_vector as cv

import pdb

#import cStringIO as sio



class material(fu.base):

    def _write_float_property(self,msio,prop,val):
        if val is None:return
        msio.write(prop)
        msio.write(' = ')
        msio.write(str(val))
        msio.write(',\n')

    def _write_path_property(self,msio,prop,val):
        if val is None:return
        msio.write(prop)
        msio.write(' = `')
        msio.write(val)
        msio.write('`,\n')

    def _write_vector_property(self,msio,prop,val):
        if val is None:return
        msio.write(prop)
        msio.write(' = {')

        vstr = val.__str__()
        vstr = vstr[:vstr.find('(')]
        vstr.replace('(','{',1)
        vstr.replace(')','}',1)
        msio.write(vstr)

        msio.write('},\n')

    def _write(self,msio):
        msio.write('\nmaterial `')
        msio.write(self.name)
        msio.write('` {\n')
        self._write_properties(msio)
        msio.write('}\n')

    def _write_properties(self,msio):
        self._write_alpha_properties(msio)
        self._write_shadow_properties(msio)
        self._write_misc_properties(msio)
        self._write_diffuse_properties(msio)
        self._write_emissive_properties(msio)

    def _write_alpha_properties(self,msio):
        self._write_float_property(msio,'alpha',self.alpha)

    def _write_shadow_properties(self,msio):
        self._write_float_property(msio,'shadowObliqueCutOff',self.shadowObliqueCutOff)

    def _write_misc_properties(self,msio):
        self._write_vector_property(msio,'textureScale',self.textureScale)
        '''#
        txsc = self.textureScale
        if not txsc == [1,1]:
            msio.write('textureScale = {')
            msio.write(str(txsc[0]))
            msio.write(',')
            msio.write(str(txsc[1]))
            msio.write('},\n')
        '''#

    def _write_diffuse_properties(self,msio):
        self._write_path_property(msio,'diffuseMap',self.diffuseMap)
        #if self.diffuseMap:
        #    msio.write('diffuseMap = `')
        #    msio.write(self.diffuseMap)
        #    msio.write('`,\n')

    def _write_normal_properties(self,msio):pass

    def _write_emissive_properties(self,msio):
        emcl = self.emissiveColour
        if not emcl == [0,0,0]:
            msio.write('emissiveColour = {')
            msio.write(str(emcl[0]))
            msio.write(',')
            msio.write(str(emcl[1]))
            msio.write(',')
            msio.write(str(emcl[2]))
            msio.write('},\n')

    def _write_gloss_properties(self,msio):pass
    def _write_translucency_properties(self,msio):pass
    def _write_paint_properties(self,msio):pass

    def _add_diffuse(self,path):
        self.diffuseMap = path
        return self

    def __init__(self,name,**kwargs):
        self.name = name

        ### alpha ###
        self._default_('alpha',None,**kwargs)
        self._default_('depthSort',True,**kwargs)
        self._default_('vertexAlpha',False,**kwargs)
        self._default_('alphaReject',0.5,**kwargs)
        self._default_('premultipliedAlpha',False,**kwargs)

        ### shadows ###
        self._default_('castShadows',True,**kwargs)
        self._default_('shadowAlphaReject',False,**kwargs)
        self._default_('shadowBias',0.1,**kwargs)
        self._default_('shadowObliqueCutOff',None,**kwargs)

        ### misc ###
        self._default_('backfaces',False,**kwargs)
        self._default_('blendedBones',0,**kwargs)
        self._default_('clamp',False,**kwargs)
        self._default_('depthWrite',True,**kwargs)
        self._default_('stipple',False,**kwargs)
        self._default_('textureAnimation',[0,0],**kwargs)
        self._default_('textureScale',cv.one2d(),**kwargs)
        #self._default_('textureScale',[1,1],**kwargs)

        ### diffuse ###
        self._default_('diffuseColour',[1,1,1],**kwargs)
        self._default_('diffuseMap',None,**kwargs)
        self._default_('vertexDiffuse',False,**kwargs)

        ### normal ###
        self._default_('normalMap',None,**kwargs)

        ### emissive ###
        self._default_('emissiveMap',None,**kwargs)
        self._default_('emissiveColour',[0,0,0],**kwargs)

        ### gloss ###
        self._default_('glossMap',None,**kwargs)
        self._default_('noSpecularChannel',False,**kwargs)
        self._default_('specular',0.0,**kwargs)
        self._default_('gloss',0.0,**kwargs)

        ### translucency ###
        self._default_('translucencyMap',None,**kwargs)

        ### painting ###
        self._default_('paintColour',1,**kwargs)
        self._default_('paintByDiffuseAlpha',False,**kwargs)

default_materials = []
def write_default_materials(msio):
    write_concrete_materials()
    write_metal_materials()
    write_nature_materials()
    write_misc_materials()
    write_emissive_materials()

    generic_grid = material('cubemat')._add_diffuse('../textures/cubetex.png')
    generic_octg = material('octagonmat')._add_diffuse('../textures/octagontex.png')
    #generic_green = material('green')._add_diffuse('../textures/green.png')
    default_materials.append(generic_grid)
    default_materials.append(generic_octg)
    #default_materials.append(generic_green)

    for dfm in default_materials:
        dfm._write(msio)

def write_concrete_materials():
    concrete = material('concrete')._add_diffuse('../textures/concrete.png')
    asphalt = material('asphalt')._add_diffuse('../textures/asphalt.jpg')
    brick = material('brick')._add_diffuse('../textures/brick.jpg')
    brick.textureScale = [4,4]
    hokie = material('hokie')._add_diffuse('../textures/hokiestone.jpg')
    road = material('road')._add_diffuse('../textures/road.png')
    default_materials.append(concrete)
    default_materials.append(asphalt)
    default_materials.append(brick)
    default_materials.append(hokie)

def write_metal_materials():
    metal = material('metal')._add_diffuse('../textures/metal.png')
    default_materials.append(metal)

def write_nature_materials():
    grass = material('grass')._add_diffuse('../textures/grass.dds')
    grass.textureScale = [2,2]
    grass.shadowObliqueCutOff = 0
    default_materials.append(grass)

def write_misc_materials():
    rubber = material('rubber')._add_diffuse('../textures/rubber.png')
    glass = material('glass')._add_diffuse('../textures/glass.png')
    glass.alpha = 0.2
    default_materials.append(rubber)
    default_materials.append(glass)

def write_emissive_materials():
    light = material('light')._add_diffuse('../textures/light.png')
    light.emissiveColour = [1,1,1]
    default_materials.append(light)

def enumerate_materials():
    dfmnames = []
    for dfm in default_materials:
        print 'default material:',dfm.name
        dfmnames.append(dfm.name)
    return dfmnames





'''
material `name` { 
alpha = 0.5 # Render transparent (implemented with scene blending, z sorting, no depth write, etc.) This is a fixed uniform alpha for the whole material, that is multiplied by any alpha value in the diffuse map. Zero means fully transparent, one means fully opaque. You can thus set it to 1 (or true) if you want the transparency to be defined only by the alpha mask of the diffuse map. Defaults to false (no alpha except alpha rejection, below).
depthSort = true # This forces a depth sort, i.e. causes meshes in the scene to be rendered in order starting with the furthest. Defaults to true for alpha materials and false otherwise.
vertexAlpha = true # Causes alpha from the vertex colours to be used as an additional mask (default false).
alphaReject = x # The alpha reject value, any alpha values below this will be culled without blending. This is independent of alpha transparency. Set to false if you don't want alpha rejection. Defaults to 0.25 (i.e. anything up to 25% alpha is culled).
premultipliedAlpha = true # See PremultipliedAlpha. Defaults to false.

castShadows = false # Disable casting shadows for a particular material. Default is true.
shadowAlphaReject = true
# Whether or not to use the alpha value from the diffuse map and the alpha reject
# value when casting shadows. Defaults to true when alphaReject is set, false
# otherwise.
shadowBias = 0.1
# The bias of the shadow depth (in metres) when casting shadows. Defaults to 0.
# Use a higher value to avoid artefacts, but too high a value will cause shadow
# disconnection?.
shadowObliqueCutOff = 30
# Stop drawing shadows when the polygon is nearly in-line with the light
# source. A higher value gets rid of normal bending artefacts?. A lower value
# will have more distinctive shadows. Default is 5 degrees, maximum is 90
# degrees (which will disable shadow reception on the surface entirely.

backfaces = true
# Render polies as double sided (back faces) if not specified, defaults to false.
# The normal is automatically inverted for the back faces.
blendedBones = 0
# The max number of bone weights per vertex used by the mesh wearing this
# material. If this is too large, the vertexes may be corrupted. Default 0 (i.e. no skeleton is present).
clamp = true
# Whether or not to enable clamping the texture instead of wrapping it. This avoids bleeding across the texture in mipmaps, which is often
# what you want for e.g. vegetation. Default is false (i.e. wrap).
depthWrite = true
# This forces depth writing to the stencil buffer. Defaults to false for alpha materials and true otherwise. Using this with alpha is
# necessary for GTA SA style trees and alpha LOD fading.
stipple = false
# Whether or not to use the 'stipple' effect for fading out
# objects or the traditional 'alpha fade'. Defaults to false
# unless the material is already alpha blended in which case
# defaults to true.
textureAnimation={U,V}
# Offset of the UV coordinates as time progresses. The U and V values are the rate of change of the UV data per second.
# Default is 0 for both U and V (i.e. no animation).
textureScale ={U,V}
# Used to change the tiling of textures. Values 1,1 are default, use 2 for double, etc...

diffuseColour = {r,g,b} # The diffuse colour in rgb using floats. Defaults to white, i.e., {1.0, 1.0, 1.0}.
diffuseMap = `path/name` # A diffuse texture?. Includes the path and the texture name. Masked by the diffuse colour, if given.
vertexDiffuse = true/false # Whether the RGB components of the vertex colour channel are used as an additional mask (default false).

normalMap = `path/name`

emissiveMap = `path/name`
# Emissive means light emitted from the material directly, i.e. not due to
# reflecting sun or other lights. E.g. neon/backlit signs, LEDs, or incandescent
# materials (fire, plasma, etc). Default is nil.
emissiveColour = {r,g,b} # A solid emissive colour, masked with the map if one is used. Defaults to {0,0,0} if no emissive map is defined, or {1,1,1} otherwise.

#NOTE: The engine now uses physically-based shading which requires specific
#values of specular and gloss to match real-life materials. This needs
#documenting properly.
glossMap = `path/name` # The blue channel is specular, the red channel is gloss.
noSpecularChannel = true # Indicates that the gloss map has no specular channel. Default false.
specular = value # The specular intensity, a solid colour or a mask on the value from the map. Default 1 if gloss map with specular channel (blue) provided, 0 otherwise.
gloss = value # Glossiness, as a solid value or a mask on the value from the map. Default 1 if gloss map provided, 0.03 otherwise.

translucencyMap = `path/name`

paintColour = 1
paintByDiffuseAlpha = true
}
'''





