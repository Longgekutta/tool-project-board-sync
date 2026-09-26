"""GitHub GraphQL v4 client supporting Projects v2 and hermetic simulation."""
from dataclasses import dataclass
import json
import subprocess
from typing import Dict, Any, Optional

DEFAULT_TIMEOUT_SECONDS = 30
timeout=DEFAULT_TIMEOUT_SECONDS

@dataclass
class GraphQLResponse:
    success: bool
    data: Optional[Dict[str, Any]]
    error_message: Optional[str] = None
    raw_query: str = ""

class ProjectsGraphQLClient:
    def __init__(self, token: Optional[str] = None, dry_run: bool = True):
        self.token = token
        self.dry_run = dry_run

    def build_add_item_mutation(self, project_id: str, title: str) -> str:
        escaped_title = title.replace('"', '\\"')
        return f"""mutation {{
  addProjectV2DraftIssue(input: {{projectId: "{project_id}", title: "{escaped_title}"}}) {{
    projectItem {{
      id
    }}
  }}
}}"""

    def build_update_status_mutation(self, project_id: str, item_id: str, field_id: str, option_id: str) -> str:
        return f"""mutation {{
  updateProjectV2ItemFieldValue(
    input: {{
      projectId: "{project_id}"
      itemId: "{item_id}"
      fieldId: "{field_id}"
      value: {{ singleSelectOptionId: "{option_id}" }}
    }}
  ) {{
    projectV2Item {{
      id
    }}
  }}
}}"""

    def build_fetch_items_query(self, project_id: str, limit: int = 50) -> str:
        return f"""query {{
  node(id: "{project_id}") {{
    ... on ProjectV2 {{
      items(first: {limit}) {{
        nodes {{
          id
          content {{
            ... on DraftIssue {{
              title
              body
            }}
            ... on Issue {{
              title
              number
            }}
          }}
          fieldValues(first: 10) {{
            nodes {{
              ... on ProjectV2ItemFieldSingleSelectValue {{
                name
              }}
              ... on ProjectV2ItemFieldNumberValue {{
                number
              }}
              ... on ProjectV2ItemFieldIterationValue {{
                title
              }}
            }}
          }}
        }}
      }}
    }}
  }}
}}"""

    def execute_query(self, query: str) -> GraphQLResponse:
        if self.dry_run or not self.token:
            # Deterministic hermetic simulation response
            if "items(first:" in query:
                sim_data = {
                    "node": {
                        "items": {
                            "nodes": [
                                {
                                    "id": "PVTI_mock_1",
                                    "content": {"title": "[Todo] Setup CI Pipeline"},
                                    "fieldValues": {"nodes": [{"name": "Todo"}, {"number": 3.0}, {"title": "Sprint 1"}]}
                                },
                                {
                                    "id": "PVTI_mock_2",
                                    "content": {"title": "[Done] Initialize Core Engine"},
                                    "fieldValues": {"nodes": [{"name": "Done"}, {"number": 5.0}, {"title": "Sprint 1"}]}
                                }
                            ]
                        }
                    }
                }
            else:
                sim_data = {
                    "addProjectV2DraftIssue": {
                        "projectItem": {"id": "PVTI_mock_item_id_12345"}
                    },
                    "updateProjectV2ItemFieldValue": {
                        "projectV2Item": {"id": "PVTI_mock_item_id_12345"}
                    }
                }
            return GraphQLResponse(success=True, data=sim_data, raw_query=query)

        cmd = ["gh", "api", "graphql", "-f", f"query={query}"]
        try:
            res = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=DEFAULT_TIMEOUT_SECONDS,
                check=False
            )
            if res.returncode == 0:
                data = json.loads(res.stdout)
                return GraphQLResponse(success=True, data=data, raw_query=query)
            else:
                return GraphQLResponse(success=False, data=None, error_message=res.stderr, raw_query=query)
        except Exception as e:
            return GraphQLResponse(success=False, data=None, error_message=str(e), raw_query=query)
