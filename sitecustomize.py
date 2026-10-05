import importlib.util
import os
import sys
import asyncio
import functools
import logging
from pathlib import Path

# Setup logging for debugging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


def _apply_start_panel_fix():
    """Apply compatibility fixes to blastbot_py module."""
    py_path = Path(__file__).resolve().with_name("py.py")
    if not py_path.exists():
        logger.warning(f"py.py not found at {py_path}")
        return

    try:
        spec = importlib.util.spec_from_file_location("blastbot_py", py_path)
        if spec is None or spec.loader is None:
            logger.error("Failed to create spec for blastbot_py")
            return

        mod = importlib.util.module_from_spec(spec)
        sys.modules.setdefault("blastbot_py", mod)
        spec.loader.exec_module(mod)
        logger.info("Successfully loaded blastbot_py module")

    except Exception as e:
        logger.error(f"Error loading blastbot_py: {e}", exc_info=True)
        return

    # Patch send_fire_effect_private
    _patch_fire_effect(mod)

    # Patch panel text functions
    _patch_panel_functions(mod)

    logger.info("All patches applied successfully")


def _patch_fire_effect(mod):
    """Safely patch the send_fire_effect_private function."""
    original_fire = getattr(mod, "send_fire_effect_private", None)
    if original_fire is None:
        logger.warning("send_fire_effect_private not found in module")
        return

    # Check if original function is async
    is_async = asyncio.iscoroutinefunction(original_fire)

    def safe_fire_sync(bot, chat_id):
        """Synchronous wrapper for fire effect."""
        try:
            d = mod.load()
            allowed = {mod.MAIN_OWNER, *mod.SUPER_ADMINS, *(d.get("owners", [])), *(d.get("admins", []))}
            if chat_id in allowed:
                return None
        except Exception as e:
            logger.error(f"Error in safe_fire_sync: {e}")
            pass
        return original_fire(bot, chat_id)

    async def safe_fire_async(bot, chat_id):
        """Asynchronous wrapper for fire effect."""
        try:
            d = mod.load()
            allowed = {mod.MAIN_OWNER, *mod.SUPER_ADMINS, *(d.get("owners", [])), *(d.get("admins", []))}
            if chat_id in allowed:
                return None
        except Exception as e:
            logger.error(f"Error in safe_fire_async: {e}")
            pass

        if is_async:
            return await original_fire(bot, chat_id)
        else:
            return original_fire(bot, chat_id)

    # Apply the appropriate wrapper
    try:
        if is_async:
            mod.send_fire_effect_private = safe_fire_async
        else:
            mod.send_fire_effect_private = safe_fire_sync
        logger.info(f"Patched send_fire_effect_private ({'async' if is_async else 'sync'})")
    except Exception as e:
        logger.error(f"Error patching send_fire_effect_private: {e}", exc_info=True)


def _patch_panel_functions(mod):
    """Safely patch panel text functions with proper backwards compatibility."""
    
    # Patch owner_panel_text
    _patch_single_function(mod, "owner_panel_text", "owner_panel_compat")
    
    # Patch admin_panel_text
    _patch_single_function(mod, "admin_panel_text", "admin_panel_compat")


def _patch_single_function(mod, original_name, compat_name):
    """Patch a single panel function with proper signature handling."""
    original_func = getattr(mod, original_name, None)
    if original_func is None:
        logger.warning(f"{original_name} not found in module")
        return

    is_async = asyncio.iscoroutinefunction(original_func)

    def compat_wrapper_sync(*args, **kwargs):
        """Handle both old (uid) and new (dict) signatures for sync functions."""
        try:
            # Try calling with first positional argument (should work for both cases)
            if len(args) == 1:
                return original_func(args[0])
            elif len(args) >= 2:
                # If multiple args, pass the dict (second arg)
                return original_func(args[1])
            elif kwargs:
                # Handle kwargs-only calls
                return original_func(**kwargs)
            else:
                return original_func()
        except TypeError as e:
            logger.error(f"Error calling {original_name}: {e}")
            # Fallback: try passing first arg only
            try:
                return original_func(args[0] if args else None)
            except Exception as e2:
                logger.error(f"Fallback also failed for {original_name}: {e2}")
                raise

    async def compat_wrapper_async(*args, **kwargs):
        """Handle both old (uid) and new (dict) signatures for async functions."""
        try:
            # Try calling with first positional argument
            if len(args) == 1:
                result = original_func(args[0])
            elif len(args) >= 2:
                # If multiple args, pass the dict (second arg)
                result = original_func(args[1])
            elif kwargs:
                result = original_func(**kwargs)
            else:
                result = original_func()
            
            if asyncio.iscoroutine(result):
                return await result
            return result
        except TypeError as e:
            logger.error(f"Error calling {original_name}: {e}")
            # Fallback: try passing first arg only
            try:
                result = original_func(args[0] if args else None)
                if asyncio.iscoroutine(result):
                    return await result
                return result
            except Exception as e2:
                logger.error(f"Fallback also failed for {original_name}: {e2}")
                raise

    try:
        if is_async:
            setattr(mod, original_name, compat_wrapper_async)
        else:
            setattr(mod, original_name, compat_wrapper_sync)
        logger.info(f"Patched {original_name} ({'async' if is_async else 'sync'})")
    except Exception as e:
        logger.error(f"Error patching {original_name}: {e}", exc_info=True)


# Apply fixes on import
_apply_start_panel_fix()
