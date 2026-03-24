/**
 * CRE Enterprise Suite - iOS Native Integration Module
 * Push Notifications, Face ID, Camera, Offline Sync, Native Share
 * 
 * Add to: mobile/src/ios/iosIntegration.js
 */

import * as Notifications from 'expo-notifications';
import * as LocalAuthentication from 'expo-local-authentication';
import * as ImagePicker from 'expo-image-picker';
import * as Sharing from 'expo-sharing';
import * as FileSystem from 'expo-file-system';
import * as Linking from 'expo-linking';
import { Alert, Platform } from 'react-native';

// ============ PUSH NOTIFICATIONS ============

// Configure notification behavior
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: true,
    shouldShowBanner: true,
    shouldShowList: true,
  }),
});

class PushNotificationService {
  constructor() {
    this.token = null;
    this.listeners = [];
  }

  // Request notification permissions (iOS will prompt user)
  async requestPermissions() {
    const { status: existingStatus } = await Notifications.getPermissionsAsync();
    let finalStatus = existingStatus;
    
    if (existingStatus !== 'granted') {
      const { status } = await Notifications.requestPermissionsAsync();
      finalStatus = status;
    }
    
    if (finalStatus !== 'granted') {
      console.log('Notification permissions not granted');
      return false;
    }
    
    // Get Expo push token (works for both iOS and Android)
    if (Platform.OS === 'android') {
      await Notifications.setNotificationChannelAsync('cre-alerts', {
        name: 'CRE Alerts',
        importance: Notifications.AndroidImportance.HIGH,
        vibrationPattern: [0, 250, 250, 250],
        lightColor: '#3B82F6',
        sound: 'default',
      });
    }
    
    const { data: token } = await Notifications.getExpoPushTokenAsync({
      projectId: 'your-expo-project-id', // Replace with your Expo project ID
    });
    
    this.token = token;
    console.log('Push token:', token);
    return token;
  }

