from __future__ import annotations

import copy
import unittest

from toolshift import load_seed_suite
from toolshift.api_surface_smoke import API_SURFACE_SMOKE_SPECS, run_api_surface_smoke
from toolshift.official_request_smoke import load_benchmark_payload


class ApiSurfaceSmokeTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.benchmark_path = "data/real_evolution_benchmark.json"
        cls.suite = load_seed_suite(cls.benchmark_path)
        cls.payload = load_benchmark_payload(cls.benchmark_path)
        cls.doc_map = cls._build_fake_doc_map()
        cls.json_map = cls._build_fake_json_map()

    @classmethod
    def _build_fake_doc_map(cls) -> dict[str, str]:
        doc_fragments: dict[str, list[str]] = {}
        sources = cls.payload["sources"]
        for spec in API_SURFACE_SMOKE_SPECS:
            for source_id in spec.doc_source_ids:
                url = sources[source_id]["url"]
                doc_fragments.setdefault(url, []).extend(spec.doc_needles)
        return {url: "\n".join(fragments) for url, fragments in doc_fragments.items()}

    @staticmethod
    def _build_fake_json_map() -> dict[str, dict]:
        drive_v2 = {
            "resources": {
                "parents": {
                    "methods": {
                        "insert": {
                            "httpMethod": "POST",
                            "path": "files/{fileId}/parents",
                            "parameters": {"fileId": {}, "supportsAllDrives": {}, "supportsTeamDrives": {}},
                            "request": {"$ref": "ParentReference"},
                        }
                    }
                }
            },
            "schemas": {"ParentReference": {"properties": {"id": {}, "selfLink": {}}}},
        }
        drive_v3 = {
            "resources": {
                "files": {
                    "methods": {
                        "update": {
                            "httpMethod": "PATCH",
                            "path": "files/{fileId}",
                            "parameters": {"fileId": {}, "addParents": {}, "removeParents": {}},
                            "request": {"$ref": "File"},
                        }
                    }
                }
            },
            "schemas": {"File": {"properties": {"name": {}, "mimeType": {}}}},
        }
        sheets_v4 = {
            "resources": {
                "spreadsheets": {
                    "methods": {
                        "get": {
                            "httpMethod": "GET",
                            "path": "v4/spreadsheets/{spreadsheetId}",
                            "parameters": {"spreadsheetId": {}, "fields": {}},
                        }
                    },
                    "resources": {
                        "values": {
                            "methods": {
                                "append": {
                                    "httpMethod": "POST",
                                    "path": "v4/spreadsheets/{spreadsheetId}/values/{range}:append",
                                    "parameters": {"spreadsheetId": {}, "range": {}, "valueInputOption": {}},
                                    "request": {"$ref": "ValueRange"},
                                },
                                "update": {
                                    "httpMethod": "PUT",
                                    "path": "v4/spreadsheets/{spreadsheetId}/values/{range}",
                                    "parameters": {"spreadsheetId": {}, "range": {}, "valueInputOption": {}},
                                    "request": {"$ref": "ValueRange"},
                                },
                            }
                        }
                    },
                }
            },
            "schemas": {
                "ValueRange": {"properties": {"range": {}, "majorDimension": {}, "values": {}}},
            },
        }
        people_v1 = {
            "resources": {
                "people": {
                    "methods": {
                        "createContact": {
                            "httpMethod": "POST",
                            "path": "v1/people:createContact",
                            "parameters": {"personFields": {}, "sources": {}},
                            "request": {"$ref": "Person"},
                        },
                    },
                    "resources": {
                        "connections": {
                            "methods": {
                                "list": {
                                    "httpMethod": "GET",
                                    "path": "v1/{+resourceName}/connections",
                                    "parameters": {"resourceName": {}, "pageSize": {}, "personFields": {}},
                                }
                            }
                        }
                    },
                },
                "contactGroups": {
                    "methods": {
                        "list": {
                            "httpMethod": "GET",
                            "path": "v1/contactGroups",
                            "parameters": {"groupFields": {}, "pageSize": {}},
                        }
                    }
                },
                "otherContacts": {
                    "methods": {
                        "copyOtherContactToMyContactsGroup": {
                            "httpMethod": "POST",
                            "path": "v1/{+resourceName}:copyOtherContactToMyContactsGroup",
                            "parameters": {"resourceName": {}},
                            "request": {"$ref": "CopyOtherContactToMyContactsGroupRequest"},
                        }
                    }
                },
            },
            "schemas": {
                "Person": {"properties": {"names": {}, "emailAddresses": {}}},
                "CopyOtherContactToMyContactsGroupRequest": {"properties": {"readMask": {}}},
            },
        }
        jira_v2 = {
            "paths": {
                "/rest/api/2/issue/{issueIdOrKey}/assignee": {
                    "put": {
                        "parameters": [{"name": "issueIdOrKey"}],
                        "requestBody": {
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/User"}}
                            }
                        },
                    }
                }
            },
            "components": {
                "schemas": {
                    "User": {
                        "properties": {"name": {}, "accountId": {}},
                    }
                }
            },
        }
        jira_v3 = {
            "paths": {
                "/rest/api/3/issue/{issueIdOrKey}/assignee": {
                    "put": {
                        "parameters": [{"name": "issueIdOrKey"}],
                        "requestBody": {
                            "content": {
                                "application/json": {"schema": {"$ref": "#/components/schemas/User"}}
                            }
                        },
                    }
                },
                "/rest/api/3/user/assignable/search": {
                    "get": {
                        "parameters": [{"name": "project"}, {"name": "query"}, {"name": "accountId"}],
                    }
                },
            },
            "components": {
                "schemas": {
                    "User": {
                        "properties": {"name": {}, "accountId": {}},
                    }
                }
            },
        }
        confluence_v2 = {
            "servers": [{"url": "https://{your-domain}/wiki/api/v2"}],
            "paths": {
                "/pages/{id}": {
                    "get": {
                        "parameters": [{"name": "id"}, {"name": "body-format"}],
                    }
                },
                "/pages/{id}/title": {
                    "put": {
                        "parameters": [{"name": "id"}],
                        "requestBody": {"$ref": "#/components/requestBodies/PageTitleUpdateRequest"},
                    }
                },
                "/pages/{id}/children": {
                    "get": {
                        "parameters": [{"name": "id"}, {"name": "cursor"}],
                    }
                },
            },
            "components": {
                "requestBodies": {
                    "PageTitleUpdateRequest": {
                        "content": {
                            "application/json": {
                                "schema": {"$ref": "#/components/schemas/PageTitleUpdate"}
                            }
                        }
                    }
                },
                "schemas": {
                    "PageTitleUpdate": {
                        "properties": {"status": {}, "title": {}},
                    }
                }
            },
        }
        bitbucket_swagger = {
            "swagger": "2.0",
            "basePath": "/2.0",
            "paths": {
                "/workspaces/{workspace}": {
                    "get": {
                        "parameters": [{"name": "workspace", "in": "path"}],
                    }
                },
                "/repositories/{workspace}": {
                    "get": {
                        "parameters": [{"name": "workspace", "in": "path"}, {"name": "q", "in": "query"}],
                    }
                },
                "/workspaces/{workspace}/members": {
                    "get": {
                        "parameters": [{"name": "workspace", "in": "path"}],
                    }
                },
            },
        }
        return {
            "https://www.googleapis.com/discovery/v1/apis/drive/v2/rest": drive_v2,
            "https://www.googleapis.com/discovery/v1/apis/drive/v3/rest": drive_v3,
            "https://www.googleapis.com/discovery/v1/apis/people/v1/rest": people_v1,
            "https://www.googleapis.com/discovery/v1/apis/sheets/v4/rest": sheets_v4,
            "https://developer.atlassian.com/cloud/jira/platform/swagger.v3.json": jira_v2,
            "https://developer.atlassian.com/cloud/jira/platform/swagger-v3.v3.json": jira_v3,
            "https://dac-static.atlassian.com/cloud/confluence/openapi-v2.v3.json": confluence_v2,
            "https://api.bitbucket.org/swagger.json": bitbucket_swagger,
        }

    def test_fake_specs_make_all_cases_pass(self) -> None:
        records, summary = run_api_surface_smoke(
            suite=self.suite,
            benchmark_payload=self.payload,
            fetch_json=self.json_map.__getitem__,
            fetch_text=self.doc_map.__getitem__,
        )
        self.assertEqual(len(records), len(API_SURFACE_SMOKE_SPECS))
        self.assertEqual(summary["pass_rate"], 1.0)
        self.assertEqual(summary["emit_expected_pass_rate"], 1.0)
        self.assertEqual(summary["block_expected_pass_rate"], 1.0)
        self.assertEqual(summary["by_kind"]["bitbucket_swagger"]["count"], 3)
        self.assertEqual(summary["by_kind"]["confluence_openapi"]["count"], 3)
        self.assertEqual(summary["by_kind"]["drive_discovery"]["count"], 2)
        self.assertEqual(summary["by_kind"]["jira_openapi"]["count"], 3)
        self.assertEqual(summary["by_kind"]["people_discovery"]["count"], 3)
        self.assertEqual(summary["by_kind"]["sheets_discovery"]["count"], 3)
        self.assertEqual(summary["by_kind"]["negative_docs"]["count"], 6)

    def test_missing_drive_query_param_in_spec_fails_positive_migration(self) -> None:
        broken_json = copy.deepcopy(self.json_map)
        broken_json["https://www.googleapis.com/discovery/v1/apis/drive/v3/rest"]["resources"]["files"]["methods"]["update"]["parameters"].pop(
            "addParents"
        )
        records, summary = run_api_surface_smoke(
            suite=self.suite,
            benchmark_payload=self.payload,
            fetch_json=broken_json.__getitem__,
            fetch_text=self.doc_map.__getitem__,
        )
        record = next(
            item
            for item in records
            if item.view_id == "drive_add_parent_to_file::positive_version_migration"
        )
        self.assertFalse(record.passed)
        self.assertIn("machine-readable spec mismatch", record.reason)
        self.assertFalse(record.spec_hits["query_keys"])
        self.assertLess(summary["pass_rate"], 1.0)

    def test_negative_legacy_identifier_case_remains_blocked(self) -> None:
        records, _ = run_api_surface_smoke(
            suite=self.suite,
            benchmark_payload=self.payload,
            fetch_json=self.json_map.__getitem__,
            fetch_text=self.doc_map.__getitem__,
        )
        record = next(
            item
            for item in records
            if item.view_id == "jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed"
        )
        self.assertTrue(record.passed)
        self.assertFalse(record.emitted)
        self.assertEqual(record.validation_kind, "negative_docs")
        self.assertEqual(record.spec_hits, {})
        self.assertIn("capability gap", record.reason)


if __name__ == "__main__":
    unittest.main()
