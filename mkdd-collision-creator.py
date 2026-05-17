# BCOnvert.py v0.1 by Yoshi2

import os
from re import match
from struct import pack, unpack
from math import floor, ceil
import math


def collides(face_v1, face_v2, face_v3, box_mid_x, box_mid_z, box_size_x, box_size_z):
    min_x = min(face_v1[0], face_v2[0], face_v3[0]) - box_mid_x
    max_x = max(face_v1[0], face_v2[0], face_v3[0]) - box_mid_x

    min_z = min(face_v1[2], face_v2[2], face_v3[2]) - box_mid_z
    max_z = max(face_v1[2], face_v2[2], face_v3[2]) - box_mid_z

    half_x = box_size_x / 2.0
    half_z = box_size_z / 2.0

    if max_x < -half_x or min_x > +half_x:
        return False
    if max_z < -half_z or min_z > +half_z:
        return False

    return True

def normalize_vector(v1):
    n = (v1[0]**2 + v1[1]**2 + v1[2]**2)**0.5
    return v1[0]/n, v1[1]/n, v1[2]/n


def create_vector(v1, v2):
    return v2[0]-v1[0],v2[1]-v1[1],v2[2]-v1[2]


def cross_product(v1, v2):
    cross_x = v1[1]*v2[2] - v1[2]*v2[1]
    cross_y = v1[2]*v2[0] - v1[0]*v2[2]
    cross_z = v1[0]*v2[1] - v1[1]*v2[0]
    return cross_x, cross_y, cross_z


def calc_lookuptable(v1, v2, v3):
    min_x = min_z = max_x = max_z = None

    if v1[0] <= v2[0] and v1[0] <= v3[0]:
        min_x = 0
    elif v2[0] <= v1[0] and v2[0] <= v3[0]:
        min_x = 1
    elif v3[0] <= v1[0] and v3[0] <= v2[0]:
        min_x = 2

    if v1[0] >= v2[0] and v1[0] >= v3[0]:
        max_x = 0
    elif v2[0] >= v1[0] and v2[0] >= v3[0]:
        max_x = 1
    elif v3[0] >= v1[0] and v3[0] >= v2[0]:
        max_x = 2

    if v1[2] <= v2[2] and v1[2] <= v3[2]:
        min_z = 0
    elif v2[2] <= v1[2] and v2[2] <= v3[2]:
        min_z = 1
    elif v3[2] <= v1[2] and v3[2] <= v2[2]:
        min_z = 2

    if v1[2] >= v2[2] and v1[2] >= v3[2]:
        max_z = 0
    elif v2[2] >= v1[2] and v2[2] >= v3[2]:
        max_z = 1
    elif v3[2] >= v1[2] and v3[2] >= v2[2]:
        max_z = 2

    return min_x, min_z, max_x, max_z


def read_int(f):
    val = f.read(0x4)
    return unpack(">I", val)[0]


def read_float_tripple(f):
    val = f.read(0xC)
    return unpack(">fff", val)


def write_uint32(f, val):
    f.write(pack(">I", val))


def write_int32(f, val):
    f.write(pack(">i", val))


def write_ushort(f, val):
    f.write(pack(">H", val))


def write_short(f, val):
    f.write(pack(">h", val))


def write_byte(f, val):
    f.write(pack("B", val))


def write_float(f, val):
    f.write(pack(">f", val))


def subdivide_coordinates(startx, startz, endx, endz):
    halfx = (startx+endx)/2.0
    halfz = (startz+endz)/2.0
    quadrant00 = (startx, startz, halfx, halfz)
    quadrant10 = (halfx, startz, endx, halfz)
    quadrant01 = (startx, halfz, halfx, endz)
    quadrant11 = (halfx, halfz, endx, endz)
    return quadrant00, quadrant10, quadrant01, quadrant11


def subdivide_cell(cell_start_x, cell_start_z, cell_end_x, cell_end_z, triangles, vertices):
    quadrants = ([], [], [], [])
    quadrant_coords = subdivide_coordinates(cell_start_x, cell_start_z,
                                            cell_end_x, cell_end_z)

    for i, quadrant in enumerate(quadrant_coords):
        startx, startz, endx, endz = quadrant
        midx, midz = (startx+endx)/2.0, (startz+endz)/2.0
        sizex, sizez = endx-startx, endz-startz

        for j, face in triangles:
            v1_index, v2_index, v3_index = face

            v1 = vertices[v1_index - 1]
            v2 = vertices[v2_index - 1]
            v3 = vertices[v3_index - 1]

            if collides(v1, v2, v3,
                        midx,
                        midz,
                        sizex,
                        sizez):
                # print(i, "collided")
                quadrants[i].append((j, face))

    return quadrants, quadrant_coords


