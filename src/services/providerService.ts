import axios from 'axios';
import { API_BASE_URL } from '../config';

export interface Provider {
  id: string;
  user: {
    id: string;
    first_name: string;
    last_name: string;
    email: string;
    phone: string;
  };
  business_type: string;
  company_name: string;
  company_reg_number: string;
  vat_registered: boolean;
  vat_number: string;
  business_description: string;
  website: string;
  founded_year: number;
  operating_areas: string[];
  contact_person_name: string;
  contact_person_position: string;
  contact_person_email: string;
  contact_person_phone: string;
  bank_account_holder: string;
  bank_name: string;
  bank_account_number: string;
  bank_routing_number: string;
  service_categories: any[];
  specializations: any[];
  service_image: string;
  base_location: any;
  hourly_rate: number;
  accepts_instant_bookings: boolean;
  service_radius_km: number;
  insurance_policies: any[];
  payment_methods: any[];
  minimum_job_value: number;
  verification_status: string;
  last_verified: string;
  service_areas: any[];
  documents: any[];
  reviews: any[];
  payments: any[];
  average_rating: number;
  completed_bookings_count: number;
  vehicle_count: number;
  last_active: string;
}

export const providerService = {
  getProviderById: async (id: string): Promise<Provider> => {
    const response = await axios.get(`${API_BASE_URL}/api/providers/${id}/`);
    return response.data;
  },

  activateProvider: async (id: string): Promise<void> => {
    await axios.post(`${API_BASE_URL}/api/providers/${id}/activate/`);
  },

  suspendProvider: async (id: string): Promise<void> => {
    await axios.post(`${API_BASE_URL}/api/providers/${id}/suspend/`);
  },

  verifyProvider: async (id: string): Promise<void> => {
    await axios.post(`${API_BASE_URL}/api/providers/${id}/verify/`);
  },

  deleteProvider: async (id: string): Promise<void> => {
    await axios.delete(`${API_BASE_URL}/api/providers/${id}/`);
  },

  getProviderDocuments: async (id: string): Promise<any[]> => {
    const response = await axios.get(`${API_BASE_URL}/api/providers/${id}/documents/`);
    return response.data;
  },

  getProviderReviews: async (id: string): Promise<any[]> => {
    const response = await axios.get(`${API_BASE_URL}/api/providers/${id}/reviews/`);
    return response.data;
  },

  getProviderPayments: async (id: string): Promise<any[]> => {
    const response = await axios.get(`${API_BASE_URL}/api/providers/${id}/payments/`);
    return response.data;
  },

  getProviderSavedJobs: async (id: string): Promise<any[]> => {
    const response = await axios.get(`${API_BASE_URL}/api/providers/${id}/saved_jobs/`);
    return response.data;
  },

  getProviderWatchedJobs: async (id: string): Promise<any[]> => {
    const response = await axios.get(`${API_BASE_URL}/api/providers/${id}/watched_jobs/`);
    return response.data;
  }
}; 