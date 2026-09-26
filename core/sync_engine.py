"""Sync engine reconciling local tasks against GitHub Projects v2."""
from dataclasses import dataclass
from typing import List, Dict, Any
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

    def pull_tasks(self, limit: int = 50) -> List[TaskItem]:
        query = self.client.build_fetch_items_query(self.project_id, limit=limit)
        res = self.client.execute_query(query)
        if not res.success or not res.data:
            return []

        nodes = res.data.get("node", {}).get("items", {}).get("nodes", [])
        tasks: List[TaskItem] = []
        for idx, n in enumerate(nodes, start=1):
            item_id = n.get("id")
            content = n.get("content") or {}
            title = content.get("title") or f"Untitled Item {idx}"
            
            # Parse status, iteration, estimate from fieldValues
            status = TaskStatus.TODO
            iteration = None
            estimate = None

            fields = n.get("fieldValues", {}).get("nodes", [])
            for f in fields:
                if "name" in f:
                    for s in TaskStatus:
                        if s.value.lower() == f["name"].lower():
                            status = s
                            break
                elif "number" in f:
                    estimate = float(f["number"])
                elif "title" in f:
                    iteration = f["title"]

            tasks.append(TaskItem(
                task_id=f"remote-{idx}",
                title=title,
                status=status,
                project_item_id=item_id,
                iteration=iteration,
                estimate=estimate
            ))
        return tasks

    def reconcile(self, local_tasks: List[TaskItem], project_title: str = "Reconciled Board") -> Dict[str, Any]:
        remote_tasks = self.pull_tasks()
        remote_titles = {r.title.lower(): r for r in remote_tasks}
        
        to_push = []
        in_sync = []
        for l in local_tasks:
            key = f"[{l.status.value}] {l.title}".lower()
            key_plain = l.title.lower()
            if key in remote_titles or key_plain in remote_titles:
                in_sync.append(l)
            else:
                to_push.append(l)

        sync_res = self.sync_tasks(to_push, project_title=project_title)
        return {
            "local_total": len(local_tasks),
            "remote_total": len(remote_tasks),
            "in_sync_count": len(in_sync),
            "newly_pushed": sync_res.synced_items,
            "board_view": sync_res.board_view
        }

    def export_sprint_burndown_summary(self, view: ProjectBoardView) -> Dict[str, Any]:
        total_tasks = sum(len(items) for items in view.columns.values())
        done_tasks = len(view.columns.get(TaskStatus.DONE, []))
        in_progress = len(view.columns.get(TaskStatus.IN_PROGRESS, []))
        todo_tasks = len(view.columns.get(TaskStatus.TODO, []))
        blocked_tasks = len(view.columns.get(TaskStatus.BLOCKED, []))

        pct = (done_tasks / total_tasks * 100.0) if total_tasks > 0 else 0.0

        return {
            "project_title": view.project_title,
            "total_tasks": total_tasks,
            "done_tasks": done_tasks,
            "in_progress_tasks": in_progress,
            "todo_tasks": todo_tasks,
            "blocked_tasks": blocked_tasks,
            "completion_percentage": round(pct, 1)
        }

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
                    iter_str = f" [{item.iteration}]" if item.iteration else ""
                    est_str = f" ({item.estimate} pts)" if item.estimate is not None else ""
                    lines.append(f"- [{item.task_id}] {item.title}{assignee_str}{iter_str}{est_str}")
            lines.append("")
        return "\n".join(lines)
