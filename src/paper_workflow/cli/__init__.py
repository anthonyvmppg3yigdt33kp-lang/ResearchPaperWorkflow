"""CLI surface for the Research Paper Workflow Framework."""


def main(*args, **kwargs):
    from paper_workflow.cli.main import main as _main

    return _main(*args, **kwargs)

__all__ = ["main"]
