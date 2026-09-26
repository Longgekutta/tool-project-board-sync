"""Task parser extracting structured tasks from JSON or Markdown checklists."""
import json
from pathlib import Path
import re
from typing import List
from .models import TaskItem, TaskStatus

DEFAULT_TIMEOUT_SECONDS = 30
timeout=DEFAULT_TIMEOUT_SECONDS

def parse_tasks_from_markdown(content: str) -> List[TaskItem]:
    tasks: List[TaskItem] = []
    lines = content.splitlines()

    for idx, line in enumerate(lines, start=1):
        line = line.strip()
        # Markdown checklist: - [ ] or - [x] or - [/]
        m = re.match(r"^-\s*\[([ xX/~!])\]\s*(.+)$", line)
        if m:
            mark = m.group(1).lower()
            title = m.group(2).strip()

            if mark == "x":
                status = TaskStatus.DONE
            elif mark in ["/", "~"]:
                status = TaskStatus.IN_PROGRESS
            elif mark == "!":
                status = TaskStatus.BLOCKED
            else:
                status = TaskStatus.TODO

            tasks.append(TaskItem(
                task_id=f"task-{idx}",
                title=title,
                status=status
            ))

    return tasks

def parse_tasks_from_file(file_path: str | Path) -> List[TaskItem]:
    path = Path(file_path).resolve()
    if not path.is_file():
        return []

    try:
        content = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return []

    if path.suffix.lower() == ".json":
        try:
            data = json.loads(content)
            tasks = []
            items = data if isinstance(data, list) else data.get("tasks", [])
            for idx, item in enumerate(items, start=1):
                tid = str(item.get("id") or f"task-{idx}")
                title = str(item.get("title") or item.get("name") or "Untitled Task")
                status_raw = str(item.get("status", "Todo")).title()
                
                status = TaskStatus.TODO
                for s in TaskStatus:
                    if s.value.lower() == status_raw.lower():
                        status = s
                        break

                tasks.append(TaskItem(
                    task_id=tid,
                    title=title,
                    status=status,
                    assignee=item.get("assignee"),
                    labels=item.get("labels", [])
                ))
            return tasks
        except Exception:
            return []

    return parse_tasks_from_markdown(content)
