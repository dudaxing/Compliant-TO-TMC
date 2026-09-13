"""Independent HF interfaces. Version 0.1 supplies linear diagnostics only."""
__version__ = "0.1.0"

def evaluate(geometry_file, task_config, solver_config, output_directory=None):
    """Evaluate one immutable geometry under an explicit diagnostic task."""
    from .evaluation import evaluate as run
    return run(geometry_file, task_config, solver_config, output_directory)
