#!/usr/bin/env python
from __future__ import annotations

import argparse
import json
from pathlib import Path

from generate_real_evolution_benchmark import (
    _abstain,
    _action,
    _ask,
    _canonical_arg,
    _canonical_tool,
    _case,
    _rendered_arg,
    _rendered_tool,
    _view,
)


def build_sources() -> dict[str, dict[str, str]]:
    return {
        "toolevo_paper": {
            "vendor": "toolevo",
            "kind": "paper",
            "url": "https://arxiv.org/abs/2410.06617",
            "summary": "ToolEVO paper introducing the ToolQA-D benchmark and API-kernel evolution settings Pc, Ps_in, and Ps_OOD.",
        },
        "toolevo_readme": {
            "vendor": "toolevo",
            "kind": "repository",
            "url": "https://github.com/Chen-GX/ToolEVO",
            "summary": "Official ToolEVO repository README describing ToolQA-D, public code/data release, and the api_kernel_version controls.",
        },
        "toolevo_api_vary": {
            "vendor": "toolevo",
            "kind": "code",
            "url": "https://github.com/Chen-GX/ToolEVO/blob/main/MCTS/src/api_vary.py",
            "summary": "Official ToolEVO API variation file mapping legacy ToolQA tool names and argument schemas to Ps_in and Ps_OOD variants.",
        },
        "toolevo_prompts": {
            "vendor": "toolevo",
            "kind": "code",
            "url": "https://github.com/Chen-GX/ToolEVO/blob/main/MCTS/src/prompts.py",
            "summary": "Official ToolEVO prompt file containing UpdateTool examples that document legacy-to-current tool migration behavior.",
        },
        "toolevo_few_shot_airbnb": {
            "vendor": "toolevo",
            "kind": "code",
            "url": "https://github.com/Chen-GX/ToolEVO/blob/main/MCTS/src/few_shots/toolqa_easy/airbnb-easy.py",
            "summary": "ToolEVO few-shot trajectories showing LoadDB, FilterDB, and GetValue usage on ToolQA-D airbnb tasks.",
        },
        "toolevo_few_shot_dblp": {
            "vendor": "toolevo",
            "kind": "code",
            "url": "https://github.com/Chen-GX/ToolEVO/blob/main/MCTS/src/few_shots/toolqa_easy/dblp-easy.py",
            "summary": "ToolEVO few-shot trajectories showing LoadGraph and NodeCheck usage on ToolQA-D dblp tasks.",
        },
    }


