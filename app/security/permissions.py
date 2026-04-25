def has_scope(scopes: set, action: str, registry: str) -> bool:
    """Return True if the required `<action>:<registry>` scope is present.
    Example: action='read', registry='syphilis' => 'read:syphilis'
    """
    required = f"{action}:{registry}"
    return required in scopes
