#!/usr/bin/env python3
"""turtleCommander: Subscribes to 'shape_cmd' and draws shapes via turtlesim services.

Listens for std_msgs/String: {aquarius, rainbow, cap, stop, clear}.
Implements drawing using TeleportAbsolute and SetPen service calls.
"""

import time
import threading
from typing import Optional

import rclpy
from rclpy.node import Node
from std_msgs.msg import String
from turtlesim.srv import SetPen, TeleportAbsolute
from std_srvs.srv import Empty

from .shapes import SHAPES, circle_points, arc_points, star_points, px_to_units


class TurtleCommander(Node):
    def __init__(self):
        super().__init__('turtle_commander')
        self.declare_parameter('turtle', 'turtle1')
        self.declare_parameter('auto_clear', True)
        self.declare_parameter('star_scale', 1.45)
        self.declare_parameter('star_rotation', 90.0)

        self.turtle = self.get_parameter('turtle').get_parameter_value().string_value

        # Service clients
        self.cli_pen = self.create_client(SetPen, f'/{self.turtle}/set_pen')
        self.cli_tp = self.create_client(TeleportAbsolute, f'/{self.turtle}/teleport_absolute')
        self.cli_clear = self.create_client(Empty, '/clear')

        self.cli_pen.wait_for_service(timeout_sec=5.0)
        self.cli_tp.wait_for_service(timeout_sec=5.0)
        self.cli_clear.wait_for_service(timeout_sec=5.0)

        # Subscriber
        self.sub = self.create_subscription(String, 'shape_cmd', self.on_cmd, 10)

        # Control state
        self._lock = threading.Lock()
        self._current_thread: Optional[threading.Thread] = None
        self._cancel = False

    # --- basic service helpers (synchronous: wait for completion) ---
    def _call_and_wait(self, future):
        while rclpy.ok() and not future.done():
            time.sleep(0.001)
        return future.result() if future.done() else None

    def set_pen(self, r, g, b, width, off=0):
        req = SetPen.Request(); req.r = int(r); req.g = int(g); req.b = int(b); req.width = int(width); req.off = int(off)
        fut = self.cli_pen.call_async(req)
        self._call_and_wait(fut)

    def teleport(self, x, y, theta=0.0):
        req = TeleportAbsolute.Request(); req.x = float(x); req.y = float(y); req.theta = float(theta)
        fut = self.cli_tp.call_async(req)
        self._call_and_wait(fut)

    def clear(self):
        fut = self.cli_clear.call_async(Empty.Request())
        self._call_and_wait(fut)

    # --- drawing primitives ---
    def draw_poly(self, pts, color=(0,0,0), width=3, delay=0.08, close=True):
        if not pts:
            return
        # pen up to move to start
        self.set_pen(*color, width, off=1)
        time.sleep(0.03)
        sx, sy = pts[0]
        self.teleport(sx, sy, 0.0)
        time.sleep(0.06)
        # pen down
        self.set_pen(*color, width, off=0)
        for (x, y) in pts[1:]:
            if self._cancel:
                break
            self.teleport(x, y, 0.0)
            time.sleep(delay)
        if close and not self._cancel:
            self.teleport(sx, sy, 0.0)
            time.sleep(0.06)
        # pen up
        self.set_pen(*color, width, off=1)

    def draw_path(self, pts, color=(0,0,0), width=3, delay=0.08):
        self.draw_poly(pts, color=color, width=width, delay=delay, close=False)

    def fill_star(self, cx, cy, r_outer, r_inner, color=(255,255,255), steps=16, width=3, rotation_deg=90.0):
        import math
        rot = math.radians(rotation_deg)
        for i in range(1, steps + 1):
            if self._cancel:
                break
            t = i / steps
            pts = star_points(cx, cy, r_outer * t, r_inner * t, rotation=rot)
            self.draw_poly(pts, color=color, width=width, delay=0.02)

    # --- subscriber callback and drawing logic ---
    def on_cmd(self, msg: String):
        cmd = msg.data.strip().lower()
        self.get_logger().info(f"Received shape_cmd: '{cmd}'")
        if cmd == 'clear':
            # Run clear asynchronously to avoid blocking the executor thread
            threading.Thread(target=self._do_clear, daemon=True).start()
            return
        if cmd == 'stop':
            with self._lock:
                self._cancel = True
            return
        if cmd not in ('aquarius', 'rainbow', 'cap'):
            self.get_logger().warn("Unknown command. Expected one of {aquarius,rainbow,cap,stop,clear}")
            return

        with self._lock:
            self._cancel = False
            if self._current_thread and self._current_thread.is_alive():
                return
            t = threading.Thread(target=self._draw_shape, args=(cmd,), daemon=True)
            self._current_thread = t
            t.start()

    def _do_clear(self):
        try:
            self.clear()
        except Exception as e:
            self.get_logger().error(f'Clear failed: {e}')

    def _draw_shape(self, name: str):
        try:
            if self.get_parameter('auto_clear').get_parameter_value().bool_value:
                self.clear()
                time.sleep(0.05)
            if name == 'cap':
                self._draw_cap()
            elif name == 'rainbow':
                self._draw_rainbow()
            else:
                self._draw_aquarius()
        except Exception as e:
            self.get_logger().error(f'Error drawing {name}: {e}')

    def _draw_cap(self):
        shape = SHAPES['cap']
        cx, cy = shape['center']
        r_outer, r_w1, r_w2, r_blue = shape['radii']
        if self._cancel: return
        self.draw_poly(circle_points(cx, cy, r_outer, n=128), color=(200, 0, 0), width=30, delay=0.02, close=True)
        if self._cancel: return
        self.draw_poly(circle_points(cx, cy, r_w1, n=112), color=(255, 255, 255), width=44, delay=0.02, close=True)
        if self._cancel: return
        self.draw_poly(circle_points(cx, cy, r_w2, n=96), color=(200, 0, 0), width=30, delay=0.02, close=True)
        if self._cancel: return
        scale = float(self.get_parameter('star_scale').get_parameter_value().double_value)
        rotation = float(self.get_parameter('star_rotation').get_parameter_value().double_value)
        self.fill_star(cx, cy, r_blue * 0.88 * scale, r_blue * 0.34 * scale, color=(255, 255, 255), steps=18, width=3, rotation_deg=rotation)

    def _draw_rainbow(self):
        import math
        shape = SHAPES['rainbow']
        cx_px, cy_px = shape['center_px']
        outer = shape['outer_radius_px']
        thick = shape['band_thickness_px']
        for i, col in enumerate(shape['colors']):
            if self._cancel: return
            r_px = outer - i * thick
            r = (r_px * 11.0 / 500.0)
            cx, cy = px_to_units(cx_px, cy_px)
            arc = arc_points(cx, cy, r, 0.0, math.pi, n=120)
            self.draw_path(arc, color=col, width=int(thick), delay=0.003)

    def _draw_aquarius(self):
        import math
        aq = SHAPES['aquarius']
        left = aq['left_px']; right = aq['right_px']
        amp = aq['amplitude_px']; wave = aq['wavelength_px']
        stroke = int(aq['stroke_px']); col = aq['color']
        cx, cy = 5.5, 5.5
        ring_color = (200, 170, 70)
        ring_radii = [4.7, 4.3, 2.8, 1.3]
        for r in ring_radii:
            if self._cancel: return
            self.draw_poly(circle_points(cx, cy, r, n=160), color=ring_color, width=2, delay=0.002, close=True)
        for deg in range(0, 360, 30):
            if self._cancel: return
            a = math.radians(deg)
            x1 = cx + 0.4 * math.cos(a)
            y1 = cy + 0.4 * math.sin(a)
            x2 = cx + ring_radii[0] * math.cos(a)
            y2 = cy + ring_radii[0] * math.sin(a)
            self.draw_path([(x1,y1),(x2,y2)], color=ring_color, width=2, delay=0.002)
        # Oval lens
        major = 3.8; minor = 0.9
        top = arc_points(cx, cy, minor, math.pi, 2*math.pi, n=60)
        top = [(cx + (x - cx) * (major/minor), y) for (x,y) in top]
        bottom = arc_points(cx, cy, minor, 0.0, math.pi, n=60)
        bottom = [(cx + (x - cx) * (major/minor), y) for (x,y) in bottom][::-1]
        lens = top + bottom
        if self._cancel: return
        self.draw_poly(lens, color=ring_color, width=2, delay=0.002, close=True)
        # Zigzags
        def zigzag(yc_px):
            pts = []
            x = left
            dir_up = True
            while x <= right:
                y = yc_px + (amp if dir_up else -amp)
                pts.append(px_to_units(x, y))
                x += wave / 2.0
                dir_up = not dir_up
            if (len(pts) % 2) == 0:
                pts.append(px_to_units(right, yc_px + (amp if not dir_up else -amp)))
            return pts
        if self._cancel: return
        self.draw_path(zigzag(aq['y_top_px']), color=col, width=stroke, delay=0.01)
        if self._cancel: return
        self.draw_path(zigzag(aq['y_bottom_px']), color=col, width=stroke, delay=0.01)


def main(args=None):
    rclpy.init(args=args)
    node = TurtleCommander()
    try:
        rclpy.spin(node)
    finally:
        node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == '__main__':
    main()
