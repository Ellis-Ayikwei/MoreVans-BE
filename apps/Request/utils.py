from decimal import Decimal
from typing import Dict, Any

def determine_vehicle_type(total_weight: float, total_dimensions: Dict[str, float]) -> str:
    """
    Determine the appropriate vehicle type based on cargo requirements.
    Returns one of: 'small_van', 'medium_van', 'large_van', 'car_transporter', 'box_truck'
    
    UK Vehicle Categories:
    - Small Van (e.g., Ford Transit Connect): Up to 1.2 tonnes, ~2.5m³
    - Medium Van (e.g., Ford Transit Custom): Up to 2.0 tonnes, ~5m³
    - Large Van (e.g., Mercedes Sprinter): Up to 3.5 tonnes, ~8m³
    - Car Transporter: For vehicle transportation
    - Box Truck: For larger loads
    """
    volume = total_dimensions.get('volume', 0)
    weight = total_weight
    length = total_dimensions.get('length', 0)
    width = total_dimensions.get('width', 0)
    height = total_dimensions.get('height', 0)

    # Define thresholds based on UK vehicle specifications
    VOLUME_THRESHOLDS = {
        'small_van': 2.5,     # ~2.5 cubic meters (e.g., Transit Connect)
        'medium_van': 5.0,    # ~5 cubic meters (e.g., Transit Custom)
        'large_van': 8.0,     # ~8 cubic meters (e.g., Sprinter)
        'box_truck': 12.0     # ~12 cubic meters
    }

    WEIGHT_THRESHOLDS = {
        'small_van': 1200,    # 1.2 tonnes
        'medium_van': 2000,   # 2.0 tonnes
        'large_van': 3500,    # 3.5 tonnes
        'box_truck': 7500     # 7.5 tonnes
    }

    # Check if this is a car transportation request
    # Typical car dimensions: ~4.5m x 1.8m x 1.5m
    is_car_transport = (
        length >= 4.0 and  # Car length threshold
        width >= 1.6 and   # Car width threshold
        height >= 1.4      # Car height threshold
    )

    if is_car_transport:
        return 'car_transporter'
    elif volume > VOLUME_THRESHOLDS['box_truck'] or weight > WEIGHT_THRESHOLDS['box_truck']:
        return 'box_truck'
    elif volume > VOLUME_THRESHOLDS['large_van'] or weight > WEIGHT_THRESHOLDS['large_van']:
        return 'large_van'
    elif volume > VOLUME_THRESHOLDS['medium_van'] or weight > WEIGHT_THRESHOLDS['medium_van']:
        return 'medium_van'
    elif volume > VOLUME_THRESHOLDS['small_van'] or weight > WEIGHT_THRESHOLDS['small_van']:
        return 'small_van'
    else:
        return 'small_van'  # Default to small van for smaller loads

def calculate_request_totals(request) -> Dict[str, Any]:
    """
    Calculate total weight and dimensions from a request's items.
    Returns a dictionary with total_weight and total_dimensions.
    """
    total_weight = Decimal('0')
    total_dimensions = {
        'length': Decimal('0'),
        'width': Decimal('0'),
        'height': Decimal('0'),
        'volume': Decimal('0')
    }
    
    # Calculate totals from items
    for item in request.items.all():
        # Add weight
        if item.weight:
            total_weight += Decimal(str(item.weight))
            
        # Add dimensions
        if item.dimensions:
            try:
                # Parse dimensions string (format: "L × W × H cm")
                dims = item.dimensions.split('×')
                if len(dims) == 3:
                    length = Decimal(dims[0].strip().replace('cm', '').strip())
                    width = Decimal(dims[1].strip().replace('cm', '').strip())
                    height = Decimal(dims[2].strip().replace('cm', '').strip())
                    
                    total_dimensions['length'] = max(total_dimensions['length'], length)
                    total_dimensions['width'] = max(total_dimensions['width'], width)
                    total_dimensions['height'] += height
                    
                    # Calculate volume for this item
                    item_volume = length * width * height
                    total_dimensions['volume'] += item_volume
            except (ValueError, TypeError, AttributeError):
                # Skip invalid dimension formats
                continue
    
    return {
        'total_weight': float(total_weight),
        'total_dimensions': {
            'length': float(total_dimensions['length']),
            'width': float(total_dimensions['width']),
            'height': float(total_dimensions['height']),
            'volume': float(total_dimensions['volume'])
        }
    }

def get_request_forecast_data(request) -> Dict[str, Any]:
    """
    Get all necessary data from a request for price forecasting.
    This includes calculated totals and request-specific data.
    Properties like number_of_rooms, floor_number, and loading times are determined
    from the stops and their associated items.
    """
    # Calculate totals
    totals = calculate_request_totals(request)
    
    # Determine vehicle type based on cargo requirements
    vehicle_type = determine_vehicle_type(totals['total_weight'], totals['total_dimensions'])
    
    # Initialize forecast data with basic request information
    forecast_data = {
        'distance': float(request.estimated_distance or 0),
        'weight': totals['total_weight'],
        'service_level': request.service_level or 'standard',
        'vehicle_type': vehicle_type,
        'request_id': str(request.id),
        'request_type': request.request_type,
        'total_dimensions': totals['total_dimensions'],
        # Initialize with default values
        'number_of_rooms': 1,
        'floor_number': 0,
        'has_elevator': False,
        'loading_time': 0,
        'unloading_time': 0
    }
    
    # Process pickup location (first stop)
    if request.pickup_location:
        forecast_data['pickup_city'] = request.pickup_location.city
        forecast_data['property_type'] = request.pickup_location.property_type or 'house'
        
        # Get pickup location specific data
        if hasattr(request.pickup_location, 'number_of_rooms'):
            forecast_data['number_of_rooms'] = request.pickup_location.number_of_rooms
        if hasattr(request.pickup_location, 'floor'):
            forecast_data['floor_number'] = request.pickup_location.floor
        if hasattr(request.pickup_location, 'has_elevator'):
            forecast_data['has_elevator'] = request.pickup_location.has_elevator
            
        # Calculate loading time based on items at pickup
        pickup_items = request.items.filter(location=request.pickup_location)
        if pickup_items.exists():
            # Base loading time of 15 minutes per item
            forecast_data['loading_time'] = len(pickup_items) * 15
    
    # Process dropoff location (second stop)
    if request.dropoff_location:
        forecast_data['dropoff_city'] = request.dropoff_location.city
        
        # Calculate unloading time based on items at dropoff
        dropoff_items = request.items.filter(location=request.dropoff_location)
        if dropoff_items.exists():
            # Base unloading time of 15 minutes per item
            forecast_data['unloading_time'] = len(dropoff_items) * 15
            
        # If dropoff is on a higher floor, update floor_number
        if hasattr(request.dropoff_location, 'floor'):
            forecast_data['floor_number'] = max(
                forecast_data['floor_number'],
                request.dropoff_location.floor or 0
            )
            
        # If dropoff has elevator, update has_elevator
        if hasattr(request.dropoff_location, 'has_elevator'):
            forecast_data['has_elevator'] = forecast_data['has_elevator'] or request.dropoff_location.has_elevator
    
    return forecast_data 