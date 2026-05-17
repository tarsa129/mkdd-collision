bl_info = {
    "name" : "MKDD Collision Helper",
    "author" : "tarsa129",
    "version" : (0, 0, 0),
    "blender" : (5, 0, 0),
    "location" : "View3d > Tool",
    "category": "Export",
}

import bpy, bmesh
from bpy.props import EnumProperty, PointerProperty, IntProperty, BoolProperty, CollectionProperty, StringProperty, FloatProperty
from bpy_extras.io_utils import ImportHelper, ExportHelper
import re
import os

bco_reader = bpy.data.texts["mkdd-collision-reader"].as_module()
bco_writer = bpy.data.texts["mkdd-collision-writer"].as_module()
#from . import bco_reader
#from . import bco_writer

def dummyBCOFunction(self,context):
    active=context.active_object
    if(active):
        bpy.context.view_layer.objects.active=active
    return

particle_coltypes = ["0x00", "0x01", "0x03", "0x04", "0x13"]
respawn_coltypes = ["0x05", "0x07","0x09", "0x0a", "0x0d", "0x0e", "0x0f", "0x10", "0x11", "0x37", "0x47"]
collision_colors = {
    "0x00": (250, 213, 160),
    "0x01": (128, 128, 128),
    "0x02": (192, 192, 192),
    "0x03": (76, 255, 0),
    "0x04": (0, 255, 255),
    "0x07": (255, 106, 0),
    "0x08": (255, 106, 0),
    "0x0C": (250, 213, 160),
    "0x0F": (0, 38, 255),
    "0x10": (250, 213, 160),
    "0x12": (64, 64, 64),
    "0x13": (250, 213, 160),
    "0x37": (255, 106, 0),
    "0x47": (255, 106, 0),
}
default_collision_color = (40, 40, 40)
bco_material_name_prefix = "Roadtype_"
bco_material_name_regex = "^0x([0-9A-F]{2})([0-9A-F]{2})_0x([0-9A-F]{2})_0x([0-9A-F]{1})([01]{1})00([01]{1})([01]{1})([0-9A-F]{2})$"
bco_material_name_matcher = re.compile(bco_material_name_regex)

bco_material_data_len = 8
def read_material_flag(material_name):
    if not material_name.startswith(bco_material_name_prefix):
        return None
    material_name = material_name[len(bco_material_name_prefix):]

    if len(material_name) != 6 and len(material_name) != 22:
        return None
    if len(material_name) == 6:
        material_name += "_0x01_0x00000000"

    match = bco_material_name_matcher.search(material_name)
    if not match:
        return None

    return (match.group(1), match.group(2),
            match.group(3), match.group(4), match.group(5), match.group(6), match.group(7), match.group(8))

def get_collision_color(collision_type):
    collision_color = default_collision_color
    if collision_type in collision_colors:
        collision_color = collision_colors[collision_type]
    return (collision_color[0] / 255.0, collision_color[1] / 255.0, collision_color[2] / 255.0, 1)

def get_or_create_material(matname):
    material_data = read_material_flag(matname)

    material = bpy.data.materials.get(matname)
    if material is None:
        material = bpy.data.materials.new(name=matname)
        collision_color = get_collision_color(f"0x{material_data[0]}")
        print(collision_color)
        material.diffuse_color = collision_color
        principled = material.node_tree.nodes["Principled BSDF"]
        principled.inputs["Base Color"].default_value = collision_color
    return material

