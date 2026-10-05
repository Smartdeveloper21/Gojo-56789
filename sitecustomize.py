import importlib.util
import os
import sys
from pathlib import Path


def _apply_start_panel_fix():
    py_path = Path(__file__).resolve().with_name("py.py")
    if not py_path.exists():
        return

    spec = importlib.util.spec_from_file_location("blastbot_py", py_path)
    if spec is None or spec.loader is None:
        return

    mod = importlib.util.module_from_spec(spec)
    sys.modules.setdefault("blastbot_py", mod)
    try:
        spec.loader.exec_module(mod)
    except Exception:
        return

    original_fire = getattr(mod, "send_fire_effect_private", None)
    if original_fire is not None:
        async def safe_fire(bot, chat_id):
            try:
                d = mod.load()
                allowed = {mod.MAIN_OWNER, *mod.SUPER_ADMINS, *(d.get("owners", [])), *(d.get("admins", []))}
                if chat_id in allowed:
                    return
            except Exception:
                pass
            return await original_fire(bot, chat_id)
        mod.send_fire_effect_private = safe_fire

    def owner_panel_compat(d_or_uid, d=None):
        if d is None:
            return mod.owner_panel_text(d_or_uid)
        return mod.owner_panel_text(d)
    mod.owner_panel_text = owner_panel_compat

    def admin_panel_compat(d_or_uid, d=None):
        if d is None:
            return mod.admin_panel_text(d_or_uid)
        return mod.admin_panel_text(d)
    mod.admin_panel_text = admin_panel_compat

_apply_start_panel_fix()
