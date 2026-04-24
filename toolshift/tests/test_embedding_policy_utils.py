from __future__ import annotations

import unittest
from unittest.mock import patch

import toolshift.embedding_policy as embedding_policy_module
from toolshift import load_seed_suite
from toolshift.schema import ControlTag
from toolshift.embedding_policy import (
    CAPABILITY_CONTINUOUS_FEATURE_NAMES,
    CAPABILITY_CUE_FEATURE_NAMES,
    CAPABILITY_DESCRIPTION_POOL_FEATURE_NAMES,
    CAPABILITY_EMBEDDING_FEATURE_NAMES,
    CAPABILITY_RAWTEXT_FEATURE_NAMES,
    CROSS_ENCODER_CLAUSE_FEATURE_NAMES,
    CROSS_ENCODER_FEATURE_NAMES,
    CrossEncoderBinaryTaskSpec,
    CrossEncoderCapabilityGate,
    CrossEncoderClauseLocalizer,
    EmbeddingPolicyConfig,
    LearnedCapabilityScorer,
    LearnedClauseLocalizer,
    _capability_dense_feature_vector,
    _best_binary_threshold,
    _best_asymmetric_binary_threshold,
    _best_dual_threshold_band,
    _build_class_balanced_hard_negative_weights,
    _capability_cue_clauses,
    _cross_encoder_clause_feature_map,
    _dual_threshold_control,
    _cross_encoder_execute_margin_penalty,
    _capability_feature_map,
    _configure_cross_encoder_finetuning,
    _cross_encoder_feature_map,
    _cross_encoder_should_inhibit,
    _flatten_cross_encoder_binary_tasks,
    _fit_listwise_clause_ranker,
    _parse_method,
    _select_cross_encoder_clause,
    _tool_contract_compatible,
    _tool_has_description_capability_gap,
    _tool_request_capability_overlap,
    build_slot_vocab,
    serialize_view,
    train_embedding_policy_agent,
)


