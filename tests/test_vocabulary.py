import pytest

import build
import vocabulary
from helpers import vocab
from vocabulary import VocabularyError


def test_names_come_from_tech_stack(cv, tmp_path):
    assert vocab(cv, tmp_path).names == [
        "Python", "SQL", "Databricks + MLflow", "Delta Lake", "Go", "Kubernetes", "DynamoDB"]


def test_alias_file_wins_over_model_canonical(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"K8s": "Kubernetes"})
    assert v.canonical("k8s", "Docker") == "Kubernetes"


def test_alias_also_applies_to_the_model_canonical(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"K8s": "Kubernetes"})
    assert v.canonical("Kubernetes en producción", "K8s") == "Kubernetes"


def test_canonical_uses_vocabulary_casing(cv, tmp_path):
    assert vocab(cv, tmp_path).canonical("PYTHON") == "Python"


def test_unknown_term_keeps_model_canonical(cv, tmp_path):
    assert vocab(cv, tmp_path).canonical("DBT Core", "dbt") == "dbt"


def test_three_states(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"MLflow": "Databricks + MLflow"})
    assert v.state("Python") == "covered"
    assert v.state(v.canonical("MLflow")) == "covered"
    assert v.state("Pandas") == "mentioned"      # solo en una viñeta
    assert v.state("Snowflake") == "gap"
    assert v.state("R") == "gap"                 # "DeepSeek R-1" no cuenta


def test_alias_form_counts_as_mention(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"Gin": "Gin Web Framework"})
    assert v.state("Gin Web Framework") == "mentioned"   # el CV dice "Gin", no el canónico


def test_general_term_inherits_best_state(cv, tmp_path):
    v = vocab(cv, tmp_path, general_terms={"Lakehouse": ["Delta Lake"], "Dataframes": ["Pandas"]})
    assert v.state("Lakehouse") == "covered" and v.backing("Lakehouse") == ["Delta Lake"]
    assert v.state("Dataframes") == "mentioned"
    assert v.canonical("lakehouse") == "Lakehouse" and v.backing("Python") == []


def test_general_term_backed_by_gap_fails(cv, tmp_path):
    with pytest.raises(VocabularyError, match="Snowflake"):
        vocab(cv, tmp_path, general_terms={"Data Warehouse": ["Snowflake"]})


def test_forms(cv, tmp_path):
    v = vocab(cv, tmp_path, aliases={"K8s": "Kubernetes", "kube": "Kubernetes"})
    assert v.forms("Kubernetes") == ["Kubernetes", "K8s", "kube"]


def test_missing_file_means_no_aliases(cv, tmp_path):
    assert vocabulary.load(cv, tmp_path / "no.json").state("Python") == "covered"


def test_real_files_load():
    vocabulary.load(build.load_json(build.DATA_FILE))
