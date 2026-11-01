import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from lab_interfaces.action import DriveDistance
from my_robot_interfaces.action import Rotate
from nav_msgs.msg import Odometry

class SquareDriver(Node):
    def __init__(self):
        super().__init__('square_driver')
        self.declare_parameter('side_length', 0.5)

        self.drive_client = ActionClient(self, DriveDistance, '/drive_distance')
        self.rotate_client = ActionClient(self, Rotate, '/rotate')

        self.get_logger().info('Waiting for action servers...')
        self.drive_client.wait_for_server()
        self.rotate_client.wait_for_server()
        self.get_logger().info('Action servers connected!')

        self.side_length = self.get_parameter('side_length').value
        self.sides_completed = 0
        self.started = False

        self.odom_sub = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        self.get_logger().info('Waiting for /odom to start...')

    def odom_callback(self, msg):
        if not self.started:
            self.started = True
            self.get_logger().info('Odometry received! Starting square...')
            self.destroy_subscription(self.odom_sub)
            self.create_timer(1.0, self.start_drive_once)

    def start_drive_once(self):
        self.start_drive()

    def start_drive(self):
        if self.sides_completed >= 4:
            self.get_logger().info('Square complete!')
            return

        self.get_logger().info(f'--- Side {self.sides_completed + 1} ---')
        goal_msg = DriveDistance.Goal()
        goal_msg.distance = self.side_length

        self.get_logger().info(f'Sending drive goal: {self.side_length} m')
        self.drive_client.send_goal_async(goal_msg).add_done_callback(self.drive_goal_response_callback)

    def drive_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Drive goal rejected')
            return
        goal_handle.get_result_async().add_done_callback(self.drive_result_callback)

    def drive_result_callback(self, future):
        result = future.result().result
        if not result.reached:
            self.get_logger().error('Failed to reach distance. Aborting.')
            return
        self.start_rotate()

    def start_rotate(self):
        goal_msg = Rotate.Goal()
        goal_msg.angle = 1.5708

        self.get_logger().info(f'Sending rotate goal: {goal_msg.angle} rad')
        self.rotate_client.send_goal_async(goal_msg).add_done_callback(self.rotate_goal_response_callback)

    def rotate_goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Rotate goal rejected')
            return
        goal_handle.get_result_async().add_done_callback(self.rotate_result_callback)

    def rotate_result_callback(self, future):
        self.sides_completed += 1
        self.start_drive()

def main(args=None):
    rclpy.init(args=args)
    node = SquareDriver()
    rclpy.spin(node)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
