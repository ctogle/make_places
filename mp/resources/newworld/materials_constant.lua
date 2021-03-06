local soc = 20
soc = 0

material "grass2" {
    --vertexDiffuse=true,
    vertexDiffuse=false,
    --diffuseMap="/solemn/textures/grass.dds", 
    --normalMap="/solemn/textures/grass_N.dds", 
    --glossMap="/solemn/textures/grass_S.tga", 
    diffuseMap='../textures/grass.dds', 
    --normalMap='../textures/grass_N.dds', 
    --glossMap='../textures/grass_S.tga', 
    textureScale={2,2},
    shadowObliqueCutOff = soc,
}

material "Tree_aelmTrunk" {
    --vertexDiffuse = true,
    vertexDiffuse = false,
    diffuseMap = '../textures/tree_aelm.dds',
    normalMap = '../textures/tree_aelm_N.dds',
    gloss = 0,
    specular = 0,
}

material "Tree_aelmLev" {
    vertexDiffuse = false,
    diffuseMap = '../textures/tree_aelm.dds',
    clamp = true,
    alphaReject = 0.5,
    normalMap = '../textures/tree_aelm_N.dds',
    gloss = 0,
    specular = 0,
}

material "GrassTuft1" {
    backfaces=true,
    diffuseMap = '../textures/GrassTuft1_D.dds',
    clamp = true,
    alphaReject = 0.9,
    grassLighting = true,
    gloss = 0,
    specular = 0,
}

material "grasstuft2" {
    backfaces=true,
    diffuseMap = '../textures/GrassTuft2_D.dds',
    normalMap = '../textures/GrassTuft2_N.dds',
    clamp = true,
    alphaReject = 0.33,
    grassLighting = true,
    gloss = 0,
    specular = 0,
}

material "ocean" {
	diffuseColour = V_ZERO,
	--diffuseMap="textures/ocean_D.dds",
	normalMap='../textures/ocean_N.tga',
	glossMap='../textures/ocean_S.tga',
    depthWrite=true,
	alpha = 0.9,
	textureAnimation={-0.1,0},
}

-- taxi materials
material `Atlas` {
    glossMap = `../textures/taxi/Gloss.png`, 
    diffuseMap = `../textures/taxi/Diffuse.png`, 
    shadowBias = 0.05, 
}
material `GlowingParts` {
    glossMap=`../textures/taxi/Gloss.png`, 
    diffuseMap=`../textures/taxi/Diffuse.png`, 
    emissiveMap=`../textures/taxi/Diffuse.png`, 
    emissiveColour=vec(0.4,0.4,0.4), 
    shadowBias=0.05, 
}
material `LightOn` {
    emissiveMap=`../textures/taxi/Diffuse.png`, 
    emissiveColour=vec(4,4,4), 
}
material `LightBrakeOn` {
    emissiveMap=`../textures/taxi/Diffuse.png`,
    emissiveColour=vec(6,0,0), 
    diffuseColour=vec(0,0,0),
    specular=0,
    gloss=0,
}
material `LightBrakeDim` {
    emissiveMap=`../textures/taxi/Diffuse.png`, 
    emissiveColour=vec(2,0,0), 
    diffuseColour=vec(0,0,0), 
    specular=0,
    gloss=0, 
}
material `LightHeadLeft` {
    glossMap=`../textures/taxi/Gloss.png`, 
    diffuseMap=`../textures/taxi/Diffuse.png`, 
    shadowBias=0.05, 
}
material `LightHeadRight` {
    glossMap=`../textures/taxi/Gloss.png`, 
    diffuseMap=`../textures/taxi/Diffuse.png`, 
    shadowBias=0.05, 
}
material `LightBrakeLeft` {
    glossMap=`../textures/taxi/Gloss.png`, 
    diffuseMap=`../textures/taxi/Diffuse.png`, 
    shadowBias=0.05, 
}
material `LightBrakeRight` {
    glossMap=`../textures/taxi/Gloss.png`, 
    diffuseMap=`../textures/taxi/Diffuse.png`, 
    shadowBias=0.05, 
}





