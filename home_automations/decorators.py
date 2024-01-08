def event(event_type):
    def decorator(method):
        method._event_type = event_type
        return method

    return decorator
