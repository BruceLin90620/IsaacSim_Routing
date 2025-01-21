#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from geometry_msgs.msg import PoseWithCovarianceStamped
from std_srvs.srv import Trigger
import json
import os
from datetime import datetime
import argparse

class PoseCollector(Node):
    def __init__(self, map_name):
        super().__init__('pose_collector')
        
        # Store map name for ID generation
        self.map_name = map_name.zfill(3)  # Ensure it's 3 digits
        
        # Subscribe to initial pose topic
        self.subscription = self.create_subscription(
            PoseWithCovarianceStamped,
            'initialpose',
            self.pose_callback,
            10
        )
        
        # Create a service for saving the file
        self.srv = self.create_service(
            Trigger,
            'save_waypoints',
            self.save_service_callback
        )
        
        # Store collected poses
        self.poses = {}
        self.pose_count = 0
        
        self.get_logger().info(f'Pose collector node started for map {self.map_name}. Ready to collect poses from Rviz2...')
        self.get_logger().info('Use "ros2 service call /save_waypoints std_srvs/srv/Trigger" to save the waypoints.')
        
    def pose_callback(self, msg):
        # Generate unique ID for new pose (format: XXX_YYY where XXX is map_name and YYY is count)
        pose_id = f"{self.map_name}_{self.pose_count:03d}"
        
        # Extract position
        position = msg.pose.pose.position
        
        # Create new pose entry in same format as original JSON
        self.poses[pose_id] = {
            "edges": [],  # Start with empty edges list
            "local_location": [
                float(position.x),
                float(position.y),
                0.0  # Set z to 0 as requested
            ]
        }
        
        # Check alignment with all existing points and add edges if aligned
        self.update_edges_for_new_point(pose_id)
        
        self.pose_count += 1
        
        # Log the new pose
        self.get_logger().info(f'Received new pose: {pose_id} at position: [{position.x:.3f}, {position.y:.3f}]')
        
    def check_aligned(self, p1, p2, position_threshold=0.3, distance_threshold=2.5):
        """
        Check if two points are aligned (share similar x or y) and within distance threshold
        p1, p2: points as [x, y, z]
        position_threshold: maximum allowed difference in x or y to be considered aligned (meters)
        distance_threshold: maximum allowed total distance between points (meters)
        """
        # Check if x coordinates are similar
        x_aligned = abs(p1[0] - p2[0]) < position_threshold
        
        # Check if y coordinates are similar
        y_aligned = abs(p1[1] - p2[1]) < position_threshold
        
        # Calculate total distance between points
        distance = ((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)**0.5
        
        # Points should be aligned in either x or y, and within distance threshold
        return (x_aligned or y_aligned) and distance < distance_threshold
        
    def update_edges_for_new_point(self, new_point_id):
        """Update edges for a newly added point"""
        new_pos = self.poses[new_point_id]["local_location"]
        
        # Check alignment with all existing points
        for existing_id, existing_data in self.poses.items():
            if existing_id == new_point_id:
                continue
                
            # If points are aligned and within distance, add edges
            if self.check_aligned(new_pos, existing_data["local_location"]):
                self.poses[new_point_id]["edges"].append(existing_id)
                self.poses[existing_id]["edges"].append(new_point_id)
                self.get_logger().info(f'Added edge between aligned points {new_point_id} and {existing_id}')

    def save_service_callback(self, request, response):
        """Service callback to save the waypoints file"""
        try:
            if self.pose_count > 0:
                filename = self.save_to_file()
                response.success = True
                response.message = f'Successfully saved {self.pose_count} poses to {filename}'
            else:
                response.success = False
                response.message = 'No poses collected yet'
        except Exception as e:
            response.success = False
            response.message = f'Failed to save file: {str(e)}'
        return response
        
    def save_to_file(self):
        # Generate filename with timestamp and map name
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f'waypointgraph_{self.map_name}_{timestamp}.json'
        
        # Save with pretty printing
        with open(filename, 'w') as f:
            json.dump(self.poses, f, indent=2)
        
        self.get_logger().info(f'Saved {self.pose_count} poses to {filename}')
        return filename

def main():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Collect waypoints from Rviz2')
    parser.add_argument('map_name', type=str, help='Map identifier (will be used as XXX in point IDs XXX_YYY)')
    args = parser.parse_args()
    
    rclpy.init()
    node = PoseCollector(args.map_name)
    
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        if node.pose_count > 0:
            node.save_to_file()
            print("\nSaved waypoints file before shutting down.")
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()