def build_tools() -> list[dict[str, object]]:
    return [
        _canonical_tool(
            "toolevo.agenda.retrieve",
            "Retrieve agenda entries that match a query string.",
            [
                _canonical_arg("query", "Agenda retrieval query text.", "string"),
                _canonical_arg("result_limit", "Optional agenda passage limit.", "integer", required=False),
            ],
            semantic_tags=["toolevo", "agenda", "retrieval"],
        ),
        _canonical_tool(
            "toolevo.scirex.retrieve",
            "Retrieve Scirex passages that match a query string.",
            [_canonical_arg("query", "Scirex retrieval query text.", "string")],
            semantic_tags=["toolevo", "scirex", "retrieval"],
        ),
        _canonical_tool(
            "toolevo.database.load",
            "Load a ToolQA database into the active workspace.",
            [_canonical_arg("database_name", "Database identifier to load.", "string")],
            semantic_tags=["toolevo", "database", "load"],
        ),
        _canonical_tool(
            "toolevo.database.filter",
            "Filter the active database with a single filter condition.",
            [
                _canonical_arg("condition", "Primary filter condition applied to the active database.", "string"),
                _canonical_arg("condition_secondary", "Optional secondary filter condition.", "string", required=False),
            ],
            semantic_tags=["toolevo", "database", "filter"],
        ),
        _canonical_tool(
            "toolevo.database.get_value",
            "Retrieve a field value from the active filtered database rows.",
            [
                _canonical_arg("field_name", "Field name to retrieve from the active table.", "string"),
                _canonical_arg("return_result", "Optional flag requesting explicit value materialization.", "boolean", required=False),
            ],
            semantic_tags=["toolevo", "database", "value"],
        ),
        _canonical_tool(
            "toolevo.graph.load",
            "Load a graph dataset into the active workspace.",
            [_canonical_arg("graph_name", "Graph identifier to load.", "string")],
            semantic_tags=["toolevo", "graph", "load"],
        ),
        _canonical_tool(
            "toolevo.graph.node_check",
            "Inspect whether a node exists in the loaded graph.",
            [
                _canonical_arg("graph_name", "Graph identifier to inspect.", "string"),
                _canonical_arg("node", "Node label to inspect.", "string"),
            ],
            semantic_tags=["toolevo", "graph", "node"],
        ),
        _canonical_tool(
            "toolevo.sql.execute",
            "Execute a SQL query through the ToolQA SQL interpreter.",
            [_canonical_arg("sql_query", "SQL query string to execute.", "string")],
            semantic_tags=["toolevo", "sql", "execution"],
        ),
        _canonical_tool(
            "toolevo.python.execute",
            "Execute a Python code snippet through the ToolQA Python interpreter.",
            [_canonical_arg("python_code", "Python code string to execute.", "string")],
            semantic_tags=["toolevo", "python", "execution"],
        ),
    ]