def subdivide_grid(minx, minz,
                   gridx_start, gridx_end, gridz_start, gridz_end,
                   cell_size, triangles, vertices, result):
    # print("Subdivision with", gridx_start, gridz_start, gridx_end, gridz_end, (gridx_start+gridx_end) // 2, (gridz_start+gridz_end) // 2)
    if gridx_start == gridx_end - 1 and gridz_start == gridz_end - 1:
        if gridx_start not in result:
            result[gridx_start] = {}
        result[gridx_start][gridz_start] = triangles

        return True

    assert gridx_end > gridx_start or gridz_end > gridz_start

    halfx = (gridx_start + gridx_end) // 2
    halfz = (gridz_start + gridz_end) // 2

    quadrants = (
        [], [], [], []
    )
    # x->
    # 2 3 ^
    # 0 1 z
    coordinates = (
        (0, gridx_start, halfx, gridz_start, halfz),  # Quadrant 0
        (1, halfx, gridx_end, gridz_start, halfz),  # Quadrant 1
        (2, gridx_start, halfx, halfz, gridz_end),  # Quadrant 2
        (3, halfx, gridx_end, halfz, gridz_end)  # Quadrant 3
    )
    skip = []
    if gridx_start == halfx:
        skip.append(0)
        skip.append(2)
    if halfx == gridx_end:
        skip.append(1)
        skip.append(3)
    if gridz_start == halfz:
        skip.append(0)
        skip.append(1)
    if halfz == gridz_end:
        skip.append(2)
        skip.append(3)

    for i, face in triangles:
        v1_index, v2_index, v3_index = face

        v1 = vertices[v1_index - 1]
        v2 = vertices[v2_index - 1]
        v3 = vertices[v3_index - 1]

        for quadrant, startx, endx, startz, endz in coordinates:
            if quadrant not in skip:
                area_size_x = (endx - startx) * cell_size
                area_size_z = (endz - startz) * cell_size

                if collides(v1, v2, v3,
                            minx + startx * cell_size + area_size_x // 2,
                            minz + startz * cell_size + area_size_z // 2,
                            area_size_x,
                            area_size_z):
                    # print(i, "collided")
                    quadrants[quadrant].append((i, face))

    for quadrant, startx, endx, startz, endz in coordinates:
        # print("Doing subdivision, skipping:", skip)
        if quadrant not in skip:
            # print("doing subdivision with", coordinates[quadrant])
            subdivide_grid(minx, minz,
                           startx, endx, startz, endz,
                           cell_size, quadrants[quadrant], vertices, result)

