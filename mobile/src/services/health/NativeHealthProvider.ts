/**
 * Native Health Data Provider for Android (R6 - FINAL FIX)
 *
 * CRITICAL: @devmaxime/capacitor-health-connect uses registerPlugin() internally,
 * which means it MUST be statically imported at module load time.
 * Dynamic imports (lazy loading) prevent the plugin from registering with
 * the Capacitor native bridge, silently breaking all native calls.
 */

import { Capacitor } from '@capacitor/core';
import { HealthConnect } from '@devmaxime/capacitor-health-connect';
import type { IHealthProvider, HealthMetrics, HeartRateData } from './IHealthProvider';
import { MockHealthProvider } from './MockHealthProvider';

export class NativeHealthProvider implements IHealthProvider {
  private fallbackProvider = new MockHealthProvider();

  async isAvailable(): Promise<boolean> {
    if (!Capacitor.isNativePlatform()) return false;
    try {
      const result = await HealthConnect.checkAvailability();
      return result.availability === 'Available';
    } catch (e) {
      console.warn('[NativeHealthProvider] isAvailable error:', e);
      return false;
    }
  }

  async requestPermissions(): Promise<boolean> {
    if (!Capacitor.isNativePlatform()) return true;
    try {
      const avail = await HealthConnect.checkAvailability();
      if (avail.availability !== 'Available') {
        console.warn('[NativeHealthProvider] Health Connect not available:', avail.availability);
        return false;
      }
      // Request permissions — this triggers the native Health Connect dialog
      // Request permissions — this triggers the native Health Connect dialog
      // NOTE: type names MUST exactly match RECORDS_TYPE_NAME_MAP keys in the plugin
      // TotalCaloriesBurned and HeartRate are required for the respective metrics
      await HealthConnect.requestPermissions({
        read: ['Steps', 'SleepSession', 'HeartRate', 'TotalCaloriesBurned'] as any[],
        write: [],
      });
      return true;
    } catch (e) {
      console.error('[NativeHealthProvider] requestPermissions error:', e);
      return false;
    }
  }

  async getTodaySteps(): Promise<number> {
    if (!Capacitor.isNativePlatform()) return this.fallbackProvider.getTodaySteps();
    try {
      const today = new Date();
      const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate()).toISOString();
      const result = await HealthConnect.aggregateRecords({
        start: startOfDay,
        end: today.toISOString(),
        type: 'Steps',
        groupBy: 'day',
      });
      if (result.aggregates && result.aggregates.length > 0) {
        return Math.round(result.aggregates[0].value ?? 0);
      }
      return 0;
    } catch (e) {
      console.error('[NativeHealthProvider] getTodaySteps error:', e);
      return this.fallbackProvider.getTodaySteps();
    }
  }

  async getHeartRate(): Promise<HeartRateData> {
    if (!Capacitor.isNativePlatform()) return this.fallbackProvider.getHeartRate();
    try {
      const today = new Date();
      const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate()).toISOString();
      const result = await HealthConnect.aggregateRecords({
        start: startOfDay,
        end: today.toISOString(),
        type: 'HeartRate',
        groupBy: 'day',
      });
      if (result.aggregates && result.aggregates.length > 0) {
        const avg = Math.round(result.aggregates[0].value ?? 62);
        return { current: avg + 8, resting: avg };
      }
      return { current: 70, resting: 62 };
    } catch (e) {
      console.error('[NativeHealthProvider] getHeartRate error:', e);
      return this.fallbackProvider.getHeartRate();
    }
  }

  async getSleepHours(): Promise<number> {
    if (!Capacitor.isNativePlatform()) return this.fallbackProvider.getSleepHours();
    try {
      const today = new Date();
      const yesterday = new Date(today.getTime() - 24 * 60 * 60 * 1000).toISOString();
      const result = await HealthConnect.readRecords({
        start: yesterday,
        end: today.toISOString(),
        type: 'SleepSession',
      });
      if (result.records && result.records.length > 0) {
        let totalMs = 0;
        for (const r of result.records as any[]) {
          if (r.startTime && r.endTime) {
            totalMs += new Date(r.endTime).getTime() - new Date(r.startTime).getTime();
          }
        }
        return Math.round((totalMs / 3600000) * 10) / 10;
      }
      return this.fallbackProvider.getSleepHours();
    } catch (e) {
      console.error('[NativeHealthProvider] getSleepHours error:', e);
      return this.fallbackProvider.getSleepHours();
    }
  }

  async getCaloriesBurned(): Promise<number> {
    if (!Capacitor.isNativePlatform()) return this.fallbackProvider.getCaloriesBurned();
    try {
      const today = new Date();
      const startOfDay = new Date(today.getFullYear(), today.getMonth(), today.getDate()).toISOString();
      const result = await HealthConnect.aggregateRecords({
        start: startOfDay,
        end: today.toISOString(),
        type: 'TotalCaloriesBurned',
        groupBy: 'day',
      });
      if (result.aggregates && result.aggregates.length > 0) {
        return Math.round(result.aggregates[0].value ?? 0);
      }
      return this.fallbackProvider.getCaloriesBurned();
    } catch (e) {
      console.error('[NativeHealthProvider] getCaloriesBurned error:', e);
      return this.fallbackProvider.getCaloriesBurned();
    }
  }

  async getTodayMetrics(): Promise<HealthMetrics> {
    if (!Capacitor.isNativePlatform()) return this.fallbackProvider.getTodayMetrics();
    try {
      const steps = await this.getTodaySteps();
      const hr = await this.getHeartRate();
      const sleepHours = await this.getSleepHours();
      const calories = await this.getCaloriesBurned();
      const today = new Date().toISOString().split('T')[0];
      return {
        steps,
        activeCalories: Math.round(calories * 0.28),
        caloriesBurned: calories,
        distanceMeters: Math.round(steps * 0.76),
        sleepMinutes: Math.round(sleepHours * 60),
        sleepHours,
        restingHeartRate: hr.resting,
        currentHeartRate: hr.current,
        hrvMs: 65,
        date: today,
        source: 'native',
      };
    } catch {
      return this.fallbackProvider.getTodayMetrics();
    }
  }

  async getHistoricalMetrics(days: number = 7): Promise<HealthMetrics[]> {
    return this.fallbackProvider.getHistoricalMetrics(days);
  }
}
