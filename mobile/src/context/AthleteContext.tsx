/**
 * AthleteContext (R3)
 * Provides global state for athlete profile, dynamic daily streak,
 * today's 1-day rolling Quests, and biometric health metrics.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { api, type UserProfile, type Quest } from '../services/api';
import { getHealthProvider, type HealthMetrics } from '../services/health';
import { useAuth } from './AuthContext';

export interface AthleteContextType {
  athlete: UserProfile | null;
  streak: number;
  greeting: string;
  quests: Quest[];
  loading: boolean;
  healthMetrics: HealthMetrics | null;
  healthProviderName: string;
  completeQuest: (questId: number) => Promise<void>;
  refreshQuests: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  updateGoal: (goal: string) => Promise<void>;
  completeGoal: () => Promise<void>;
  syncHealth: () => Promise<void>;
}

const AthleteContext = createContext<AthleteContextType | undefined>(undefined);

function computeGreeting(name: string = 'Champ'): string {
  const hour = new Date().getHours();
  if (hour < 12) {
    return `Good Morning, ${name}!`;
  } else if (hour < 17) {
    return `Good Afternoon, ${name}!`;
  } else {
    return `Good Evening, ${name}!`;
  }
}

export const AthleteProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [athlete, setAthlete] = useState<UserProfile | null>(null);
  const [streak, setStreak] = useState<number>(12);
  const [quests, setQuests] = useState<Quest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [healthMetrics, setHealthMetrics] = useState<HealthMetrics | null>(null);
  const [healthProviderName, setHealthProviderName] = useState<string>('Mock Health Provider Active');

  

  

  const { userId } = useAuth();
  const healthProvider = useMemo(() => getHealthProvider(), []);

  const refreshProfile = useCallback(async () => {
    if (!userId) return;
    try {
      const profile = await api.getProfile(userId);
      setAthlete(profile);
      setStreak(profile.current_streak ?? 12);
    } catch {
      // Fallback already handled in api.ts
    }
  }, [userId]);

  const refreshQuests = useCallback(async () => {
    if (!userId) return;
    try {
      const todayQuests = await api.get7DayPlan(userId);
      setQuests(todayQuests);
    } catch {
      // Fallback already handled in api.ts
    }
  }, [userId]);

  const updateGoal = useCallback(async (goal: string) => {
    if (!userId) return;
    setLoading(true);
    await api.updateGoal(goal, userId);
    await refreshProfile();
    // Setting a new goal also recalculates the plan
    await api.generatePlan(userId, goal);
    await refreshQuests();
    setLoading(false);
  }, [userId, refreshProfile, refreshQuests]);

  const completeGoal = useCallback(async () => {
    if (!userId) return;
    setLoading(true);
    await api.completeGoal(userId);
    await refreshProfile();
    setLoading(false);
  }, [userId, refreshProfile]);

  const syncHealth = useCallback(async () => {
    try {
      const isNative = !(healthProvider.constructor.name === 'MockHealthProvider');
      setHealthProviderName(isNative ? 'Native HealthKit / Health Connect' : 'Mock Health Provider Active');

      // Ensure we have permission before attempting to read metrics
      await healthProvider.requestPermissions();

      const metrics = await healthProvider.getTodayMetrics();
      setHealthMetrics(metrics);

      // Opportunistically sync telemetry to backend (fire-and-forget, won't block UI)
      api.syncHealthTelemetry({
        user_id: userId || 1,
        steps: metrics.steps,
        active_calories: metrics.activeCalories,
        calories_burned: metrics.caloriesBurned,
        distance_meters: metrics.distanceMeters,
        sleep_minutes: metrics.sleepMinutes,
        resting_hr: metrics.restingHeartRate,
        source: metrics.source,
      }).catch(() => {/* silent — backend may be cold-starting */});
    } catch {
      // Silent error suppression
    }
  }, [userId, healthProvider]);

  // Initial load
  useEffect(() => {
    let isMounted = true;
    async function init() {
      if (!userId) return;
      setLoading(true);
      await Promise.all([refreshProfile(), refreshQuests(), syncHealth()]);
      if (isMounted) setLoading(false);
    }
    init();
    return () => {
      isMounted = false;
    };
  }, [userId, refreshProfile, refreshQuests, syncHealth]);

  /**
   * Toggle quest completion and dynamically increment streak on completion.
   */
  const completeQuest = useCallback(async (questId: number) => {
    setQuests((prevQuests) => {
      let targetNewState = false;
      const updated = prevQuests.map((q) => {
        if (q.id === questId) {
          targetNewState = !q.is_completed;
          return {
            ...q,
            is_completed: targetNewState,
            completed_at: targetNewState ? new Date().toISOString() : null,
          };
        }
        return q;
      });

      // Dynamically update streak
      setStreak((prevStreak) => {
        if (targetNewState) {
          return prevStreak + 1;
        } else {
          return Math.max(1, prevStreak - 1);
        }
      });

      // Asynchronously notify backend
      if (userId) {
        api.completeQuest(questId, targetNewState, userId).then((res) => {
          if (res && typeof res.currentStreak === 'number') {
            setStreak(res.currentStreak);
          }
        }).catch(() => {
          // Fallback state retained
        });
      }

      return updated;
    });
  }, []);

  const greeting = useMemo(() => {
    const firstName = athlete?.name ? athlete.name.split(' ')[0] : 'Champ';
    return computeGreeting(firstName);
  }, [athlete]);

  return (
    <AthleteContext.Provider
      value={{
        athlete,
        streak,
        greeting,
        quests,
        loading,
        healthMetrics,
        healthProviderName,
        completeQuest,
        refreshQuests,
        refreshProfile,
        syncHealth,
        updateGoal,
        completeGoal,
      }}
    >
      {children}
    </AthleteContext.Provider>
  );
};

export function useAthlete(): AthleteContextType {
  const context = useContext(AthleteContext);
  if (!context) {
    throw new Error('useAthlete must be used within an AthleteProvider');
  }
  return context;
}
