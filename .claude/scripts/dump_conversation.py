#!/usr/bin/env python3
"""
dump_conversation.py — 导出当前 Claude Code 会话为 Markdown
用法: python dump_conversation.py [--session-id UUID] [--output PATH]
默认: 取最新会话,输出到 bigmemory/冷区/会话记录/YYYY-MM-DD_HHMM.md
"""

import json
import os
import sys
import glob
import argparse
from datetime import datetime, timezone, timedelta
from pathlib import Path

# ------------------------------------------------------------------ #
#  常量
# ------------------------------------------------------------------ #

PROJ_DIR = Path(__file__).resolve().parents[2]                # DQN10/
CLAUDE_PROJ = Path.home() / ".claude" / "projects"
# 项目 hash 目录名: 把路径中的 / 替换成 -,前面加 -
PROJ_HASH = "-" + str(PROJ_DIR).replace("/", "-").lstrip("-")
SESS_DIR = CLAUDE_PROJ / PROJ_HASH

BJ_TZ = timezone(timedelta(hours=8))                         # UTC+8


# ------------------------------------------------------------------ #
#  工具函数
# ------------------------------------------------------------------ #

def find_latest_session(sess_dir: Path) -> Path:
    """找到最新的 .jsonl 会话文件(按修改时间)"""
    jsonls = sorted(sess_dir.glob("*.jsonl"), key=os.path.getmtime, reverse=True)
    if not jsonls:
        sys.exit(f"[错误] 在 {sess_dir} 下未找到 .jsonl 文件")
    return jsonls[0]


def find_subagent_files(sess_dir: Path, session_id: str) -> list[Path]:
    """找到该会话的所有 subagent JSONL"""
    sub_dir = sess_dir / session_id / "subagents"
    if not sub_dir.exists():
        return []
    return sorted(sub_dir.glob("*.jsonl"), key=os.path.getmtime)


def parse_timestamp(ts_str: str) -> datetime:
    """ISO 时间戳 → 北京时间"""
    dt = datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    return dt.astimezone(BJ_TZ)


def extract_text(content) -> str:
    """从 message.content 中提取纯文本(跳过 thinking/tool_use)"""
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        parts = []
        for block in content:
            if block.get("type") == "text":
                parts.append(block["text"].strip())
        return "\n\n".join(parts)
    return ""


def extract_tool_calls(content) -> list[str]:
    """提取 tool_use 摘要(工具名 + 简短参数)"""
    if not isinstance(content, list):
        return []
    calls = []
    for block in content:
        if block.get("type") == "tool_use":
            name = block.get("name", "?")
            inp = block.get("input", {})
            # 只取关键参数的前 80 字符
            summary_parts = []
            for k, v in inp.items():
                v_str = str(v)[:80]
                if len(str(v)) > 80:
                    v_str += "..."
                summary_parts.append(f"{k}={v_str}")
            summary = ", ".join(summary_parts[:3])
            if len(summary_parts) > 3:
                summary += ", ..."
            calls.append(f"`{name}({summary})`")
    return calls


def process_jsonl(jsonl_path: Path, label: str = "主会话") -> list[str]:
    """解析一个 JSONL 文件,返回 markdown 行列表"""
    lines = []
    lines.append(f"### {label}")
    lines.append("")

    with open(jsonl_path) as f:
        for raw_line in f:
            obj = json.loads(raw_line)
            msg_type = obj.get("type")

            if msg_type not in ("user", "assistant"):
                continue

            msg = obj.get("message", {})
            content = msg.get("content", "")
            ts_str = obj.get("timestamp", "")

            # 时间戳
            time_label = ""
            if ts_str:
                try:
                    dt = parse_timestamp(ts_str)
                    time_label = dt.strftime("%H:%M")
                except Exception:
                    pass

            if msg_type == "user":
                text = extract_text(content)
                if not text:
                    continue
                # 跳过系统注入的 meta 消息
                if obj.get("isMeta"):
                    continue
                # 跳过纯 system-reminder / task-notification
                if text.startswith("<system-reminder>") or text.startswith("<task-notification>"):
                    continue
                # 跳过 local-command 输出
                if text.startswith("<local-command"):
                    continue
                # 清理 command 消息
                if "<command-name>" in text:
                    # 提取命令名
                    import re
                    cmd = re.search(r"<command-name>(.*?)</command-name>", text)
                    if cmd:
                        text = f"/{cmd.group(1)}"

                lines.append(f"**Dr Sun** [{time_label}]:")
                lines.append(f"> {text}")
                lines.append("")

            elif msg_type == "assistant":
                text = extract_text(content)
                tools = extract_tool_calls(content)

                if not text and not tools:
                    continue

                lines.append(f"**AI** [{time_label}]:")
                if text:
                    # 截断超长输出(保留前 500 字)
                    if len(text) > 2000:
                        text = text[:2000] + "\n\n... (截断,完整内容见原始 JSONL)"
                    lines.append(text)
                if tools:
                    lines.append("")
                    lines.append("工具调用: " + " → ".join(tools[:5]))
                    if len(tools) > 5:
                        lines.append(f"  ... 共 {len(tools)} 个调用")
                lines.append("")

    return lines


# ------------------------------------------------------------------ #
#  主流程
# ------------------------------------------------------------------ #

def main():
    parser = argparse.ArgumentParser(description="导出 Claude Code 会话为 Markdown")
    parser.add_argument("--session-id", help="指定会话 UUID,默认取最新")
    parser.add_argument("--output", "-o", help="输出路径,默认 bigmemory/冷区/会话记录/")
    args = parser.parse_args()

    # 定位会话文件
    if args.session_id:
        jsonl_path = SESS_DIR / f"{args.session_id}.jsonl"
        if not jsonl_path.exists():
            sys.exit(f"[错误] 找不到会话: {jsonl_path}")
    else:
        jsonl_path = find_latest_session(SESS_DIR)

    session_id = jsonl_path.stem
    mod_time = datetime.fromtimestamp(jsonl_path.stat().st_mtime, tz=BJ_TZ)

    print(f"[信息] 会话: {session_id}")
    print(f"[信息] 文件: {jsonl_path}")
    print(f"[信息] 大小: {jsonl_path.stat().st_size / 1024:.0f} KB")

    # 解析主会话
    md_lines = []
    md_lines.append(f"# 会话记录")
    md_lines.append(f"> 会话 ID: `{session_id}`")
    md_lines.append(f"> 导出时间: {mod_time.strftime('%Y-%m-%d %H:%M')}")
    md_lines.append("")

    md_lines.extend(process_jsonl(jsonl_path, "主会话"))

    # 解析 subagent 会话
    sub_files = find_subagent_files(SESS_DIR, session_id)
    if sub_files:
        md_lines.append("---")
        md_lines.append("")
        md_lines.append("## Subagent 会话")
        md_lines.append("")
        for sf in sub_files:
            agent_name = sf.stem
            md_lines.extend(process_jsonl(sf, f"Agent: {agent_name}"))
            md_lines.append("---")
            md_lines.append("")

    # 输出
    output_text = "\n".join(md_lines)

    if args.output:
        out_path = Path(args.output)
    else:
        out_dir = PROJ_DIR / "bigmemory" / "冷区" / "会话记录"
        out_dir.mkdir(parents=True, exist_ok=True)
        out_path = out_dir / f"{mod_time.strftime('%Y-%m-%d_%H%M')}.md"

    out_path.write_text(output_text, encoding="utf-8")
    print(f"[完成] 已导出到 {out_path}")
    print(f"[信息] 共 {len(output_text)} 字符, {output_text.count(chr(10))} 行")


if __name__ == "__main__":
    main()
