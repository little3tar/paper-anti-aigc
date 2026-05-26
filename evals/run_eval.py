#!/usr/bin/env python3
"""Skill 触发评估运行器。

读取 evals/trigger-evals.json，执行触发评估，生成 benchmark.json。

用法：
    python run_eval.py                  # 全部 skill
    python run_eval.py --skill docx-translator  # 单个 skill
    python run_eval.py --json           # JSON 输出到 stdout

评估模式：
    - 手动模式（默认）：逐条打印 query，等待用户输入实际触发的 skill
    - 自动模式：需要 Claude Code eval runner 基础设施（暂未集成）

输出：
    evals/benchmark.json — 包含逐条结果、按 skill 汇总和整体准确率
"""

from __future__ import annotations

import json
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

EVALS_DIR = Path(__file__).resolve().parent
EVALS_FILE = EVALS_DIR / "trigger-evals.json"
BENCHMARK_FILE = EVALS_DIR / "benchmark.json"


def load_evals() -> list[dict]:
    return json.loads(EVALS_FILE.read_text(encoding="utf-8"))


def run_manual(eval_cases: list[dict], skill_filter: str | None = None) -> list[dict]:
    """手动模式：逐条展示 query，等待用户输入触发的 skill 名称。"""
    results = []
    cases = [c for c in eval_cases if not skill_filter or c["skill_name"] == skill_filter]

    print(f"共 {len(cases)} 条用例，逐条评估。输入触发的 skill 名称（无触发输入 -）\n")

    for i, tc in enumerate(cases):
        print(f"[{i+1}/{len(cases)}] skill={tc['skill_name']} | 预期触发={'是' if tc['should_trigger'] else '否'}")
        print(f"  Query: {tc['query']}")
        actual = input("  实际触发 skill: ").strip()
        if actual == "-":
            actual = ""

        triggered = actual == tc["skill_name"]
        passed = triggered == tc["should_trigger"]

        results.append({
            "skill_name": tc["skill_name"],
            "query": tc["query"],
            "should_trigger": tc["should_trigger"],
            "expected_reason": tc["expected_reason"],
            "actual_skill": actual or None,
            "triggered": bool(actual),
            "passed": passed,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })

        status = "PASS" if passed else "FAIL"
        print(f"  => {status}\n")

    return results


def compute_summary(results: list[dict]) -> dict:
    """计算汇总统计。"""
    total = len(results)
    passed = sum(1 for r in results if r["passed"])
    failed = total - passed

    # 按 skill 汇总
    skills = sorted(set(r["skill_name"] for r in results))
    by_skill = []
    for skill in skills:
        skill_results = [r for r in results if r["skill_name"] == skill]
        pos = [r for r in skill_results if r["should_trigger"]]
        neg = [r for r in skill_results if not r["should_trigger"]]
        pos_pass = sum(1 for r in pos if r["passed"])
        neg_pass = sum(1 for r in neg if r["passed"])
        by_skill.append({
            "skill_name": skill,
            "positive_total": len(pos),
            "positive_pass": pos_pass,
            "negative_total": len(neg),
            "negative_pass": neg_pass,
            "trigger_accuracy": pos_pass / len(pos) if pos else 1.0,
            "false_trigger_rate": (len(neg) - neg_pass) / len(neg) if neg else 0.0,
        })

    return {
        "total": total,
        "passed": passed,
        "failed": failed,
        "accuracy": passed / total if total else 0.0,
        "by_skill": by_skill,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


def print_summary(summary: dict) -> None:
    """打印汇总报告。"""
    print(f"\n{'='*60}")
    print(f"  整体准确率: {summary['accuracy']:.1%} ({summary['passed']}/{summary['total']})")
    print(f"{'='*60}")
    print(f"  {'Skill':<38} {'触发':>6} {'误触发':>6}")
    print(f"  {'-'*38} {'-'*6} {'-'*6}")
    for s in summary["by_skill"]:
        ta = f"{s['trigger_accuracy']:.0%}"
        ft = f"{s['false_trigger_rate']:.0%}"
        print(f"  {s['skill_name']:<38} {ta:>6} {ft:>6}")
    print(f"{'='*60}")


def main() -> None:
    import argparse
    parser = argparse.ArgumentParser(description="Skill 触发评估运行器")
    parser.add_argument("--skill", help="只评估指定 skill")
    parser.add_argument("--json", action="store_true", help="JSON 输出到 stdout（不交互）")
    parser.add_argument("--summary-only", action="store_true", help="只显示已有 benchmark 的汇总")
    args = parser.parse_args()

    if args.summary_only:
        if BENCHMARK_FILE.exists():
            data = json.loads(BENCHMARK_FILE.read_text(encoding="utf-8"))
            print_summary(data["summary"])
        else:
            print("benchmark.json 不存在，请先运行评估。")
        return

    cases = load_evals()

    if args.json:
        # 非交互模式：输出 eval 用例列表供外部工具使用
        print(json.dumps(cases, ensure_ascii=False, indent=2))
        return

    # 手动交互模式
    results = run_manual(cases, args.skill)
    summary = compute_summary(results)

    benchmark = {
        "results": results,
        "summary": summary,
    }
    BENCHMARK_FILE.write_text(json.dumps(benchmark, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\n结果已写入 {BENCHMARK_FILE}")

    print_summary(summary)


if __name__ == "__main__":
    main()
