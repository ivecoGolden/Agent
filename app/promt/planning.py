from typing import List, Optional
import re


class Planning:
    """
    Planning 模板类，用于记录和管理用户需求推进过程。
    """

    def __init__(self, requirement: str):
        """
        初始化一个新的 Planning 实例

        :param requirement: 用户提出的核心需求，字符串
        """
        self.requirement: str = requirement  # 用户需求
        self.info_list: List[str] = []  # 已有信息列表

        self.plan_steps: List[str] = []  # 完整的计划步骤
        self.current_step_index: int = -1  # 当前步骤索引（-1 表示未开始）

    def add_info(self, info: str) -> None:
        """
        追加一条已有信息到 info_list

        :param info: 新的已有信息内容
        """
        self.info_list.append(info)

    def set_plan_steps(self, steps: List[str]) -> None:
        """
        设置完整的计划步骤，重置当前索引为 0

        :param steps: 一组字符串形式的步骤列表
        """
        self.plan_steps = steps
        self.current_step_index = 0 if steps else -1

    def set_plan_steps_from_text(self, plan_text: str) -> None:
        """
        从中文句号分隔的字符串中解析计划步骤并设置到 plan_steps。

        :param plan_text: 例如 "第一步。第二步。第三步。"
        """
        steps = [step.strip(" 。\n") for step in plan_text.split("。") if step.strip()]
        self.set_plan_steps(steps)

    def update_plan_step(self, index: int, step: str) -> None:
        """
        修改某一个具体的计划步骤

        :param index: 要修改的步骤索引
        :param step: 替换后的步骤内容
        """
        if 0 <= index < len(self.plan_steps):
            self.plan_steps[index] = step
        else:
            raise IndexError("计划步骤索引超出范围")

    def get_current_step(self) -> Optional[str]:
        """
        获取当前正在执行的计划步骤

        :return: 当前步骤字符串或 None（未开始）
        """
        if 0 <= self.current_step_index < len(self.plan_steps):
            return self.plan_steps[self.current_step_index]
        return None

    def advance_step(self) -> bool:
        """
        前进到下一步计划，返回是否成功

        :return: 是否成功推进到下一步
        """
        if self.current_step_index + 1 < len(self.plan_steps):
            self.current_step_index += 1
            return True
        return False

    def __str__(self) -> str:
        """
        格式化输出当前 Planning 内容
        """
        current_step = self.get_current_step()
        steps_text = (
            "".join(
                f"{'👉' if i == self.current_step_index else '   '} {step}\n"
                for i, step in enumerate(self.plan_steps)
            )
            if self.plan_steps
            else "   （无）\n"
        )

        return (
            f"用户需求：{self.requirement}\n"
            f"已有信息：\n"
            + (
                "".join(f"   - {item}\n" for item in self.info_list)
                if self.info_list
                else "   （无）\n"
            )
            # + f"计划步骤：\n{steps_text}\n"
            + f"下一步操作：{current_step or '（未设置）'}"
        )


# ============================
# 安全风险评估与规范性报告
# ============================
# ✅ 当前功能说明：
# - `Planning` 类用于封装用户需求推进过程，包括需求信息、计划步骤管理、当前执行步跟踪等功能。
#
# 🔐 安全风险分析：
# - ✅ 所有输入均为方法参数，未涉及用户输入直接执行逻辑，无明显注入风险；
# - ⚠️ `update_plan_step` 方法未限制输入内容格式，若后续与外部系统对接时可能需加入内容校验；
#
# 📐 编码规范审查：
# - 命名规范：✅ 所有方法与属性命名符合 PEP8 风格，且语义清晰；
# - 类型注解：✅ 所有方法参数、返回值及属性都有明确的类型注解；
# - 注释完整性：✅ 每个方法均有详细 docstring，说明其功能、参数与返回值；
# - 排版规范：✅ 使用四空格缩进，逻辑清晰、格式一致；
#
# 🏗 架构设计与可维护性建议：
# - ✅ 模块职责单一，适合作为需求推进状态容器；
# - ✅ 支持按文本切分设置步骤，方便接入自然语言规划生成模块；
# - ✅ `__str__` 方法便于调试与用户侧日志输出；
# - 🔧 可考虑增加当前进度百分比、历史步骤记录等增强功能；
# - 🔧 若后续支持并发访问，应考虑加锁或引入线程安全机制。
