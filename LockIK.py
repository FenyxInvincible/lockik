bl_info = {
    "name": "LockIK",
    "author": "Yevhen Rebrakov",
    "version": (1, 0),
    "blender": (2, 91, 2),
    "location": "View3D > Toolbar",
    "description": "Allows to add IK to bone and lock it's position",
    "warning": "", 
    "category": "3D View"
}

import bpy
import mathutils

# Global list to store the bones with IK, 
# and a dictionary to store the IK settings
bones_with_ik = []
ik_settings = {}

class LockSelectedBonesOperator(bpy.types.Operator):
    bl_idname = "object.lock_selected_bones_operator"
    bl_label = "Lock Selected Bones"
    bl_description = "Adds an IK constraint to the selected bones, creates a temporary custom bone at tail position and sets it as the IK target."

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE'

    def execute(self, context):
        # Create the custom shape cube if it doesn't exist
        armature = context.object
        shape_cube = bpy.data.objects.get('LockIKTargetDisplay')
        if shape_cube is None:
            bpy.ops.object.mode_set(mode='OBJECT')
            bpy.ops.mesh.primitive_cube_add(size=0.2, enter_editmode=False, align='WORLD', location=(0, 0, 0), scale=(1, 1, 1))
            shape_cube = bpy.context.object
            shape_cube.name = 'LockIKTargetDisplay'
            shape_cube.hide_set(True)
            # Switch back to pose mode
            bpy.context.view_layer.objects.active = armature  # Restore the active object to armature
            bpy.ops.object.mode_set(mode='POSE')

        # Get the armature from the context object
        armature = context.object

        for bone in bpy.context.selected_pose_bones:

            # Check if the bone already has a LockIK constraint
            if 'LockIK' not in (c.name for c in bone.constraints):

                # Save the currently selected armature
                saved_armature = context.active_object

                bpy.ops.object.mode_set(mode='EDIT')

                # Create the helper bone at the tail location
                helper_bone = armature.data.edit_bones.new(bone.name + "_LockIKTarget")
                helper_bone.head = bone.tail
                helper_bone.tail = bone.tail + mathutils.Vector((0, 0.2, 0))  # Give the bone some length
                helper_bone.parent = None  # The helper bone is not connected to the parent
                helper_bone_name = helper_bone.name
    
                # Switch back to pose mode for setting the IK constraint
                bpy.ops.object.mode_set(mode='POSE')
    
                # Add an IK constraint to the selected bone with the helper bone as the target
                helper_pose_bone = armature.pose.bones[helper_bone_name]
                helper_pose_bone.custom_shape = shape_cube
    
                constraint = bone.constraints.new('IK')
                constraint.name = 'LockIK'
                constraint.target = saved_armature
                constraint.subtarget = helper_bone_name
    
                # If settings exist in the ik_settings dictionary, use them
                if bone.name in ik_settings:
                    constraint.iterations = ik_settings[bone.name]['iterations']
                    constraint.chain_count = ik_settings[bone.name]['chain_count']
                    constraint.use_tail = ik_settings[bone.name]['use_tail']
    
                # Otherwise, calculate chain length based on connected parent bones
                else:
                    parent_bone = bone.parent
                    chain_length = 1
                    while parent_bone and parent_bone.bone.use_connect:
                        chain_length += 1
                        parent_bone = parent_bone.parent
                    constraint.chain_count = chain_length + 1  # Include the bone itself in the chain length

        return {'FINISHED'}

class InsertKeyframesOperator(bpy.types.Operator):
    bl_idname = "object.insert_keyframes_operator"
    bl_label = "Insert Keyframes"
    bl_description = " Doesn't clear IK lock. Inserts a keyframe for every bone's location and rotation, not only for the selected ones."

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE'

    def execute(self, context):

        # Remember if a single helper bone is selected
        selected_helper_bone_name = None
        if is_helper_bone_selected(context):
            selected_helper_bone_name = context.selected_pose_bones[0].name

        # Execute the bake operator
        bpy.ops.object.bake_operator()

        armature = bpy.context.object

        # Unselect all bones
        bpy.ops.pose.select_all(action='DESELECT')
        
        for bone_name in bones_with_ik:
            bone = armature.data.bones.get(bone_name)
            if bone:
                bone.select = True
                armature.data.bones.active = bone
    
        # Execute the Lock Selected Bones operator on the selected bones
        bpy.ops.object.lock_selected_bones_operator()

        # If a single helper bone was selected, select it again, otherwise select bones in the bones_with_ik list
        if selected_helper_bone_name is not None:
            helper_bone = armature.data.bones.get(selected_helper_bone_name)
            if helper_bone:
                bpy.ops.pose.select_all(action='DESELECT')
                helper_bone.select = True
                armature.data.bones.active = helper_bone
        return {'FINISHED'}
        
def save_bone_transforms(bone):
    saved_transforms[bone.name] = bone.matrix.copy()
    for child in bone.children:
        save_bone_transforms(child)