TOOL_VARIANTS: dict[str, dict[str, object]] = {
    "toolevo.agenda.retrieve": {
        "source": "toolevo_prompts",
        "notes": "Legacy RetrieveAgenda evolves into Fetch_Agenda_Data and Call_Retrieve_On_Agenda across ToolEVO API kernels.",
        "distractors": ["toolevo.scirex.retrieve", "toolevo.database.load"],
        "versions": {
            "clean": {
                "rendered_name": "RetrieveAgenda",
                "description": "Retrieve agenda passages that match the provided keyword.",
                "arguments": [
                    _rendered_arg("keyword", "query", "Agenda keyword query.", "string"),
                ],
            },
            "version_v1": {
                "rendered_name": "Fetch_Agenda_Data",
                "description": "Updated agenda retrieval tool that uses Query and optional return_num.",
                "arguments": [
                    _rendered_arg("Query", "query", "Agenda query text.", "string"),
                    _rendered_arg("return_num", "result_limit", "Optional return count hint.", "integer", required=False, position=1),
                ],
            },
            "version_v2": {
                "rendered_name": "Call_Retrieve_On_Agenda",
                "description": "Current ToolEVO agenda retrieval tool using searchTerm and optional passage_num.",
                "arguments": [
                    _rendered_arg("searchTerm", "query", "Agenda search text.", "string"),
                    _rendered_arg("passage_num", "result_limit", "Optional passage count hint.", "integer", required=False, position=1),
                ],
            },
        },
    },
    "toolevo.scirex.retrieve": {
        "source": "toolevo_prompts",
        "notes": "Legacy RetrieveScirex evolves into FetchScirexData and CallRetrieveOnScirex.",
        "distractors": ["toolevo.agenda.retrieve", "toolevo.database.load"],
        "versions": {
            "clean": {
                "rendered_name": "RetrieveScirex",
                "description": "Retrieve Scirex passages that match the provided keyword.",
                "arguments": [
                    _rendered_arg("keyword", "query", "Scirex keyword query.", "string"),
                ],
            },
            "version_v1": {
                "rendered_name": "FetchScirexData",
                "description": "Updated Scirex retrieval tool using QueryText.",
                "arguments": [
                    _rendered_arg("QueryText", "query", "Scirex query text.", "string"),
                ],
            },
            "version_v2": {
                "rendered_name": "CallRetrieveOnScirex",
                "description": "Current ToolEVO Scirex retrieval tool using queryKeyword.",
                "arguments": [
                    _rendered_arg("queryKeyword", "query", "Scirex query text.", "string"),
                ],
            },
        },
    },
    "toolevo.database.load": {
        "source": "toolevo_few_shot_airbnb",
        "notes": "Legacy LoadDB evolves into InitializeDatabase and Init_DB.",
        "distractors": ["toolevo.database.filter", "toolevo.graph.load"],
        "versions": {
            "clean": {
                "rendered_name": "LoadDB",
                "description": "Load a ToolQA database by DBName.",
                "arguments": [
                    _rendered_arg("DBName", "database_name", "Database name to load.", "string"),
                ],
            },
            "version_v1": {
                "rendered_name": "InitializeDatabase",
                "description": "Updated database loader using DatabaseName.",
                "arguments": [
                    _rendered_arg("DatabaseName", "database_name", "Database name to initialize.", "string"),
                ],
            },
            "version_v2": {
                "rendered_name": "Init_DB",
                "description": "Current ToolEVO database loader using databaseIdentifier.",
                "arguments": [
                    _rendered_arg("databaseIdentifier", "database_name", "Database identifier to initialize.", "string"),
                ],
            },
        },
    },
    "toolevo.database.filter": {
        "source": "toolevo_prompts",
        "notes": "Legacy FilterDB evolves into Apply_Database_Filters and DoFilter_OnDatabase.",
        "distractors": ["toolevo.database.get_value", "toolevo.graph.node_check"],
        "versions": {
            "clean": {
                "rendered_name": "FilterDB",
                "description": "Filter the active database with a single condition string.",
                "arguments": [
                    _rendered_arg("condition", "condition", "Database filter condition.", "string"),
                ],
            },
            "version_v1": {
                "rendered_name": "Apply_Database_Filters",
                "description": "Updated database filter tool using condition1 and optional condition2.",
                "arguments": [
                    _rendered_arg("condition1", "condition", "Primary filter condition.", "string"),
                    _rendered_arg("condition2", "condition_secondary", "Optional secondary filter condition.", "string", required=False, position=1),
                ],
            },
            "version_v2": {
                "rendered_name": "DoFilter_OnDatabase",
                "description": "Current ToolEVO database filter tool using filterCriteria1 and optional filterCriteria2.",
                "arguments": [
                    _rendered_arg("filterCriteria1", "condition", "Primary filter condition.", "string"),
                    _rendered_arg("filterCriteria2", "condition_secondary", "Optional secondary filter condition.", "string", required=False, position=1),
                ],
            },
        },
    },
    "toolevo.database.get_value": {
        "source": "toolevo_few_shot_airbnb",
        "notes": "Legacy GetValue evolves into FetchValue_ByKey and Extract_Value.",
        "distractors": ["toolevo.database.filter", "toolevo.sql.execute"],
        "versions": {
            "clean": {
                "rendered_name": "GetValue",
                "description": "Retrieve the value of a column from the active filtered table.",
                "arguments": [
                    _rendered_arg("column_name", "field_name", "Column name to retrieve.", "string"),
                ],
            },
            "version_v1": {
                "rendered_name": "FetchValue_ByKey",
                "description": "Updated value retrieval tool using column1 and optional ReturnResult.",
                "arguments": [
                    _rendered_arg("column1", "field_name", "Column name to retrieve.", "string"),
                    _rendered_arg("ReturnResult", "return_result", "Optional return flag.", "boolean", required=False, position=1),
                ],
            },
            "version_v2": {
                "rendered_name": "Extract_Value",
                "description": "Current ToolEVO value retrieval tool using fieldName1 and optional ReturnValue.",
                "arguments": [
                    _rendered_arg("fieldName1", "field_name", "Field name to retrieve.", "string"),
                    _rendered_arg("ReturnValue", "return_result", "Optional return flag.", "boolean", required=False, position=1),
                ],
            },
        },
    },
    "toolevo.graph.load": {
        "source": "toolevo_few_shot_dblp",
        "notes": "Legacy LoadGraph evolves into InitializeGraphData and Import_Graph.",
        "distractors": ["toolevo.graph.node_check", "toolevo.database.load"],
        "versions": {
            "clean": {
                "rendered_name": "LoadGraph",
                "description": "Load a graph dataset by GraphName.",
                "arguments": [
                    _rendered_arg("GraphName", "graph_name", "Graph name to load.", "string"),
                ],
            },
            "version_v1": {
                "rendered_name": "InitializeGraphData",
                "description": "Updated graph loader using Graph_Name.",
                "arguments": [
                    _rendered_arg("Graph_Name", "graph_name", "Graph name to initialize.", "string"),
                ],
            },
            "version_v2": {
                "rendered_name": "Import_Graph",
                "description": "Current ToolEVO graph loader using Graph.",
                "arguments": [
                    _rendered_arg("Graph", "graph_name", "Graph name to import.", "string"),
                ],
            },
        },
    },
    "toolevo.graph.node_check": {
        "source": "toolevo_few_shot_dblp",
        "notes": "Legacy NodeCheck evolves into ValidateGraphNode and Inspect_TheNodes.",
        "distractors": ["toolevo.graph.load", "toolevo.database.get_value"],
        "versions": {
            "clean": {
                "rendered_name": "NodeCheck",
                "description": "Inspect whether a node exists in a named graph.",
                "arguments": [
                    _rendered_arg("GraphName", "graph_name", "Graph name to inspect.", "string"),
                    _rendered_arg("Node", "node", "Node to inspect.", "string", position=1),
                ],
            },
            "version_v1": {
                "rendered_name": "ValidateGraphNode",
                "description": "Updated graph node inspection tool using Graph_Name and graphNode.",
                "arguments": [
                    _rendered_arg("Graph_Name", "graph_name", "Graph name to inspect.", "string"),
                    _rendered_arg("graphNode", "node", "Node to inspect.", "string", position=1),
                ],
            },
            "version_v2": {
                "rendered_name": "Inspect_TheNodes",
                "description": "Current ToolEVO graph node inspection tool using Graph and Vertex.",
                "arguments": [
                    _rendered_arg("Graph", "graph_name", "Graph name to inspect.", "string"),
                    _rendered_arg("Vertex", "node", "Node to inspect.", "string", position=1),
                ],
            },
        },
    },
    "toolevo.sql.execute": {
        "source": "toolevo_prompts",
        "notes": "Legacy SQLInterpreter evolves into ExecuteSQLQuery and ProcessSQLQuery.",
        "distractors": ["toolevo.python.execute", "toolevo.database.get_value"],
        "versions": {
            "clean": {
                "rendered_name": "SQLInterpreter",
                "description": "Execute a SQL query string.",
                "arguments": [
                    _rendered_arg("SQL", "sql_query", "SQL query to execute.", "string"),
                ],
            },
            "version_v1": {
                "rendered_name": "ExecuteSQLQuery",
                "description": "Updated SQL interpreter using SQLCommand.",
                "arguments": [
                    _rendered_arg("SQLCommand", "sql_query", "SQL query to execute.", "string"),
                ],
            },
            "version_v2": {
                "rendered_name": "ProcessSQLQuery",
                "description": "Current ToolEVO SQL interpreter using SQL_Query.",
                "arguments": [
                    _rendered_arg("SQL_Query", "sql_query", "SQL query to execute.", "string"),
                ],
            },
        },
    },
    "toolevo.python.execute": {
        "source": "toolevo_prompts",
        "notes": "Legacy PythonInterpreter evolves into Execute_Python_Script and Process_Python_Code.",
        "distractors": ["toolevo.sql.execute", "toolevo.database.get_value"],
        "versions": {
            "clean": {
                "rendered_name": "PythonInterpreter",
                "description": "Execute a Python code string.",
                "arguments": [
                    _rendered_arg("Python", "python_code", "Python code to execute.", "string"),
                ],
            },
            "version_v1": {
                "rendered_name": "Execute_Python_Script",
                "description": "Updated Python interpreter using PythonCode.",
                "arguments": [
                    _rendered_arg("PythonCode", "python_code", "Python code to execute.", "string"),
                ],
            },
            "version_v2": {
                "rendered_name": "Process_Python_Code",
                "description": "Current ToolEVO Python interpreter using python_execute_Code.",
                "arguments": [
                    _rendered_arg("python_execute_Code", "python_code", "Python code to execute.", "string"),
                ],
            },
        },
    },
}


