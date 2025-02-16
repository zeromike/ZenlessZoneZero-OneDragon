from one_dragon.base.operation.one_dragon_context import OneDragonContext
from one_dragon.utils import i18_utils
from zzz_od.application.devtools.screenshot_helper.screenshot_helper_config import ScreenshotHelperConfig
from zzz_od.application.battle_assistant.battle_assistant_config import BattleAssistantConfig
from zzz_od.application.email.email_run_record import EmailRunRecord
from zzz_od.config.game_config import GameConfig, GamePlatformEnum
from zzz_od.controller.zzz_pc_controller import ZPcController
from zzz_od.game_data.map_area import MapAreaService


class ZContext(OneDragonContext):

    def __init__(self):
        OneDragonContext.__init__(self)

        instance_idx = 0

        # 其它上下文
        from zzz_od.context.battle_context import BattleContext
        self.battle: BattleContext = BattleContext(self)

        from zzz_od.context.yolo_context import YoloContext
        self.yolo: YoloContext = YoloContext(self)

        # 基础配置
        self.game_config: GameConfig = GameConfig(instance_idx)

        # 游戏数据
        self.map_service: MapAreaService = MapAreaService()

        # 应用配置
        self.screenshot_helper_config: ScreenshotHelperConfig = ScreenshotHelperConfig(instance_idx)
        self.battle_assistant_config: BattleAssistantConfig = BattleAssistantConfig(instance_idx)

        # 运行记录
        self.email_run_record: EmailRunRecord = EmailRunRecord(instance_idx)

    def init_by_config(self) -> None:
        """
        根据配置进行初始化
        :return:
        """
        OneDragonContext.init_by_config(self)
        i18_utils.update_default_lang(self.game_config.game_language)

        if self.game_config.platform == GamePlatformEnum.PC.value.value:
            self.controller = ZPcController(
                game_config=self.game_config,
                win_title=self.game_config.win_title,
                standard_width=self.project_config.screen_standard_width,
                standard_height=self.project_config.screen_standard_height
            )