class EmbeddingPolicyUtilsTest(unittest.TestCase):
    class _FakeEncoder:
        def __init__(self) -> None:
            self.device = "cpu"
            self.batch_size = 8
            self.instruction = "test instruction"

        def _with_instruction(self, text: str) -> str:
            return text

        def encode_texts(self, texts):
            torch = embedding_policy_module.torch
            rows = []
            for text in texts:
                values = [0.1] * 8
                for index, char in enumerate(text.encode("utf-8")):
                    values[index % 8] += ((char % 31) + 1) / 31.0
                rows.append(torch.tensor(values, dtype=torch.float32))
            return torch.stack(rows)

    class _FakeCrossEncoder:
        def score_pairs(self, *, instruction: str, pairs):
            scores = []
            for _query, document in pairs:
                lowered = document.lower()
                if "no direct replacement" in lowered or "not supported" in lowered or "read-only" in lowered:
                    scores.append(0.95)
                elif "candidate clause" in lowered:
                    scores.append(0.05)
                else:
                    scores.append(0.15)
            return scores

    def test_capability_cue_feature_names_exclude_generic_score_terms(self) -> None:
        self.assertIn("cue_clause_count", CAPABILITY_CUE_FEATURE_NAMES)
        self.assertIn("has_gap_rule", CAPABILITY_CUE_FEATURE_NAMES)
        self.assertNotIn("best_active_score", CAPABILITY_CUE_FEATURE_NAMES)
        self.assertNotIn("score_margin", CAPABILITY_CUE_FEATURE_NAMES)
        self.assertNotIn("tool_overlap", CAPABILITY_CUE_FEATURE_NAMES)

    def test_capability_continuous_feature_names_exclude_binary_cues(self) -> None:
        self.assertIn("description_overlap", CAPABILITY_CONTINUOUS_FEATURE_NAMES)
        self.assertIn("max_cue_overlap", CAPABILITY_CONTINUOUS_FEATURE_NAMES)
        self.assertIn("total_cue_overlap", CAPABILITY_CONTINUOUS_FEATURE_NAMES)
        self.assertNotIn("cue_clause_count", CAPABILITY_CONTINUOUS_FEATURE_NAMES)
        self.assertNotIn("has_gap_rule", CAPABILITY_CONTINUOUS_FEATURE_NAMES)
        self.assertNotIn("is_deprecated", CAPABILITY_CONTINUOUS_FEATURE_NAMES)

    def test_capability_embedding_feature_names_use_similarity_terms(self) -> None:
        self.assertEqual(
            CAPABILITY_EMBEDDING_FEATURE_NAMES,
            ("description_similarity", "max_cue_similarity", "mean_cue_similarity"),
        )

    def test_capability_rawtext_feature_names_use_whole_text_similarity_terms(self) -> None:
        self.assertEqual(
            CAPABILITY_RAWTEXT_FEATURE_NAMES,
            ("tool_similarity", "description_similarity", "argument_similarity"),
        )

    def test_capability_description_pool_feature_names_use_non_cue_clause_pooling(self) -> None:
        self.assertEqual(
            CAPABILITY_DESCRIPTION_POOL_FEATURE_NAMES,
            (
                "tool_similarity",
                "description_similarity",
                "argument_similarity",
                "max_description_clause_similarity",
                "mean_description_clause_similarity",
            ),
        )

    def test_parse_method_supports_prototype_gate_variants(self) -> None:
        self.assertEqual(_parse_method("aug_only"), ("aug_only", False))
        self.assertEqual(_parse_method("scc_lite"), ("scc_lite", False))
        self.assertEqual(_parse_method("aug_proto_gate"), ("aug_only", True))
        self.assertEqual(_parse_method("scc_proto_gate"), ("scc_lite", True))

    def test_build_slot_vocab_includes_case_slots(self) -> None:
        suite = load_seed_suite("data/family_benchmark.json")
        slot_vocab = build_slot_vocab(suite)
        first_case_slots = set(suite.cases[0].slot_values)
        self.assertTrue(first_case_slots.issubset(set(slot_vocab)))

    def test_train_embedding_policy_agent_seed_only_filters_to_clean_examples(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        suite = load_seed_suite("data/family_benchmark.json")
        train_examples = tuple(example for example in suite.examples if example.case.case_id == "fx_eur_to_gbp")
        torch = embedding_policy_module.torch
        feature_lookup = {
            example.schema_view.view_id: torch.tensor([float(index + 1)] * 6, dtype=torch.float32)
            for index, example in enumerate(train_examples)
        }
        agent, metrics = train_embedding_policy_agent(
            name="seed_only_smoke",
            suite=suite,
            train_examples=train_examples,
            feature_lookup=feature_lookup,
            config=EmbeddingPolicyConfig(epochs=1, bottleneck_dim=4, learning_rate=1e-2, weight_decay=0.0),
            method="seed_only",
            encoder=None,
        )
        self.assertEqual(agent.name, "seed_only_smoke")
        self.assertEqual(metrics["train_examples"], 1.0)

    def test_train_embedding_policy_agent_supports_teacher_distilled_bottleneck_scc(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        suite = load_seed_suite("data/family_benchmark.json")
        train_examples = tuple(example for example in suite.examples if example.case.case_id == "fx_eur_to_gbp")
        encoder = self._FakeEncoder()
        feature_lookup = {
            example.schema_view.view_id: encoder.encode_texts([encoder._with_instruction(serialize_view(example))])[0]
            for example in train_examples
        }
        agent, metrics = train_embedding_policy_agent(
            name="teacher_distilled_smoke",
            suite=suite,
            train_examples=train_examples,
            feature_lookup=feature_lookup,
            config=EmbeddingPolicyConfig(
                epochs=2,
                bottleneck_dim=8,
                learning_rate=1e-2,
                weight_decay=0.0,
                seed=0,
            ),
            method="teacher_distilled_bottleneck_scc",
            encoder=encoder,
        )
        self.assertIn("L_slot", metrics)
        self.assertIn("L_distill_ctl", metrics)
        self.assertIn("L_distill_gap", metrics)
        self.assertGreater(metrics["slot_vocab_size"], 0.0)
        prediction = agent.predict(train_examples[0])
        self.assertIn(prediction.control, tuple(ControlTag))

    def test_best_binary_threshold_separates_execute_scores(self) -> None:
        scores = [-0.7, -0.3, 0.2, 0.8]
        labels = [False, False, True, True]
        threshold = _best_binary_threshold(scores, labels)
        predictions = [score >= threshold for score in scores]
        self.assertEqual(predictions, labels)

    def test_best_binary_threshold_prefers_execute_recall_on_tie(self) -> None:
        scores = [-0.2, 0.1, 0.1, 0.5]
        labels = [False, True, True, False]
        threshold = _best_binary_threshold(scores, labels)
        predictions = [score >= threshold for score in scores]
        self.assertGreaterEqual(sum(int(pred and label) for pred, label in zip(predictions, labels, strict=True)), 2)

    def test_best_binary_threshold_respects_sample_weights(self) -> None:
        scores = [0.1, 0.2, 0.3, 0.4]
        labels = [False, False, True, False]
        unweighted = _best_binary_threshold(scores, labels)
        weighted = _best_binary_threshold(scores, labels, sample_weights=[1.0, 1.0, 1.0, 5.0])
        self.assertGreater(weighted, unweighted)

    def test_best_asymmetric_binary_threshold_enforces_execute_retention(self) -> None:
        scores = [0.1, 0.2, 0.3, 0.4]
        labels = [False, False, True, False]
        weighted = _best_binary_threshold(scores, labels, sample_weights=[1.0, 1.0, 5.0, 5.0])
        asymmetric = _best_asymmetric_binary_threshold(
            scores,
            labels,
            sample_weights=[1.0, 1.0, 5.0, 5.0],
            min_execute_retention=0.99,
        )
        self.assertGreater(asymmetric, weighted)
        predictions = [score >= asymmetric for score in scores]
        execute_keep = [
            (not prediction)
            for prediction, label in zip(predictions, labels, strict=True)
            if not label
        ]
        self.assertTrue(all(execute_keep))

    def test_cross_encoder_execute_margin_penalty_only_hits_execute_logits_above_margin(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        penalty = _cross_encoder_execute_margin_penalty(
            embedding_policy_module.torch.tensor([-0.4, 0.3, 0.9], dtype=embedding_policy_module.torch.float32),
            embedding_policy_module.torch.tensor([0.0, 0.0, 1.0], dtype=embedding_policy_module.torch.float32),
            execute_margin=0.0,
        )
        self.assertAlmostEqual(float(penalty.item()), 0.15, places=6)
        zero_penalty = _cross_encoder_execute_margin_penalty(
            embedding_policy_module.torch.tensor([-0.4, 0.3, 0.9], dtype=embedding_policy_module.torch.float32),
            embedding_policy_module.torch.tensor([0.0, 0.0, 1.0], dtype=embedding_policy_module.torch.float32),
            execute_margin=0.5,
        )
        self.assertAlmostEqual(float(zero_penalty.item()), 0.0, places=6)

    def test_best_dual_threshold_band_prefers_abstain_for_abstain_only_negative(self) -> None:
        abstain_threshold, ask_threshold = _best_dual_threshold_band(
            scores=[0.10, 0.45, 0.55, 0.95],
            should_execute=[True, True, False, False],
            allowed_nonexecute_controls=[
                frozenset(),
                frozenset(),
                frozenset({ControlTag.ABSTAIN}),
                frozenset({ControlTag.ABSTAIN, ControlTag.ASK_CLARIFICATION}),
            ],
        )
        predictions = [
            _dual_threshold_control(score, abstain_threshold=abstain_threshold, ask_threshold=ask_threshold)
            for score in [0.10, 0.45, 0.55, 0.95]
        ]
        self.assertLess(abstain_threshold, ask_threshold)
        self.assertEqual(
            predictions,
            [
                ControlTag.EXECUTE,
                ControlTag.EXECUTE,
                ControlTag.ABSTAIN,
                ControlTag.ASK_CLARIFICATION,
            ],
        )

    def test_tool_contract_compatible_detects_negative_contract_mutation(self) -> None:
        suite = load_seed_suite("data/family_benchmark.json")
        clean_example = next(item for item in suite.examples if item.schema_view.view_id == "fx_eur_to_gbp::clean")
        negative_example = next(item for item in suite.examples if item.schema_view.view_id == "fx_eur_to_gbp::negative_contract")
        clean_tool = next(tool for tool in clean_example.schema_view.tools if tool.canonical_tool_id == "finance.convert_currency")
        negative_tool = next(tool for tool in negative_example.schema_view.tools if tool.canonical_tool_id == "finance.convert_currency")
        self.assertTrue(_tool_contract_compatible(clean_tool, clean_example.case.slot_values))
        self.assertFalse(_tool_contract_compatible(negative_tool, negative_example.case.slot_values))

    def test_description_capability_gap_detects_replacement_semantics(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "notion_list_shared_databases::negative_search_replacement"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "notion.databases.list_shared")
        self.assertTrue(_tool_has_description_capability_gap(tool, example.case.request))

    def test_description_capability_gap_detects_removed_capability(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "stripe_list_customers_total_count::negative_removed_capability"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "stripe.customers.list_with_total_count")
        self.assertTrue(_tool_has_description_capability_gap(tool, example.case.request))

    def test_description_capability_gap_detects_parent_scope_change(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "notion_create_page_in_database::negative_parent_scope_change"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "notion.pages.create_in_container")
        self.assertTrue(_tool_has_description_capability_gap(tool, example.case.request))

    def test_description_capability_gap_detects_drive_shortcut_replacement(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "drive_add_file_to_second_folder::negative_shortcut_replacement"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "drive.files.add_secondary_parent")
        self.assertTrue(_tool_has_description_capability_gap(tool, example.case.request))

    def test_description_capability_gap_detects_jira_legacy_identifier_removal(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "jira_search_assignable_user_legacy_username::negative_legacy_identifier_removed"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "jira.users.search_by_legacy_username")
        self.assertTrue(_tool_has_description_capability_gap(tool, example.case.request))

    def test_description_capability_gap_detects_sheets_feed_removal(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "sheets_list_accessible_spreadsheets::negative_drive_scope_replacement"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "sheets.spreadsheets.list_accessible")
        self.assertTrue(_tool_has_description_capability_gap(tool, example.case.request))

    def test_description_capability_gap_detects_people_other_contact_read_only(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "people.other_contacts.update_email")
        self.assertTrue(_tool_has_description_capability_gap(tool, example.case.request))

    def test_description_capability_gap_detects_confluence_space_key_lookup_split(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "confluence_list_pages_by_space_key::negative_space_key_lookup_split"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "confluence.pages.list_by_space_key")
        self.assertTrue(_tool_has_description_capability_gap(tool, example.case.request))

    def test_description_capability_gap_detects_bitbucket_legacy_account_split(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "bitbucket_get_legacy_account::negative_account_object_removed"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "bitbucket.accounts.get_legacy_account")
        self.assertTrue(_tool_has_description_capability_gap(tool, example.case.request))

    def test_select_cross_encoder_clause_avoids_cue_extraction(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "people.other_contacts.update_email")
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            clause = _select_cross_encoder_clause(
                request=example.case.request,
                tool=tool,
                cross_encoder=self._FakeCrossEncoder(),
                clause_localizer=CrossEncoderClauseLocalizer(threshold=0.5),
            )
        self.assertIsNotNone(clause)
        self.assertIn("modified directly", clause.lower())

    def test_select_cross_encoder_clause_top_mode_avoids_cue_extraction(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "people.other_contacts.update_email")
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            clause = _select_cross_encoder_clause(
                request=example.case.request,
                tool=tool,
                cross_encoder=self._FakeCrossEncoder(),
                clause_localizer=CrossEncoderClauseLocalizer(threshold=1.1, selection_mode="top"),
            )
        self.assertIsNotNone(clause)
        self.assertIn("modified directly", clause.lower())

    def test_cross_encoder_should_inhibit_avoids_cue_extraction(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "people.other_contacts.update_email")
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            inhibit, confidence = _cross_encoder_should_inhibit(
                request=example.case.request,
                tool=tool,
                selected_clause="This endpoint is read-only and cannot directly update Other Contacts.",
                cross_encoder=self._FakeCrossEncoder(),
                capability_gate=CrossEncoderCapabilityGate(threshold=0.5),
            )
        self.assertTrue(inhibit)
        self.assertGreater(confidence, 0.5)

    def test_cross_encoder_feature_map_avoids_cue_extraction(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "people.other_contacts.update_email")
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            feature_map, selected_clause = _cross_encoder_feature_map(
                request=example.case.request,
                tool=tool,
                best_active_score=0.8,
                second_active_score=0.2,
                cross_encoder=self._FakeCrossEncoder(),
                clause_localizer=CrossEncoderClauseLocalizer(threshold=0.5),
                capability_instruction="test capability instruction",
                feature_names=CROSS_ENCODER_FEATURE_NAMES,
            )
        self.assertEqual(set(feature_map), set(CROSS_ENCODER_FEATURE_NAMES))
        self.assertIsNotNone(selected_clause)
        self.assertIn("modified directly", selected_clause.lower())
        self.assertGreater(feature_map["top_clause_score"], 0.5)
        self.assertGreater(feature_map["localized_capability_score"], 0.5)

    def test_cross_encoder_clause_feature_map_avoids_cue_extraction(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "people.other_contacts.update_email")
        clause = "Other contacts cannot be modified directly and are effectively read-only."
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            feature_map = _cross_encoder_clause_feature_map(
                request=example.case.request,
                tool=tool,
                clause=clause,
                cross_encoder=self._FakeCrossEncoder(),
                localizer_instruction="test localizer instruction",
                capability_instruction="test capability instruction",
                feature_names=CROSS_ENCODER_CLAUSE_FEATURE_NAMES,
            )
        self.assertEqual(set(feature_map), set(CROSS_ENCODER_CLAUSE_FEATURE_NAMES))
        self.assertGreater(feature_map["localizer_score"], 0.5)
        self.assertGreater(feature_map["clause_capability_score"], 0.5)

    def test_select_cross_encoder_clause_learned_mode_avoids_cue_extraction(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "people.other_contacts.update_email")
        ranker = LearnedCapabilityScorer(
            weights=(1.0, 0.0, 0.0),
            bias=0.0,
            threshold=0.0,
            feature_means=(0.0, 0.0, 0.0),
            feature_scales=(1.0, 1.0, 1.0),
            feature_names=CROSS_ENCODER_CLAUSE_FEATURE_NAMES,
        )
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            clause = _select_cross_encoder_clause(
                request=example.case.request,
                tool=tool,
                cross_encoder=self._FakeCrossEncoder(),
                clause_localizer=CrossEncoderClauseLocalizer(
                    threshold=0.0,
                    selection_mode="learned",
                    ranker=ranker,
                ),
            )
        self.assertIsNotNone(clause)
        self.assertIn("modified directly", clause.lower())

    def test_capability_cue_clauses_extract_negative_clauses_only(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        negative = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "notion_list_shared_databases::negative_search_replacement"
        )
        negative_tool = next(
            tool for tool in negative.schema_view.tools if tool.canonical_tool_id == "notion.databases.list_shared"
        )
        positive = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "drive_add_parent_to_file::positive_version_migration"
        )
        positive_tool = next(
            tool for tool in positive.schema_view.tools if tool.canonical_tool_id == "drive.files.add_parent"
        )
        self.assertGreaterEqual(len(_capability_cue_clauses(negative_tool)), 1)
        self.assertEqual(_capability_cue_clauses(positive_tool), ())

    def test_capability_feature_map_marks_negative_gap(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "people.other_contacts.update_email")
        feature_map = _capability_feature_map(
            tool=tool,
            request=example.case.request,
            best_active_score=0.7,
            second_active_score=0.4,
        )
        self.assertEqual(feature_map["has_gap_rule"], 1.0)
        self.assertGreaterEqual(feature_map["cue_clause_count"], 1.0)
        self.assertGreaterEqual(feature_map["description_overlap"], 2.0)

    def test_capability_feature_map_ignores_positive_migration(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "jira_assign_issue_user_ref::positive_version_migration"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "jira.issues.assign_user")
        feature_map = _capability_feature_map(
            tool=tool,
            request=example.case.request,
            best_active_score=0.7,
            second_active_score=0.4,
        )
        self.assertEqual(feature_map["has_gap_rule"], 0.0)
        self.assertEqual(feature_map["cue_clause_count"], 0.0)

    def test_capability_feature_map_rawtext_features_do_not_require_clause_extraction(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "people.other_contacts.update_email")
        torch = embedding_policy_module.torch

        def fake_lookup(text: str) -> torch.Tensor:
            scale = float((sum(ord(char) for char in text) % 7) + 1)
            return torch.tensor([scale, scale / 10.0], dtype=torch.float32)

        request_feature = torch.tensor([1.0, 0.5], dtype=torch.float32)
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            feature_map = _capability_feature_map(
                tool=tool,
                request=example.case.request,
                best_active_score=0.7,
                second_active_score=0.4,
                request_feature=request_feature,
                text_feature_lookup=fake_lookup,
                feature_names=CAPABILITY_RAWTEXT_FEATURE_NAMES,
            )
        self.assertEqual(set(feature_map), set(CAPABILITY_RAWTEXT_FEATURE_NAMES))
        self.assertEqual(feature_map["tool_similarity"], 0.7)
        self.assertGreater(feature_map["description_similarity"], 0.0)
        self.assertGreater(feature_map["argument_similarity"], 0.0)

    def test_capability_feature_map_description_pool_features_do_not_require_cue_extraction(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "confluence_list_pages_by_space_key::negative_space_key_lookup_split"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "confluence.pages.list_by_space_key")
        torch = embedding_policy_module.torch

        def fake_lookup(text: str) -> torch.Tensor:
            scale = float((sum(ord(char) for char in text) % 11) + 1)
            return torch.tensor([scale, scale / 5.0], dtype=torch.float32)

        request_feature = torch.tensor([1.0, 0.25], dtype=torch.float32)
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            feature_map = _capability_feature_map(
                tool=tool,
                request=example.case.request,
                best_active_score=0.8,
                second_active_score=0.3,
                request_feature=request_feature,
                text_feature_lookup=fake_lookup,
                feature_names=CAPABILITY_DESCRIPTION_POOL_FEATURE_NAMES,
            )
        self.assertEqual(set(feature_map), set(CAPABILITY_DESCRIPTION_POOL_FEATURE_NAMES))
        self.assertGreaterEqual(feature_map["max_description_clause_similarity"], feature_map["mean_description_clause_similarity"])

    def test_capability_dense_feature_vector_uses_description_clauses_without_cue_extraction(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "bitbucket_get_legacy_account::negative_account_object_removed"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "bitbucket.accounts.get_legacy_account")
        torch = embedding_policy_module.torch

        def fake_lookup(text: str) -> torch.Tensor:
            values = [(ord(char) % 13) / 13.0 for char in text[:4]]
            padded = values + [0.25] * (4 - len(values))
            return torch.tensor(padded, dtype=torch.float32)

        request_feature = torch.tensor([0.5, 0.25, 0.75, 0.125], dtype=torch.float32)
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            vector = _capability_dense_feature_vector(
                tool=tool,
                request=example.case.request,
                request_feature=request_feature,
                best_active_score=0.9,
                second_active_score=0.4,
                text_feature_lookup=fake_lookup,
                mode="localized_clause_interaction",
            )
        self.assertEqual(vector.shape[0], request_feature.shape[0] + 10)

    def test_capability_dense_feature_vector_learned_localizer_path_avoids_cue_extraction(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "notion_list_shared_databases::negative_search_replacement"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "notion.databases.list_shared")
        torch = embedding_policy_module.torch

        def fake_lookup(text: str) -> torch.Tensor:
            values = [(ord(char) % 17) / 17.0 for char in text[:4]]
            padded = values + [0.125] * (4 - len(values))
            return torch.tensor(padded, dtype=torch.float32)

        request_feature = torch.tensor([0.5, 0.25, 0.75, 0.125], dtype=torch.float32)
        localizer = LearnedClauseLocalizer(
            weights=(0.1,) * 9,
            bias=0.0,
            threshold=0.0,
            feature_means=(0.0,) * 9,
            feature_scales=(1.0,) * 9,
        )
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            vector = _capability_dense_feature_vector(
                tool=tool,
                request=example.case.request,
                request_feature=request_feature,
                best_active_score=0.9,
                second_active_score=0.4,
                text_feature_lookup=fake_lookup,
                mode="learned_clause_localization_interaction",
                clause_localizer=localizer,
            )
        self.assertEqual(vector.shape[0], request_feature.shape[0] + 10)

    def test_capability_dense_feature_vector_learned_localizer_scalar_mode_is_low_dim(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "confluence_list_pages_by_space_key::negative_space_key_lookup_split"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "confluence.pages.list_by_space_key")
        torch = embedding_policy_module.torch

        def fake_lookup(text: str) -> torch.Tensor:
            values = [(ord(char) % 19) / 19.0 for char in text[:4]]
            padded = values + [0.2] * (4 - len(values))
            return torch.tensor(padded, dtype=torch.float32)

        request_feature = torch.tensor([0.5, 0.25, 0.75, 0.125], dtype=torch.float32)
        localizer = LearnedClauseLocalizer(
            weights=(0.1,) * 9,
            bias=0.0,
            threshold=0.0,
            feature_means=(0.0,) * 9,
            feature_scales=(1.0,) * 9,
        )
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            vector = _capability_dense_feature_vector(
                tool=tool,
                request=example.case.request,
                request_feature=request_feature,
                best_active_score=0.9,
                second_active_score=0.4,
                text_feature_lookup=fake_lookup,
                mode="learned_clause_localization_scalar",
                clause_localizer=localizer,
            )
        self.assertEqual(vector.shape[0], 10)

    def test_capability_dense_feature_vector_pair_text_mode_avoids_cue_extraction(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "people_update_other_contact_email::negative_other_contacts_read_only"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "people.other_contacts.update_email")
        torch = embedding_policy_module.torch

        def fake_lookup(text: str) -> torch.Tensor:
            values = [(ord(char) % 23) / 23.0 for char in text[:4]]
            padded = values + [0.3] * (4 - len(values))
            return torch.tensor(padded, dtype=torch.float32)

        request_feature = torch.tensor([0.5, 0.25, 0.75, 0.125], dtype=torch.float32)
        localizer = LearnedClauseLocalizer(
            weights=(0.1,) * 9,
            bias=0.0,
            threshold=0.0,
            feature_means=(0.0,) * 9,
            feature_scales=(1.0,) * 9,
        )
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            vector = _capability_dense_feature_vector(
                tool=tool,
                request=example.case.request,
                request_feature=request_feature,
                best_active_score=0.9,
                second_active_score=0.4,
                text_feature_lookup=fake_lookup,
                mode="learned_clause_localization_pair_text",
                clause_localizer=localizer,
            )
        self.assertEqual(vector.shape[0], request_feature.shape[0] + 10)

    def test_capability_dense_feature_vector_pair_text_mlp_mode_avoids_cue_extraction(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "confluence_list_pages_by_space_key::negative_space_key_lookup_split"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "confluence.pages.list_by_space_key")
        torch = embedding_policy_module.torch

        def fake_lookup(text: str) -> torch.Tensor:
            values = [(ord(char) % 29) / 29.0 for char in text[:4]]
            padded = values + [0.35] * (4 - len(values))
            return torch.tensor(padded, dtype=torch.float32)

        request_feature = torch.tensor([0.5, 0.25, 0.75, 0.125], dtype=torch.float32)
        localizer = LearnedClauseLocalizer(
            weights=(0.1,) * 9,
            bias=0.0,
            threshold=0.0,
            feature_means=(0.0,) * 9,
            feature_scales=(1.0,) * 9,
        )
        with patch("toolshift.embedding_policy._capability_cue_clauses", side_effect=AssertionError("should not run")):
            vector = _capability_dense_feature_vector(
                tool=tool,
                request=example.case.request,
                request_feature=request_feature,
                best_active_score=0.9,
                second_active_score=0.4,
                text_feature_lookup=fake_lookup,
                mode="learned_clause_localization_pair_text_mlp",
                clause_localizer=localizer,
            )
        self.assertEqual(vector.shape[0], request_feature.shape[0] + 10)

    def test_fit_listwise_clause_ranker_prefers_positive_clause(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        ranker, stats = _fit_listwise_clause_ranker(
            feature_maps_by_example=[
                [
                    {"localizer_score": 2.0, "clause_capability_score": 1.5, "clause_minus_full": 1.0},
                    {"localizer_score": -1.0, "clause_capability_score": -0.5, "clause_minus_full": -0.75},
                    {"localizer_score": -0.5, "clause_capability_score": -0.25, "clause_minus_full": -0.5},
                ],
                [
                    {"localizer_score": 1.8, "clause_capability_score": 1.2, "clause_minus_full": 0.8},
                    {"localizer_score": -0.8, "clause_capability_score": -0.6, "clause_minus_full": -0.9},
                ],
            ],
            labels_by_example=[
                [True, False, False],
                [True, False],
            ],
            feature_names=CROSS_ENCODER_CLAUSE_FEATURE_NAMES,
        )
        positive_score = ranker.score(
            {"localizer_score": 2.1, "clause_capability_score": 1.4, "clause_minus_full": 0.9}
        )
        negative_score = ranker.score(
            {"localizer_score": -0.9, "clause_capability_score": -0.4, "clause_minus_full": -0.8}
        )
        self.assertGreater(positive_score, negative_score)
        self.assertGreater(stats.train_accuracy, 0.5)
        self.assertGreater(stats.train_positive_recall, 0.5)

    def test_configure_cross_encoder_finetuning_only_unfreezes_last_layer(self) -> None:
        if embedding_policy_module.torch is None:
            self.skipTest("torch unavailable in this environment")
        nn = embedding_policy_module.nn

        class _FakeBackbone(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.layers = nn.ModuleList([nn.Linear(2, 2), nn.Linear(2, 2), nn.Linear(2, 2)])
                self.norm = nn.LayerNorm(2)

        class _FakeModel(nn.Module):
            def __init__(self) -> None:
                super().__init__()
                self.model = _FakeBackbone()
                self.lm_head = nn.Linear(2, 2)

        model = _FakeModel()
        trainable = _configure_cross_encoder_finetuning(model, tune_last_n_layers=1)
        self.assertGreater(len(trainable), 0)
        self.assertFalse(any(parameter.requires_grad for parameter in model.model.layers[0].parameters()))
        self.assertFalse(any(parameter.requires_grad for parameter in model.model.layers[1].parameters()))
        self.assertTrue(all(parameter.requires_grad for parameter in model.model.layers[2].parameters()))
        self.assertTrue(all(parameter.requires_grad for parameter in model.model.norm.parameters()))
        self.assertTrue(all(parameter.requires_grad for parameter in model.lm_head.parameters()))

    def test_flatten_cross_encoder_binary_tasks_balances_task_weights(self) -> None:
        rows, task_counts = _flatten_cross_encoder_binary_tasks(
            [
                CrossEncoderBinaryTaskSpec(
                    name="localizer",
                    instruction="loc",
                    pairs=(("q1", "d1"), ("q2", "d2"), ("q3", "d3")),
                    labels=(True, False, True),
                ),
                CrossEncoderBinaryTaskSpec(
                    name="capability",
                    instruction="cap",
                    pairs=(("q4", "d4"),),
                    labels=(False,),
                ),
            ]
        )
        self.assertEqual(task_counts, {"localizer": 3, "capability": 1})
        localizer_weights = [weight for instruction, _pair, _label, weight in rows if instruction == "loc"]
        capability_weights = [weight for instruction, _pair, _label, weight in rows if instruction == "cap"]
        self.assertEqual(len(localizer_weights), 3)
        self.assertEqual(len(capability_weights), 1)
        self.assertGreater(capability_weights[0], localizer_weights[0])

    def test_build_class_balanced_hard_negative_weights_upweights_negative_core(self) -> None:
        weights, stats = _build_class_balanced_hard_negative_weights(
            labels=[False, False, False, True],
            hard_negative_flags=[False, False, False, True],
            class_balance_power=0.5,
            hard_negative_multiplier=1.5,
        )
        self.assertEqual(len(weights), 4)
        self.assertAlmostEqual(sum(weights) / len(weights), 1.0)
        self.assertEqual(stats["inhibit_examples"], 1.0)
        self.assertEqual(stats["execute_examples"], 3.0)
        self.assertEqual(stats["hard_negative_examples"], 1.0)
        self.assertGreater(stats["mean_inhibit_weight"], stats["mean_execute_weight"])
        self.assertGreater(stats["mean_hard_negative_weight"], stats["mean_execute_weight"])

    def test_description_capability_gap_ignores_positive_version_migration(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "stripe_create_customer_with_tax_id::positive_version_migration"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "stripe.customers.create_with_tax_id")
        self.assertFalse(_tool_has_description_capability_gap(tool, example.case.request))

    def test_tool_request_capability_overlap_counts_drive_positive_tokens(self) -> None:
        suite = load_seed_suite("data/real_evolution_benchmark.json")
        example = next(
            item
            for item in suite.examples
            if item.schema_view.view_id == "drive_add_parent_to_file::positive_version_migration"
        )
        tool = next(tool for tool in example.schema_view.tools if tool.canonical_tool_id == "drive.files.add_parent")
        self.assertGreaterEqual(_tool_request_capability_overlap(tool, example.case.request), 2)


if __name__ == "__main__":
    unittest.main()
