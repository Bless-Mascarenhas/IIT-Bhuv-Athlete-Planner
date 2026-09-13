declare module '@capawesome-team/capacitor-health' {
  export interface HealthPlugin {
    isAvailable(): Promise<{ available: boolean }>;
    requestPermissions(options?: any): Promise<void>;
    queryDailySummary?(options?: any): Promise<any>;
    queryHeartRate?(options?: any): Promise<any>;
    [key: string]: any;
  }
  export const Health: HealthPlugin;
}

declare module '@capawesome/capacitor-health' {
  export interface HealthPlugin {
    isAvailable(): Promise<{ available: boolean }>;
    requestPermissions(options?: any): Promise<void>;
    [key: string]: any;
  }
  export const Health: HealthPlugin;
}
