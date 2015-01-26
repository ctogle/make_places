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

    def _write_bool_property(self,msio,prop,val):
        if val is None:return
        msio.write(prop)
        msio.write(' = ')
        msio.write(str(val).lower())
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
        vstr = vstr[vstr.find('(')+1:-1]
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
        self._write_normal_properties(msio)
        self._write_emissive_properties(msio)
        self._write_gloss_properties(msio)
        self._write_translucency_properties(msio)
        self._write_paint_properties(msio)

    def _write_alpha_properties(self,msio):
        self._write_float_property(msio,'alpha',self.alpha)
        self._write_bool_property(msio,'depthSort',self.depthSort)
        self._write_bool_property(msio,'vertexAlpha',self.vertexAlpha)
        self._write_float_property(msio,'alphaReject',self.alphaReject)
        self._write_bool_property(msio,'premultipliedAlpha',self.premultipliedAlpha)

    def _write_shadow_properties(self,msio):
        self._write_bool_property(msio,'castShadows',self.castShadows)
        self._write_bool_property(msio,'shadowAlphaReject',self.shadowAlphaReject)
        self._write_float_property(msio,'shadowBias',self.shadowBias)
        self._write_float_property(msio,'shadowObliqueCutOff',self.shadowObliqueCutOff)

    def _write_misc_properties(self,msio):
        self._write_bool_property(msio,'backfaces',self.backfaces)
        self._write_float_property(msio,'blendedBones',self.blendedBones)
        self._write_bool_property(msio,'clamp',self.clamp)
        self._write_bool_property(msio,'depthWrite',self.depthWrite)
        self._write_bool_property(msio,'stipple',self.stipple)
        self._write_vector_property(msio,'textureAnimation',self.textureAnimation)
        self._write_vector_property(msio,'textureScale',self.textureScale)

    def _write_diffuse_properties(self,msio):
        self._write_vector_property(msio,'diffuseColour',self.diffuseColour)
        self._write_path_property(msio,'diffuseMap',self.diffuseMap)
        self._write_bool_property(msio,'vertexDiffuse',self.vertexDiffuse)

    def _write_normal_properties(self,msio):
        self._write_path_property(msio,'normalMap',self.normalMap)

    def _write_emissive_properties(self,msio):
        self._write_path_property(msio,'emissiveMap',self.emissiveMap)
        self._write_vector_property(msio,'emissiveColour',self.emissiveColour)

    def _write_gloss_properties(self,msio):
        self._write_path_property(msio,'glossMap',self.glossMap)
        self._write_bool_property(msio,'noSpecularChannel',self.noSpecularChannel)
        self._write_float_property(msio,'specular',self.specular)
        self._write_float_property(msio,'gloss',self.gloss)

    def _write_translucency_properties(self,msio):
        self._write_path_property(msio,'translucencyMap',self.translucencyMap)

    def _write_paint_properties(self,msio):
        self._write_float_property(msio,'paintColour',self.paintColour)
        self._write_bool_property(msio,'paintByDiffuseAlpha',self.paintByDiffuseAlpha)

    def _add_diffuse(self,path):
        self.diffuseMap = path
        return self

    def _add_normal(self,path):
        self.normalMap = path
        return self

    def _add_gloss(self,path):
        self.glossMap = path
        return self

    def __init__(self,name,**kwargs):
        self.name = name

        ### alpha ###
        self._default_('alpha',None,**kwargs)
        self._default_('depthSort',None,**kwargs)
        self._default_('vertexAlpha',None,**kwargs)
        self._default_('alphaReject',None,**kwargs)
        self._default_('premultipliedAlpha',None,**kwargs)

        ### shadows ###
        self._default_('castShadows',None,**kwargs)
        self._default_('shadowAlphaReject',None,**kwargs)
        self._default_('shadowBias',None,**kwargs)
        self._default_('shadowObliqueCutOff',None,**kwargs)

        ### misc ###
        self._default_('backfaces',None,**kwargs)
        self._default_('blendedBones',None,**kwargs)
        self._default_('clamp',None,**kwargs)
        self._default_('depthWrite',None,**kwargs)
        self._default_('stipple',None,**kwargs)
        self._default_('textureAnimation',None,**kwargs)
        self._default_('textureScale',None,**kwargs)

        ### diffuse ###
        self._default_('diffuseColour',None,**kwargs)
        self._default_('diffuseMap',None,**kwargs)
        self._default_('vertexDiffuse',None,**kwargs)

        ### normal ###
        self._default_('normalMap',None,**kwargs)

        ### emissive ###
        self._default_('emissiveMap',None,**kwargs)
        self._default_('emissiveColour',None,**kwargs)

        ### gloss ###
        self._default_('glossMap',None,**kwargs)
        self._default_('noSpecularChannel',None,**kwargs)
        self._default_('specular',None,**kwargs)
        self._default_('gloss',None,**kwargs)

        ### translucency ###
        self._default_('translucencyMap',None,**kwargs)

        ### painting ###
        self._default_('paintColour',None,**kwargs)
        self._default_('paintByDiffuseAlpha',None,**kwargs)