class SoundValueProperties(bpy.types.PropertyGroup):
    col_flag: EnumProperty(name = "Flags",
        items = [("0x00", "0x00", ""),
                 ("0x01", "0x01", ""),
                 ("0x02", "0x02", ""),
                 ("0x03", "0x03", ""),
                 ("0x04", "0x04", ""),
                 ("0x05", "0x05", ""),
                 ("0x06", "0x06", ""),
                 ("0x07", "0x07", ""),
                 ("0x08", "0x08", ""),
                 ("0x09", "0x09", ""),
                 ("0x0A", "0x0A", ""),
                 ("0x0B", "0x0B", ""),
                 ("0x0C", "0x0C", ""),
                 ("0x0D", "0x0D", ""),
                 ("0x0E", "0x0E", ""),
                 ("0x0F", "0x0F", ""),
                 ("0x10", "0x10", ""),
                 ("0x11", "0x11", ""),
                 ("0x12", "0x12", ""),
                 ("0x13", "0x13d", ""),
                 ("0x37", "0x37", ""),
                 ("0x47", "0x47", "")],
        update = dummyBCOFunction,
        default = "0x01")
    col_attribute: IntProperty(name = "sound_id", min=0, max=255, default=0)
    sound_id: IntProperty(name = "sound_id", min=0, max=255, default=0)

class BCOProperties(bpy.types.PropertyGroup):
    track_slots: EnumProperty(name = "Slots",
        items = [("24", "Luigi Circuit", ""), ("22", "Peach Beach", ""), ("21", "Baby Park", ""), ("32", "Dry Dry Desert", ""),
                 ("28", "Mushroom Bridge", ""), ("25", "Mario Circuit", ""), ("23", "Daisy Cruiser", ""), ("2a", "Waluigi Stadium", ""),
                 ("33", "Sherbet Land", ""), ("29", "Mushroom City", ""), ("26", "Yoshi Circuit", ""), ("2d", "DK Mountain", ""),
                 ("2b", "Wario Colosseum", ""), ("2c", "Dino Dino Jungle", ""), ("2f", "Bowser's Castle", ""), ("31", "Rainbow Road", ""),
                 ("3a", "Cookie Land", ""), ("36", "Block City", ""), ("35", "Nintendo Gamecube", ""),
                 ("3b", "Pipe Plaza", ""), ("34", "Luigi's Mansion", ""), ("38", "Tilt-a-Kart", "")],
        update = dummyBCOFunction)

    bco_flags: EnumProperty(name = "Flags",
        items = [("0x00", "0x00 - Medium Offroad", ""),
                 ("0x01", "0x01 - Normal Road", ""),
                 ("0x02", "0x02 - Wall (Player + Item)", ""),
                 ("0x03", "0x03 - Offroad", ""),
                 ("0x04", "0x04 - Slippery Ice", ""),
                 ("0x05", "0x05 - Deadzone (Horizontal Bar)", ""),
                 ("0x06", "0x06 - Unknown", ""),
                 ("0x07", "0x07 - Boost (on a ramp)", ""),
                 ("0x08", "0x08 - Boost", ""),
                 ("0x09", "0x09 - Cannon", ""),
                 ("0x0A", "0x0A - Deadzone (Circle)", ""),
                 ("0x0B", "0x0B - Road", ""),
                 ("0x0C", "0x0C - Weak Offroad", ""),
                 ("0x0D", "0x0D - Pipe Teleportation", ""),
                 ("0x0E", "0x0E - Deadzone (Sand)", ""),
                 ("0x0F", "0x0F - Deadzone (Wavy)", ""),
                 ("0x10", "0x10 - Deadzone (Quicksand Sinkhole)", ""),
                 ("0x11", "0x11 - Peach Beach Sand", ""),
                 ("0x12", "0x12 - Wall (Player Only)", ""),
                 ("0x13", "0x13 - Heavy Offorad", ""),
                 ("0x37", "0x37 - Boost (on a large ramp)", ""),
                 ("0x47", "0x47 - Boost (on a large ramp)", "")],
        update = dummyBCOFunction,
        default = "0x01")

    #col materials by course
    effect_material: IntProperty(name = "effect_material", min=0, max=14, default=0)
    jugem_point: IntProperty(name = "jugem_point", min=0, max=255, default=0)
    other_attr: IntProperty(name = "addi_attr", min=0, max=255, default=0)

    #look into more
    camera_code: EnumProperty(name = "Camera Code",
        items = [("0x00", "0x00 - Unknown", ""),
                 ("0x01", "0x01 - Default", ""),
                 ("0x02", "0x02 - Unknown", ""),
                 ("0x03", "0x03 - Unknown", ""),
                 ("0x04", "0x04 - Unknown", ""),
                 ("0x05", "0x05 - Unknown", "")],
        update = dummyBCOFunction,
        default = "0x01")

    #0x20 bytes
    thickness_value: IntProperty(name="Thickness Value", min=0, max=15, default=0)
    disallow_items: BoolProperty(name="Prevent Items", default=False)

    #0x21 byte - look into more

    #0x22 byte
    stagger_code: BoolProperty(name="Stagger Code", default=False)
    spiral_code: BoolProperty(name="Spiral Code", default=False)

    #0x23 byte
    geosplash_id: IntProperty(name="Geosplash ID", min=0, max=255, default=0)

    #Sound Values
    sound_values: CollectionProperty(type=SoundValueProperties)

