import axios, { AxiosInstance, AxiosError, InternalAxiosRequestConfig } from 'axios';
import { toast } from 'react-hot-toast';
import { useAuthStore } from '../store/authStore';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api';

// Create axios instance
const api: AxiosInstance = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = useAuthStore.getState().tokens?.access;
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error: AxiosError) => {
    return Promise.reject(error);
  }
);

// Response interceptor
api.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as any;

    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      try {
        const refreshToken = useAuthStore.getState().tokens?.refresh;
        if (refreshToken) {
          const response = await axios.post(`${API_URL}/auth/token/refresh/`, {
            refresh: refreshToken,
          });
          
          const { access } = response.data;
          useAuthStore.getState().setTokens({ access, refresh: refreshToken });
          
          originalRequest.headers.Authorization = `Bearer ${access}`;
          return api(originalRequest);
        }
      } catch (refreshError) {
        useAuthStore.getState().logout();
        window.location.href = '/login';
      }
    }

    // Show error message
    if (error.response?.data) {
      const errorData = error.response.data as any;
      const message = errorData.detail || errorData.message || 'An error occurred';
      toast.error(message);
    } else if (error.message) {
      toast.error(error.message);
    }

    return Promise.reject(error);
  }
);

// API endpoints
export const authAPI = {
  login: (credentials: { email: string; password: string }) =>
    api.post('/auth/token/', credentials),
  
  refresh: (refreshToken: string) =>
    api.post('/auth/token/refresh/', { refresh: refreshToken }),
  
  verify: (token: string) =>
    api.post('/auth/token/verify/', { token }),
  
  register: (userData: any) =>
    api.post('/v1/users/register/', userData),
  
  me: () =>
    api.get('/v1/users/me/'),
  
  updateProfile: (data: any) =>
    api.patch('/v1/users/me/', data),
  
  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post('/v1/users/change-password/', data),
};

export const usersAPI = {
  list: (params?: any) =>
    api.get('/v1/users/', { params }),
  
  get: (id: number) =>
    api.get(`/v1/users/${id}/`),
  
  create: (data: any) =>
    api.post('/v1/users/', data),
  
  update: (id: number, data: any) =>
    api.patch(`/v1/users/${id}/`, data),
  
  delete: (id: number) =>
    api.delete(`/v1/users/${id}/`),
};

export const zonesAPI = {
  list: (params?: any) =>
    api.get('/v1/bins/zones/', { params }),
  
  get: (id: number) =>
    api.get(`/v1/bins/zones/${id}/`),
  
  create: (data: any) =>
    api.post('/v1/bins/zones/', data),
  
  update: (id: number, data: any) =>
    api.patch(`/v1/bins/zones/${id}/`, data),
  
  delete: (id: number) =>
    api.delete(`/v1/bins/zones/${id}/`),
  
  stats: (id: number) =>
    api.get(`/v1/bins/zones/${id}/stats/`),
};

export const binsAPI = {
  list: (params?: any) =>
    api.get('/v1/bins/', { params }),
  
  get: (id: number) =>
    api.get(`/v1/bins/${id}/`),
  
  create: (data: any) =>
    api.post('/v1/bins/', data),
  
  update: (id: number, data: any) =>
    api.patch(`/v1/bins/${id}/`, data),
  
  delete: (id: number) =>
    api.delete(`/v1/bins/${id}/`),
  
  nearby: (lat: number, lng: number, radius: number = 1000) =>
    api.get('/v1/bins/nearby/', { params: { lat, lng, radius } }),
  
  maintenance: (id: number) =>
    api.get(`/v1/bins/${id}/maintenance/`),
  
  createMaintenance: (id: number, data: any) =>
    api.post(`/v1/bins/${id}/maintenance/`, data),
};

export const sensorsAPI = {
  readings: (binId: number, params?: any) =>
    api.get(`/v1/sensors/readings/`, { params: { bin: binId, ...params } }),
  
  latestReading: (binId: number) =>
    api.get(`/v1/sensors/readings/latest/`, { params: { bin: binId } }),
  
  aggregatedData: (binId: number, period: string, params?: any) =>
    api.get(`/v1/sensors/aggregated/`, { params: { bin: binId, period, ...params } }),
  
  alerts: (params?: any) =>
    api.get('/v1/sensors/alerts/', { params }),
  
  calibrate: (binId: number, data: any) =>
    api.post(`/v1/sensors/calibrate/`, { bin: binId, ...data }),
};

