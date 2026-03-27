import pytest
from wish_engine.module_scorer import score_router, score_searcher, score_ranker, score_presenter, score_e2e, score_all


class TestModuleScorer:
    def test_router_score_reasonable(self):
        ms = score_router()
        assert ms.score >= 0.7

    def test_searcher_score_reasonable(self):
        ms = score_searcher()
        assert ms.score >= 0.6

    def test_ranker_score_reasonable(self):
        ms = score_ranker()
        assert ms.score >= 0.6

    def test_presenter_score_reasonable(self):
        ms = score_presenter()
        assert ms.score >= 0.5

    def test_e2e_score_reasonable(self):
        ms = score_e2e()
        assert ms.score >= 0.8

    def test_score_all_returns_all_modules(self):
        scores = score_all()
        assert "router" in scores
        assert "searcher" in scores
        assert "ranker" in scores
        assert "presenter" in scores
        assert "e2e" in scores
