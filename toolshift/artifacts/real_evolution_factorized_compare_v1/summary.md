# Fixed Panel Method Comparison

- Records: `artifacts/real_evolution_family_holdout_v11/records.json`
- Benchmark: `data/real_evolution_benchmark.json`
- Regime: `family_holdout_cv`
- Methods: `semantic_contract_gate, semantic_capability_gate`

## Overall Metrics

| method | CAA | CAA+ | NOS | POC | coverage | selective_risk | contract_validity |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| semantic_contract_gate | 0.889 | 1.000 | 0.273 | 1.000 | 0.986 | 0.113 | 1.000 |
| semantic_capability_gate | 1.000 | 1.000 | 1.000 | 1.000 | 0.986 | 0.000 | 1.000 |

## semantic_capability_gate vs semantic_contract_gate

- improved_pair_count: `16`
- regressed_pair_count: `0`
- improved_distinct_views: `8`
- regressed_distinct_views: `0`
- strictly_fixed_views: `["bitbucket_get_legacy_account::negative_account_object_removed", "confluence_list_pages_by_space_key::negative_space_key_lookup_split", "jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed", "notion_create_page_in_database::negative_parent_scope_change", "notion_list_shared_databases::negative_search_replacement", "people_update_other_contact_email::negative_other_contacts_read_only", "stripe_list_customers_total_count::negative_removed_capability", "stripe_update_subscription_source::negative_source_removed"]`

### Delta Metrics

- CAA_clean: `0.000`
- CAA_negative: `0.727`
- CAA_overall: `0.111`
- CAA_positive: `0.000`
- NOS: `0.727`
- POC: `0.000`
- contract_validity: `0.000`
- coverage: `0.000`
- negative_coverage: `0.000`
- selective_risk: `-0.113`

### Incremental Fixes

- by_transform: `{"negative_account_object_removed": 2, "negative_legacy_identifier_removed": 2, "negative_other_contacts_read_only": 2, "negative_parent_scope_change": 2, "negative_removed_capability": 2, "negative_search_replacement": 2, "negative_source_removed": 2, "negative_space_key_lookup_split": 2}`
- by_family_tag: `{"bitbucket": 2, "confluence": 2, "jira": 2, "notion": 4, "people": 2, "stripe": 4}`
- by_primary_tool_id: `{"bitbucket.accounts.get_legacy_account": 2, "confluence.pages.list_by_space_key": 2, "jira.users.search_by_legacy_username": 2, "notion.databases.list_shared": 2, "notion.pages.create_in_container": 2, "people.other_contacts.update_email": 2, "stripe.customers.list_with_total_count": 2, "stripe.subscriptions.update_default_source": 2}`
- from_group: `{"tool_choice_error": 16}`
- from_bucket: `{"wrong_tool_choice": 16}`

### Regressions

- by_transform: `{}`
- by_family_tag: `{}`
- from_bucket: `{}`

### Representative Fixes

- `bitbucket_get_legacy_account::negative_account_object_removed` (bitbucket / negative_account_object_removed / bitbucket.accounts.get_legacy_account): `wrong_tool_choice -> correct_non_execute`
- `bitbucket_get_legacy_account::negative_account_object_removed` (bitbucket / negative_account_object_removed / bitbucket.accounts.get_legacy_account): `wrong_tool_choice -> correct_non_execute`
- `confluence_list_pages_by_space_key::negative_space_key_lookup_split` (confluence / negative_space_key_lookup_split / confluence.pages.list_by_space_key): `wrong_tool_choice -> correct_non_execute`
- `confluence_list_pages_by_space_key::negative_space_key_lookup_split` (confluence / negative_space_key_lookup_split / confluence.pages.list_by_space_key): `wrong_tool_choice -> correct_non_execute`
- `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed` (jira / negative_legacy_identifier_removed / jira.users.search_by_legacy_username): `wrong_tool_choice -> correct_non_execute`
- `jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed` (jira / negative_legacy_identifier_removed / jira.users.search_by_legacy_username): `wrong_tool_choice -> correct_non_execute`
- `notion_create_page_in_database::negative_parent_scope_change` (notion / negative_parent_scope_change / notion.pages.create_in_container): `wrong_tool_choice -> correct_non_execute`
- `notion_create_page_in_database::negative_parent_scope_change` (notion / negative_parent_scope_change / notion.pages.create_in_container): `wrong_tool_choice -> correct_non_execute`
- `notion_list_shared_databases::negative_search_replacement` (notion / negative_search_replacement / notion.databases.list_shared): `wrong_tool_choice -> correct_non_execute`
- `notion_list_shared_databases::negative_search_replacement` (notion / negative_search_replacement / notion.databases.list_shared): `wrong_tool_choice -> correct_non_execute`

## By Family

### semantic_contract_gate

- `bitbucket`: `CAA=0.875` `CAA+=1.000` `NOS=0.000` `count=16`
- `confluence`: `CAA=0.875` `CAA+=1.000` `NOS=0.000` `count=16`
- `drive`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `jira`: `CAA=0.875` `CAA+=1.000` `NOS=0.000` `count=16`
- `notion`: `CAA=0.750` `CAA+=1.000` `NOS=0.000` `count=16`
- `people`: `CAA=0.875` `CAA+=1.000` `NOS=0.000` `count=16`
- `sheets`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `slack`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `stripe`: `CAA=0.750` `CAA+=1.000` `NOS=0.000` `count=16`

### semantic_capability_gate

- `bitbucket`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `confluence`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `drive`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `jira`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `notion`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `people`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `sheets`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `slack`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
- `stripe`: `CAA=1.000` `CAA+=1.000` `NOS=1.000` `count=16`
