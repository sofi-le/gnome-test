import { Platform } from 'react-native';

/**
 * API base URL resolution:
 *   1. EXPO_PUBLIC_API_BASE_URL (set in .env or shell before `expo start`)
 *   2. Sensible per-platform localhost fallback
 *
 * The Android emulator cannot reach the host loopback at 127.0.0.1 —
 * 10.0.2.2 is the alias Android uses for the host machine.
 *
 * For a physical phone via Expo Go, override with the LAN IP of the
 * machine running uvicorn, e.g. EXPO_PUBLIC_API_BASE_URL=http://192.168.1.42:8000
 */
const fromEnv = process.env.EXPO_PUBLIC_API_BASE_URL;

const defaultByPlatform =
  Platform.OS === 'android' ? 'http://10.0.2.2:8000' : 'http://127.0.0.1:8000';

export const API_BASE_URL = fromEnv ?? defaultByPlatform;
