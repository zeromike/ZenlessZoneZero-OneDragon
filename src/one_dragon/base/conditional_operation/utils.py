from typing import List, Callable, Set

from one_dragon.base.conditional_operation.atomic_op import AtomicOp
from one_dragon.base.conditional_operation.operation_template import OperationTemplate
from one_dragon.base.conditional_operation.scene_handler import SceneHandler
from one_dragon.base.conditional_operation.state_handler_template import StateHandlerTemplate
from one_dragon.base.conditional_operation.state_cal_tree import construct_state_cal_tree, StateCalNode
from one_dragon.base.conditional_operation.state_handler import StateHandler
from one_dragon.base.conditional_operation.state_recorder import StateRecorder


def construct_scene_handler(
        scene_data: dict,
        state_recorders: List[StateRecorder],
        op_getter: Callable[[str, List[str]], AtomicOp],
        scene_handler_getter: Callable[[str], StateHandlerTemplate],
        operation_template_getter: Callable[[str], OperationTemplate],
):
    interval_seconds = scene_data.get('interval', 0.5)

    state_handlers = _get_state_handlers(
        scene_data.get('handlers', []),
        state_recorders, op_getter, scene_handler_getter, operation_template_getter,
        set()
    )

    return SceneHandler(interval_seconds, state_handlers)


def _get_state_handlers_by_template(
        template_name: str,
        state_recorders: List[StateRecorder],
        op_getter: Callable[[str, List[str]], AtomicOp],
        scene_handler_getter: Callable[[str], StateHandlerTemplate],
        operation_template_getter: Callable[[str], OperationTemplate],
        usage_states_handler_templates: Set[str]
) -> List[StateHandler]:
    """
    根据模板加载
    :return:
    """
    if template_name in usage_states_handler_templates:
        raise ValueError('循环引入状态处理器模板 ' + template_name)
    if template_name is None or len(template_name) == 0:
        raise ValueError('状态处理器模板名称为空 handler_template')
    template: StateHandlerTemplate = scene_handler_getter(template_name)
    if template is None:
        raise ValueError('找不到状态处理器模板 ' + template_name)

    usage_states_handler_templates.add(template_name)
    state_handlers = _get_state_handlers(
        template.get('handlers', []),
        state_recorders, op_getter, scene_handler_getter, operation_template_getter,
        usage_states_handler_templates
    )
    usage_states_handler_templates.remove(template_name)

    return state_handlers


def _get_state_handlers(
        handler_data_list: List[dict],
        state_recorders: List[StateRecorder],
        op_getter: Callable[[str, List[str]], AtomicOp],
        scene_handler_getter: Callable[[str], StateHandlerTemplate],
        operation_template_getter: Callable[[str], OperationTemplate],
        usage_states_handler_templates: Set[str]
) -> List[StateHandler]:
    state_handlers = []

    for handler_data_item in handler_data_list:
        if 'state_template' in handler_data_item:
            template_state_handlers = _get_state_handlers_by_template(
                handler_data_item.get('state_template', ''),
                state_recorders, op_getter, scene_handler_getter, operation_template_getter,
                usage_states_handler_templates)
            for i in template_state_handlers:
                state_handlers.append(i)
        else:
            state_handlers.append(construct_state_handler(
                handler_data_item, state_recorders,
                op_getter, scene_handler_getter, operation_template_getter,
                usage_states_handler_templates
            ))

    return state_handlers


def construct_state_handler(
        state_data: dict,
        state_recorders: List[StateRecorder],
        op_getter: Callable[[str, List[str]], AtomicOp],
        scene_handler_getter: Callable[[str], StateHandlerTemplate],
        operation_template_getter: Callable[[str], OperationTemplate],
        usage_scene_templates: Set[str],
) -> StateHandler:
    """
    构造一个场景处理器
    包含状态判断 + 对应指令
    :param state_data: 场景配置数据
    :param state_recorders: 状态记录器
    :param op_getter: 指令获取器
    :param operation_template_getter: 指令模板获取器
    :return:
    """
    states_expr = state_data.get("states", '')
    state_cal_tree = construct_state_cal_tree(states_expr, state_recorders)
    if 'sub_states' in state_data:
        sub_state_data_list = state_data.get('sub_states', [])
        if len(sub_state_data_list) == 0:
            raise ValueError('状态( %s )下子状态为空', states_expr)
        sub_handler_list: List[StateHandler] = _get_state_handlers(
            sub_state_data_list,
            state_recorders,
            op_getter,
            scene_handler_getter,
            operation_template_getter,
            usage_scene_templates
        )
        return StateHandler(states_expr, state_cal_tree, sub_states=sub_handler_list)
    else:
        ops = _get_ops_from_data(
            state_data.get('operations', []),
            op_getter, operation_template_getter,
            set())
        if len(ops) == 0:
            raise ValueError('状态( %s )下指令为空', states_expr)
        return StateHandler(states_expr, state_cal_tree, operations=ops)


def get_ops_by_template(
        template_name: str,
        op_getter: Callable[[str, List[str]], AtomicOp],
        operation_template_getter: Callable[[str], OperationTemplate],
        usage_operation_templates: Set[str]
) -> List[AtomicOp]:
    if template_name in usage_operation_templates:
        raise ValueError('循环引入指令模板 ' + template_name)
    if template_name is None or len(template_name) == 0:
        raise ValueError('指令模板名称为空 handler_template')
    template: OperationTemplate = operation_template_getter(template_name)
    if template is None:
        raise ValueError('找不到指令模板 ' + template_name)

    usage_operation_templates.add(template_name)
    ops = _get_ops_from_data(template.get('operations', []),
                             op_getter, operation_template_getter,
                             usage_operation_templates)

    usage_operation_templates.remove(template_name)

    return ops


def _get_ops_from_data(
        operation_data_list: List[dict],
        op_getter: Callable[[str, List[str]], AtomicOp],
        operation_template_getter: Callable[[str], OperationTemplate],
        usage_templates: Set[str]
):
    ops = []
    for operation_data_item in operation_data_list:
        if 'operation_template' in operation_data_item:
            template_ops = get_ops_by_template(
                operation_data_item['operation_template'],
                op_getter, operation_template_getter,
                usage_templates
            )
            for op in template_ops:
                ops.append(op)
        else:
            op_name = operation_data_item.get('op_name', '')
            op_data = operation_data_item.get('data', [])
            op = op_getter(op_name, op_data)
            ops.append(op)
    return ops