default_materials = []
def write_default_materials(msio):
    write_generic_materials()
    write_concrete_materials()
    write_metal_materials()
    write_nature_materials()
    write_misc_materials()
    write_emissive_materials()

    for dfm in default_materials:
        dfm._write(msio)

def write_generic_materials():
    generic_grid = material('gridmat')._add_diffuse('../textures/generic/orangeboxtex.png')
    default_materials.append(generic_grid)

    generic_cube = material('cubemat')._add_diffuse('../textures/generic/cubetex.png')
    default_materials.append(generic_cube)

    generic_octg = material('octagonmat')._add_diffuse('../textures/generic/octagontex.png')
    default_materials.append(generic_octg)

def write_concrete_materials():
    concrete1 = material('concrete1')._add_diffuse('../textures/concrete/concrete.png')
    concrete1.textureScale = cv.vector2d(2,2)
    concrete1.diffuseColour = cv.vector(0.5,0.5,0.5)
    default_materials.append(concrete1)

    concrete2 = material('concrete2')._add_diffuse('../textures/concrete/concrete2.png')
    concrete2.textureScale = cv.vector2d(4,4)
    default_materials.append(concrete2)

    concrete3 = material('concrete3')._add_diffuse('../textures/concrete/concrete2.png')
    concrete3.textureScale = cv.vector2d(4,4)
    concrete3.diffuseColour = cv.vector(0.4,0.4,0.2)
    default_materials.append(concrete3)

    concrete4 = material('concrete4')._add_diffuse('../textures/concrete/concrete3.jpg')
    concrete4.textureScale = cv.vector2d(4,4)
    default_materials.append(concrete4)

    cement1 = material('cement1')._add_diffuse('../textures/concrete/indoor-cement.jpg')
    cement1.textureScale = cv.vector2d(4,4)
    default_materials.append(cement1)

    sidewalk1 = material('sidewalk1')._add_diffuse('../textures/concrete/sidewalk1.jpg')
    default_materials.append(sidewalk1)

    sidewalk2 = material('sidewalk2')._add_diffuse('../textures/concrete/sidewalk2.jpg')
    default_materials.append(sidewalk2)

    asphalt = material('asphalt')._add_diffuse('../textures/concrete/asphalt.jpg')
    asphalt.textureScale = cv.vector2d(4,4)
    asphalt.specular = 0
    asphalt.diffuseColour = cv.vector(0.75,0.75,0.75)
    default_materials.append(asphalt)

    roadline_y = material('roadline_y')._add_diffuse('../textures/concrete/roadline.png')
    roadline_y.specular = 0
    roadline_y.alphaReject = 0.5
    roadline_y.diffuseColour = cv.vector(0.8,0.8,0.8)
    default_materials.append(roadline_y)

    #roadline_y_cont = material('roadline_y_cont')._add_diffuse('../textures/concrete/roadline_continuous.png')
    #roadline_y_cont.specular = 0
    #roadline_y_cont.alphaReject = 0.5
    #roadline_y_cont.diffuseColour = cv.vector(0.8,0.8,0.8)
    #default_materials.append(roadline_y_cont)
    roadline_y_cont = material('roadline_y_cont')._add_diffuse('../textures/concrete/roadline_w_continuous.png')
    #roadline_y_cont.specular = 0
    roadline_y_cont.alphaReject = 0.5
    roadline_y_cont.diffuseColour = cv.vector(1.0,0.8,0.2)
    default_materials.append(roadline_y_cont)

    roadline_w_cont = material('roadline_w_cont')._add_diffuse('../textures/concrete/roadline_w_continuous.png')
    #roadline_w_cont.specular = 0
    roadline_w_cont.alphaReject = 0.5
    roadline_w_cont.diffuseColour = cv.vector(0.8,0.8,0.8)
    default_materials.append(roadline_w_cont)

    brick1 = material('brick1')._add_diffuse('../textures/concrete/brick.jpg')
    brick1.textureScale = cv.vector2d(4,4)
    default_materials.append(brick1)
    
    brick2 = material('brick2')._add_diffuse('../textures/concrete/brick2.jpg')
    brick2.textureScale = cv.vector2d(3,3)
    default_materials.append(brick2)

    hokie = material('hokie')._add_diffuse('../textures/concrete/hokiestone.jpg')
    hokie.textureScale = cv.vector2d(10,10)
    default_materials.append(hokie)
    
    road = material('road')._add_diffuse('../textures/concrete/road.png')
    default_materials.append(road)

