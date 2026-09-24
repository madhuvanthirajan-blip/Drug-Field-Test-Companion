def normalize_location(latitude, longitude):
    try:
        return float(latitude), float(longitude)
    except (TypeError, ValueError):
        return None, None
