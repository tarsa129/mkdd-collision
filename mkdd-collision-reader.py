from struct import unpack_from

def read_array(buffer, offset, length):
    return buffer[offset:offset+length]


def read_float(buffer, offset):
    return unpack_from(">f", buffer, offset)[0]


def read_int32(buffer, offset):
    return unpack_from(">i", buffer, offset)[0]


def read_uint32(buffer, offset):
    return unpack_from(">I", buffer, offset)[0]


def read_uint16(buffer, offset):
    return unpack_from(">H", buffer, offset)[0]


def read_uint8(buffer, offset):
    return unpack_from("B", buffer, offset)[0]


class BCOTriangle(object):
    def __init__(self):
        pass

    @classmethod
    def from_array(cls, buffer, offset, i):
        triangle_data = read_array(buffer, offset+i*0x24, 0x24)
        tri = cls()

        tri.v1 = read_uint32(triangle_data, 0x00)
        tri.v2 = read_uint32(triangle_data, 0x04)
        tri.v3 = read_uint32(triangle_data, 0x08)
        tri.d = read_float(triangle_data, 0x0C)
        tri.norm_x = read_uint16(triangle_data, 0x10)
        tri.norm_y = read_uint16(triangle_data, 0x12)
        tri.norm_z = read_uint16(triangle_data, 0x14)
        tri.floor_type = read_uint16(triangle_data, 0x16)
        tri.minmax_lookup = read_uint8(triangle_data, 0x18)
        tri.camera_code = read_uint8(triangle_data, 0x19)
        tri.n1 = read_uint16(triangle_data, 0x1A)
        tri.n2 = read_uint16(triangle_data, 0x1C)
        tri.n3 = read_uint16(triangle_data, 0x1E)

        tri.settings = read_uint32(triangle_data, 0x20)

        return tri

class SoundValue:
    def __init__(self, col_flag, col_attr, sound_value, unk1, unk2):
        self.col_flag = col_flag
        self.col_attr = col_attr
        self.sound_value = sound_value
        self.unk1 = unk1
        self.unk2 = unk2

    @classmethod
    def from_file(cls, f):
        col_flag, col_attr, sound_value, int1, int2 = unpack_from(">BBHII", f.read(0xC), 0)
        return cls(col_flag, col_attr, sound_value, int1, int2)


class RacetrackCollision(object):
    def __init__(self):
        self._data = None
        self.identifier = b"0003"
        self.grid_xsize = 0
        self.grid_zsize = 0
        self.coordinate1_x = 0
        self.coordinate1_z = 0
        self.coordinate2_x = 0
        self.coordinate2_z = 0
        self.entrycount = 0
        self.padding = 0

        self.gridtable_offset = 0
        self.triangles_indices_offset = 0
        self.trianglesoffset = 0
        self.verticesoffset = 0
        self.unknownoffset = 0

        self.grids = []
        self.triangles = []
        self.vertices = []

    def get_python_vertices(self, rotate_poster=True, scale = 1.0):
        vertices = []
        for vertex in self.vertices:
            x, y, z = vertex
            new_vertex = (x * scale, y * scale, z * scale)
            if rotate_poster:
                new_vertex = (new_vertex[0], -new_vertex[2], new_vertex[1])
            vertices.append(new_vertex)

        return vertices

    def get_python_faces_materials(self):
        faces = []
        materials = []
        for triangle in self.triangles:
            faces.append([triangle.v1, triangle.v2, triangle.v3])
            materials.append((triangle.floor_type, triangle.camera_code, triangle.settings))
        return faces, materials

    def load_file(self, f):
        data = f.read()
        self._data = data
        if data[:0x4] != b"0003":
            raise RuntimeError("Expected header start 0003, but got {0}. "
                               "Likely not MKDD collision!".format(data[:0x4]))

        self.identifier = data[:0x4]


        self.grid_xsize = read_uint16(data, 0x4)
        self.grid_zsize = read_uint16(data, 0x6)

        self.coordinate1_x = read_int32(data, 0x8)
        self.coordinate1_z = read_int32(data, 0xC)
        self.gridcell_xsize = read_int32(data, 0x10)
        self.gridcell_zsize = read_int32(data, 0x14)

        self.entrycount = read_uint16(data, 0x18)
        self.padding = read_uint16(data, 0x1A)

        self.gridtable_offset = 0x2C
        self.triangles_indices_offset = read_uint32(data, 0x1C)
        self.trianglesoffset = read_uint32(data, 0x20)
        self.verticesoffset = read_uint32(data, 0x24)
        self.unknownoffset = read_uint32(data, 0x28)

        # Parse triangles
        trianglescount = (self.verticesoffset-self.trianglesoffset) // 0x24
        print((self.verticesoffset-self.trianglesoffset)%0x24)

        for i in range(trianglescount):
            self.triangles.append(BCOTriangle.from_array(data, self.trianglesoffset, i))

        # Parse vertices
        vertcount = (self.unknownoffset-self.verticesoffset) // 0xC
        print((self.unknownoffset-self.verticesoffset) % 0xC)

        biggestx = biggestz = -99999999
        smallestx = smallestz = 99999999

        for i in range(vertcount):
            x = read_float(data, self.verticesoffset + i*0xC + 0x00)
            y = read_float(data, self.verticesoffset + i*0xC + 0x04)
            z = read_float(data, self.verticesoffset + i*0xC + 0x08)
            self.vertices.append((x,y,z))

            if x > biggestx:
                biggestx = x
            if x < smallestx:
                smallestx = x

            if z > biggestz:
                biggestz = z
            if z < smallestz:
                smallestz = z
            #print(x,y,z)
        print("smallest/smallest vertex coordinates:",smallestx, smallestz, biggestx, biggestz)
        f.seek(self.unknownoffset)
        self.matentries = []

        for i in range(self.entrycount):
            self.matentries.append( SoundValue.from_file(f) )