class import_bco_file(bpy.types.Operator, ImportHelper):
    bl_idname = "bco.import_bco"
    bl_label = "Import BCO"
    filename_ext = '.bco'
    bl_options = {'UNDO'}
    bl_description = "Loads BCO file"

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for importing the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )

    filter_glob: StringProperty(
        default='*.bco',
        options={'HIDDEN'}
    )

    bco_prerotate_mesh: BoolProperty(name = "Rotate Mesh", default=True)
    bco_import_scale : FloatProperty(name = "Import Scale", default=1, max=100,min=0.0001)

    def create_materials_mapping(self, raw_material_data):
        materials = {}

        for material in raw_material_data:
            material_name = bco_material_name_prefix + f"0x{material[0]:0{4}X}"
            if material[1] != 0x1 or material[2] != 0:
                material_name += f"_0x{material[1]:0{2}X}_0x{material[2]:0{8}X}"
            if material not in materials:
                materials[material] = material_name
        return materials

    def assign_collision_materials(self, collision_object, material_data):
        #From the material tuple (flag,camera,settings) to a material name
        material_mapping = self.create_materials_mapping(material_data)

        collision_bmesh = bmesh.new()
        collision_bmesh.from_mesh(collision_object.data)
        collision_bmesh.faces.ensure_lookup_table()

        current_materials = [slot.material for slot in collision_object.material_slots]

        for i, face in enumerate(collision_bmesh.faces):

            material_name = material_mapping[material_data[i]]
            material = get_or_create_material(material_name)

            if material not in current_materials:
                material_index = len(current_materials)
                collision_object.data.materials.append(material)
                current_materials.append(material)
            else:
                material_index = current_materials.index(material)
            face.material_index = material_index
        collision_bmesh.to_mesh(collision_object.data)
        collision_bmesh.free()

    def execute(self, context):
        scene = context.scene
        mkdd_bco_tool = scene.mkdd_bco_tool

        if(bpy.context.active_object):
            bpy.ops.object.mode_set(mode='OBJECT')
        bpy.ops.object.select_all(action='DESELECT')

        with open(self.filepath, "rb") as f:
            col = bco_reader.RacetrackCollision()
            col.load_file(f)

        collision_mesh = bpy.data.meshes.new("imported_collision_mesh")
        vertices = col.get_python_vertices(rotate_poster = self.bco_prerotate_mesh, scale = self.bco_import_scale)
        faces, materials = col.get_python_faces_materials()
        collision_mesh.from_pydata(vertices, [], faces)
        collision_mesh.update()
        file_name = os.path.basename(self.filepath)
        collision_object = bpy.data.objects.new(file_name, collision_mesh)

        self.assign_collision_materials(collision_object, materials)
        collision_mesh.update()

        for sound in col.matentries:
            new_item = mkdd_bco_tool.sound_values.add()
            new_item.col_flag = f"0x{sound.col_flag:0{2}X}"
            new_item.col_attribute = sound.col_attr
            new_item.sound_id = sound.sound_value

        bpy.context.scene.collection.objects.link(collision_object)
        return {'FINISHED'}