def build_cases() -> list[dict[str, object]]:
    return [
        _case(
            case_id="toolevo_load_airbnb_db",
            request="Load the airbnb database into the current workspace.",
            tool_ids=["toolevo.database.load", "toolevo.database.filter", "toolevo.graph.load"],
            slot_values={"database_name": "airbnb"},
            action=_action("toolevo.database.load", database_name="airbnb"),
            family_tag="toolevo_bridge",
            notes="sources=toolevo_paper,toolevo_readme,toolevo_few_shot_airbnb;pair=legacy_name_to_versioned_loader",
        ),
        _case(
            case_id="toolevo_filter_by_author_name",
            request="In the current database, filter rows where NAME=Chao Zhang.",
            tool_ids=["toolevo.database.filter", "toolevo.database.get_value", "toolevo.graph.node_check"],
            slot_values={"condition": "NAME=Chao Zhang"},
            action=_action("toolevo.database.filter", condition="NAME=Chao Zhang"),
            family_tag="toolevo_bridge",
            notes="sources=toolevo_paper,toolevo_api_vary,toolevo_prompts;pair=legacy_name_to_split_filter_schema",
        ),
        _case(
            case_id="toolevo_get_price_column",
            request="From the current filtered table, return the price column.",
            tool_ids=["toolevo.database.get_value", "toolevo.database.filter", "toolevo.sql.execute"],
            slot_values={"field_name": "price"},
            action=_action("toolevo.database.get_value", field_name="price"),
            family_tag="toolevo_bridge",
            notes="sources=toolevo_paper,toolevo_api_vary,toolevo_few_shot_airbnb;pair=legacy_column_name_to_field_key",
        ),
        _case(
            case_id="toolevo_load_dblp_graph",
            request="Load the dblp graph into the current workspace.",
            tool_ids=["toolevo.graph.load", "toolevo.graph.node_check", "toolevo.database.load"],
            slot_values={"graph_name": "dblp"},
            action=_action("toolevo.graph.load", graph_name="dblp"),
            family_tag="toolevo_bridge",
            notes="sources=toolevo_paper,toolevo_api_vary,toolevo_few_shot_dblp;pair=legacy_name_to_versioned_graph_loader",
        ),
        _case(
            case_id="toolevo_check_author_node",
            request="Check whether K. John exists as a node in the AuthorNet graph.",
            tool_ids=["toolevo.graph.node_check", "toolevo.graph.load", "toolevo.database.get_value"],
            slot_values={"graph_name": "AuthorNet", "node": "K. John"},
            action=_action("toolevo.graph.node_check", graph_name="AuthorNet", node="K. John"),
            family_tag="toolevo_bridge",
            notes="sources=toolevo_paper,toolevo_api_vary,toolevo_few_shot_dblp;pair=legacy_graph_arg_rename",
        ),
        _case(
            case_id="toolevo_retrieve_agenda_entry",
            request="Retrieve agenda entries matching Amelia Breakfast Meeting 2022/01/16.",
            tool_ids=["toolevo.agenda.retrieve", "toolevo.scirex.retrieve", "toolevo.database.load"],
            slot_values={"query": "Amelia Breakfast Meeting 2022/01/16"},
            action=_action("toolevo.agenda.retrieve", query="Amelia Breakfast Meeting 2022/01/16"),
            family_tag="toolevo_bridge",
            notes="sources=toolevo_paper,toolevo_api_vary,toolevo_prompts;pair=legacy_keyword_to_search_term",
        ),
        _case(
            case_id="toolevo_execute_sql_query",
            request="Execute the SQL query: SELECT Volume FROM coffee.coffee_data WHERE Date = '2000-01-14'.",
            tool_ids=["toolevo.sql.execute", "toolevo.python.execute", "toolevo.database.get_value"],
            slot_values={"sql_query": "SELECT Volume FROM coffee.coffee_data WHERE Date = '2000-01-14'"},
            action=_action("toolevo.sql.execute", sql_query="SELECT Volume FROM coffee.coffee_data WHERE Date = '2000-01-14'"),
            family_tag="toolevo_bridge",
            notes="sources=toolevo_paper,toolevo_api_vary,toolevo_prompts;pair=legacy_sql_arg_rename",
        ),
        _case(
            case_id="toolevo_execute_python_mean",
            request="Execute this Python code: import numpy as np\\nprint(np.mean([247.0, 253.0, 230.0]))",
            tool_ids=["toolevo.python.execute", "toolevo.sql.execute", "toolevo.database.get_value"],
            slot_values={"python_code": "import numpy as np\\nprint(np.mean([247.0, 253.0, 230.0]))"},
            action=_action("toolevo.python.execute", python_code="import numpy as np\nprint(np.mean([247.0, 253.0, 230.0]))"),
            family_tag="toolevo_bridge",
            notes="sources=toolevo_paper,toolevo_api_vary,toolevo_prompts;pair=legacy_python_arg_rename",
        ),
    ]


