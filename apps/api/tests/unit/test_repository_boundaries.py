"""Static guards for scoped HTTP/service repository boundaries."""

import ast
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[2] / "app"
REPOSITORY_PATH = APP_ROOT / "db" / "repositories" / "knowledge.py"
AUTHENTICATION_PATH = APP_ROOT / "security" / "authentication.py"

_KNOWLEDGE_REPOSITORIES = {
    "KnowledgeBaseRepository",
    "KnowledgeBaseMembershipRepository",
    "DocumentRepository",
    "DocumentChunkRepository",
    "IngestionJobRepository",
}
_AUTHENTICATION_REPOSITORIES = {"UserRepository", "UserSessionRepository"}


def _method_names(class_names: set[str], *, containing: str) -> set[str]:
    tree = ast.parse(REPOSITORY_PATH.read_text())
    return {
        item.name
        for node in tree.body
        if isinstance(node, ast.ClassDef) and node.name in class_names
        for item in node.body
        if isinstance(item, ast.AsyncFunctionDef) and containing in item.name
    }


def _called_attributes(path: Path) -> set[str]:
    tree = ast.parse(path.read_text())
    return {
        node.func.attr
        for node in ast.walk(tree)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
    }


def test_user_facing_knowledge_code_cannot_call_unrestricted_repository_methods() -> None:
    unrestricted = _method_names(_KNOWLEDGE_REPOSITORIES, containing="_internal")
    user_facing_paths = {
        APP_ROOT / "api" / "v1" / "endpoints" / "knowledge.py",
        APP_ROOT / "services" / "knowledge_intake.py",
    }

    violations = {
        f"{path.relative_to(APP_ROOT)}:{method}"
        for path in user_facing_paths
        for method in (_called_attributes(path) & unrestricted)
    }

    assert unrestricted
    assert violations == set()


def test_authentication_repository_methods_are_called_only_by_authentication_service() -> None:
    authentication_methods = _method_names(
        _AUTHENTICATION_REPOSITORIES,
        containing="_for_authentication",
    )
    production_paths = {
        path
        for path in APP_ROOT.rglob("*.py")
        if path not in {REPOSITORY_PATH, AUTHENTICATION_PATH}
    }

    violations = {
        f"{path.relative_to(APP_ROOT)}:{method}"
        for path in production_paths
        for method in (_called_attributes(path) & authentication_methods)
    }

    assert authentication_methods
    assert violations == set()
