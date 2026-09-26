# PowerShell runner for tool-project-board-sync
param(
    [string]$Command = "health",
    [string]$Target = ".",
    [string]$ProjectId = "PVT_kwDOB12345"
)

switch ($Command) {
    "setup"  { python main.py setup }
    "run"    { python main.py run --target $Target }
    "test"   { python main.py test }
    "health" { python main.py health }
    "clean"  { python main.py clean }
    "sync"   { python main.py sync --target $Target --project-id $ProjectId }
    "status" { python main.py status --target $Target }
    Default  { python main.py $Command }
}
