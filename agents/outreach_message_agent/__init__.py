import os
if os.environ.get("CREO_SKIP_AGENT_AUTOLOAD") != "1":
    from . import agent  # noqa: F401
