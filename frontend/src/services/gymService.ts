/**
 * Gym Service - Interface with GymPulse Backend APIs
 * Provides typed methods for branches, machines, alerts, and chatbot tools
 */

import { apiClient } from './api';

// Type definitions for API responses
export interface Branch {
  id: string;
  name: string;
  coordinates: {
    lat: number;
    lon: number;
  };
  categories: {
    [category: string]: {
      free: number;
      total: number;
    };
  };
}

export interface BranchesResponse {
  branches: Branch[];
  warnings?: string;
}

export interface Machine {
  machineId: string;
  name: string;
  status: 'free' | 'occupied' | 'offline' | 'unknown';
  lastUpdate: number;
  lastChange?: number;
  category: string;
  gymId: string;
  coordinates?: {
    lat: number;
    lon: number;
  };
  alertEligible: boolean;
}

export interface MachinesResponse {
  machines: Machine[];
  branchId: string;
  category: string;
  totalCount: number;
  freeCount: number;
  occupiedCount: number;
}

export interface HistoryBin {
  timestamp: number;
  occupancyRatio: number;
  freeCount: number;
  totalCount: number;
  status: string;
}

export interface MachineHistoryResponse {
  machineId: string;
  history: HistoryBin[];
  timeRange: {
    start: number;
    end: number;
    duration: string;
  };
  forecast: {
    likelyFreeIn30m: boolean;
    confidence: 'low' | 'medium' | 'high';
    reason: string;
  };
  totalBins: number;
}

export interface CreateAlertRequest {
  machineId: string;
  userId?: string;
  quietHours?: {
    start: number;
    end: number;
  };
}

export interface AlertResponse {
  alertId: string;
  message: string;
  machineId: string;
  userId: string;
  quietHours: {
    start: number;
    end: number;
  };
  expiresAt: number;
  estimatedNotification: string;
}

export interface Alert {
  alertId: string;
  machineId: string;
  gymId: string;
  category: string;
  createdAt: number;
  expiresAt: number;
  quietHours: {
    start: number;
    end: number;
  };
  machineName: string;
}

export interface AlertsListResponse {
  userId: string;
  alerts: Alert[];
  count: number;
}

// Chatbot Tool Types
export interface AvailabilityToolRequest {
  lat: number;
  lon: number;
  category: string;
  radius?: number;
}

export interface BranchAvailability {
  branchId: string;
  name: string;
  coordinates: [number, number];
  distance: number;
  freeCount: number;
  totalCount: number;
}

export interface AvailabilityToolResponse {
  branches: BranchAvailability[];
}

export interface RouteMatrixRequest {
  userCoordinate: {
    lat: number;
    lon: number;
  };
  branchCoordinates: Array<{
    branchId: string;
    lat: number;
    lon: number;
  }>;
}

export interface RouteMatrixResponse {
  routes: Array<{
    branchId: string;
    durationSeconds: number;
    distanceKm: number;
    eta: string;
  }>;
}

/**
 * Gym Service Class
 */
class GymService {
  /**
   * Get all branches with current availability counts
   */
  async getBranches(): Promise<BranchesResponse> {
    return apiClient.get<BranchesResponse>('/branches');
  }

  /**
   * Get machines for a specific branch and category
   */
  async getMachines(branchId: string, category: string): Promise<MachinesResponse> {
    return apiClient.get<MachinesResponse>(`/branches/${branchId}/categories/${category}/machines`);
  }

  /**
   * Get 24-hour history for a specific machine
   */
  async getMachineHistory(machineId: string): Promise<MachineHistoryResponse> {
    return apiClient.get<MachineHistoryResponse>(`/machines/${machineId}/history`);
  }

  /**
   * Create alert for "notify when free" functionality
   */
  async createAlert(request: CreateAlertRequest): Promise<AlertResponse> {
    return apiClient.post<AlertResponse>('/alerts', request);
  }

  /**
   * List active alerts for a user
   */
  async listAlerts(userId: string = 'anonymous'): Promise<AlertsListResponse> {
    return apiClient.get<AlertsListResponse>(`/alerts?userId=${encodeURIComponent(userId)}`);
  }

  /**
   * Cancel a specific alert
   */
  async cancelAlert(alertId: string): Promise<{ message: string; alertId: string }> {
    return apiClient.delete(`/alerts/${alertId}`);
  }

  /**
   * Update alert settings (e.g., quiet hours)
   */
  async updateAlert(
    alertId: string,
    updates: { quietHours: { start: number; end: number } }
  ): Promise<{ message: string; alertId: string; quietHours: any }> {
    return apiClient.put(`/alerts/${alertId}`, updates);
  }

  /**
   * Health check endpoint
   */
  async healthCheck(): Promise<{ status: string; service: string; timestamp: number; version: string }> {
    return apiClient.get('/health');
  }

  // Chatbot Tool Methods
  
  /**
   * Get availability by category for chatbot
   */
  async getAvailabilityByCategory(request: AvailabilityToolRequest): Promise<AvailabilityToolResponse> {
    return apiClient.post<AvailabilityToolResponse>('/tools/availability', {
      lat: request.lat,
      lon: request.lon,
      category: request.category,
      radius: request.radius || 5, // Default 5km radius
    });
  }

  /**
   * Calculate route matrix for chatbot
   */
  async getRouteMatrix(request: RouteMatrixRequest): Promise<RouteMatrixResponse> {
    return apiClient.post<RouteMatrixResponse>('/tools/route-matrix', request);
  }
}

// Create and export service instance
export const gymService = new GymService();

// Export types for use in components
export type {
  Branch,
  Machine,
  Alert,
  HistoryBin,
  BranchAvailability,
};