/**
 * AthleteContext (R3)
 * Provides global state for athlete profile, dynamic daily streak,
 * today's 1-day rolling Quests, and biometric health metrics.
 */

import React, { createContext, useContext, useState, useEffect, useCallback, useMemo } from 'react';
import { api, type UserProfile, type Quest, type CalendarEvent } from '../services/api';
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
  events: CalendarEvent[];
  eventsLoading: boolean;
  completeQuest: (questId: number) => Promise<void>;
  refreshQuests: () => Promise<void>;
  refreshProfile: () => Promise<void>;
  refreshEvents: () => Promise<void>;
  addEvent: (event: CalendarEvent) => void;
  removeEvent: (eventId: number) => void;
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
  const [streak, setStreak] = useState<number>(0);
  const [quests, setQuests] = useState<Quest[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [healthMetrics, setHealthMetrics] = useState<HealthMetrics | null>(null);
  const [healthProviderName, setHealthProviderName] = useState<string>('Mock Health Provider Active');
  const [events, setEvents] = useState<CalendarEvent[]>([]);
  const [eventsLoading, setEventsLoading] = useState<boolean>(false);

  

  

  const { userId } = useAuth();
  const healthProvider = useMemo(() => getHealthProvider(), []);

  const refreshProfile = useCallback(async () => {
    if (!userId) return;
    try {
      const profile = await api.getProfile(userId);
      setAthlete(profile);
      setStreak(profile.current_streak ?? 0);
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

  const refreshEvents = useCallback(async () => {
    if (!userId) return;
    setEventsLoading(true);
    try {
      const data = await api.getEvents(userId);
      setEvents(data);
    } catch {
      // silent
    } finally {
      setEventsLoading(false);
    }
  }, [userId]);

  const addEvent = useCallback((event: CalendarEvent) => {
    setEvents((prev) => [...prev, event]);
  }, []);

  const removeEvent = useCallback((eventId: number) => {
    setEvents((prev) => prev.filter((e) => e.id !== eventId));
  }, []);

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
      await Promise.all([refreshProfile(), refreshQuests(), syncHealth(), refreshEvents()]);
      if (isMounted) setLoading(false);
    }
    init();
    return () => {
      isMounted = false;
    };
  }, [userId, refreshProfile, refreshQuests, syncHealth, refreshEvents]);

  /**
   * Toggle quest completion and dynamically increment streak on completion.
   */
  const completeQuest = useCallback(async (questId: number) => {
    const todayStr = new Date().toISOString().split('T')[0];

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

      // Only count today's quests for the streak calculation
      const todaysQuests = updated.filter(q => q.plan_date === todayStr);
      const prevTodaysQuests = prevQuests.filter(q => q.plan_date === todayStr);

      const allCompleted = todaysQuests.length > 0 && todaysQuests.every(q => q.is_completed);
      const previouslyAllCompleted = prevTodaysQuests.length > 0 && prevTodaysQuests.every(q => q.is_completed);

      // Optimistically update streak based on completing ALL of today's tasks
      setStreak((prevStreak) => {
        if (allCompleted && !previouslyAllCompleted) {
          return prevStreak + 1;
        } else if (!allCompleted && previouslyAllCompleted) {
          return Math.max(0, prevStreak - 1);
        }
        return prevStreak;
      });

      // Asynchronously notify backend
      if (userId) {
        api.completeQuest(questId, targetNewState, userId).then((res) => {
          if (res && typeof res.currentStreak === 'number' && res.currentStreak > 0) {
            setStreak(res.currentStreak);
          }
        }).catch(() => {
          // Fallback state retained
        });
      }

      return updated;
    });
  }, [userId]);

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
        events,
        eventsLoading,
        completeQuest,
        refreshQuests,
        refreshProfile,
        refreshEvents,
        addEvent,
        removeEvent,
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
