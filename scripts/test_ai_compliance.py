# -*- coding: utf-8 -*-
"""test_ai_compliance.py — AI 合规模块单元测试"""
import json
import sys
import tempfile
from pathlib import Path

# 确保能 import 同目录的 ai_compliance(无论从何处运行)
sys.path.insert(0, str(Path(__file__).resolve().parent))

from ai_compliance import AILogger


def test_full_workflow():
    """测试完整工作流：初始化→记录→声明→支撑材料→打包。"""
    with tempfile.TemporaryDirectory() as tmpdir:
        logger = AILogger(tmpdir)

        # 1. 初始化
        logger.start_session(["Claude Code", "DeepSeek-R1"])
        assert logger._log["tools"] == ["Claude Code", "DeepSeek-R1"]
        assert logger._log["session_started"] is not None
        print("✓ 初始化通过")

        # 2. 记录交互
        logger.log_interaction(
            stage="Stage 2 问题拆解",
            purpose="子问题分解与变量定义",
            prompt="请将本题拆解为3个子问题，每题列出核心变量和约束。",
            response="子问题1: 最小化运输成本...\n子问题2: 考虑时间窗约束...\n子问题3: 多目标权衡...",
            adopted=True,
            human_changes="调整了子问题2的约束条件表述，增加了容量限制",
        )
        logger.log_interaction(
            stage="Stage 5 模型求解",
            purpose="SA-PSO算法代码生成",
            prompt="用Python实现SA-PSO混合算法求解TSP问题",
            response="```python\nimport numpy as np\ndef sa_pso(...):\n```",
            adopted=True,
            human_changes="修改了退火速率参数，增加了收敛判断",
        )
        logger.log_interaction(
            stage="Stage 8 论文写作",
            purpose="语言润色",
            prompt="润色以下摘要段落...",
            response="优化后的摘要...",
            adopted=False,
            human_changes="AI润色过于书面化，保留原始表述并微调",
        )
        assert len(logger._log["interactions"]) == 3
        print("✓ 交互记录通过（3条）")

        # 3. 汇总
        summary = logger.get_summary()
        assert summary["total_interactions"] == 3
        assert summary["adopted_count"] == 2
        assert summary["modified_count"] == 3
        print(f"✓ 汇总通过: {summary['total_interactions']}次交互, "
              f"{summary['adopted_count']}次采纳, {summary['modified_count']}次修改")

        # 4. 生成声明
        decl = logger.generate_declaration(used_ai=True)
        assert "AI工具使用声明" in decl
        assert "代码调试" in decl or "子问题" in decl
        print("✓ 声明生成通过")

        # 5. 生成支撑材料
        support_path = logger.generate_support_pdf()
        assert Path(support_path).exists()
        content = Path(support_path).read_text(encoding="utf-8")
        assert "\\begin{longtable}" in content
        assert "Stage 2" in content
        print("✓ 支撑材料LaTeX生成通过")

        # 6. 一键打包
        checklist = logger.generate_compliance_package(used_ai=True)
        assert checklist["checklist"]["prompt_log_complete"] is True
        assert checklist["checklist"]["tools_listed"] is True
        assert checklist["checklist"]["human_review_documented"] is True
        print("✓ 合规打包通过")

        # 7. 验证未使用AI的声明
        decl_no = logger.generate_declaration(used_ai=False)
        assert "未使用任何AI工具" in decl_no
        print("✓ 未使用AI声明通过")

        # 8. 验证JSON日志完整性
        log_data = json.loads((Path(tmpdir) / "state/ai_interaction_log.json").read_text(encoding="utf-8"))
        assert len(log_data["interactions"]) == 3
        assert log_data["tools"] == ["Claude Code", "DeepSeek-R1"]
        print("✓ JSON日志完整性通过")

        print("\n" + "=" * 50)
        print("全部测试通过！")
        print("=" * 50)


if __name__ == "__main__":
    test_full_workflow()
