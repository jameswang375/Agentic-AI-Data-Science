_emit = None

def setup(emit_fn):
    global _emit
    _emit = emit_fn

def teardown():
    global _emit
    _emit = None

def emit(event: dict):
    if _emit:
        _emit(event)