  // Register token with backend
  async registerTokenWithBackend(userId, token) {
    try {
      const response = await fetch(`${API_URL}/users/${userId}/push-token`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${global.token}`,
        },
        body: JSON.stringify({
          token,
          platform: Platform.OS,
          appVersion: '1.0.0',
        }),
      });
      return response.ok;
    } catch (error) {
      console.error('Failed to register push token:', error);
      return false;
    }
  }

  // Schedule a notification (e.g., lease expiring soon)
  async scheduleLeaseExpiryAlert(leaseEndDate, unitNumber, daysBeforeAlert = 30) {
    const alertDate = new Date(leaseEndDate);
    alertDate.setDate(alertDate.getDate() - daysBeforeAlert);
    
    if (alertDate <= new Date()) return; // Don't schedule past alerts
    
    await Notifications.scheduleNotificationAsync({
      content: {
        title: '🏢 Lease Expiring Soon',
        body: `Unit ${unitNumber} lease expires in ${daysBeforeAlert} days. Review and plan renewal.`,
        data: { type: 'lease_expiry', unitNumber, leaseEndDate },
        sound: 'default',
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.DATE,
        date: alertDate,
      },
    });
  }

  // Schedule a portfolio summary notification (e.g., every Monday 9am)
  async scheduleWeeklyPortfolioSummary() {
    // Cancel any existing weekly notification
    await Notifications.cancelAllScheduledNotificationsAsync();
    
    // Calculate next Monday 9am
    const now = new Date();
    const nextMonday = new Date(now);
    const dayOfWeek = now.getDay();
    const daysUntilMonday = (8 - dayOfWeek) % 7 || 7;
    nextMonday.setDate(now.getDate() + daysUntilMonday);
    nextMonday.setHours(9, 0, 0, 0);
    
    await Notifications.scheduleNotificationAsync({
      content: {
        title: '📊 Weekly Portfolio Summary',
        body: 'Your weekly CRE portfolio report is ready. Tap to view metrics and alerts.',
        data: { type: 'weekly_summary' },
        sound: 'default',
      },
      trigger: {
        type: Notifications.SchedulableTriggerInputTypes.WEEKLY,
        weekday: 2, // Monday
        hour: 9,
        minute: 0,
      },
    });
  }

  // Handle notification received while app is foregrounded
  addNotificationReceivedListener(callback) {
    const subscription = Notifications.addNotificationReceivedListener(notification => {
      callback(notification);
    });
    this.listeners.push(subscription);
    return subscription;
  }

  // Handle notification tapped
  addNotificationResponseListener(callback) {
    const subscription = Notifications.addNotificationResponseReceivedListener(response => {
      const data = response.notification.request.content.data;
      callback(data);
    });
    this.listeners.push(subscription);
    return subscription;
  }

  // Remove all listeners
  cleanup() {
    this.listeners.forEach(sub => sub.remove());
    this.listeners = [];
  }

  // Send test notification (local)
  async sendTestNotification() {
    await Notifications.scheduleNotificationAsync({
      content: {
        title: '🔔 CRE Toolkit Connected',
        body: 'Push notifications are working! You\'ll receive alerts for lease expirations and portfolio updates.',
        data: { type: 'test' },
      },
      trigger: null, // Immediate
    });
  }
}

// ============ BIOMETRIC AUTHENTICATION ============

class BiometricAuth {
  constructor() {
    this.isEnrolled = false;
    this.supportedType = null;
  }

  // Check if device supports biometrics
  async checkSupport() {
    const compatible = await LocalAuthentication.hasHardwareAsync();
    const enrolled = await LocalAuthentication.isEnrolledAsync();
    
    if (!compatible) {
      return { supported: false, reason: 'No biometric hardware' };
    }
    
    if (!enrolled) {
      return { supported: false, reason: 'No biometrics enrolled' };
    }
    
    const types = await LocalAuthentication.supportedAuthenticationTypesAsync();
    this.supportedType = types.includes(LocalAuthentication.AuthenticationType.FACIAL_RECOGNITION)
      ? 'Face ID'
      : 'Touch ID';
    
    this.isEnrolled = true;
    return { supported: true, type: this.supportedType };
  }

  // Authenticate with biometrics
  async authenticate(reason = 'Authenticate to access CRE Suite') {
    const support = await this.checkSupport();
    
    if (!support.supported) {
      // Fall back to PIN/passcode or just allow access
      return { success: true, method: 'fallback', message: support.reason };
    }
    
    try {
      const result = await LocalAuthentication.authenticateAsync({
        promptMessage: reason,
        fallbackLabel: 'Use Passcode',
        disableDeviceFallback: false,
        cancelLabel: 'Cancel',
      });
      
      return {
        success: result.success,
        method: support.type,
        message: result.success ? 'Authenticated' : 'Authentication failed',
      };
    } catch (error) {
      return {
        success: false,
        method: support.type,
        message: error.message,
      };
    }
  }

  // Store auth preference
  async setAuthPreference(userId, requireBiometric) {
    try {
      await fetch(`${API_URL}/users/${userId}/auth-preference`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${global.token}`,
        },
        body: JSON.stringify({ requireBiometric }),
      });
      return true;
    } catch {
      return false;
    }
  }
}

// ============ CAMERA & DOCUMENT SCANNING ============

class DocumentScanner {
  constructor() {
    this.permissionStatus = null;
  }

  async requestCameraPermission() {
    const { status } = await ImagePicker.requestCameraPermissionsAsync();
    this.permissionStatus = status;
    return status === 'granted';
  }

