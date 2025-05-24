from decimal import Decimal


def calculate_request_weight(request):
    """
    Calculate the total weight of all items in a request.

    Args:
        request: The request object containing items

    Returns:
        Decimal: The total weight in kilograms
    """
    # Handle case where request is None
    if not request:
        return Decimal("0.0")

    # Check if request has items
    if not hasattr(request, "items") or not request.items.exists():
        return Decimal("0.0")

    # Calculate total weight from all items
    total_weight = Decimal("0.0")

    for item in request.items.all():
        # Skip items without weight or with invalid weight
        if not hasattr(item, "weight") or item.weight is None:
            continue

        try:
            # Convert to Decimal for precise calculation
            item_weight = Decimal(str(item.weight))

            # Multiply by quantity if available
            quantity = Decimal("1.0")
            if hasattr(item, "quantity") and item.quantity:
                quantity = Decimal(str(item.quantity))

            # Add to total weight
            total_weight += item_weight * quantity

        except (ValueError, TypeError):
            # Skip items with invalid weight values
            continue

    return total_weight


def estimate_weight_from_dimensions(length, width, height, density=Decimal("0.1")):
    """
    Estimate weight based on item dimensions when actual weight is not provided.

    Args:
        length: Length in centimeters
        width: Width in centimeters
        height: Height in centimeters
        density: Density in kg/cm³ (default is 0.1 for typical furniture)

    Returns:
        Decimal: Estimated weight in kilograms
    """
    try:
        # Convert all inputs to Decimal for precise calculation
        length = Decimal(str(length))
        width = Decimal(str(width))
        height = Decimal(str(height))
        density = Decimal(str(density))

        # Calculate volume (cm³)
        volume = length * width * height

        # Calculate weight using density (kg)
        weight = volume * density

        return weight
    except (ValueError, TypeError):
        return Decimal("0.0")