class export_bco_file(bpy.types.Operator, ExportHelper):
    bl_idname = "bco.export_bco"
    bl_label = "Export BCO"
    bl_options = {'UNDO','PRESET'}
    filename_ext = ".bco"

    filter_glob: StringProperty(
        default='*.bco',
        options={'HIDDEN'}
    )

    filepath: StringProperty(
        name="File Path",
        description="Filepath used for exporting the file",
        maxlen=1024,
        subtype='FILE_PATH',
    )
    check_existing: BoolProperty(
        name="Check Existing",
        description="Check and warn on overwriting existing files",
        default=True,
        options={'HIDDEN'},
    )

    bco_export_only_visible: BoolProperty(name="Export Only Visible", default=True)
    bco_export_only_selected: BoolProperty(name="Export Only Selected", default=False)

    bco_prerotate_mesh: BoolProperty(name = "Rotate Mesh", default=True)
    bco_export_scale : FloatProperty(name = "Export Scale", default=1, max=100,min=0.0001)

    bco_remove_steep_faces: BoolProperty(name="Remove steep faces", default=True, description="If set, remove steep faces from being exported")
    bco_steep_face_angle: FloatProperty(name="Steep Face Angle", default=89.5, max=90, min=0, description="Minimum angle from the horizontal in degrees a face needs to have to count as a steep face.")
    bco_cell_size: IntProperty(name="Cell Size", default=100, max=100000, min=1, description="Size of a single cell in the grid. Bigger size results in smaller grid size but higher amount of triangles in a single cell")
    bco_quadtree_depth: IntProperty(name="Quadtree Depth", default=2, max=10, min=1, description="Depth of the quadtree structure that's used for optimizing collision detection. "
                              "Quadtrees are used to subdivide cells in the grid further when a cell has too many triangles.")
    bco_max_tri_count: IntProperty(name="Max Quadtree Tri Count", default=20, max=100, min=1, description="The maximum amount of triangles a cell or a leaf of a quadtree is allowed to have before it is subdivided further.")

    def get_export_objects(self, context):
        scene = context.scene
        scene_objects = set(o for o in scene.objects if o.type == 'MESH')

        if self.bco_export_only_visible:
            scene_objects = set([o for o in scene_objects if o.visible_get()])
        if self.bco_export_only_selected:
            scene_objects = set([o for o in scene_objects if o.select_get()])

        return scene_objects

    def get_vertices_faces_from_objects(self, collision_objects):
        vertices = []
        faces = []

        def chunk_mat_data(mat_data):
            if not mat_data or len(mat_data) != bco_material_data_len:
                return None
            return (int(f"{mat_data[0]}{mat_data[1]}", 16), int(f"{mat_data[2]}", 16),
                    int(f"{mat_data[3]}{mat_data[4]}00{mat_data[5]}{mat_data[6]}{mat_data[7]}", 16))

        for collision_object in collision_objects:
            col_mats = [slot.material.name for slot in collision_object.material_slots]
            col_mats = [read_material_flag(mat_name) for mat_name in col_mats]
            if not list(filter(lambda x: x is not None, col_mats)):
                continue
            col_mats = [chunk_mat_data(mat_info) for mat_info in col_mats]

            used_vertices = set()
            object_faces = []
            for polygon in collision_object.data.polygons:
                if len(polygon.vertices) < 3:
                    continue

                mat_info = col_mats[polygon.material_index]
                if not mat_info:
                    continue

                for i in range(1, len(polygon.vertices) - 1):
                    object_faces.append((polygon.vertices[0], polygon.vertices[i], polygon.vertices[i+1],
                                                mat_info[0], mat_info[1], mat_info[2]))
                    used_vertices.update([polygon.vertices[0], polygon.vertices[i], polygon.vertices[i+1]])

            used_vertices = sorted(list(used_vertices))
            used_vertices_map = {}
            used_vertices_cos = []
            for i, used_vertex in enumerate(used_vertices):
                used_vertices_map[used_vertex] = i
                used_vertices_cos.append(list(collision_object.matrix_world @ collision_object.data.vertices[used_vertex].co))

            for i, object_face in enumerate(object_faces):
                new_vertices = (used_vertices_map[object_face[0]], used_vertices_map[object_face[1]], used_vertices_map[object_face[2]])
                object_faces[i] = (new_vertices[0], new_vertices[1], new_vertices[2], object_face[3], object_face[4], object_face[5])

            vertices.extend(used_vertices_cos)
            faces.extend(object_faces)

        return vertices, faces

    def execute(self, context):
        scene = context.scene
        mkdd_bco_tool = scene.mkdd_bco_tool

        scene_objects = self.get_export_objects(context)
        vertices, faces = self.get_vertices_faces_from_objects(scene_objects)
        if not vertices or not faces:
            return {'CANCELLED'}
        if len(faces) > 2**16:
            return {'CANCELLED'}

        for vertex in vertices:
            vertex[0] = vertex[0] * self.bco_export_scale
            vertex[1] = vertex[1] * self.bco_export_scale
            vertex[2] = vertex[2] * self.bco_export_scale
            if self.bco_prerotate_mesh:
                vertex[1], vertex[2] = vertex[2], -vertex[1]

        grid = [vertices[0][0], vertices[0][2], vertices[0][0], vertices[0][2]]
        for vertex in vertices[1:]:
            grid[0] = min(grid[0], vertex[0])
            grid[1] = min(grid[1], vertex[2])
            grid[2] = max(grid[2], vertex[0])
            grid[3] = max(grid[3], vertex[2])

        sounds_map = {}
        for material in bpy.data.materials:
            col_props = read_material_flag(material.name)
            if not col_props:
                continue
            sound_values = (int(col_props[0], 16), int(col_props[1], 16))
            if sound_values not in sounds_map:
                sounds_map[sound_values] = 0
        for item in mkdd_bco_tool.sound_values:
            sounds[(item.col_flag, item.col_attribute)] = item.sound_value
        sounds = [(key[0], key[1], value) for key,value in sounds_map.items()]

        args = {"output":self.filepath,
                "remove_steep_faces": self.bco_remove_steep_faces, "steep_face_angle": self.bco_steep_face_angle,
                "cell_size": self.bco_cell_size,
                "quadtree_depth": self.bco_quadtree_depth, "max_quadtree_tri_count": self.bco_max_tri_count}

        bco_writer.export_bco(args, vertices, faces, grid, sounds)
        return {'FINISHED'}

