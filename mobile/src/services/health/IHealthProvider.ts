/**
 * Health Data Architecture - Provider Interface Contract (R4)
 * Authoritative specification for athlete biometric telemetry.
 */

export interface HealthMetrics {
  steps: number;
  activeCalories: number;
  caloriesBurned?: number;
  distanceMeters: number;
  sleepMinutes: number;
  sleepHours?: number;
  restingHeartRate: number;
  currentHeartRate?: number;
  hrvMs?: number;
  date: string;
  source: 'native' | 'mock';
}

export interface HeartRateData {
  current: number;
  resting: number;
}

export interface IHealthProvider {
  /** Check if the health provider service is available */
  isAvailable(): Promise<boolean>;

  /** Request permissions from health platform (HealthKit / Health Connect) */
  requestPermissions(): Promise<boolean>;

  /** Total step count for today */
  getTodaySteps(): Promise<number>;

  /** Current and resting heart rate biometrics */
  getHeartRate(): Promise<HeartRateData>;

  /** Total sleep duration for previous night in hours */
  getSleepHours(): Promise<number>;

  /** Total calories burned for today */
  getCaloriesBurned(): Promise<number>;

  /** Unified daily telemetry metrics matching the interface contract */
  getTodayMetrics(): Promise<HealthMetrics>;

  /** Historical metrics telemetry for trending charts */
  getHistoricalMetrics?(days?: number): Promise<HealthMetrics[]>;
}
