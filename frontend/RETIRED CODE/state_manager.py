class StateManager:
    def __init__(self):
        self._state = {}
        self._listeners = {}

    def set_state(self, key, value):
        self._state[key] = value
        self._notify_listeners(key, value)

    def get_state(self, key, default=None):
        return self._state.get(key, default)

    def subscribe(self, key, callback):
        if key not in self._listeners:
            self._listeners[key] = []
        self._listeners[key].append(callback)

    def _notify_listeners(self, key, value):
        for callback in self._listeners.get(key, []):
            callback(value)


state_manager = StateManager()