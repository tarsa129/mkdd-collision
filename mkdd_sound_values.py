import bpy
from bpy.props import EnumProperty, IntProperty

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
        default = "0x01")
    col_attribute: IntProperty(name = "sound_id", min=0, max=255, default=0)
    sound_id: IntProperty(name = "sound_id", min=0, max=255, default=0)

def get_defined_sound_ids(mkdd_bco_tool):
    sound_values = {}
    for item in mkdd_bco_tool.sound_values:
        col_flag = item.col_flag[2:]
        col_attr = f"{item.col_attribute:0{2}X}"
        sound_values[(col_flag, col_attr)] = item.sound_id
    return sound_values

def combine_sound_flags(used_collision_flags, defined_sound_ids):
    final_sound_ids = []
    for col_flag in used_collision_flags:
        sound_id = 0
        if col_flag in defined_sound_ids:
            sound_id = defined_sound_ids[col_flag]
        final_sound_ids.append((col_flag[0], col_flag[1], sound_id))
    final_sound_ids.sort()
    return final_sound_ids

def write_sound_values(mkdd_bco_tool, final_sound_ids):
    mkdd_bco_tool.sound_values.clear()
    for final_sound_id in final_sound_ids:
        new_item = mkdd_bco_tool.sound_values.add()
        new_item.col_flag = "0x" + final_sound_id[0]
        new_item.col_attribute = int(final_sound_id[1])
        new_item.sound_id = final_sound_id[2]

def sync_sound_values(mkdd_bco_tool, col_mat_info, incoming_sound_entries = {}):
    used_collision_flags = set([(col_props[0], col_props[1]) for col_props in col_mat_info])
    defined_sound_ids = get_defined_sound_ids(mkdd_bco_tool) | incoming_sound_entries
    final_sound_ids = combine_sound_flags(used_collision_flags, defined_sound_ids)
    write_sound_values(mkdd_bco_tool, final_sound_ids)