def _variant(tool_id: str, version_key: str, *, deprecated: bool = False) -> dict[str, object]:
    payload = TOOL_VARIANTS[tool_id]
    variant = payload["versions"][version_key]
    description = str(variant["description"])
    status = "active"
    if deprecated:
        replacement = payload["versions"]["version_v1"]["rendered_name"]
        description = f"Deprecated: {description} Use {replacement} instead."
        status = "deprecated"
    return _rendered_tool(
        tool_id,
        variant["rendered_name"],
        description,
        list(variant["arguments"]),
        status=status,
    )


def _version_tools(primary_tool_id: str, version_key: str) -> list[dict[str, object]]:
    payload = TOOL_VARIANTS[primary_tool_id]
    tool_ids = [primary_tool_id, *payload["distractors"]]
    return [_variant(tool_id, version_key) for tool_id in tool_ids]


def _negative_tools(primary_tool_id: str) -> list[dict[str, object]]:
    payload = TOOL_VARIANTS[primary_tool_id]
    tool_ids = [primary_tool_id, *payload["distractors"]]
    rendered: list[dict[str, object]] = []
    for tool_id in tool_ids:
        rendered.append(_variant(tool_id, "clean", deprecated=(tool_id == primary_tool_id)))
    return rendered


def build_views(cases: list[dict[str, object]]) -> list[dict[str, object]]:
    views: list[dict[str, object]] = []
    for case in cases:
        case_id = str(case["case_id"])
        primary_tool_id = str(case["admissible_actions"][0]["tool_id"])
        payload = TOOL_VARIANTS[primary_tool_id]
        views.append(
            _view(
                case_id=case_id,
                view_id=f"{case_id}::clean",
                transform_name="clean",
                shift_kind="clean",
                tools=_version_tools(primary_tool_id, "clean"),
                notes=f"ToolEVO bridge clean view. {payload['notes']}",
            )
        )
        views.append(
            _view(
                case_id=case_id,
                view_id=f"{case_id}::positive_version_v1",
                transform_name="positive_version_v1",
                shift_kind="positive_orbit",
                tools=_version_tools(primary_tool_id, "version_v1"),
                notes=f"ToolEVO Ps_in bridge view derived from api_kernel_version=1. {payload['notes']}",
            )
        )
        views.append(
            _view(
                case_id=case_id,
                view_id=f"{case_id}::positive_version_v2",
                transform_name="positive_version_v2",
                shift_kind="positive_orbit",
                tools=_version_tools(primary_tool_id, "version_v2"),
                notes=f"ToolEVO Ps_OOD bridge view derived from api_kernel_version=2. {payload['notes']}",
            )
        )
        views.append(
            _view(
                case_id=case_id,
                view_id=f"{case_id}::negative_legacy_deprecate",
                transform_name="negative_legacy_deprecate",
                shift_kind="negative_near_orbit",
                tools=_negative_tools(primary_tool_id),
                notes=f"ToolEVO bridge negative view: only the legacy deprecated tool remains visible. {payload['notes']}",
                admissible_actions=[_ask(), _abstain()],
            )
        )
    return views