def restore_bone_transforms(bone):
    if bone.name in saved_transforms:
        bone.matrix = saved_transforms[bone.name]
    bone.keyframe_insert(data_path="location", frame=bpy.context.scene.frame_current)
    bone.keyframe_insert(data_path="rotation_quaternion", frame=bpy.context.scene.frame_current)
    for child in bone.children:
        restore_bone_transforms(child)

def remove_ik_constraints(bone):
    
    for constraint in bone.constraints:
        if constraint.name == 'LockIK':
            bones_with_ik.append(bone.name)
            ik_settings[bone.name] = {
                'iterations': constraint.iterations,
                'chain_count': constraint.chain_count,
                'use_tail': constraint.use_tail
            }
            #bpy.data.objects.remove(constraint.target, do_unlink=True)  # Removing the target cube
            bone.constraints.remove(constraint)  # Removing the constraint
            
    for child in bone.children:
        remove_ik_constraints(child)

def is_helper_bone_selected(context):
    return (len(context.selected_pose_bones) == 1 and
            (context.selected_pose_bones[0].name.endswith('_Pole_LockIKTarget') or
             context.selected_pose_bones[0].name.endswith('_LockIKTarget')))

def get_original_bone(context):
    if len(context.selected_pose_bones) != 1:
        return False
    bone = context.selected_pose_bones[0]
    if bone.name.endswith('_Pole_LockIKTarget'):
        return context.object.pose.bones[bone.name.replace('_Pole_LockIKTarget', '')]
    elif bone.name.endswith('_LockIKTarget'):
        return context.object.pose.bones[bone.name.replace('_LockIKTarget', '')]
    elif 'LockIK' in (c.name for c in bone.constraints):
        return bone
    else:
        return False

class AddPoleTargetOperator(bpy.types.Operator):
    bl_idname = "object.add_pole_target_operator"
    bl_label = "Add Pole Target"
    bl_description = "Adds a pole target for the selected bones"

    @classmethod
    def poll(cls, context):
        if context.mode != 'POSE':
            return False

        # Check if all selected pose bones have a LockIK constraint
        armature = context.object
        for bone in context.selected_pose_bones:
            if 'LockIK' not in (c.name for c in bone.constraints):
                return False

        return True

    def execute(self, context):
        armature = context.object

        for bone in context.selected_pose_bones:
            # Assuming 'LockIK' is the name of the IK constraint
            constraint = bone.constraints['LockIK']

            # Create the pole target bone at the head location
            bpy.ops.object.mode_set(mode='EDIT')
            pole_helper_bone = armature.data.edit_bones.new(bone.name + "_Pole_LockIKTarget")
            pole_helper_bone.head = bone.head
            pole_helper_bone.tail = bone.head + mathutils.Vector((0, 0.1, 0))  # Should be adjusted according to your requirements
            pole_helper_bone.parent = None  # The helper bone is not connected to the parent
            pole_helper_bone_name = pole_helper_bone.name

            bpy.ops.object.mode_set(mode='POSE')

            # Set helper_bone custom shape to shape_cube 
            pole_helper_pose_bone = armature.pose.bones[pole_helper_bone_name]

            # Add custom shape
            shape_cube = bpy.data.objects.get('LockIKTargetDisplay')
            if shape_cube is not None:  # Make sure the cube exists
                pole_helper_pose_bone.custom_shape = shape_cube

            # Set the created helper bone as the pole target
            constraint.pole_target = armature
            constraint.pole_subtarget = pole_helper_bone_name

            # Compute the pole angle (if needed) and assign to the constraint here

        return {'FINISHED'}

class BakeOperator(bpy.types.Operator):
    bl_idname = "object.bake_operator"
    bl_label = "Bake/Unlock all"
    bl_description = " Clear IK constraints for all locked bones. Inserts a keyframe for every bone's location and rotation, not only for the selected ones."

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE'

    def execute(self, context):
        global saved_transforms
        saved_transforms = {}
        
        bones_with_ik.clear()
        
        armature = context.object  # get the armature from the context object

        for bone in armature.pose.bones:
            save_bone_transforms(bone)
            remove_ik_constraints(bone)
            restore_bone_transforms(bone)

         # Switch to edit mode to remove all helper bones at once
        bpy.ops.object.mode_set(mode='EDIT')
        armature = context.object  # Reobtain the reference after mode switching

        print("Removing helper bones")
        for bone in armature.data.edit_bones:
            # The name check ensures only helper bones are removed
            if "_LockIKTarget" in bone.name:
                print(bone.name)
                armature.data.edit_bones.remove(bone)

        # Return to pose mode after all helper bones were removed
        bpy.ops.object.mode_set(mode='POSE')
        
        if armature.animation_data is not None and armature.animation_data.action is not None:
            fcurves = armature.animation_data.action.fcurves
            # Iterate in reverse so we can safely delete items
            for i in reversed(range(len(fcurves))):
                if "_LockIKTarget" in fcurves[i].data_path:
                    fcurves.remove(fcurves[i])
        
        return {'FINISHED'}