def export_bco_button(self, context):
    self.layout.operator("bco.export_bco", text="Export BCO")
def import_bco_button(self, context):
    self.layout.operator("bco.import_bco", text="Import BCO")

class match_sound_with_used(bpy.types.Operator):
    bl_idname = "bco.matchsoundtypeused"
    bl_label = "Match With Used Flags"
    bl_options = {'UNDO'}
    bl_description = "Match with used flags"

    def get_collision_materials(self):
        used_collision_flags = set()
        for material in bpy.data.materials:
            col_props =  read_material_flag(material.name)
            if col_props:
                used_collision_flags.add((col_props[0], col_props[1]))
        return used_collision_flags

    def get_defined_sound_ids(self, mkdd_bco_tool):
        sound_values = {}
        for item in mkdd_bco_tool.sound_values:
            col_flag = item.col_flag[2:]
            col_attr = f"{item.col_attribute:0{2}X}"
            sound_values[(col_flag, col_attr)] = item.sound_id
        return sound_values

    def combine_sound_flags(self, used_collision_flags, defined_sound_ids):
        final_sound_ids = []
        for col_flag in used_collision_flags:
            sound_id = 0
            if col_flag in defined_sound_ids:
                sound_id = defined_sound_ids[col_flag]
            final_sound_ids.append((col_flag[0], col_flag[1], sound_id))
        final_sound_ids.sort()
        return final_sound_ids


    def execute(self, context):
        scene = context.scene
        mkdd_bco_tool = scene.mkdd_bco_tool

        used_collision_flags = self.get_collision_materials()
        defined_sound_ids = self.get_defined_sound_ids(mkdd_bco_tool)
        final_sound_ids = self.combine_sound_flags(used_collision_flags, defined_sound_ids)

        mkdd_bco_tool.sound_values.clear()
        for final_sound_id in final_sound_ids:
            new_item = mkdd_bco_tool.sound_values.add()
            new_item.col_flag = "0x" + final_sound_id[0]
            new_item.col_attr = int(final_sound_id[1])
            new_item.sound_id = final_sound_id[2]

        return {'FINISHED'}

