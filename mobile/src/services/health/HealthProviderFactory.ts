/**
 * Health Provider Factory (R4)
 * Instantiates NativeHealthProvider on iOS/Android native platforms,
 * or gracefully falls back to MockHealthProvider in web browsers and local development.
 * Completely eliminates "Plugin 'Health' not implemented on web" runtime errors.
 */

import { Capacitor } from '@capacitor/core';
import type { IHealthProvider } from './IHealthProvider';
import { MockHealthProvider } from './MockHealthProvider';
import { NativeHealthProvider } from './NativeHealthProvider';

export class HealthProviderFactory {
  private static cachedProvider: IHealthProvider | null = null;

  /**
   * Resolves the appropriate Health Provider based on environment or explicit flag.
   * @param isNativePlatform Optional boolean override (default: Capacitor.isNativePlatform())
   */
  static getProvider(isNativePlatform?: boolean): IHealthProvider {
    const native = isNativePlatform !== undefined ? isNativePlatform : Capacitor.isNativePlatform();

    if (!native) {
      return new MockHealthProvider();
    }

    try {
      return new NativeHealthProvider();
    } catch {
      return new MockHealthProvider();
    }
  }

  /**
   * Singleton provider accessor for the application lifecycle.
   */
  static getInstance(): IHealthProvider {
    if (!HealthProviderFactory.cachedProvider) {
      HealthProviderFactory.cachedProvider = HealthProviderFactory.getProvider();
    }
    return HealthProviderFactory.cachedProvider;
  }
}

/**
 * Convenience helper to get the active health provider instance.
 */
export function getHealthProvider(): IHealthProvider {
  return HealthProviderFactory.getInstance();
}
