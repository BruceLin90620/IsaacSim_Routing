from launch import LaunchDescription
from launch_ros.actions import Node
from launch.actions import DeclareLaunchArgument,ExecuteProcess
from launch.substitutions import LaunchConfiguration

from rclpy.node import Node
from launch import LaunchContext, LaunchDescription, LaunchService
from launch.actions import RegisterEventHandler
from launch.events.process import ProcessStarted
from launch_ros.actions import Node
from launch.event_handlers import OnProcessExit,OnExecutionComplete,OnProcessStart


def generate_launch_description():

    runServer=ExecuteProcess(cmd=[['ros2 run routing_agent server']],shell=True)

    loadGraphArg=ExecuteProcess(cmd=[['ros2 run routing_agent loadGraph src/routing_engine/test_run/sample_data/waypointgraph.json']],shell=True)
    loadTaskAndVehicleArg=ExecuteProcess(cmd=[['ros2 run routing_agent routingClient src/routing_engine/test_run/sample_data/task_data.json src/routing_engine/test_run/sample_data/vehicle_data.json']],shell=True)

    # Define dependencies using event handlers
    process_2_after_1 = RegisterEventHandler(
        OnProcessStart(
            target_action=runServer,
            on_start=[loadGraphArg]
        )
    )

    process_3_after_2 = RegisterEventHandler(
        OnExecutionComplete(
            target_action=loadGraphArg,
            on_completion=[loadTaskAndVehicleArg]
        )
    )


    return LaunchDescription([
        runServer,
        process_2_after_1,
        process_3_after_2,
    ])