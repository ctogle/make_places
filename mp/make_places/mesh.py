




class face:

    def __init__(self,edges,indices,m = 0,pm = 0):
        self.mat = m
        self.pmat = pm
        self.indices = indices

def write_vertex(x,y,z,nx,ny,nz,ux,uy):
        xlines = []
        xlines.append(" "*12 + "<vertex>\n")
        xlines.append("                <position x=\""+str(x)+"\" y=\""+str(y)+"\" z=\""+str(z)+"\" />\n")
        xlines.append("                <normal x=\""+str(nx)+"\" y=\""+str(ny)+"\" z=\""+str(nz)+"\" />\n")
        xlines.append("                <texcoord u=\""+str(ux)+"\" v=\""+str(1.0-uy)+"\" />\n")
        xlines.append("            </vertex>\n")
        return xlines

# it should be possible to use the same mesh for two different primitives
class mesh:
    
    def face_data(faces,materials):
        ifaces = [f.indices for f in faces]
        face_materials = [f.mat for f in faces]

        mcnt = len(materials)
        fcnt = len(face_materials)
        fa = {}
        for mdx in range(mcnt):
            ma = materials[mdx]
            fa[ma] = []
            for fmdx in range(fcnt):
                if face_materials[fmdx] == mdx:
                    fa[ma].append(ifaces[fmdx])
            if not fa[ma]: del fa[ma]
        return fa

    def as_xml(self):
        faces = self.face_data()
        _32bitindices = self.requires_32bit_indices()

        xlines = []
        xlines.append("<mesh>\n")
        xlines.append("    <sharedgeometry>\n")
        xlines.append("        <vertexbuffer positions=\"true\"normals=\""+("true")+"\" colours_diffuse=\""+("false")+"\" texture_coord_dimensions_0=\"float2\" texture_coords=\"1\">\n")
        coords  = self.pverts
        ncoords = self.nverts
        ucoords = self.uverts
        vcnt = len(coords)
        for vdx in range(vcnt):
            p = coords[vdx]
            x,y,z = p.x,p.y,p.z
            n = ncoords[vdx]
            nx,ny,nz = n.x,n.y,n.z
            u = ucoords[vdx]
            ux,uy = u.x,u.y

            xlines.extend(write_vertex(x,y,z,nx,ny,nz,ux,uy))

        xlines.append("        </vertexbuffer>\n")
        xlines.append("    </sharedgeometry>\n")
        xlines.append("    <submeshes>\n")
        for m in faces.keys():
            xlines.append("        <submesh material=\""+m+"\" usesharedvertices=\"true\" use32bitindexes=\""+_32bitindices+"\" operationtype=\"triangle_list\">\n")
            xlines.append("            <faces>\n")
            for f in faces[m]:
                xlines.append("                <face v1=\""+str(f[0])+"\" v2=\""+str(f[1])+"\" v3=\""+str(f[2])+"\" />\n")
            xlines.append("            </faces>\n")
            xlines.append("        </submesh>\n")
        xlines.append("    </submeshes>\n")
        xlines.append("</mesh>\n")
        self.xml_representation = '\n'.join(xlines)
        return self.xml_representation

    def requires_32bit_indices(self):
        vcnt = len(self.pverts)
        _32bitindices = True if vcnt > 65000 else False
        _32bitindices = 'true' if _32bitindices else 'false'
        return _32bitindices

    def __init__(self):
        self.pverts = []
        self.nverts = []
        self.uverts = []

        self.edges = []
        self.faces = []

        self.materials = []
        self.phys_materials = []

    def add_vertex(self,pos,norm,uv):
        self.pverts.append(pos)
        self.nverts.append(norm)
        self.uverts.append(uv)
        
    def add_edge(self,edg):
        self.edges.append(edg)
        
    def add_face(self,fac):
        self.faces.append(fac)






def testmesh():
    #me = mesh()
    v1 = cv.vector(10,0,0)
    v2 = cv.vector(10,10,0)
    v3 = cv.vector(100,20,0)
    v4 = cv.vector(100,30,0)

    splinedb = mpu.spline(v1,v2,v3,v4,10)
    splinedt = [s.copy().translate_z(3) for s in splineb]

    vs = []
    nvs = []
    nus = []
    nfs = []
    fms = []
    pfms = []

    pwargs = {
            'verts' : newverts, 
            'nverts' : newnorml, 
            'uvs' : newuvs, 
            'faces' : newfaces, 
            'materials' : self.materials[:], 
            'face_materials' : fmats, 
            'phys_materials' : self.phys_materials[:], 
            'phys_face_materials' : pfmats, 
            'xmlfilename' : xmlfile, 
            'force_normal_calc' : True, 
            'prevent_normal_calc' : False, 
            'smooth_normals' : True, 
            'is_lod' : lod, 
            'has_lod' : False,
            #'has_lod' : not lod, 
                }
    mesh = pr.arbitrary_primitive(**pwargs)
    return mesh

    edgeb = edge_walk(splinedb)
    edget = edge_walk(splinedt)
    faces = bridge(edgeb,edget)

    for f in faces: me.add_face(f)



      