export const alertsAPI = {
  list: (params?: any) =>
    api.get('/v1/alerts/', { params }),
  
  get: (id: number) =>
    api.get(`/v1/alerts/${id}/`),
  
  create: (data: any) =>
    api.post('/v1/alerts/', data),
  
  update: (id: number, data: any) =>
    api.patch(`/v1/alerts/${id}/`, data),
  
  acknowledge: (id: number) =>
    api.post(`/v1/alerts/${id}/acknowledge/`),
  
  resolve: (id: number, data?: any) =>
    api.post(`/v1/alerts/${id}/resolve/`, data),
  
  close: (id: number) =>
    api.post(`/v1/alerts/${id}/close/`),
  
  comments: (id: number) =>
    api.get(`/v1/alerts/${id}/comments/`),
  
  addComment: (id: number, data: any) =>
    api.post(`/v1/alerts/${id}/comments/`, data),
  
  rules: (params?: any) =>
    api.get('/v1/alerts/rules/', { params }),
  
  createRule: (data: any) =>
    api.post('/v1/alerts/rules/', data),
  
  updateRule: (id: number, data: any) =>
    api.patch(`/v1/alerts/rules/${id}/`, data),
  
  deleteRule: (id: number) =>
    api.delete(`/v1/alerts/rules/${id}/`),
};

export const vehiclesAPI = {
  list: (params?: any) =>
    api.get('/v1/routes/vehicles/', { params }),
  
  get: (id: number) =>
    api.get(`/v1/routes/vehicles/${id}/`),
  
  create: (data: any) =>
    api.post('/v1/routes/vehicles/', data),
  
  update: (id: number, data: any) =>
    api.patch(`/v1/routes/vehicles/${id}/`, data),
  
  delete: (id: number) =>
    api.delete(`/v1/routes/vehicles/${id}/`),
  
  updateLocation: (id: number, location: { lat: number; lng: number }) =>
    api.post(`/v1/routes/vehicles/${id}/update-location/`, location),
  
  maintenance: (id: number) =>
    api.get(`/v1/routes/vehicles/${id}/maintenance/`),
};

export const routesAPI = {
  list: (params?: any) =>
    api.get('/v1/routes/', { params }),
  
  get: (id: number) =>
    api.get(`/v1/routes/${id}/`),
  
  create: (data: any) =>
    api.post('/v1/routes/', data),
  
  update: (id: number, data: any) =>
    api.patch(`/v1/routes/${id}/`, data),
  
  delete: (id: number) =>
    api.delete(`/v1/routes/${id}/`),
  
  stops: (id: number) =>
    api.get(`/v1/routes/${id}/stops/`),
  
  addStop: (id: number, data: any) =>
    api.post(`/v1/routes/${id}/stops/`, data),
  
  updateStop: (routeId: number, stopId: number, data: any) =>
    api.patch(`/v1/routes/${routeId}/stops/${stopId}/`, data),
  
  removeStop: (routeId: number, stopId: number) =>
    api.delete(`/v1/routes/${routeId}/stops/${stopId}/`),
  
  optimize: (id: number, params?: any) =>
    api.post(`/v1/routes/${id}/optimize/`, params),
  
  start: (id: number) =>
    api.post(`/v1/routes/${id}/start/`),
  
  complete: (id: number, data?: any) =>
    api.post(`/v1/routes/${id}/complete/`, data),
  
  cancel: (id: number, reason?: string) =>
    api.post(`/v1/routes/${id}/cancel/`, { reason }),
};

export const analyticsAPI = {
  kpis: (params?: any) =>
    api.get('/v1/analytics/kpis/', { params }),
  
  predictions: (params?: any) =>
    api.get('/v1/analytics/predictions/', { params }),
  
  reports: (params?: any) =>
    api.get('/v1/analytics/reports/', { params }),
  
  generateReport: (data: any) =>
    api.post('/v1/analytics/reports/generate/', data),
  
  downloadReport: (id: number, format: 'pdf' | 'excel') =>
    api.get(`/v1/analytics/reports/${id}/download/`, { 
      params: { format },
      responseType: 'blob'
    }),
  
  dashboards: () =>
    api.get('/v1/analytics/dashboards/'),
  
  getDashboard: (id: number) =>
    api.get(`/v1/analytics/dashboards/${id}/`),
  
  createDashboard: (data: any) =>
    api.post('/v1/analytics/dashboards/', data),
  
  updateDashboard: (id: number, data: any) =>
    api.patch(`/v1/analytics/dashboards/${id}/`, data),
  
  deleteDashboard: (id: number) =>
    api.delete(`/v1/analytics/dashboards/${id}/`),
  
  exportData: (data: any) =>
    api.post('/v1/analytics/export/', data),
  
  getExport: (id: string) =>
    api.get(`/v1/analytics/export/${id}/`),
  
  downloadExport: (id: string) =>
    api.get(`/v1/analytics/export/${id}/download/`, { responseType: 'blob' }),
};

export default api;