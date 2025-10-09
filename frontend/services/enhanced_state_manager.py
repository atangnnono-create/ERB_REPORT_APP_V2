import streamlit as st
import json
import pickle
import zlib
from typing import Any, Dict, List, Callable
from datetime import datetime, timedelta


class EnhancedStateManager:
    def __init__(self):
        self._state = {}
        self._listeners = {}
        self._persisted_keys = set()

    def set_state(self, key: str, value: Any, persist: bool = False):
        """Set state with optional persistence"""
        self._state[key] = value

        if persist:
            self._persisted_keys.add(key)
            self._persist_state(key, value)

        self._notify_listeners(key, value)

    def get_state(self, key: str, default: Any = None) -> Any:
        """Get state, trying persisted storage first"""
        # Check memory first
        if key in self._state:
            return self._state[key]

        # Check persisted storage
        persisted_value = self._get_persisted_state(key)
        if persisted_value is not None:
            self._state[key] = persisted_value
            return persisted_value

        return default

    def subscribe(self, key: str, callback: Callable):
        """Subscribe to state changes"""
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)

    def persist_key(self, key: str):
        """Mark a key for persistence"""
        self._persisted_keys.add(key)
        # Immediately persist current value if it exists
        if key in self._state:
            self._persist_state(key, self._state[key])

    def _persist_state(self, key: str, value: Any):
        """Persist state to session state with compression"""
        try:
            # Compress large data
            serialized = pickle.dumps(value)
            if len(serialized) > 1000:  # Compress if larger than 1KB
                serialized = zlib.compress(serialized)

            st.session_state[f"persisted_{key}"] = {
                'data': serialized,
                'timestamp': datetime.now().isoformat(),
                'compressed': len(serialized) > 1000
            }
        except Exception as e:
            print(f"Failed to persist state {key}: {e}")

    def _get_persisted_state(self, key: str) -> Any:
        """Retrieve persisted state from session state"""
        try:
            persisted_data = st.session_state.get(f"persisted_{key}")
            if not persisted_data:
                return None

            data = persisted_data['data']
            if persisted_data.get('compressed', False):
                data = zlib.decompress(data)

            return pickle.loads(data)
        except Exception as e:
            print(f"Failed to retrieve persisted state {key}: {e}")
            return None

    def _notify_listeners(self, key: str, value: Any):
        """Notify all listeners of state change"""
        for callback in self._listeners.get(key, []):
            try:
                callback(value)
            except Exception as e:
                print(f"Error in state listener for {key}: {e}")

    def clear_persisted(self, key: str = None):
        """Clear persisted state"""
        if key:
            if key in self._persisted_keys:
                self._persisted_keys.remove(key)
            st.session_state.pop(f"persisted_{key}", None)
        else:
            for key in list(self._persisted_keys):
                st.session_state.pop(f"persisted_{key}", None)
            self._persisted_keys.clear()

    def get_all_persisted_keys(self) -> List[str]:
        """Get list of all persisted keys"""
        return list(self._persisted_keys)

    def export_state(self) -> Dict[str, Any]:
        """Export current state for backup"""
        return {
            'state': self._state.copy(),
            'persisted_keys': list(self._persisted_keys),
            'timestamp': datetime.now().isoformat()
        }

    def import_state(self, state_data: Dict[str, Any]):
        """Import state from backup"""
        if 'state' in state_data:
            self._state.update(state_data['state'])
        if 'persisted_keys' in state_data:
            self._persisted_keys.update(state_data['persisted_keys'])


# Global state manager instance
state_manager = EnhancedStateManager()