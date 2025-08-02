import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, AuthTokens, LoginCredentials } from '../types';
import { authAPI } from '../services/api';
import wsService from '../services/websocket';

interface AuthStore {
  user: User | null;
  tokens: AuthTokens | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  
  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => void;
  register: (userData: any) => Promise<void>;
  refreshToken: () => Promise<void>;
  fetchUser: () => Promise<void>;
  setUser: (user: User) => void;
  setTokens: (tokens: AuthTokens) => void;
  updateProfile: (data: any) => Promise<void>;
  changePassword: (data: { old_password: string; new_password: string }) => Promise<void>;
}

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      tokens: null,
      isAuthenticated: false,
      isLoading: false,

      login: async (credentials) => {
        set({ isLoading: true });
        try {
          const response = await authAPI.login(credentials);
          const tokens = response.data;
          
          set({ tokens, isAuthenticated: true });
          
          // Fetch user data
          await get().fetchUser();
          
          // Connect WebSocket
          wsService.connect();
        } catch (error) {
          set({ isAuthenticated: false, user: null, tokens: null });
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      logout: () => {
        set({
          user: null,
          tokens: null,
          isAuthenticated: false,
        });
        
        // Disconnect WebSocket
        wsService.disconnect();
        
        // Clear persisted state
        localStorage.removeItem('auth-storage');
      },

      register: async (userData) => {
        set({ isLoading: true });
        try {
          await authAPI.register(userData);
          
          // Auto-login after registration
          await get().login({
            email: userData.email,
            password: userData.password,
          });
        } catch (error) {
          throw error;
        } finally {
          set({ isLoading: false });
        }
      },

      refreshToken: async () => {
        const { tokens } = get();
        if (!tokens?.refresh) {
          throw new Error('No refresh token available');
        }

        try {
          const response = await authAPI.refresh(tokens.refresh);
          const newTokens = {
            access: response.data.access,
            refresh: tokens.refresh,
          };
          
          set({ tokens: newTokens });
        } catch (error) {
          get().logout();
          throw error;
        }
      },

      fetchUser: async () => {
        try {
          const response = await authAPI.me();
          set({ user: response.data });
        } catch (error) {
          throw error;
        }
      },

      setUser: (user) => {
        set({ user });
      },

      setTokens: (tokens) => {
        set({ tokens, isAuthenticated: true });
      },

      updateProfile: async (data) => {
        try {
          const response = await authAPI.updateProfile(data);
          set({ user: response.data });
        } catch (error) {
          throw error;
        }
      },

      changePassword: async (data) => {
        try {
          await authAPI.changePassword(data);
        } catch (error) {
          throw error;
        }
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({
        user: state.user,
        tokens: state.tokens,
        isAuthenticated: state.isAuthenticated,
      }),
    }
  )
);