def export_bco(args, vertices, triangles, grid, sounds):
    entry_max_tri_count = args["max_quadtree_tri_count"]
    quadtree_depth = args["quadtree_depth"]
    remove_steep_faces = args["remove_steep_faces"]
    cos_steep_face_angle = math.cos(math.radians(args["steep_face_angle"]))

    smallest_x, smallest_z, biggest_x, biggest_z = grid
    
    cell_size_x = args["cell_size"]
    cell_size_z = args["cell_size"]

    grid_start_x = floor(smallest_x / cell_size_x) * cell_size_x
    grid_start_z = floor(smallest_z / cell_size_z) * cell_size_z

    grid_end_x = ceil(biggest_x / cell_size_x) * cell_size_x
    grid_end_z = ceil(biggest_z / cell_size_z) * cell_size_z

    grid_size_x = (grid_end_x - grid_start_x) / cell_size_x
    grid_size_z = (grid_end_z - grid_start_z) / cell_size_z

    print(grid_start_x, grid_start_z, grid_end_x, grid_end_z)
    print(grid_size_x, grid_size_z)

    assert grid_size_x % 1 == 0
    assert grid_size_z % 1 == 0

    grid_size_x = int(grid_size_x)
    grid_size_z = int(grid_size_z)

    grid = {}
    print("calculating grid")

    def calc_average_height(face):
        return (vertices[face[0] - 1][1]+
                vertices[face[1] - 1][1]+
                vertices[face[2] - 1][1])/3.0

    triangles.sort(key=calc_average_height, reverse=True)

    triangles_indexed = ((i, face[:3]) for i, face in enumerate(triangles))
    subdivide_grid(grid_start_x, grid_start_z,
                   0, grid_size_x, 0, grid_size_z, cell_size_x,
                   triangles_indexed, vertices,
                   grid)
    print("grid calculated")
    print("writing bco file")

    with open(args["output"], "wb") as f:
        f.write(b"0003")
        write_ushort(f, grid_size_x)
        write_ushort(f, grid_size_z)
        write_int32(f, int(grid_start_x))
        write_int32(f, int(grid_start_z))
        write_uint32(f, int(cell_size_x))
        write_uint32(f, int(cell_size_z))
        write_ushort(f, 0x0000) # Entry count of last section
        write_ushort(f, 0x0000) # Padding?

        # Placeholder values for later
        write_uint32(f, 0x1234ABCD) # Triangle indices offset
        write_uint32(f, 0x2345ABCD) # triangles offset
        write_uint32(f, 0x3456ABCD) # vertices offset
        write_uint32(f, 0x00000000) # unknown section offset

        assert f.tell() == 0x2C
        groups = []

        triangle_group_index = 0

        class GridEntry(object):
            def __init__(self):
                self.triangles = []
                self.child_index = 0
                self.triangle_index = 0
                self.coords = None

        base_offset = grid_size_x*grid_size_z
        remaining_entries = []


        #for entry in grid:
        for iz in range(grid_size_z):
            print("progress:",iz+1, "/",grid_size_z)
            for ix in range(grid_size_x):
                entry = grid[ix][iz]
                tricount = len(entry)

                if tricount > entry_max_tri_count:
                    write_byte(f, 0x00)
                    write_byte(f, 0x00)
                    write_ushort(f, base_offset+len(remaining_entries))
                    write_uint32(f, triangle_group_index) # We can simply reuse the group index

                    startx = grid_start_x + ix*cell_size_x
                    startz = grid_start_z + iz*cell_size_z
                    endx = startx + cell_size_x
                    endz = startz + cell_size_z

                    quadrants, quadrant_coords = subdivide_cell(startx, startz, endx, endz, entry, vertices)
                    has_tris = False

                    for quadrant, coords in zip(quadrants, quadrant_coords):
                        gridentry = GridEntry()
                        if len(quadrant) > 0:
                            has_tris = True
                        #if len(quadrant) > 30:
                        #    pass
                        #    #more_quadrants, more_quadrant_coords = subdivide_cell()
                        #else:
                        gridentry.coords = coords
                        gridentry.triangles = quadrant
                        gridentry.triangle_index = triangle_group_index
                        triangle_group_index += len(quadrant)
                        remaining_entries.append(gridentry)
                        groups.append(quadrant)
                    assert has_tris is True

                else:
                    write_byte(f, tricount)
                    write_byte(f, 0x00)
                    write_ushort(f, 0x0000)
                    write_uint32(f, triangle_group_index)

                    triangle_group_index += tricount
                    groups.append(entry)

        for i in range(quadtree_depth):
            base_offset += len(remaining_entries)
            new_remaining_entries = []
            original_length = len(remaining_entries)
            print("quadtree depth", i, original_length)
            for gridentry in remaining_entries:
                if i == quadtree_depth - 1 and len(gridentry.triangles) > 250:
                    print(len(gridentry.triangles))
                    print(gridentry.coords)
                    raise RuntimeError("Too many triangles in a portion of the model")

                if i < quadtree_depth - 1 and len(gridentry.triangles) > entry_max_tri_count:
                    write_byte(f, 0x00) # A grid entry with children has no triangles
                    write_byte(f, 0x00) # Padding
                    write_ushort(f, base_offset+len(new_remaining_entries))
                    write_uint32(f, triangle_group_index)

                    startx, startz, endx, endz = gridentry.coords

                    quadrants, quadrant_coords = subdivide_cell(startx, startz, endx, endz,
                                                                gridentry.triangles, vertices)
                    has_tris = False

                    for quadrant, coords in zip(quadrants, quadrant_coords):
                        gridentry = GridEntry()
                        if len(quadrant) > 0:
                            has_tris = True

                        gridentry.coords = coords
                        gridentry.triangles = quadrant
                        gridentry.triangle_index = triangle_group_index
                        triangle_group_index += len(quadrant)
                        new_remaining_entries.append(gridentry)
                        groups.append(quadrant)
                    assert has_tris is True

                else:
                    write_byte(f, len(gridentry.triangles))
                    write_byte(f, 0x00)
                    write_ushort(f, gridentry.child_index)
                    write_uint32(f, gridentry.triangle_index)

            remaining_entries = new_remaining_entries

        print("written grid")
        tri_indices_offset = f.tell()
        for trianglegroup in groups:
            for triangle_index, triangle in trianglegroup:
                write_ushort(f, triangle_index)
        print("written triangle indices")
        assert (f.tell() % 4) in (2, 0)
        if f.tell() % 4 == 2:
            write_ushort(f, 0x00) # Padding
        tri_offset = f.tell()
        assert tri_offset % 4 == 0


        neighbours = {}

        floor_sound_types = {}

        for i, triangle in enumerate(triangles):
            print(i, triangle)
            v1_index = triangle[0]
            v2_index = triangle[1]
            v3_index = triangle[2]

            floor_type = triangle[3]
            extra_unknown = triangle[4]
            extra_settings = triangle[5]

            v1 = vertices[v1_index-1]
            v2 = vertices[v2_index-1]
            v3 = vertices[v3_index-1]

            v1tov2 = create_vector(v1,v2)
            v1tov3 = create_vector(v1,v3)

            cross_norm = cross_product(v1tov2, v1tov3)

            if cross_norm[0] == cross_norm[1] == cross_norm[2] == 0.0:
                norm = cross_norm
                print(cross_norm)
                print(v1tov2, v1tov3)
                print("Triangle:", v1, v2, v3)
                print("norm calculation failed")
            else:
                norm = normalize_vector(cross_norm)

            norm_x = int(round(norm[0], 4) * 10000)
            norm_y = int(round(norm[1], 4) * 10000)
            norm_z = int(round(norm[2], 4) * 10000)

            midx = (v1[0]+v2[0]+v3[0])/3.0
            midy = (v1[1]+v2[1]+v3[1])/3.0
            midz = (v1[2]+v2[2]+v3[2])/3.0

            if floor_type is None:
                continue

            if extra_settings is None:
                extra_settings = 0

            if extra_unknown is None:
                extra_unknown = 0x01


            floatval = (-1)*(round(norm[0], 4) * midx + round(norm[1], 4) * midy + round(norm[2], 4) * midz)

            min_x, min_z, max_x, max_z = calc_lookuptable(v1, v2, v3)

            vlist = (v1, v2, v3)
            assert vlist[min_x][0] == min(v1[0], v2[0], v3[0])
            assert vlist[min_z][2] == min(v1[2], v2[2], v3[2])

            assert vlist[max_x][0] == max(v1[0], v2[0], v3[0])
            assert vlist[max_z][2] == max(v1[2], v2[2], v3[2])

            indices = [v1_index, v2_index, v3_index]  # sort the indices to always have them in the same order
            indices.sort()

            local_neighbours = []
            for edge in ((indices[0], indices[1]), (indices[1], indices[2]), (indices[2], indices[0])):
                if edge in neighbours:
                    neighbour = neighbours[edge]
                    if len(neighbour) == 1: # Only this triangle has that edge
                        local_neighbours.append(0xFFFF)
                    elif i == neighbour[0]:# and triangles[neighbour[1]][3] != None and (floor_type & 0xFF00) == (triangles[neighbour[1]][3] & 0xFF00):
                        local_neighbours.append(neighbour[1])
                    elif i == neighbour[1]:# and triangles[neighbour[0]][3] != None and (floor_type & 0xFF00) == (triangles[neighbour[0]][3] & 0xFF00):
                        local_neighbours.append(neighbour[0])
                    else:
                        local_neighbours.append(0xFFFF)
                else:
                    local_neighbours.append(0xFFFF)

            start = f.tell()

            write_uint32(f, v1_index)
            write_uint32(f, v2_index)
            write_uint32(f, v3_index)

            write_float(f, floatval)

            write_short(f, norm_x)
            write_short(f, norm_y)
            write_short(f, norm_z)

            write_ushort(f,floor_type)
            floor_sound_types[floor_type] = True

            write_byte(f, (max_z << 6) | (max_x << 4) | (min_z << 2) | min_x)  # Lookup table for min/max values
            write_byte(f, extra_unknown)  # Unknown

            # Neighbours is bugged atm, can cause some walls to be fall-through
            write_ushort(f, 0xFFFF)#local_neighbours[0]) # Triangle index, 0xFFFF means no triangle reference
            write_ushort(f, 0xFFFF) #local_neighbours[1]) # Triangle index
            write_ushort(f, 0xFFFF) #local_neighbours[2]) # Triangle index

            write_uint32(f, extra_settings)
            end = f.tell()
            assert (end-start) == 0x24

        vertex_offset = f.tell()
        print("written triangle data")
        assert f.tell() % 4 == 0
        for x, y, z in vertices:
            write_float(f, x)
            write_float(f, y)
            write_float(f, z)
        print("written vertices")
        unknown_offset = f.tell()

        f.seek(0x1C)

        write_uint32(f, tri_indices_offset)  # Triangle indices offset
        write_uint32(f, tri_offset)  # triangles offset
        write_uint32(f, vertex_offset)  # vertices offset
        write_uint32(f, unknown_offset)  # unknown section offset
        f.seek(unknown_offset)

        for sound in sounds:
            write_byte(f, sound[0])  # floortype
            write_byte(f, sound[1])  # subfloortype
            write_short(f, sound[2])  # Sound to be played?
            write_uint32(f, 0)
            write_uint32(f, 0)

        f.seek(0x18)
        write_ushort(f, len(floor_sound_types))