  // Take a photo of a document
  async takeDocumentPhoto() {
    const hasPermission = await this.requestCameraPermission();
    if (!hasPermission) {
      Alert.alert('Permission Required', 'Camera access is needed to scan documents.');
      return null;
    }

    const result = await ImagePicker.launchCameraAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
      aspect: [8.5, 11], // Letter paper ratio
    });

    if (!result.canceled && result.assets[0]) {
      return {
        uri: result.assets[0].uri,
        width: result.assets[0].width,
        height: result.assets[0].height,
        type: result.assets[0].type,
      };
    }
    return null;
  }

  // Pick image from gallery
  async pickImage() {
    const { status } = await ImagePicker.requestMediaLibraryPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert('Permission Required', 'Photo library access is needed.');
      return null;
    }

    const result = await ImagePicker.launchImageLibraryAsync({
      mediaTypes: ImagePicker.MediaTypeOptions.Images,
      allowsEditing: true,
      quality: 0.8,
    });

    if (!result.canceled && result.assets[0]) {
      return {
        uri: result.assets[0].uri,
        width: result.assets[0].width,
        height: result.assets[0].height,
      };
    }
    return null;
  }

  // Upload image to backend for OCR processing
  async uploadForOCR(imageUri, documentType = 'general') {
    try {
      const formData = new FormData();
      const filename = imageUri.split('/').pop();
      
      formData.append('file', {
        uri: imageUri,
        name: filename,
        type: 'image/jpeg',
      });
      formData.append('documentType', documentType);

      const response = await fetch(`${API_URL}/documents/ocr`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${global.token}`,
          // NOTE: Do NOT set Content-Type for FormData - browser sets it with boundary
        },
        body: formData,
      });

      if (!response.ok) throw new Error('OCR upload failed');
      return await response.json();
    } catch (error) {
      console.error('OCR upload error:', error);
      return null;
    }
  }
}

// ============ NATIVE SHARE SHEET ============

class NativeShare {
  // Share a memo as text
  async shareMemo(memoContent, propertyName) {
    try {
      const isAvailable = await Sharing.isAvailableAsync();
      if (!isAvailable) {
        // Fall back to system share
        await Linking.openURL(
          `mailto:?subject=${encodeURIComponent(`CRE Memo: ${propertyName}`)}&body=${encodeURIComponent(memoContent)}`
        );
        return true;
      }

      // Create temp file for sharing
      const filename = `CRE_Memo_${propertyName.replace(/\s+/g, '_')}_${Date.now()}.txt`;
      const fileUri = `${FileSystem.documentDirectory}${filename}`;
      
      await FileSystem.writeAsStringAsync(fileUri, memoContent, {
        encoding: FileSystem.EncodingType.UTF8,
      });

      await Sharing.shareAsync(fileUri, {
        mimeType: 'text/plain',
        dialogTitle: `Share Memo: ${propertyName}`,
      });

      // Cleanup
      await FileSystem.deleteAsync(fileUri, { idempotent: true });
      return true;
    } catch (error) {
      console.error('Share error:', error);
      return false;
    }
  }

  // Share valuation results
  async shareValuation(propertyName, metrics) {
    const text = `
📊 CRE Valuation Report
========================
Property: ${propertyName}
Date: ${new Date().toLocaleDateString()}

KEY METRICS:
• IRR: ${metrics.irr}%
• Cap Rate: ${metrics.capRate}%
• CoC: ${metrics.coc}%
• DSCR: ${metrics.dscr}

Generated by CRE Enterprise Suite
    `.trim();

    return this.shareMemo(text, propertyName);
  }
}

// ============ OFFLINE SYNC ============

class OfflineSync {
  constructor() {
    this.storageKey = 'cre_offline_cache';
    this.pendingActions = [];
  }

  // Save data to local storage
  async cacheData(key, data) {
    try {
      const cached = await FileSystem.readAsStringAsync(
        `${FileSystem.documentDirectory}${this.storageKey}_${key}.json`
      ).catch(() => '{}');
      
      const parsed = JSON.parse(cached);
      parsed[data.id || 'default'] = {
        ...data,
        cachedAt: new Date().toISOString(),
      };
      
      await FileSystem.writeAsStringAsync(
        `${FileSystem.documentDirectory}${this.storageKey}_${key}.json`,
        JSON.stringify(parsed)
      );
      return true;
    } catch (error) {
      console.error('Cache error:', error);
      return false;
    }
  }

  // Get cached data
  async getCachedData(key, id = 'default') {
    try {
      const cached = await FileSystem.readAsStringAsync(
        `${FileSystem.documentDirectory}${this.storageKey}_${key}.json`
      );
      const parsed = JSON.parse(cached);
      return parsed[id] || null;
    } catch {
      return null;
    }
  }

  // Queue an action for sync when online
  async queueAction(action) {
    this.pendingActions.push({
      ...action,
      queuedAt: new Date().toISOString(),
    });
    
    // Persist queue
    await FileSystem.writeAsStringAsync(
      `${FileSystem.documentDirectory}cre_pending_actions.json`,
      JSON.stringify(this.pendingActions)
    );
  }

  // Sync pending actions when back online
  async syncPendingActions() {
    if (this.pendingActions.length === 0) return { synced: 0 };
    
    const results = { synced: 0, failed: 0 };
    
    for (const action of this.pendingActions) {
      try {
        const response = await fetch(`${API_URL}${action.endpoint}`, {
          method: action.method || 'POST',
          headers: {
            'Content-Type': 'application/json',
            'Authorization': `Bearer ${global.token}`,
          },
          body: JSON.stringify(action.payload),
        });
        
        if (response.ok) {
          results.synced++;
        } else {
          results.failed++;
        }
      } catch {
        results.failed++;
      }
    }
    
    if (results.failed === 0) {
      this.pendingActions = [];
      await FileSystem.deleteAsync(
        `${FileSystem.documentDirectory}cre_pending_actions.json`,
        { idempotent: true }
      );
    }
    
    return results;
  }

  // Check network connectivity
  async isOnline() {
    try {
      const response = await fetch(`${API_URL}/health`, {
        method: 'GET',
        cache: 'no-cache',
      });
      return response.ok;
    } catch {
      return false;
    }
  }
}

// ============ iOS WIDGET DATA (WidgetKit ready) ============

class WidgetData {
  // Prepare data for iOS Widget
  async prepareWidgetData(userId) {
    try {
      const response = await fetch(`${API_URL}/users/${userId}/widget-data`, {
        headers: { 'Authorization': `Bearer ${global.token}` },
      });
      
      if (!response.ok) throw new Error('Failed to fetch widget data');
      
      const data = await response.json();
      
      // Save to shared container for WidgetKit
      // (Requires App Groups - see setup instructions)
      if (Platform.OS === 'ios') {
        // In a full implementation, use @react-native-async-storage/async-storage
        // or MMKV with App Groups for widget data sharing
        const AsyncStorage = require('@react-native-async-storage/async-storage').default;
        await AsyncStorage.setItem('widget_data', JSON.stringify(data));
      }
      
      return data;
    } catch (error) {
      console.error('Widget data error:', error);
      return null;
    }
  }
}

// ============ EXPORTS ============

export const pushNotifications = new PushNotificationService();
export const biometricAuth = new BiometricAuth();
export const documentScanner = new DocumentScanner();
export const nativeShare = new NativeShare();
export const offlineSync = new OfflineSync();
export const widgetData = new WidgetData();

// ============ USAGE EXAMPLE (add to App.js) ============
/*
import { pushNotifications, biometricAuth, documentScanner, nativeShare, offlineSync } from './src/ios/iosIntegration';

export default function App() {
  useEffect(() => {
    // 1. Request push notification permissions on login
    const setupNotifications = async () => {
      const token = await pushNotifications.requestPermissions();
      if (token) {
        await pushNotifications.registerTokenWithBackend(global.userId, token);
        await pushNotifications.scheduleWeeklyPortfolioSummary();
      }
    };
    
    // 2. Schedule lease expiry alerts
    const scheduleAlerts = async (rentRoll) => {
      for (const unit of rentRoll) {
        if (unit.leaseEnd) {
          await pushNotifications.scheduleLeaseExpiryAlert(
            unit.leaseEnd,
            unit.unitNumber,
            30
          );
        }
      }
    };
    
    // 3. Handle notification taps
    const notificationListener = pushNotifications.addNotificationResponseListener((data) => {
      if (data.type === 'lease_expiry') {
        navigation.navigate('RentRoll', { highlightUnit: data.unitNumber });
      } else if (data.type === 'weekly_summary') {
        navigation.navigate('Dashboard');
      }
    });
    
    setupNotifications();
    
    return () => {
      notificationListener.remove();
      pushNotifications.cleanup();
    };
  }, []);
}
*/
