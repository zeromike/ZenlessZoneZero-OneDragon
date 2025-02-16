from one_dragon.base.operation.operation import OperationRoundResult, OperationNode
from one_dragon.utils.i18_utils import gt
from zzz_od.context.zzz_context import ZContext
from zzz_od.operation.zzz_operation import ZOperation


class WaitNormalWorld(ZOperation):

    def __init__(self, ctx: ZContext):
        """
        等待大世界画面的加载 有超时时间的设置
        :param ctx:
        """
        ZOperation.__init__(self, ctx,
                            timeout_seconds=60,
                            op_name=gt('等待大世界画面', 'ui')
                            )

    def add_edges_and_nodes(self) -> None:
        """
        初始化前 添加边和节点 由子类实行
        :return:
        """
        check = OperationNode('画面识别', self.check_screen)

        self.param_start_node = check

    def handle_init(self):
        pass

    def check_screen(self) -> OperationRoundResult:
        """
        识别游戏画面
        :return:
        """
        screen = self.screenshot()

        return self.round_by_find_area(screen, '大世界', '信息',
                                       retry_wait=1)
