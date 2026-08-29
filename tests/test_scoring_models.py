from workers.scoring_models import ExperimentalRiskModel, WeightedRiskModel


def test_scoring_model_names():
    assert WeightedRiskModel().name == "weighted_model"
    assert ExperimentalRiskModel().name == "experimental_model"
