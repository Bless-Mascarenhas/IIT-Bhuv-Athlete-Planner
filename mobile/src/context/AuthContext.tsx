import React, { createContext, useContext, useState, useEffect } from 'react';
import { Preferences } from '@capacitor/preferences';
import { api } from '../services/api';

interface AuthContextType {
  isLoggedIn: boolean;
  hasOnboarded: boolean;
  userId: number | null;
  login: (userId: number) => Promise<void>;
  startLocalGuest: (formData: any) => Promise<void>;
  completeOnboarding: () => Promise<void>;
  logout: () => Promise<void>;
  isLoading: boolean;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [hasOnboarded, setHasOnboarded] = useState(false);
  const [userId, setUserId] = useState<number | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // 1. Fire wake up ping immediately (Cold Start Hack)
    api.wakeUp().catch(() => {});

    // 2. Load auth state from preferences
    const loadAuth = async () => {
      try {
        const { value: storedUserId } = await Preferences.get({ key: 'userId' });
        const { value: storedOnboarded } = await Preferences.get({ key: 'hasOnboarded' });

        if (storedUserId) {
          setUserId(parseInt(storedUserId, 10));
          setIsLoggedIn(true);
        }
        if (storedOnboarded === 'true') {
          setHasOnboarded(true);
        }
      } catch (e) {
        console.error('Error loading auth state:', e);
      } finally {
        setIsLoading(false);
      }
    };

    loadAuth();
  }, []);

  const login = async (newUserId: number) => {
    await Preferences.set({ key: 'userId', value: newUserId.toString() });
    setUserId(newUserId);
    setIsLoggedIn(true);
  };

  const startLocalGuest = async (formData: any) => {
    // Instantly bypass all loading/login screens and set default fallback ID (1)
    setUserId(1); 
    setIsLoggedIn(true);
    setHasOnboarded(true);
    await Preferences.set({ key: 'hasOnboarded', value: 'true' });
    
    // Background cloud sync without waiting
    (async () => {
      try {
        const cloudUserId = await api.loginGuest();
        if (cloudUserId) {
          await api.updateProfile(cloudUserId, formData);
          await login(cloudUserId);
        }
      } catch (e) {
        console.error('Failed to sync guest account to cloud in background', e);
      }
    })();
  };

  const completeOnboarding = async () => {
    await Preferences.set({ key: 'hasOnboarded', value: 'true' });
    setHasOnboarded(true);
  };

  const logout = async () => {
    await Preferences.remove({ key: 'userId' });
    await Preferences.remove({ key: 'hasOnboarded' });
    setUserId(null);
    setIsLoggedIn(false);
    setHasOnboarded(false);
  };

  return (
    <AuthContext.Provider
      value={{
        isLoggedIn,
        hasOnboarded,
        userId,
        login,
        startLocalGuest,
        completeOnboarding,
        logout,
        isLoading,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
};

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