def build_benchmark() -> dict[str, object]:
    cases = build_cases()
    benchmark = {
        "metadata": {
            "benchmark_name": "toolevo_bridge_benchmark",
            "source_benchmark": "ToolEVO / ToolQA-D",
            "panel_role": "external_bridge",
            "counts": {
                "cases": len(cases),
                "views": len(cases) * 4,
                "families": 1,
            },
        },
        "tools": build_tools(),
        "cases": cases,
        "views": build_views(cases),
        "sources": build_sources(),
    }
    return benchmark


def write_audit_markdown(path: Path, benchmark: dict[str, object]) -> None:
    cases = benchmark["cases"]
    views = benchmark["views"]
    sources = benchmark["sources"]
    lines = [
        "# ToolEVO Bridge Audit",
        "",
        f"- Benchmark: `toolevo_bridge_benchmark`",
        f"- Cases: `{len(cases)}`",
        f"- Views: `{len(views)}`",
        "- Split: all cases are `unambiguous_core` with explicit clean / positive version v1 / positive version v2 / negative legacy-deprecate views.",
        "- Provenance: bridge microcases are derived from ToolEVO public API variation definitions and few-shot usage trajectories rather than imported end-to-end ToolQA answers.",
        "",
        "## Sources",
        "",
    ]
    for source_id, payload in sources.items():
        lines.append(f"- `{source_id}`: {payload['kind']} | {payload['url']}")
        lines.append(f"  - {payload['summary']}")
    lines.extend(
        [
            "",
            "## Case Families",
            "",
            "- `toolevo_bridge`: legacy-to-current tool migrations imported from ToolEVO `api_vary.py` for retrieval, database, graph, SQL, and Python tools.",
            "",
            "## Negative Policy",
            "",
            "- `negative_legacy_deprecate` views intentionally expose only the legacy deprecated tool and unrelated distractors.",
            "- Admissible actions are `ask_clarification` or `abstain`, because ToolEVO's actual recovery path depends on discovering a replacement tool through an interactive warning loop that is outside the one-step TOOLSHIFT protocol.",
        ]
    )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="Generate a TOOLSHIFT-style bridge benchmark from public ToolEVO API-evolution assets.")
    parser.add_argument("--output", default="data/toolevo_bridge_benchmark.json")
    parser.add_argument("--audit-md", default="history/toolevo_bridge_audit.md")
    args = parser.parse_args()

    output_path = Path(args.output)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    audit_path = Path(args.audit_md)
    audit_path.parent.mkdir(parents=True, exist_ok=True)

    benchmark = build_benchmark()
    output_path.write_text(json.dumps(benchmark, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    write_audit_markdown(audit_path, benchmark)
    print(f"Wrote {output_path} with {len(benchmark['cases'])} cases and {len(benchmark['views'])} views.")
    print(f"Wrote {audit_path}.")


if __name__ == "__main__":
    main()
