# LockIK Blender Addon

This add-on initially was designed for cases when there's a pre-existing animation, such as one from Mixamo, and there's a need to adjust the pose.
The LockIK add-on allows the swift creation of Inverse Kinematic constraints and adds a target to lock bones to a specific position.
For each locked bone, the add-on adds only one constraint and one additional helper bone.
Upon 'Baking', these extra elements are removed, ensuring that the armature retains only the desired adjustments.
Unlike simply applying the constraint, this add-on allows you to see the exact final result throughout the process, which makes adjusting poses more intuitive and precise.


The LockIK addon for Blender provides users with additional tools to work with Inverse Kinematics (IK) in rigging and animation. This addon allows users to create a temporary custom bone at an existing bone's tail position and set it as the target of an IK constraint, facilitating adjustments for the character pose. A pole target can also be added to better control the IK chain's bending direction. The LockIK addon primarily contributes to a smoother and more efficient workflow for pose adjustments in character animation.

## Features and Usage

### Lock Selected Bones: 

This command adds an IK Constraint to the currently selected pose bones, with a new temporary helper bone at the tail's position as the target of the IK. A visual cube marker will be created for the helper bone if it doesn't already exist. This tool can be activated by clicking the "Lock Selected Bones" button in the 3D View toolbar.

### Insert Keyframes Operator:

This operator inserts a keyframe for every bone's location and rotation, without clearing the IK locks. Use the Ctrl + Middle Mouse Button Click shortcut to activate this operator.

### Bake/Unlock All:

This command bakes all IK constraints, inserting keyframes to preserve the pose and removing IK locks. Unlocking includes deleting all helper bones and removing their references. The operation can be activated by clicking the "Bake/Unlock all" button in the 3D View toolbar.

### Add Pole Target:

This command adds a pole target at the head location of the selected bone with IK. This tool can be activated by clicking the "Add Pole Target" button in the 3D View toolbar.

### Adjust IK Chain Length:

This command allows you to increase or decrease the chain length of a locked bone using the mouse scroll wheel. First, select a locked bone or its helper bone(Pole or Target). Then, press and hold Ctrl, and scroll the mouse wheel up or down to increase or decrease the chain length respectively. The addon will display the adjusted length on the bottom of Blender's screen.

### Remove IK Operator:

This command allows you to remove an LockIK IK constraint from the original bone and delete all helper bones (including pole targets) associated with the given bone if they exist without baking/inserting keyframes. This tool can be activated by clicking the "Remove IK" button in the 3D View toolbar.

## Examples


![Example](https://github.com/FenyxInvincible/lockik/blob/main/example.gif?raw=true)
