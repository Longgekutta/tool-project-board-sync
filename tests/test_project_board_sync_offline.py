"""Hermetic offline unit tests for tool-project-board-sync."""
import json
import tempfile
import unittest
from pathlib import Path

from core.models import TaskItem, TaskStatus
from core.task_parser import parse_tasks_from_markdown, parse_tasks_from_file
from core.graphql_client import ProjectsGraphQLClient
from core.sync_engine import SyncEngine

DEFAULT_TIMEOUT_SECONDS = 30
timeout=DEFAULT_TIMEOUT_SECONDS

class TestProjectBoardSyncOffline(unittest.TestCase):
    def test_01_parse_tasks_markdown(self):
        md = """
# Task List
- [ ] Task Alpha
- [/] Task Beta In Progress
- [x] Task Gamma Completed
- [!] Task Delta Blocked
"""
        tasks = parse_tasks_from_markdown(md)
        self.assertEqual(len(tasks), 4)
        self.assertEqual(tasks[0].status, TaskStatus.TODO)
        self.assertEqual(tasks[1].status, TaskStatus.IN_PROGRESS)
        self.assertEqual(tasks[2].status, TaskStatus.DONE)
        self.assertEqual(tasks[3].status, TaskStatus.BLOCKED)

    def test_02_parse_tasks_json(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            tmp = Path(tmpdir)
            tfile = tmp / "tasks.json"
            tdata = [
                {"id": "t1", "title": "Build Docker", "status": "In Progress"},
                {"id": "t2", "title": "Deploy Pages", "status": "Done"}
            ]
            tfile.write_text(json.dumps(tdata), encoding="utf-8")

            tasks = parse_tasks_from_file(tfile)
            self.assertEqual(len(tasks), 2)
            self.assertEqual(tasks[0].status, TaskStatus.IN_PROGRESS)
            self.assertEqual(tasks[1].status, TaskStatus.DONE)

    def test_03_graphql_mutation_builder(self):
        client = ProjectsGraphQLClient()
        mut = client.build_add_item_mutation("PVT_123", "Setup Database")
        self.assertIn("addProjectV2DraftIssue", mut)
        self.assertIn("Setup Database", mut)

        mut_field = client.build_update_status_mutation("PVT_123", "ITEM_1", "FIELD_1", "OPT_1")
        self.assertIn("updateProjectV2ItemFieldValue", mut_field)

    def test_04_sync_engine_hermetic_simulation(self):
        client = ProjectsGraphQLClient(dry_run=True)
        engine = SyncEngine(client)
        tasks = [
            TaskItem("1", "T1", TaskStatus.TODO),
            TaskItem("2", "T2", TaskStatus.DONE),
        ]
        res = engine.sync_tasks(tasks, project_title="Test Sprint")
        self.assertEqual(res.total_tasks, 2)
        self.assertEqual(res.synced_items, 2)
        self.assertTrue(res.simulation)

    def test_05_export_kanban_markdown(self):
        client = ProjectsGraphQLClient()
        engine = SyncEngine(client)
        tasks = [
            TaskItem("1", "Task One", TaskStatus.TODO),
            TaskItem("2", "Task Two", TaskStatus.DONE),
        ]
        view = engine.build_board_view("Sprint Alpha", tasks)
        md = engine.export_kanban_markdown(view)
        self.assertIn("# Kanban Board: Sprint Alpha", md)
        self.assertIn("## Todo (1)", md)
        self.assertIn("## Done (1)", md)

    def test_06_pull_tasks_and_burndown(self):
        client = ProjectsGraphQLClient(dry_run=True)
        engine = SyncEngine(client)
        pulled = engine.pull_tasks()
        self.assertEqual(len(pulled), 2)
        self.assertEqual(pulled[0].title, "[Todo] Setup CI Pipeline")
        self.assertEqual(pulled[0].status, TaskStatus.TODO)
        self.assertEqual(pulled[0].estimate, 3.0)
        self.assertEqual(pulled[0].iteration, "Sprint 1")

        view = engine.build_board_view("Sprint 1", pulled)
        summary = engine.export_sprint_burndown_summary(view)
        self.assertEqual(summary["total_tasks"], 2)
        self.assertEqual(summary["done_tasks"], 1)
        self.assertEqual(summary["completion_percentage"], 50.0)

    def test_07_reconcile_delta(self):
        client = ProjectsGraphQLClient(dry_run=True)
        engine = SyncEngine(client)
        local_tasks = [
            TaskItem("l1", "Setup CI Pipeline", TaskStatus.TODO),
            TaskItem("l2", "Brand New Feature", TaskStatus.TODO)
        ]
        report = engine.reconcile(local_tasks)
        self.assertEqual(report["local_total"], 2)
        self.assertEqual(report["in_sync_count"], 1)
        self.assertEqual(report["newly_pushed"], 1)

if __name__ == "__main__":
    unittest.main()
