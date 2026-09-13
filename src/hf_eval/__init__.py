"""Independent HF interfaces, linear diagnostics and versioned TMC code benchmark."""
__version__ = "0.2.0"

def evaluate(geometry_file, task_config, solver_config, output_directory=None):
    """Evaluate one immutable geometry under an explicit diagnostic task."""
    from .evaluation import evaluate as run
    return run(geometry_file, task_config, solver_config, output_directory)