def write_metal_materials():
    metal1 = material('metal1')._add_diffuse('../textures/metal/metal.png')
    metal1.textureScale = cv.vector2d(10,10)
    default_materials.append(metal1)

def write_nature_materials():
    grass1 = material('grass1')._add_diffuse('../textures/nature/grass.dds')
    grass1.textureScale = cv.vector2d(2,2)
    grass1.shadowObliqueCutOff = 0
    default_materials.append(grass1)

    tree1 = material('Tree_aelmTrunk')
    tree1._add_diffuse('../textures/nature/tree_aelm.dds')
    tree1._add_normal('../textures/nature/tree_aelm_N.dds')
    tree1.gloss = 0
    tree1.specular = 0
    default_materials.append(tree1)

    tree2 = material('Tree_aelmLev')
    tree2._add_diffuse('../textures/nature/tree_aelm.dds')
    tree2._add_normal('../textures/nature/tree_aelm_N.dds')
    tree2.clamp = True
    tree2.gloss = 0
    tree2.specular = 0
    tree2.alphaReject = 0.5
    default_materials.append(tree2)

    bmat1 = material('bmat1')
    bmat1._add_diffuse('../textures/nature/bush1.png')
    bmat1.alphaReject = 0.5
    bmat1.gloss = 0
    bmat1.specular = 0
    default_materials.append(bmat1)

    bmat2 = material('bmat2')
    bmat2._add_diffuse('../textures/nature/bush_tree_baum.jpg')
    bmat2.alphaReject = 0.5
    bmat2.gloss = 0
    bmat2.specular = 0
    default_materials.append(bmat2)

    ocean = material('ocean')
    ocean._add_normal('../textures/nature/ocean_N.tga')
    ocean._add_gloss('../textures/nature/ocean_S.tga')
    ocean.diffuseColour = cv.zero()
    ocean.textureAnimation = cv.vector2d(-0.1,0)
    ocean.alpha = 0.9
    ocean.depthWrite = True
    default_materials.append(ocean)

def write_misc_materials():
    bumper = material('bumper')._add_diffuse('../textures/misc/bumper.png')
    default_materials.append(bumper)
    
    greenhaze = material('greenhaze')._add_diffuse('../textures/misc/greenhaze.png')
    default_materials.append(greenhaze)
    
    rubber = material('rubber')._add_diffuse('../textures/misc/rubber.png')
    default_materials.append(rubber)

    glass = material('glass')._add_diffuse('../textures/misc/glass.png')
    glass.alpha = 0.2
    default_materials.append(glass)

def write_emissive_materials():
    light = material('light')._add_diffuse('../textures/emissive/light.png')
    light.emissiveColour = cv.vector(1,1,1)
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





