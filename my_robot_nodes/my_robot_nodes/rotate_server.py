import math
import rclpy
from rclpy.node import Node
from rclpy.action import ActionServer, CancelResponse, GoalResponse
from rclpy.callback_groups import ReentrantCallbackGroup
from rclpy.executors import MultiThreadedExecutor
from geometry_msgs.msg import Twist
from nav_msgs.msg import Odometry
from my_robot_interfaces.action import Rotate

class RotateServer(Node):
    def __init__(self):
        super().__init__('rotate_server')
        self.declare_parameter('turn_speed', 0.5)
        
        self.publisher_ = self.create_publisher(Twist, '/cmd_vel', 10)
        self.subscription = self.create_subscription(Odometry, '/odom', self.odom_callback, 10)
        
        self.current_yaw = 0.0
        self.last_yaw = None
        
        self._action_server = ActionServer(
            self,
            Rotate,
            '/rotate',
            execute_callback=self.execute_callback,
            goal_callback=self.goal_callback,
            cancel_callback=self.cancel_callback,
            callback_group=ReentrantCallbackGroup()
        )
        self.get_logger().info('Rotate action server started')

    def odom_callback(self, msg):
        q = msg.pose.pose.orientation
        siny_cosp = 2.0 * (q.w * q.z + q.x * q.y)
        cosy_cosp = 1.0 - 2.0 * (q.y * q.y + q.z * q.z)
        yaw = math.atan2(siny_cosp, cosy_cosp)
        
        if self.last_yaw is None:
            self.last_yaw = yaw
            self.current_yaw = 0.0
        else:
            diff = yaw - self.last_yaw
            if diff > math.pi:
                diff -= 2.0 * math.pi
            elif diff < -math.pi:
                diff += 2.0 * math.pi
            
            self.current_yaw += diff
            self.last_yaw = yaw

    def goal_callback(self, goal_request):
        if goal_request.angle == 0.0:
            self.get_logger().warn('Rejecting zero angle goal')
            return GoalResponse.REJECT
        return GoalResponse.ACCEPT

    def cancel_callback(self, goal_handle):
        self.get_logger().info('Received cancel request')
        return CancelResponse.ACCEPT

    async def execute_callback(self, goal_handle):
        self.get_logger().info('Executing rotate goal...')
        self.current_yaw = 0.0
        self.last_yaw = None
        
        target = goal_handle.request.angle
        turn_speed = self.get_parameter('turn_speed').value
        feedback_msg = Rotate.Feedback()
        
        cmd = Twist()
        cmd.angular.z = turn_speed if target > 0 else -turn_speed
        self.publisher_.publish(cmd)

        while rclpy.ok():
            if goal_handle.is_cancel_requested:
                goal_handle.canceled()
                self.publisher_.publish(Twist()) 
                return Rotate.Result(turned=self.current_yaw)

            feedback_msg.turned = self.current_yaw
            goal_handle.publish_feedback(feedback_msg)

            if (target > 0 and self.current_yaw >= target) or (target < 0 and self.current_yaw <= target):
                break
                
            import time
            time.sleep(0.05)

        self.publisher_.publish(Twist())
        goal_handle.succeed()
        
        result = Rotate.Result()
        result.turned = self.current_yaw
        return result

def main(args=None):
    rclpy.init(args=args)
    node = RotateServer()
    executor = MultiThreadedExecutor()
    rclpy.spin(node, executor=executor)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