class AdjustChainLengthOperator(bpy.types.Operator):
    bl_idname = "object.adjust_chain_length_operator"
    bl_label = "Adjust IK Chain Length"
    bl_description = "Increases or decreases the pole length depending on the mouse scroll direction."
    direction: bpy.props.IntProperty()  # still need this to store the scroll direction

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and get_original_bone(context) is not False

    def execute(self, context):
        armature = bpy.context.object
        original_bone = get_original_bone(context)
        if not original_bone:
            return {'CANCELLED'}

        # Check if the bone's name is in the ik_settings
        if original_bone.name not in ik_settings:
            ik_settings[original_bone.name] = {
                'iterations': None,
                'chain_count': None,
                'use_tail': None
            }

        # Find the IK constraint and adjust its pole length
        for constraint in original_bone.constraints:
            if constraint.type == 'IK':
                constraint.chain_count = max(0, constraint.chain_count + self.direction)
                ik_settings[original_bone.name]['chain_count'] = constraint.chain_count
                # Show a message with the adjusted chain length
                self.report({'INFO'}, f"Adjusted length to {constraint.chain_count}")
        return {'FINISHED'}

class RemoveIKOperator(bpy.types.Operator):
    bl_idname = "object.remove_ik_operator"
    bl_label = "Remove IK"
    bl_description = "Remove an IK constraint, and delete helper bone if it exists."

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE' and get_original_bone(context) is not False

    def execute(self, context):
        original_bone = get_original_bone(context)
        if not original_bone:
            self.report({'ERROR'}, "No valid bone to remove IK from.")
            return {'CANCELLED'}

        # Remove the 'LockIK' constraint from the original bone, if exists
        for constraint in original_bone.constraints:
            if constraint.type == 'IK' and 'LockIK' in constraint.name:
                original_bone.constraints.remove(constraint)

        # Delete the helper bones, if they exist
        remove_bone_names = [original_bone.name + suffix for suffix in ['_LockIKTarget', '_Pole_LockIKTarget']]
        remove_bones = [context.object.pose.bones.get(bone_name) for bone_name in remove_bone_names]
        if any(remove_bones):
            bpy.ops.object.mode_set(mode='EDIT')
            for remove_bone_name in remove_bone_names:
                edit_bone = context.object.data.edit_bones.get(remove_bone_name)  # Get the EditBone
                if edit_bone:
                    context.object.data.edit_bones.remove(edit_bone)
            bpy.ops.object.mode_set(mode='POSE')

        self.report({'INFO'}, f"Removed IK from {original_bone.name}")
        return {'FINISHED'}

class LockIK_Panel(bpy.types.Panel):
    bl_label = "LockIK"
    bl_idname = "OBJECT_PT_ikh_handler"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'UI'
    bl_category = 'Animation'

    @classmethod
    def poll(cls, context):
        return context.mode == 'POSE'

    def draw(self, context):
        layout = self.layout
        layout.operator("object.lock_selected_bones_operator")
        layout.operator("object.add_pole_target_operator")
        if RemoveIKOperator.poll(context) != False:
            layout.operator("object.remove_ik_operator")
        
        layout.operator("object.insert_keyframes_operator")
        layout.operator("object.bake_operator")
        # Draw label if AdjustPoleLengthOperator can be executed
        if AdjustChainLengthOperator.poll(context) != False:
            layout.label(text="Press Ctrl + Mouse Wheel to adjust chain length")

def register():
    bpy.utils.register_class(LockSelectedBonesOperator)
    bpy.utils.register_class(BakeOperator)
    bpy.utils.register_class(InsertKeyframesOperator)
    bpy.utils.register_class(LockIK_Panel)
    bpy.utils.register_class(AddPoleTargetOperator)
    bpy.utils.register_class(AdjustChainLengthOperator)
    bpy.utils.register_class(RemoveIKOperator)

    # create keymap items
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        km = kc.keymaps.new(name='3D View', space_type='VIEW_3D')
        kmi = km.keymap_items.new(AdjustChainLengthOperator.bl_idname, 'WHEELUPMOUSE', 'PRESS', ctrl=True)
        kmi.properties.direction = 1
        
        kmi = km.keymap_items.new(AdjustChainLengthOperator.bl_idname, 'WHEELDOWNMOUSE', 'PRESS', ctrl=True)
        kmi.properties.direction = -1

        km.keymap_items.new(InsertKeyframesOperator.bl_idname, 'MIDDLEMOUSE', 'PRESS', ctrl=True)

def unregister():
    bpy.utils.unregister_class(LockSelectedBonesOperator)
    bpy.utils.unregister_class(BakeOperator)
    bpy.utils.unregister_class(InsertKeyframesOperator)
    bpy.utils.unregister_class(LockIK_Panel)
    bpy.utils.unregister_class(AddPoleTargetOperator)
    bpy.utils.unregister_class(AdjustChainLengthOperator)
    bpy.utils.unregister_class(RemoveIKOperator)

    # remove keymap items
    kc = bpy.context.window_manager.keyconfigs.addon
    if kc:
        for kmi in km.keymap_items:
            if kmi.idname in ["object.adjust_chain_length_operator","object.insert_keyframes_operator"]:
                km.keymap_items.remove(kmi)

if __name__ == "__main__":
    register()
