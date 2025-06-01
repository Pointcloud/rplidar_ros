import os
from ament_index_python.packages import get_package_share_directory  # type: ignore
from launch import LaunchDescription
from launch.actions import IncludeLaunchDescription, DeclareLaunchArgument # type: ignore
from launch.launch_description_sources import PythonLaunchDescriptionSource # type: ignore
from launch.substitutions import LaunchConfiguration, PathJoinSubstitution # type: ignore
from launch_ros.actions import Node # type: ignore

def generate_launch_description():
    # Set ROS_DOMAIN_ID
    os.environ['ROS_DOMAIN_ID'] = '1'
    domain_id = os.environ.get('ROS_DOMAIN_ID', '0')
    
    # Get the share directory for rplidar_ros
    rplidar_ros_share_dir = get_package_share_directory('rplidar_ros')

    # Declare launch arguments
    use_sim_time = LaunchConfiguration('use_sim_time', default='false')
    rviz_config_file = LaunchConfiguration('rviz_config_file', default=PathJoinSubstitution([rplidar_ros_share_dir, 'rviz', 'lidar_test.rviz']))

    # 1. Static transform chain: map -> odom -> base_link -> lidar_link
    #    This is a simplified approach for testing. In a real robot:
    #    - map -> odom: typically from a localization or SLAM system.
    #    - odom -> base_link: typically from wheel odometry/IMU via a robot controller.
    #    - base_link -> lidar_link: typically from robot_state_publisher using a URDF.

    # Static transform from map to odom
    static_transform_map_to_odom = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher_map_to_odom',
        arguments=['0', '0', '0', '0', '0', '0', 'map', 'odom'], # x, y, z, yaw, pitch, roll, parent_frame, child_frame
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Static transform from odom to base_link
    static_transform_odom_to_base_link = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher_odom_to_base_link',
        arguments=['0', '0', '0', '0', '0', '0', 'odom', 'base_link'], # x, y, z, yaw, pitch, roll, parent_frame, child_frame
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # Static transform from base_link to lidar_link
    # Adjust these values based on your Lidar's actual position relative to base_link
    # Example: Lidar is 0.2m forward (x) and 0.3m up (z)
    static_transform_base_link_to_lidar_link = Node(
        package='tf2_ros',
        executable='static_transform_publisher',
        name='static_transform_publisher_base_link_to_lidar_link',
        arguments=['0.2', '0', '0.3', '0', '0', '0', 'base_link', 'lidar_link'], # x, y, z, yaw, pitch, roll, parent_frame, child_frame
        parameters=[{'use_sim_time': use_sim_time}]
    )

    # 2. Run rplidar_c1_launch.py
    rplidar_c1_launch_file = PathJoinSubstitution([
        rplidar_ros_share_dir,
        'launch',
        'rplidar_c1_launch.py'
    ])

    rplidar_node_launch = IncludeLaunchDescription(
        PythonLaunchDescriptionSource(rplidar_c1_launch_file),
        # You can pass arguments to the included launch file if needed, for example:
        # launch_arguments={'serial_port': '/dev/ttyUSB0'}.items()
    )

    # 3. Start RViz2 with the /scan topic added (via config file)
    rviz_node = Node(
        package='rviz2',
        executable='rviz2',
        name='rviz2_lidar_test',
        arguments=['-d', rviz_config_file],
        parameters=[{'use_sim_time': use_sim_time}],
        output='screen'
    )

    return LaunchDescription([
        DeclareLaunchArgument(
            'use_sim_time',
            default_value='false',
            description='Use simulation (Gazebo) clock if true'),
        DeclareLaunchArgument(
            'rviz_config_file',
            default_value=PathJoinSubstitution([rplidar_ros_share_dir, 'rviz', 'lidar_test.rviz']),
            description='Full path to the RVIZ config file to use'),

        static_transform_map_to_odom,
        static_transform_odom_to_base_link,
        static_transform_base_link_to_lidar_link,
        rplidar_node_launch,
        rviz_node
    ])
