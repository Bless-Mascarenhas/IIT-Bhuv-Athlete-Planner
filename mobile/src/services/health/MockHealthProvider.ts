/**
 * Mock Health Data Provider for Web Browser Environment
 * Pulls realistic athlete biometrics from the backend dataset API.
 */

import type { IHealthProvider, HealthMetrics, HeartRateData } from './IHealthProvider';

export class MockHealthProvider implements IHealthProvider {
  private readonly fallbackMetrics = {
    steps: 8420,
    restingHeartRate: 54,
    currentHeartRate: 64,
    sleepHours: 7.8,
    sleepMinutes: 468,
    caloriesBurned: 2150,
    activeCalories: 580,
    distanceMeters: 6200,
    hrvMs: 65,
  };

  async isAvailable(): Promise<boolean> { return true; }
  async requestPermissions(): Promise<boolean> { return true; }

  async getTodaySteps(): Promise<number> { return this.fallbackMetrics.steps; }
  async getHeartRate(): Promise<HeartRateData> {
    return { current: this.fallbackMetrics.currentHeartRate, resting: this.fallbackMetrics.restingHeartRate };
  }
  async getSleepHours(): Promise<number> { return this.fallbackMetrics.sleepHours; }
  async getCaloriesBurned(): Promise<number> { return this.fallbackMetrics.caloriesBurned; }

  async getTodayMetrics(): Promise<HealthMetrics> {
    try {
      const res = await fetch('https://pace-backend-2oyk.onrender.com/api/data/dataset_health');
      if (res.ok) {
        const json = await res.json();
        if (json.status === 'success') {
          return json.data;
        }
      }
    } catch (e) {
      console.warn("Failed to fetch from dataset API, using fallback data", e);
    }

    // Fallback if API is unreachable
    const today = new Date().toISOString().split('T')[0];
    return {
      ...this.fallbackMetrics,
      date: today,
      source: 'mock',
    };
  }

  async getHistoricalMetrics(days: number = 7): Promise<HealthMetrics[]> {
    const metrics: HealthMetrics[] = [];
    const baseDate = new Date();

    for (let i = 0; i < days; i++) {
      const d = new Date(baseDate);
      d.setDate(d.getDate() - i);
      const dayOffset = (i % 3) * 200;

      metrics.push({
        steps: 7800 + dayOffset + ((i * 123) % 800),
        activeCalories: 520 + ((i * 45) % 150),
        caloriesBurned: 2000 + ((i * 90) % 300),
        distanceMeters: 5600 + ((i * 300) % 1200),
        sleepMinutes: 440 + ((i * 25) % 50),
        sleepHours: Math.round(((440 + ((i * 25) % 50)) / 60) * 10) / 10,
        restingHeartRate: 53 + (i % 4),
        currentHeartRate: 62 + (i % 6),
        hrvMs: 62 + (i % 8),
        date: d.toISOString().split('T')[0],
        source: 'mock',
      });
    }

    return metrics;
  }
}