class add_sound_type(bpy.types.Operator):
    bl_idname = "bco.addsoundtype"
    bl_label = "Add Sound Type"
    bl_options = {'UNDO'}
    bl_description = "Add sound type"

    def execute(self, context):
        scene = context.scene
        mkdd_bco_tool = scene.mkdd_bco_tool

        new_item = mkdd_bco_tool.sound_values.add()
        new_item.sound_id = 20

        return {'FINISHED'}


class BCOSoundTypes(bpy.types.Panel):
    bl_label = "Sound Types"
    bl_idname = "MKDD_PT_Bco_Sound_Types"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MKDD Utils"

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='SPEAKER')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mkdd_bco_tool = scene.mkdd_bco_tool

        layout.operator("bco.addsoundtype")
        layout.operator("bco.matchsoundtypeused")

        for item in mkdd_bco_tool.sound_values:
            row = layout.row()
            row.prop(item, "col_flag", text=f"Flag")
            row.prop(item, "col_attribute", text=f"Attr")
            row.prop(item, "sound_id", text=f"Sound")

class apply_bco_flag(bpy.types.Operator):
    bl_idname = "bco.applyflag"
    bl_label = "Apply Flag"
    bl_options = {'UNDO'}
    bl_description = "Apply current flag"

    @classmethod
    def poll(cls,context):
        return context.selected_objects

    def get_additional_index(self, mkdd_bco_tool):
        addi_index = mkdd_bco_tool.other_attr
        if mkdd_bco_tool.bco_flags in particle_coltypes:
            addi_index = mkdd_bco_tool.effect_material
        elif mkdd_bco_tool.bco_flags in respawn_coltypes:
            addi_index = mkdd_bco_tool.jugem_point

        return f"{addi_index:0{2}X}"

    def get_advanced_options(self, mkdd_bco_tool):
        advanced_options = "_"
        need_advanced_options = False

        advanced_options += mkdd_bco_tool.camera_code + "_0x"
        if mkdd_bco_tool.camera_code != mkdd_bco_tool.bl_rna.properties["camera_code"].default:
            need_advanced_options = True

        advanced_options += f"{mkdd_bco_tool.thickness_value:0X}"
        if mkdd_bco_tool.thickness_value != mkdd_bco_tool.bl_rna.properties["thickness_value"].default:
            need_advanced_options = True
        advanced_options += f"{int(mkdd_bco_tool.disallow_items):0X}"
        if mkdd_bco_tool.disallow_items != mkdd_bco_tool.bl_rna.properties["disallow_items"].default:
            need_advanced_options = True

        advanced_options += "00"

        advanced_options += f"{int(mkdd_bco_tool.stagger_code):0X}"
        if mkdd_bco_tool.stagger_code != mkdd_bco_tool.bl_rna.properties["stagger_code"].default:
            need_advanced_options = True
        advanced_options += f"{int(mkdd_bco_tool.spiral_code):0X}"
        if mkdd_bco_tool.spiral_code != mkdd_bco_tool.bl_rna.properties["spiral_code"].default:
            need_advanced_options = True

        advanced_options += f"{mkdd_bco_tool.geosplash_id:0{2}X}"
        if mkdd_bco_tool.geosplash_id != mkdd_bco_tool.bl_rna.properties["geosplash_id"].default:
            need_advanced_options = True

        if need_advanced_options:
            return advanced_options
        return ""

    def build_material_flag(self, mkdd_bco_tool):
        additional_index = self.get_additional_index(mkdd_bco_tool)
        advanced_options = self.get_advanced_options(mkdd_bco_tool)
        return f"Roadtype_{mkdd_bco_tool.bco_flags}{additional_index}{advanced_options}"

    def execute(self, context):
        scene = context.scene
        mkdd_bco_tool = scene.mkdd_bco_tool

        if not bpy.context.object:
            self.report({'WARNING'},"Check failed. No object found")
            return {'CANCELLED'}

        matname = self.build_material_flag(mkdd_bco_tool)
        material = get_or_create_material(matname)

        current_mode = bpy.context.object.mode
        selected_objects = context.selected_objects
        if current_mode == "EDIT":
            for selected_object in selected_objects:
                bm = bmesh.from_edit_mesh(selected_object.data)
                bm.faces.ensure_lookup_table()

                selected_object_materials = [slot.material for slot in selected_object.material_slots]
                material_index = len(selected_object_materials)
                if material not in selected_object_materials:
                    selected_object.data.materials.append(material)
                else:
                    material_index = selected_object_materials.index(material)

                selected_faces = [i for i, face in enumerate(bm.faces) if face.select]
                for i in selected_faces:
                    bm.faces[i].material_index = material_index
                bmesh.update_edit_mesh(selected_object.data)
        else:
            for selected_object in selected_objects:
                selected_object.data.materials.clear()
                selected_object.data.materials.append(material)

        return {'FINISHED'}

