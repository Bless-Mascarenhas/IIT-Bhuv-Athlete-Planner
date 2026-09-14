import React, { createContext, useContext, useState, useEffect } from 'react';
import { Preferences } from '@capacitor/preferences';
import { api } from '../services/api';

interface AuthContextType {
  isLoggedIn: boolean;
  hasOnboarded: boolean;
  userId: number | null;
  isGuest: boolean;
  localProfile: any | null;
  login: (userId: number, isGuest?: boolean) => Promise<void>;
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
  const [isGuest, setIsGuest] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  // Stores onboarding form data so the UI can display it immediately
  // while the background cloud sync is in progress
  const [localProfile, setLocalProfile] = useState<any | null>(null);

  useEffect(() => {
    // 1. Fire wake up ping immediately (Cold Start Hack)
    api.wakeUp().catch(() => {});

    // 2. Load auth state from preferences
    const loadAuth = async () => {
      try {
        const { value: storedUserId } = await Preferences.get({ key: 'userId' });
        const { value: storedOnboarded } = await Preferences.get({ key: 'hasOnboarded' });
        const { value: storedIsGuest } = await Preferences.get({ key: 'isGuest' });

        if (storedUserId) {
          setUserId(parseInt(storedUserId, 10));
          setIsLoggedIn(true);
        }
        if (storedOnboarded === 'true') {
          setHasOnboarded(true);
        }
        if (storedIsGuest === 'true') {
          setIsGuest(true);
        }
      } catch (e) {
        console.error('Error loading auth state:', e);
      } finally {
        setIsLoading(false);
      }
    };

    loadAuth();
  }, []);

  const login = async (newUserId: number, guestFlag: boolean = false) => {
    await Preferences.set({ key: 'userId', value: newUserId.toString() });
    
    if (guestFlag) {
      await Preferences.set({ key: 'isGuest', value: 'true' });
      setIsGuest(true);
    } else {
      await Preferences.remove({ key: 'isGuest' });
      setIsGuest(false);
    }
    
    // Clear localProfile once we have a confirmed cloud userId
    setLocalProfile(null);
    setUserId(newUserId);
    setIsLoggedIn(true);
  };

  const startLocalGuest = async (formData: any) => {
    // Store the form data immediately so the UI can display it right away
    // before the backend cloud sync completes
    setLocalProfile(formData);
    // Instantly bypass all loading/login screens and set default fallback ID (1)
    setUserId(1); 
    setIsLoggedIn(true);
    setHasOnboarded(true);
    setIsGuest(true);
    await Preferences.set({ key: 'hasOnboarded', value: 'true' });
    await Preferences.set({ key: 'isGuest', value: 'true' });
    
    // Background cloud sync without waiting
    (async () => {
      try {
        const cloudUserId = await api.loginGuest();
        if (cloudUserId) {
          await api.updateProfile(cloudUserId, formData);
          // login() will clear localProfile and set the real userId
          await login(cloudUserId, true);
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
    await Preferences.remove({ key: 'isGuest' });
    setUserId(null);
    setIsLoggedIn(false);
    setHasOnboarded(false);
    setIsGuest(false);
  };

  return (
    <AuthContext.Provider
      value={{
        isLoggedIn,
        hasOnboarded,
        userId,
        isGuest,
        localProfile,
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
