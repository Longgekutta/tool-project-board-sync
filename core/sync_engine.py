"""Sync engine reconciling local tasks against GitHub Projects v2."""
from dataclasses import dataclass
from typing import List, Dict
from .models import TaskItem, TaskStatus, ProjectBoardView
from .graphql_client import ProjectsGraphQLClient

DEFAULT_TIMEOUT_SECONDS = 30
timeout=DEFAULT_TIMEOUT_SECONDS

@dataclass
class SyncResult:
    total_tasks: int
    synced_items: int
    failed_items: int
    board_view: ProjectBoardView
    simulation: bool

class SyncEngine:
    def __init__(self, client: ProjectsGraphQLClient, project_id: str = "PVT_kwDOB12345"):
        self.client = client
        self.project_id = project_id

    def build_board_view(self, project_title: str, tasks: List[TaskItem]) -> ProjectBoardView:
        view = ProjectBoardView(project_title=project_title)
        for t in tasks:
            view.columns[t.status].append(t)
        return view

    def sync_tasks(self, tasks: List[TaskItem], project_title: str = "Agent Sprint Board") -> SyncResult:
        board_view = self.build_board_view(project_title, tasks)
        synced = 0
        failed = 0

        for t in tasks:
            mut = self.client.build_add_item_mutation(self.project_id, f"[{t.status.value}] {t.title}")
            res = self.client.execute_query(mut)
            if res.success:
                synced += 1
            else:
                failed += 1

        return SyncResult(
            total_tasks=len(tasks),
            synced_items=synced,
            failed_items=failed,
            board_view=board_view,
            simulation=self.client.dry_run or not self.client.token
        )

    def export_kanban_markdown(self, view: ProjectBoardView) -> str:
        lines: List[str] = [f"# Kanban Board: {view.project_title}", ""]
        for status in TaskStatus:
            items = view.columns.get(status, [])
            lines.append(f"## {status.value} ({len(items)})")
            if not items:
                lines.append("_No tasks currently in this column._")
            else:
                for item in items:
                    assignee_str = f" @{item.assignee}" if item.assignee else ""
                    lines.append(f"- [{item.task_id}] {item.title}{assignee_str}")
            lines.append("")
        return "\n".join(lines)