class BCOAdvancedOptions(bpy.types.Panel):
    bl_label = "Advanced Options"
    bl_idname = "MKDD_PT_Bco_Helper_Advanced"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MKDD Utils"
    bl_parent_id = "MKDD_PT_Bco_Helper"

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='FACESEL')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mkdd_bco_tool = scene.mkdd_bco_tool

        layout.prop(mkdd_bco_tool, "camera_code", text="Camera Code")
        layout.prop(mkdd_bco_tool, "thickness_value", text="Thickness Value (100 units)")
        layout.prop(mkdd_bco_tool, "disallow_items", text="Disallow Items")
        layout.prop(mkdd_bco_tool, "stagger_code", text="Stagger Code")
        layout.prop(mkdd_bco_tool, "spiral_code", text="Spiral Code")
        layout.prop(mkdd_bco_tool, "geosplash_id", text="Geosplash Id")


class BCOUtilities(bpy.types.Panel):
    bl_label = "BCO Utilities"
    bl_idname = "MKDD_PT_Bco_Helper"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "MKDD Utils"

    def draw_header(self, _):
        layout = self.layout
        layout.label(text="", icon='FACESEL')

    def draw(self, context):
        layout = self.layout
        scene = context.scene
        mkdd_bco_tool = scene.mkdd_bco_tool

        layout.prop(mkdd_bco_tool, "track_slots", text="Track Slot")
        layout.prop(mkdd_bco_tool, "bco_flags", text="BCO Flags")

        if mkdd_bco_tool.bco_flags in particle_coltypes:
            layout.prop(mkdd_bco_tool, "effect_material", text="Particle Effect")
        elif mkdd_bco_tool.bco_flags in respawn_coltypes:
            layout.prop(mkdd_bco_tool, "jugem_point", text="Respawn Point Index")
        else:
            layout.prop(mkdd_bco_tool, "other_attr", text="Additional Attribute")

        layout.operator("bco.applyflag")

def menu_func(self, context):
    self.layout.operator(BCOUtilities.bl_idname)

classes = (import_bco_file, export_bco_file, match_sound_with_used, add_sound_type, SoundValueProperties, BCOProperties, BCOUtilities, BCOAdvancedOptions, apply_bco_flag, BCOSoundTypes)

def register():
    for cls in classes:
        bpy.utils.register_class(cls)

    bpy.types.TOPBAR_MT_file_export.append(export_bco_button)
    bpy.types.TOPBAR_MT_file_import.append(import_bco_button)

    bpy.types.Scene.mkdd_bco_tool = PointerProperty(type= BCOProperties)
    bpy.types.VIEW3D_MT_object.append(menu_func)

def unregister():
    for cls in reversed(classes):
        bpy.utils.unregister_class(cls)

    bpy.types.TOPBAR_MT_file_export.remove(export_bco_button)
    bpy.types.TOPBAR_MT_file_import.remove(import_bco_button)

    del bpy.types.Scene.mkdd_bco_tool

if __name__ == "__main__":
    register()