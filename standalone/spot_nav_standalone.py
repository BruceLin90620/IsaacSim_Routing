import argparse
from isaacsim import SimulationApp

simulation_app = SimulationApp({"renderer": "RayTracedLighting", "headless": False})

import omni
import carb
import numpy as np
import sys
from omni.isaac.core import World
from omni.isaac.core.utils.prims import define_prim, get_prim_at_path
from omni.isaac.nucleus import get_assets_root_path
from omni.isaac.quadruped.robots import SpotFlatTerrainPolicy
from omni.isaac.core.objects import VisualCuboid
from omni.isaac.core.utils.extensions import enable_extension

# enable ROS2 bridge extension
enable_extension("omni.isaac.ros2_bridge")

simulation_app.update()

import time

# Note that this is not the system level rclpy, but one compiled for omniverse
import numpy as np
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import Twist
from dataclasses import dataclass

@dataclass
class Pose:
    position = np.zeros(3)
    orientation = np.array([1.0, 0.0, 0.0, 0.0])



class SpotNav(Node):
    def __init__(self, env_usd_path, spot_init_pose: Pose):
        super().__init__("Spot_Nav")

        # setting up environment
        self.loadEnv(env_usd_path)

        self.first_step = True
        self.reset_needed = False
        self.cmd_scale = 1
        self.cmd = np.zeros(3) # [v_x, v_y, w_z]
        self.initSpot(spot_init_pose)

        self.ros_sub = self.create_subscription(Twist, "cmd_vel", self.spotCmdCallback, 1)
        self.world.reset()

    def spotCmdCallback(self, msg: Twist):
        if self.world.is_playing():
            self.cmd[0] = msg.linear.x * self.cmd_scale
            self.cmd[2] = msg.angular.z * self.cmd_scale

    def loadEnv(self, env_usd_path):
        assets_root_path = get_assets_root_path()
        if assets_root_path is None:
            carb.log_error("Could not find Isaac Sim assets folder")
            simulation_app.close()
            sys.exit()
        self.world = World(stage_units_in_meters=1.0, physics_dt=1 / 500, rendering_dt=1 / 50)

        prim = define_prim("/World/Ground", "Xform")
        asset_path = env_usd_path
        prim.GetReferences().AddReference(asset_path)
    
    def onPhysicStep(self, step_size):
        if self.first_step:
            self.spot.initialize()
            self.first_step = False
        elif self.reset_needed:
            self.world.reset(True)
            self.reset_needed = False
            self.first_step = True
        else:
            self.spot.advance(step_size, self.cmd)
        

    def initSpot(self, spot_init_pose: Pose):
        self.spot = SpotFlatTerrainPolicy(
            prim_path="/World/Spot",
            name="Spot",
            usd_path="omniverse://localhost/Library/spot.usd",
            position=spot_init_pose.position,
            orientation=spot_init_pose.orientation
        )
        self.world.add_physics_callback("physics_step", callback_fn=self.onPhysicStep)
        self.world.reset()

    def run_simulation(self):
        self.reset_needed = False
        while simulation_app.is_running():
            self.world.step(render=True)
            rclpy.spin_once(self, timeout_sec=0.0)
            if self.world.is_stopped():
                self.reset_needed = True

        # Cleanup
        self.destroy_node()
        simulation_app.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--env",
        type=str,
        choices=["lobby", "b1", "lab"],
        default="b1",
        help="Choice of navigation environment.",
    )
    args, _ = parser.parse_known_args()

    B1_USD_PATH = "omniverse://localhost/Library/tsmc_b1_map.usd"
    LOBBY_USD_PATH = "omniverse://localhost/Library/tsmc_1f_map.usd"
    LAB_USD_PATH = "omniverse://localhost/Library/MIT_LAB/MIT_LAB.usd"
    spot_init_pose = Pose()
    if args.env == "b1":
        ENV_USD_PATH = B1_USD_PATH
        spot_init_pose.position = np.array([6.65, -66.1, 0.8])
    elif args.env == "lobby":
        ENV_USD_PATH = LOBBY_USD_PATH
        spot_init_pose.position = np.array([214, -257.46, 0.8])
        spot_init_pose.orientation = np.array([0.707, 0, 0, 0.707])
    elif args.env == "lab":
        ENV_USD_PATH = LAB_USD_PATH
        spot_init_pose.position = np.array([12.58, 15.89, 0.87]) 
        spot_init_pose.orientation = np.array([0, 0, 0, np.pi])

    rclpy.init()
    subscriber = SpotNav(ENV_USD_PATH, spot_init_pose)
    subscriber.run_simulation()