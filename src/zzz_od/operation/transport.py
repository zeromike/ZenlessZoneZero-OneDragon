import time

from typing import ClassVar, List

from one_dragon.base.geometry.point import Point
from one_dragon.base.operation.operation import OperationNode, OperationRoundResult
from one_dragon.utils import cv2_utils
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.game_data.map_area import MapArea
from zzz_od.operation.back_to_normal_world import BackToNormalWorld
from zzz_od.operation.wait_normal_world import WaitNormalWorld
from zzz_od.operation.zzz_operation import ZOperation


class Transport(ZOperation):

    STATUS_NOT_IN_MAP: ClassVar[str] = '未在地图页面'

    def __init__(self, ctx: ZContext, area_name: str, tp_name: str):
        """
        传送到某个区域
        由于使用了返回大世界 应可保证在任何情况下使用
        :param ctx:
        :param area_name:
        :param tp_name:
        """
        ZOperation.__init__(self, ctx,
                            op_name='%s %s %s' % (
                                gt('传送', 'ui'),
                                gt(area_name),
                                gt(tp_name)
                            ))

        self.area_name: str = area_name
        self.tp_name: str = tp_name

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check_screen = OperationNode('画面识别', self.check_screen)
        back_to_world = OperationNode('返回大世界', op=BackToNormalWorld(self.ctx))
        self.add_edge(check_screen, back_to_world, status=Transport.STATUS_NOT_IN_MAP)

        open_map = OperationNode('打开地图', self.open_map)
        self.add_edge(back_to_world, open_map)

        choose_area = OperationNode('选择区域', self.choose_area)
        self.add_edge(choose_area, choose_area)  # 开始可能就在地图画面
        self.add_edge(open_map, choose_area)

        choose_tp = OperationNode('选择传送点', self.choose_tp)
        self.add_edge(choose_area, choose_tp)

        click_tp = OperationNode('点击传送', self.click_tp)
        self.add_edge(choose_tp, click_tp)

        wait = OperationNode('等待加载', op=WaitNormalWorld(self.ctx))
        self.add_edge(click_tp, wait)

    def handle_init(self):
        pass

    def check_screen(self) -> OperationRoundResult:
        """
        画面识别
        :return:
        """
        screen = self.screenshot()

        result = self.round_by_find_area(screen, '地图', '街区详情')
        if result.is_success:
            return self.round_success()
        else:
            return self.round_success(status=Transport.STATUS_NOT_IN_MAP)

    def open_map(self) -> OperationRoundResult:
        """
        在大世界画面 点击
        :return:
        """
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '大世界', '地图',
                                                 success_wait=2, retry_wait_round=1)

    def choose_area(self) -> OperationRoundResult:
        """
        在地图画面 选择上方的区域
        :return:
        """
        screen = self.screenshot()

        area = self.ctx.screen_loader.get_area('地图', '区域名称')
        part = cv2_utils.crop_image_only(screen, area.rect)

        ocr_area_name = self.ctx.ocr.run_ocr_single_line(part)
        target_area: MapArea = self.ctx.map_service.area_name_map[self.area_name]
        current_area: MapArea = self.ctx.map_service.get_best_match_area(ocr_area_name)

        if current_area is None:
            return self.round_retry('无法识别当前区域', wait_round_time=1)

        if current_area == target_area:
            return self.round_success()

        # 尝试点击换到目标区域
        direction = self.ctx.map_service.get_direction_to_target_area(current_area, target_area)
        if direction > 0:
            click_area = self.ctx.screen_loader.get_area('地图', '下一个区域')
        else:
            click_area = self.ctx.screen_loader.get_area('地图', '上一个区域')

        for i in range(abs(direction)):
            self.ctx.controller.click(click_area.center)
            time.sleep(0.5)

        return self.round_retry(wait=0.5)

    def choose_tp(self) -> OperationRoundResult:
        """
        在地图画面 已经选择好区域了 选择传送点
        :return:
        """
        screen = self.screenshot()

        area = self.ctx.screen_loader.get_area('地图', '传送点名称')
        part = cv2_utils.crop_image_only(screen, area.rect)

        ocr_map = self.ctx.ocr.run_ocr(part)

        if len(ocr_map) == 0:
            return self.round_retry('未识别到传送点', wait_round_time=1)

        target_ocr_str = None
        display_tp_list: List[str] = []  # 当前显示的传送点名称
        for ocr_str in ocr_map.keys():
            ocr_tp_name = self.ctx.map_service.get_best_match_tp(self.area_name, ocr_str)
            display_tp_list.append(ocr_tp_name)
            if self.tp_name == ocr_tp_name:
                target_ocr_str = ocr_str

        if target_ocr_str is not None:
            mrl = ocr_map[target_ocr_str]
            self.ctx.controller.click(mrl.max.center + area.left_top)
            return self.round_success(wait=1)

        area_tp_list: List[str] = self.ctx.map_service.area_name_map[self.area_name].tp_list  # 当前区域的传送点名称
        left_cnt: int = 0  # 当前出现在画面上的 在目标传送点左方的传送点数量
        for area_tp in area_tp_list:
            if area_tp == self.tp_name:
                break
            left_cnt += 1

        if left_cnt > 0:  # 往右滑
            from_point = area.center
            end_point = from_point + Point(-200, 0)
            self.ctx.controller.drag_to(start=from_point, end=end_point)
        else:  # 往左滑
            from_point = area.center
            end_point = from_point + Point(150, 0)  # 跟上面滑动距离稍微不一样 防止一直重复左右都找不到
            self.ctx.controller.drag_to(start=from_point, end=end_point)

        return self.round_retry(wait=0.5)

    def click_tp(self) -> OperationRoundResult:
        """
        在地图画面 已经选好传送点了 点击传送
        :return:
        """
        screen = self.screenshot()
        return self.round_by_find_and_click_area(screen, '地图', '传送',
                                                 retry_wait_round=1)
