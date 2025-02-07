"""Tests for the sklearn decision trees."""
import numpy
import pytest
from sklearn.datasets import load_breast_cancer

from concrete.ml.sklearn import DecisionTreeClassifier, RandomForestClassifier, XGBClassifier


# Get the datasets. The data generation is seeded in load_data.
@pytest.mark.parametrize(
    "parameters",
    [
        pytest.param(
            {"dataset": lambda: load_breast_cancer(return_X_y=True)},
            id="breast_cancer",
        ),
        pytest.param(
            {
                "dataset": "classification",
                "n_samples": 100,
                "n_features": 10,
                "n_classes": 2,
            },
            id="make_classification",
        ),
        pytest.param(
            {
                "dataset": "classification",
                "n_samples": 100,
                "n_features": 10,
                "n_classes": 4,
                "n_informative": 10,
                "n_redundant": 0,
            },
            id="make_classification_multiclass",
        ),
    ],
)
@pytest.mark.parametrize("use_virtual_lib", [True, False])
def test_decision_tree_classifier(
    parameters,
    load_data,
    default_configuration,
    check_is_good_execution_for_quantized_models,
    use_virtual_lib,
    is_vl_only_option,
):
    """Tests the sklearn DecisionTreeClassifier."""
    if not use_virtual_lib and is_vl_only_option:
        print("Warning, skipping non VL tests")
        return

    # Get the dataset
    x, y = load_data(**parameters)

    model = DecisionTreeClassifier(
        n_bits=6, max_depth=7, random_state=numpy.random.randint(0, 2**15)
    )
    model.fit(x, y)

    # Test compilation
    model.compile(x, default_configuration, use_virtual_lib=use_virtual_lib)

    # Compare FHE vs non-FHE
    check_is_good_execution_for_quantized_models(x=x[:5], model_predict=model.predict)


PARAMS_TREE = {
    "max_depth": [3, 4, 5, 10],
    "min_samples_split": [2, 3, 4, 5],
    "min_samples_leaf": [1, 2, 3, 4],
    "min_weight_fraction_leaf": [0.0, 0.1, 0.2, 0.3],
    "max_features": ["sqrt", "log2"],
    "max_leaf_nodes": [None, 5, 10, 20],
}


@pytest.mark.parametrize(
    "hyperparameters",
    [
        pytest.param({key: value}, id=f"{key}={value}")
        for key, values in PARAMS_TREE.items()
        for value in values  # type: ignore
    ],
)
@pytest.mark.parametrize("n_classes,", [2, 4])
@pytest.mark.parametrize("offset", [0, 1, 2])
def test_decision_tree_hyperparameters(hyperparameters, n_classes, offset, load_data):
    """Test that the hyperparameters are valid."""

    # Get the datasets. The data generation is seeded in load_data.
    x, y = load_data(
        dataset="classification",
        n_samples=1000,
        n_features=10,
        n_informative=10,
        n_redundant=0,
        n_classes=n_classes,
    )
    y += offset
    model = DecisionTreeClassifier(
        **hyperparameters, n_bits=26, random_state=numpy.random.randint(0, 2**15)
    )
    model, sklearn_model = model.fit_benchmark(x, y)

    # Check accuracy between the two models predictions
    assert abs(sklearn_model.score(x, y) - model.score(x, y)) < 0.05


@pytest.mark.parametrize("model", [XGBClassifier, RandomForestClassifier, DecisionTreeClassifier])
def test_one_class_edge_case(model):
    """Test the assertion for one class in y."""

    model = model()
    x = numpy.random.randint(0, 64, size=(100, 10))
    y = numpy.random.randint(0, 1, size=(100))

    assert len(numpy.unique(y)) == 1, "Wrong numpy randint generation for y."

    with pytest.raises(AssertionError, match="You must provide at least 2 classes in y."):
        model.fit(x, y)
