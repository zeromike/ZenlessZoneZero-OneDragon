from typing import List, Optional

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.state_cal_tree import StateCalNode
from one_dragon.utils.log_utils import log


class StateHandler:

    def __init__(self,
                 expr: str,
                 state_cal_tree: StateCalNode,
                 sub_states: Optional[List] = None,
                 operations: Optional[List[AtomicOp]] = None
                 ):
        """
        一个状态处理器 包含状态判断 + 对应指令
        :param state_cal_tree: 状态判断树
        :param operations: 执行指令
        """
        self.expr: str = expr
        self.state_cal_tree: StateCalNode = state_cal_tree
        self.sub_states: List[StateHandler] = sub_states
        self.operations: List[AtomicOp] = operations

    def get_operations(self, trigger_time: float) -> Optional[List[AtomicOp]]:
        """
        根据触发时间 和优先级 获取符合条件的场景下的指令
        :param trigger_time:
        :return:
        """
        if self.state_cal_tree.in_time_range(trigger_time):
            log.debug('触发条件 %s', self.expr)
            if self.sub_states is not None and len(self.sub_states) > 0:
                for sub_state in self.sub_states:
                    ops = sub_state.get_operations(trigger_time)
                    if ops is not None:
                        return ops
            else:
                return self.operations

        return None

    def dispose(self) -> None:
        """
        销毁
        :return:
        """
        if self.state_cal_tree is not None:
            self.state_cal_tree.dispose()
        if self.operations is not None:
            for op in self.operations:
                op.dispose()
        if self.sub_states is not None:
            for sub_state in self.sub_states:
                sub_state.dispose()
