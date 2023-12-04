#!/usr/bin/python

import sys
import math
import rospy
import moveit_commander

from geometry_msgs.msg import Pose
from moveit_msgs.msg import CollisionObject
from shape_msgs.msg import SolidPrimitive

from tf.transformations import quaternion_from_euler

# roslaunch kortex_gazebo spawn_kortex_robot.launch gazebo_gui:=false arm:=gen3_lite
# roslaunch pick_place_python run_pick_place.launch

CANDLE_DIMS = [0.02, 0.02, 0.2]
CANDLE_POSITIONS = {'candle_0': [0.05, 0.40, 0.3],
                    'candle_1': [0.05, 0.45, 0.3],
                    'candle_2': [0.05, 0.50, 0.3]}
GRID_BOTTOM_LEFT = [0.4, 0.3, 0.3]
GRID_TOP_RIGHT = [0.55, 0.15, 0.3]
GRID_DIMS = [10, 10]

FRAME_ID = 'base_link'
(X, Y, Z, W) = (0, 1, 2, 3)
OPEN = 0.9
CLOSE = 0.15

PICK_ORIENTATION_EULER = [-math.pi / 2, 0, 0]
PLACE_ORIENTATION_EULER = [-math.pi / 2, 0, -math.pi / 2]
SCENE = moveit_commander.PlanningSceneInterface()

def grid_square_to_coord(x, y):
    grid_width = GRID_TOP_RIGHT[0] - GRID_BOTTOM_LEFT[0]
    grid_height = GRID_TOP_RIGHT[1] - GRID_BOTTOM_LEFT[1]

    goal_x = (grid_width / GRID_DIMS[0]) * x + GRID_BOTTOM_LEFT[0]
    goal_y = (grid_height / GRID_DIMS[1]) * y + GRID_BOTTOM_LEFT[1]

    return [goal_x, goal_y, GRID_BOTTOM_LEFT[2]]


def create_collision_object(id, dimensions, pose):
    object = CollisionObject()
    object.id = id
    object.header.frame_id = FRAME_ID

    solid = SolidPrimitive()
    solid.type = solid.BOX
    solid.dimensions = dimensions
    object.primitives = [solid]

    object_pose = Pose()
    object_pose.position.x = pose[X]
    object_pose.position.y = pose[Y]
    object_pose.position.z = pose[Z]

    object.primitive_poses = [object_pose]
    object.operation = object.ADD
    return object

def add_candles():
    for n in ['candle_0', 'candle_1', 'candle_2']:
        candle = create_collision_object(id=n,
                                         dimensions=CANDLE_DIMS,
                                         pose=CANDLE_POSITIONS[n])
        SCENE.add_object(candle)


def add_collision_objects():
    floor_limit = create_collision_object(id='floor_limit',
                                          dimensions=[10, 10, 0.2],
                                          pose=[0, 0, -0.1])
    table_1 = create_collision_object(id='table_1',
                                      dimensions=[0.3, 0.6, 0.2],
                                      pose=[0.45, 0.3, 0.1])
    table_2 = create_collision_object(id='table_2',
                                      dimensions=[0.3, 0.3, 0.2],
                                      pose=[0.15, 0.45, 0.1])

    SCENE.add_object(floor_limit)
    SCENE.add_object(table_1)
    SCENE.add_object(table_2)

    add_candles()


def reach_named_position(arm, target):
    arm.set_named_target(target)
    return arm.execute(arm.plan(), wait=True)


def reach_pose(arm, pose, tolerance=0.001):
    arm.set_pose_target(pose)
    arm.set_goal_position_tolerance(tolerance)
    return arm.go(wait=True)


def open_gripper(gripper):
    return gripper.move(gripper.max_bound() * OPEN, True)


def close_gripper(gripper):
    gripper.move(gripper.max_bound() * CLOSE, True)


def pick_object(name, arm, gripper):
    pose = Pose()
    pose.position.x = CANDLE_POSITIONS[name][X]
    pose.position.y = CANDLE_POSITIONS[name][Y] - 0.1
    pose.position.z = CANDLE_POSITIONS[name][Z]
    orientation = quaternion_from_euler(*PICK_ORIENTATION_EULER)
    pose.orientation.x = orientation[X]
    pose.orientation.y = orientation[Y]
    pose.orientation.z = orientation[Z]
    pose.orientation.w = orientation[W]
    reach_pose(arm, pose)
    open_gripper(gripper=gripper)
    pose.position.y += 0.1
    reach_pose(arm, pose)
    close_gripper(gripper=gripper)
    arm.attach_object(name)

def move_candle_to(arm, gripper, x, y):
    goal_pos = grid_square_to_coord(x, y)

    pose = Pose()
    pose.position.x = goal_pos[X]
    pose.position.y = goal_pos[Y]
    pose.position.z = goal_pos[Z]
    orientation = quaternion_from_euler(*PLACE_ORIENTATION_EULER)
    pose.orientation.x = orientation[X]
    pose.orientation.y = orientation[Y]
    pose.orientation.z = orientation[Z]
    pose.orientation.w = orientation[W]

    reach_pose(arm, pose)
    open_gripper(gripper=gripper)
    reach_pose(arm, pose)


def main():
    moveit_commander.roscpp_initialize(sys.argv)
    rospy.init_node('gen3_lite_pick_place')
    rospy.sleep(2)

    arm = moveit_commander.MoveGroupCommander('arm',
                                              ns=rospy.get_namespace())
    robot = moveit_commander.RobotCommander('robot_description')
    # gripper = robot.get_joint('finger_joint') # for gen3
    gripper = robot.get_joint('right_finger_bottom_joint')  # for gen3 lite

    arm.set_num_planning_attempts(45)

    add_collision_objects()

    done = False
    current_candle = None
    while not done:
        print("please input a command")
        command = raw_input()
        command = command.split()
        action = command[0]
        args = command[1:]

        if action == 'pickup':
            pick_object(name='candle_' + str(args[0]), arm=arm, gripper=gripper)
            current_candle = 'candle_' + str(args[0])
        elif action == "move-to":
            move_candle_to(arm=arm, gripper=gripper, x=float(args[0]), y=float(args[1]))
        elif action == "place":
            if current_candle is not None:
                arm.detach_object(current_candle)
            current_candle = None
        elif action == "stop":
            done = True


if __name__ == '__main__':
    main()