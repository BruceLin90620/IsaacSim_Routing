#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseStamped
from tf_transformations import quaternion_from_euler 
from math import atan2
from routing_agent_interfaces.srv import NavServiceMsg
from nav2_simple_commander.robot_navigator import BasicNavigator, TaskResult
from rclpy.duration import Duration
from rclpy.qos import QoSProfile, ReliabilityPolicy, DurabilityPolicy
import json
import time


class MapManager(Node):
    def __init__(self):
        super().__init__('map_manager')
        
        # Initialize class variables
        self.path_sequence_ = []
        self.current_position_ = ""
        self.current_graph_ = {}
        self.current_map_id_ = 0
        self.last_known_position_ = None
        
        # Initialize the navigator
        self.navigator = BasicNavigator()
        
        qos = QoSProfile(
            depth=1,
            reliability=ReliabilityPolicy.RELIABLE,
            durability=DurabilityPolicy.TRANSIENT_LOCAL
        )
        
        # Create service client for navigation
        self.nav_service_client_ = self.create_client(
            NavServiceMsg,
            '/NavService',
            qos_profile = qos
        )
        
        # Wait for navigation to fully activate
        self.navigator.waitUntilNav2Active()

    def create_pose_stamped(self, target_x: float, target_y: float, current_x: float = None, current_y: float = None) -> PoseStamped:
        """Create a PoseStamped message with orientation based on movement direction
        
        Args:
            target_x: Target x coordinate
            target_y: Target y coordinate
            current_x: Current x coordinate (optional)
            current_y: Current y coordinate (optional)
        
        Returns:
            PoseStamped: The pose message with calculated orientation
        """
        pose = PoseStamped()
        pose.header.frame_id = 'map'
        pose.header.stamp = self.navigator.get_clock().now().to_msg()
        pose.pose.position.x = float(target_x)
        pose.pose.position.y = float(target_y)
        
        # Calculate orientation if current position provided
        if current_x is not None and current_y is not None:
            # Calculate direction vector
            dx = target_x - current_x  
            dy = target_y - current_y
            # Calculate yaw angle using atan2
            yaw = atan2(dy, dx)
            # Convert yaw to quaternion
            q = quaternion_from_euler(0, 0, yaw)
            pose.pose.orientation.x = q[0]
            pose.pose.orientation.y = q[1]
            pose.pose.orientation.z = q[2]
            pose.pose.orientation.w = q[3]
        else:
            # Default to forward orientation if no current position
            pose.pose.orientation.w = 1.0
        
        return pose

    def navigate_to_pose(self, goal_pose: PoseStamped) -> bool:
        """
        Navigate to the given pose
        
        Args:
            goal_pose: Target pose to navigate to
            
        Returns:
            bool: True if navigation succeeded, False otherwise
        """
        try:
            self.get_logger().info(f'Navigating to position: ({goal_pose.pose.position.x}, {goal_pose.pose.position.y})')
            
            # Send navigation goal
            self.navigator.goToPose(goal_pose)
            
            # Monitor navigation progress
            i = 0
            while not self.navigator.isTaskComplete():
                i += 1
                feedback = self.navigator.getFeedback()
                if feedback and i % 5 == 0:
                    remaining_time = Duration.from_msg(feedback.estimated_time_remaining).nanoseconds / 1e9
                    self.get_logger().info(f'ETA: {remaining_time:.0f} seconds')
                    
                    # Add timeout
                    if Duration.from_msg(feedback.navigation_time) > Duration(seconds=600.0):
                        self.navigator.cancelTask()
                        return False
                        
                # Process callbacks
                rclpy.spin_once(self, timeout_sec=0.1)
            
            # Check final result
            result = self.navigator.getResult()
            if result == TaskResult.SUCCEEDED:
                self.get_logger().info('Navigation succeeded!')
                return True
            else:
                self.get_logger().warning(f'Navigation failed with result: {result}')
                return False
                
        except Exception as e:
            self.get_logger().error(f'Error in navigate_to_pose: {str(e)}')
            return False

    def process_next_point(self, current_position: str) -> str:
        """
        Process the next point in the sequence
        
        Returns:
            str: The new current position after processing
        """
        try:
            if not self.path_sequence_:
                return current_position
                
            next_node_id = self.path_sequence_[0]
            
            # Extract map ID from node ID
            map_id = int(next_node_id[:3])
            
            if map_id != self.current_map_id_:
                self.get_logger().info(f'Map switch required from {self.current_map_id_} to {map_id}')
                self.current_map_id_ = map_id
            
            # 使用最後已知位置或當前位置
            if current_position in self.current_graph_:
                current_location = self.current_graph_[current_position]["local_location"]
                current_x, current_y = current_location[0], current_location[1]
                self.last_known_position_ = (current_x, current_y)
            elif self.last_known_position_ is not None:
                current_x, current_y = self.last_known_position_
                self.get_logger().info(f'Using last known position: ({current_x}, {current_y})')
            else:
                self.get_logger().warn(f'Current position {current_position} not found in graph, using (0,0)')
                current_x, current_y = 0.0, 0.0
                
            # Get target coordinates with validation
            if next_node_id not in self.current_graph_:
                self.get_logger().error(f'Next node {next_node_id} not found in graph')
                return current_position
                
            target_location = self.current_graph_[next_node_id]["local_location"]
            target_x, target_y = target_location[0], target_location[1]
            
            # Create goal pose with orientation
            goal_pose = self.create_pose_stamped(target_x, target_y, current_x, current_y)
            
            # Navigate to the pose
            success = self.navigate_to_pose(goal_pose)
            
            if success:
                # 成功導航後更新最後已知位置
                self.last_known_position_ = (target_x, target_y)
                # 移除已完成的路徑點
                if self.path_sequence_:
                    self.path_sequence_.pop(0)
                return next_node_id
            
            return current_position
            
        except Exception as e:
            self.get_logger().error(f'Error in process_next_point: {str(e)}')
            return current_position

    def has_active_task(self) -> bool:
        """Check if there are any active tasks in the path sequence"""
        return len(self.path_sequence_) > 0

    def request_and_process_path(self, current_position: str) -> str:
        """
        Request and process navigation path from current position
        
        Returns:
            str: Updated current position after processing
        """
        # Wait for service 
        while not self.nav_service_client_.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('NavService not available, waiting...')
            
        # Create request
        request = NavServiceMsg.Request()
        request.can_arrive = True
        request.i_am_at = current_position
        self.current_position_ = current_position
        
        self.get_logger().info(f'Sending request to NavService from position: {current_position}')
        
        try:
            # Send request and wait for response
            future = self.nav_service_client_.call_async(request)
            rclpy.spin_until_future_complete(self, future)
            
            response = future.result()
            if response is not None:
                return self.process_navigation_response(response, current_position)
            else:
                self.get_logger().error('Failed to call NavService')
                self.path_sequence_ = []
        except Exception as e:
            self.get_logger().error(f'Error in request_and_process_path: {str(e)}')
            self.path_sequence_ = []
            
        return current_position

    def process_navigation_response(self, result, current_position: str) -> str:
        """Process the navigation service response"""
        try:
            json_response = json.loads(result.path_to_next_task)
            self.path_sequence_ = json_response["node_sequence:"]
            
            if not self.path_sequence_:
                self.get_logger().info('No tasks available at the moment.')
                return current_position
                
            self.current_graph_ = json_response["graph"]
            self.log_path_sequence()
            
            if self.path_sequence_:
                return self.process_next_point(current_position)
                
        except Exception as e:
            self.get_logger().error(f'Error parsing response: {str(e)}')
            self.path_sequence_ = []
        
        return current_position

    def log_path_sequence(self):
        """Log the complete path sequence"""
        self.get_logger().info(f'Received path sequence with {len(self.path_sequence_)} points:')
        for i, node_id in enumerate(self.path_sequence_):
            location = self.current_graph_[node_id]["local_location"]
            self.get_logger().info(
                f'Point {i + 1}: {node_id} ({location[0]:.2f}, {location[1]:.2f})'
            )

def main(args=None):
    rclpy.init(args=args)
    node = MapManager()
    
    # Set initial pose
    initial_pose = PoseStamped()
    initial_pose.header.frame_id = 'map'
    initial_pose.header.stamp = node.navigator.get_clock().now().to_msg()
    initial_pose.pose.position.x = -11.975
    initial_pose.pose.position.y = -17.975
    initial_pose.pose.orientation.w = 1.0
    # node.navigator.setInitialPose(initial_pose)
    
    # Set initial position ID
    current_position = "000_000"
    
    try:
        while rclpy.ok():
            print(f"Requesting task from position: {current_position}")
            
            # Run the request and update current position
            current_position = node.request_and_process_path(current_position)
            
            # Process callbacks
            rclpy.spin_once(node, timeout_sec=0.1)
            
            # Wait if no active task
            if not node.has_active_task():
                node.get_logger().info("No active task. Waiting 5 seconds...")
                time.sleep(5)
            
    except KeyboardInterrupt:
        pass
    finally:
        node.navigator.lifecycleShutdown()
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()