// User types
export interface User {
  id: number;
  email: string;
  username: string;
  firstName: string;
  lastName: string;
  role: 'admin' | 'operator' | 'driver' | 'citizen';
  phoneNumber?: string;
  profilePicture?: string;
  address?: string;
  city: string;
  emailNotifications: boolean;
  smsNotifications: boolean;
  pushNotifications: boolean;
  createdAt: string;
  updatedAt: string;
}

// Authentication types
export interface LoginCredentials {
  email: string;
  password: string;
}

export interface AuthTokens {
  access: string;
  refresh: string;
}

export interface AuthState {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Geographic types
export interface Coordinates {
  lat: number;
  lng: number;
}

export interface Zone {
  id: number;
  name: string;
  code: string;
  boundary: any; // GeoJSON polygon
  description: string;
  population: number;
  areaSqKm: number;
  binCount: number;
  activeBinCount: number;
  createdAt: string;
  updatedAt: string;
}

// Waste bin types
export interface WasteBin {
  id: number;
  binId: string;
  location: Coordinates;
  address: string;
  zone: number;
  zoneName?: string;
  binType: 'general' | 'recyclable' | 'organic' | 'hazardous';
  capacity: number;
  status: 'active' | 'maintenance' | 'damaged' | 'inactive';
  isActive: boolean;
  currentFillLevel: number;
  lastEmptied?: string;
  lastSensorReading?: string;
  sensorId?: string;
  firmwareVersion?: string;
  batteryLevel: number;
  installationDate: string;
  installedBy: string;
  image?: string;
  qrCode?: string;
  notes: string;
  createdAt: string;
  updatedAt: string;
}

// Sensor reading types
export interface SensorReading {
  id: number;
  bin: number;
  fillLevel: number;
  temperature?: number;
  humidity?: number;
  batteryLevel: number;
  signalStrength?: number;
  weight?: number;
  methaneLevel?: number;
  timestamp: string;
  receivedAt: string;
  isValid: boolean;
  errorMessage?: string;
}

// Alert types
export interface Alert {
  id: number;
  alertType: 'bin_full' | 'bin_overflow' | 'maintenance' | 'sensor_offline' | 
             'route_delayed' | 'vehicle_breakdown' | 'illegal_dumping' | 
             'citizen_report' | 'system_error';
  severity: 'low' | 'medium' | 'high' | 'critical';
  status: 'new' | 'acknowledged' | 'in_progress' | 'resolved' | 'closed';
  title: string;
  message: string;
  bin?: number;
  binId?: string;
  route?: number;
  vehicle?: number;
  reportedBy?: number;
  location?: Coordinates;
  address?: string;
  assignedTo?: number;
  acknowledgedBy?: number;
  resolvedBy?: number;
  createdAt: string;
  updatedAt: string;
  acknowledgedAt?: string;
  resolvedAt?: string;
  closedAt?: string;
  metadata?: any;
  attachments?: string[];
}

// Vehicle types
export interface Vehicle {
  id: number;
  registrationNumber: string;
  vehicleType: 'truck' | 'van' | 'compactor' | 'tricycle';
  make: string;
  model: string;
  year: number;
  capacityKg: number;
  capacityLiters: number;
  status: 'available' | 'on_route' | 'maintenance' | 'out_of_service';
  currentLocation?: Coordinates;
  lastLocationUpdate?: string;
  fuelType: string;
  fuelEfficiency: number;
  lastMaintenanceDate?: string;
  nextMaintenanceDate?: string;
  assignedDriver?: number;
  createdAt: string;
  updatedAt: string;
}

// Route types
export interface CollectionRoute {
  id: number;
  name: string;
  code: string;
  description: string;
  scheduledDate: string;
  scheduledStartTime: string;
  estimatedDuration: string;
  assignedVehicle: number;
  assignedDriver: number;
  assignedCollectors: number[];
  zone: number;
  totalDistance: number;
  estimatedFuelConsumption: number;
  status: 'planned' | 'active' | 'completed' | 'cancelled';
  actualStartTime?: string;
  actualEndTime?: string;
  actualDistance?: number;
  actualFuelConsumption?: number;
  optimizationScore: number;
  routeGeometry?: any; // GeoJSON LineString
  binCount: number;
  createdAt: string;
  updatedAt: string;
  createdBy?: number;
}

export interface RouteStop {
  id: number;
  route: number;
  bin: number;
  binId?: string;
  stopOrder: number;
  estimatedArrivalTime: string;
  estimatedDuration: string;
  actualArrivalTime?: string;
  actualDepartureTime?: string;
  fillLevelBefore?: number;
  fillLevelAfter?: number;
  collectedWeight?: number;
  isCompleted: boolean;
  skipped: boolean;
  skipReason?: string;
  notes?: string;
}

// Analytics types
export interface KPI {
  id: number;
  kpiType: 'collection_efficiency' | 'route_optimization' | 'bin_utilization' | 
           'response_time' | 'fuel_efficiency' | 'recycling_rate' | 
           'citizen_satisfaction' | 'cost_per_ton';
  zone?: number;
  value: number;
  target: number;
  unit: string;
  date: string;
  periodType: 'daily' | 'weekly' | 'monthly';
  performancePercentage: number;
  createdAt: string;
  updatedAt: string;
}

export interface Prediction {
  id: number;
  predictionType: 'fill_level' | 'collection_time' | 'waste_generation' | 'route_duration';
  bin?: number;
  zone?: number;
  predictionDate: string;
  predictionTime?: string;
  predictedValue: number;
  confidenceScore: number;
  modelName: string;
  modelVersion: string;
  featuresUsed: string[];
  actualValue?: number;
  errorMargin?: number;
  createdAt: string;
}

// Dashboard types
export interface DashboardWidget {
  id: string;
  type: 'chart' | 'map' | 'stats' | 'table' | 'alerts';
  title: string;
  config: any;
  position: {
    x: number;
    y: number;
    w: number;
    h: number;
  };
}

export interface Dashboard {
  id: number;
  name: string;
  description: string;
  user?: number;
  isDefault: boolean;
  isPublic: boolean;
  layout: any;
  widgets: DashboardWidget[];
  createdAt: string;
  updatedAt: string;
}

// API response types
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface APIError {
  detail?: string;
  [key: string]: any;
}

// WebSocket message types
export interface WebSocketMessage {
  event: string;
  data: any;
  timestamp: string;
}

// Filter and search types
export interface BinFilters {
  zone?: number;
  binType?: string;
  status?: string;
  fillLevel?: {
    min?: number;
    max?: number;
  };
  search?: string;
}

export interface RouteFilters {
  zone?: number;
  status?: string;
  dateRange?: {
    start: string;
    end: string;
  };
  vehicle?: number;
  driver?: number;
}

export interface AlertFilters {
  alertType?: string;
  severity?: string;
  status?: string;
  dateRange?: {
    start: string;
    end: string;
  };
  zone?: number;
}