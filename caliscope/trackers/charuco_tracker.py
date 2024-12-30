# 在角点检测器和角点绘制器之间可能存在混合功能...我不确定。
# 比如,需要有一些东西来累积要绘制到显示帧上的角点。

import cv2
import numpy as np

import caliscope.calibration.draw_charuco
import caliscope.logger
from caliscope.packets import PointPacket
from caliscope.tracker import Tracker

logger = caliscope.logger.get(__name__)


class CharucoTracker(Tracker):
    def __init__(self, charuco):
        # 需要相机来获知分辨率并为相机分配标定参数
        self.charuco = charuco
        self.board = charuco.board
        self.dictionary_object = self.charuco.dictionary_object

        # 用于亚像素角点校正
        self.criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 30, 0.01)#0.0001
        self.conv_size = (11, 11)  # 不要设置太大

    @property
    def name(self):
        return "CHARUCO"
    def get_points(self, frame: np.ndarray, port: int, rotation_count: int) -> PointPacket:
        """检查帧中的charuco角点,如果没有找到,
        则在帧的镜像中寻找角点"""

        # 如果需要则反转帧进行检测
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)  # 转换为灰度图
        if self.charuco.inverted:
            gray = ~gray  # 反转

        ids, img_loc = self.find_corners_single_frame(gray, mirror=False)

        if not ids.any():
            gray = cv2.flip(gray, 1)
            ids, img_loc = self.find_corners_single_frame(gray, mirror=True)

        obj_loc = self.get_obj_loc(ids)
        point_packet = PointPacket(ids, img_loc, obj_loc)

        return point_packet
    '''def get_points(self, frame: np.ndarray, port: int, rotation_count: int) -> PointPacket:
        """檢查幀中的charuco角點，優化用於相機標定"""
    
    # 轉換為灰度圖
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 增加預處理步驟以提高角點檢測的準確性
        gray = cv2.GaussianBlur(gray, (5, 5), 0)  # 高斯模糊去噪
        gray = cv2.adaptiveThreshold(
        gray,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV,
        11,
        2
    )
    
    # 嘗試檢測角點，使用更寬鬆的參數
        ids, img_loc = self.find_corners_single_frame(
        gray, 
        mirror=False,
        params={
            'adaptiveThreshWinSizeMin': 3,
            'adaptiveThreshWinSizeMax': 23,
            'adaptiveThreshWinSizeStep': 10,
            'adaptiveThreshConstant': 7,
            'minMarkerPerimeterRate': 0.03,
            'maxMarkerPerimeterRate': 4.0,
            'cornerRefinementMethod': cv2.aruco.CORNER_REFINE_SUBPIX,
            'cornerRefinementWinSize': 5,
            'cornerRefinementMaxIterations': 30,
            'cornerRefinementMinAccuracy': 0.1
        }
    )
    
        obj_loc = self.get_obj_loc(ids)
        point_packet = PointPacket(ids, img_loc, obj_loc)
    
        return point_packet
    
    def get_points(self, frame: np.ndarray, port: int, rotation_count: int) -> PointPacket:
        """檢查幀中的charuco角點"""
    
    # 轉換為灰度圖
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    
    # 直接檢測角點，不進行鏡像處理
        ids, img_loc = self.find_corners_single_frame(gray, mirror=False)
    
        obj_loc = self.get_obj_loc(ids)
        point_packet = PointPacket(ids, img_loc, obj_loc)
    
        return point_packet'''

    def get_point_name(self, point_id: int) -> str:
        return str(point_id)

    def get_point_id(self, point_name: str) -> int:
        return int(point_name)

    def get_connected_points(self):
        return self.charuco.get_connected_points()

    def find_corners_single_frame(self, gray_frame, mirror):
        ids = np.array([])
        img_loc = np.array([])

        # 检测是否存在aruco标记
        aruco_corners, aruco_ids, rejected = cv2.aruco.detectMarkers(gray_frame, self.dictionary_object)

        # 如果存在,则插值计算Charuco角点并返回结果
        if len(aruco_corners) > 3:
            (
                success,
                _img_loc,
                _ids,
            ) = cv2.aruco.interpolateCornersCharuco(aruco_corners, aruco_ids, gray_frame, self.board)

            # 这偶尔会出错...
            # 只提供可能的优化,如果失败就继续
            try:
                _img_loc = cv2.cornerSubPix(
                    gray_frame,
                    _img_loc,
                    self.conv_size,
                    (-1, -1),
                    self.criteria,
                )
            except Exception as e:
                logger.debug(f"亚像素检测失败: {e}")

            if success:
                # 分配给跟踪器
                ids = _ids[:, 0]
                img_loc = _img_loc[:, 0]

                # 如果是镜像图像则翻转坐标
                frame_width = gray_frame.shape[1]  # 用于将镜像角点翻转回来
                if mirror:
                    img_loc[:, 0] = frame_width - img_loc[:, 0]

        return ids, img_loc

    def get_obj_loc(self, ids: np.ndarray):
        """在棋盘参考系中的charuco角点的客观位置"""
        if len(ids) > 0:
            return self.board.getChessboardCorners()[ids, :]
        else:
            return np.array([])

    # @property
    def scatter_draw_instructions(self, point_id: int) -> dict:
        rules = {"radius": 5, "color": (0, 0, 220), "thickness": 3}
        return rules
