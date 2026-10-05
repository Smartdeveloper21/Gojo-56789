import importlib.util
import asyncio
import logging
import sys
from pathlib import Path

logger = logging.getLogger("sitecustomize")


def _load_bot_module():
    py_path = Path(__file__).resolve().with_name("py.py")
    if not py_path.exists():
        return None

    try:
        spec = importlib.util.spec_from_file_location("blastbot_py", py_path)
        if spec is None or spec.loader is None:
            return None
        mod = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("blastbot_py", mod)
        spec.loader.exec_module(mod)
        return mod
    except Exception as e:
        logger.warning("Failed to load py.py: %s", e)
        return None


def _resolve_panel_data(mod, d_or_uid=None, d=None):
    if isinstance(d_or_uid, dict):
        return d_or_uid
    if isinstance(d, dict):
        return d
    try:
        return mod.load()
    except Exception:
        return {}


def _patch_panel_functions(mod):
    for name in ("owner_panel_text", "admin_panel_text"):
        original = getattr(mod, name, None)
        if original is None:
            continue

        def make_compat(original_func):
            def wrapper(*args, **kwargs):
                try:
                    if len(args) >= 2:
                        return original_func(*args, **kwargs)
                    if len(args) == 1:
                        value = args[0]
                        if isinstance(value, dict):
                            return original_func(value)
                        data = _resolve_panel_data(mod, value, None)
                        return original_func(data)
                    if kwargs:
                        return original_func(**kwargs)
                    data = _resolve_panel_data(mod, None, None)
                    return original_func(data)
                except TypeError:
                    try:
                        return original_func(*args, **kwargs)
                    except Exception:
                        pass
                except Exception:
                    pass
                return ""

            return wrapper

        setattr(mod, name, make_compat(original))


def _patch_fire_effect(mod):
    original = getattr(mod, "send_fire_effect_private", None)
    if original is None:
        return

    async def safe_fire(bot, chat_id):
        try:
            d = mod.load()
            allowed = set(getattr(mod, "MAIN_OWNER", 0))
            allowed.update(getattr(mod, "SUPER_ADMINS", []))
            allowed.update(d.get("owners", []))
            allowed.update(d.get("admins", []))
            if int(chat_id) in allowed:
                return None
        except Exception:
            pass
        return None

    mod.send_fire_effect_private = safe_fire


def _apply_start_panel_fix():
    mod = _load_bot_module()
    if mod is None:
        return
    _patch_fire_effect(mod)
    _patch_panel_functions(mod)


_apply_start_panel_fix()
