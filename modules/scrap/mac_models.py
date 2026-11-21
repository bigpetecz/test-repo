_CANONICAL_MAC_TYPES = {
    "macbook air": "MacBook Air",
    "macbook pro": "MacBook Pro",
    "mac mini": "Mac mini",
}


def normalize_mac_type(model: str) -> str:
    key = model.strip().lower()
    if key not in _CANONICAL_MAC_TYPES:
        raise ValueError(f"Unsupported Mac model: {model!r}")
    return _CANONICAL_MAC_TYPES[key]
