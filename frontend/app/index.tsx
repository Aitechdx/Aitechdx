import React, { useState, useEffect, useRef } from 'react';
import {
  View,
  Text,
  TouchableOpacity,
  StyleSheet,
  SafeAreaView,
  Alert,
  Platform,
  Vibration,
} from 'react-native';
import { StatusBar } from 'expo-status-bar';
import * as Notifications from 'expo-notifications';
import { Audio } from 'expo-av';
import AsyncStorage from '@react-native-async-storage/async-storage';

// Configure notifications
Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true,
    shouldPlaySound: true,
    shouldSetBadge: false,
  }),
});

type TimerState = 'sitting' | 'activity' | 'paused';

export default function Index() {
  const [timerState, setTimerState] = useState<TimerState>('sitting');
  const [timeRemaining, setTimeRemaining] = useState(50 * 60); // 50 minutes in seconds
  const [isRunning, setIsRunning] = useState(false);
  const [dailySessions, setDailySessions] = useState(0);
  const [currentCycle, setCurrentCycle] = useState(1);
  
  const intervalRef = useRef<NodeJS.Timeout | null>(null);
  const soundRef = useRef<Audio.Sound | null>(null);

  // Request notification permissions on app start
  useEffect(() => {
    requestNotificationPermissions();
    loadDailyProgress();
    loadAudioAlert();
  }, []);

  // Timer logic
  useEffect(() => {
    if (isRunning && timeRemaining > 0) {
      intervalRef.current = setInterval(() => {
        setTimeRemaining((prev) => {
          if (prev <= 1) {
            handleTimerComplete();
            return 0;
          }
          return prev - 1;
        });
      }, 1000);
    } else {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isRunning, timeRemaining]);

  const requestNotificationPermissions = async () => {
    const { status } = await Notifications.requestPermissionsAsync();
    if (status !== 'granted') {
      Alert.alert(
        'Permissions Required',
        'Please enable notifications to receive health reminders.',
        [{ text: 'OK' }]
      );
    }
  };

  const loadAudioAlert = async () => {
    try {
      const { sound } = await Audio.Sound.createAsync(
        { uri: 'https://www.soundjay.com/misc/sounds/bell-ringing-05.wav' },
        { shouldPlay: false }
      );
      soundRef.current = sound;
    } catch (error) {
      console.log('Audio loading failed:', error);
    }
  };

  const loadDailyProgress = async () => {
    try {
      const today = new Date().toDateString();
      const storedDate = await AsyncStorage.getItem('lastSessionDate');
      const storedSessions = await AsyncStorage.getItem('dailySessions');
      
      if (storedDate === today && storedSessions) {
        setDailySessions(parseInt(storedSessions));
      } else {
        setDailySessions(0);
        await AsyncStorage.setItem('lastSessionDate', today);
        await AsyncStorage.setItem('dailySessions', '0');
      }
    } catch (error) {
      console.log('Error loading progress:', error);
    }
  };

  const saveDailyProgress = async (sessions: number) => {
    try {
      const today = new Date().toDateString();
      await AsyncStorage.setItem('lastSessionDate', today);
      await AsyncStorage.setItem('dailySessions', sessions.toString());
    } catch (error) {
      console.log('Error saving progress:', error);
    }
  };

  const handleTimerComplete = async () => {
    setIsRunning(false);
    
    // Play sound alert
    if (soundRef.current) {
      try {
        await soundRef.current.replayAsync();
      } catch (error) {
        console.log('Sound play failed:', error);
      }
    }
    
    // Vibrate
    if (Platform.OS === 'ios') {
      Vibration.vibrate([500, 200, 500]);
    } else {
      Vibration.vibrate(1000);
    }

    if (timerState === 'sitting') {
      // Switch to activity break
      setTimerState('activity');
      setTimeRemaining(10 * 60); // 10 minutes
      
      await Notifications.scheduleNotificationAsync({
        content: {
          title: '🚶 Time to Move!',
          body: 'Stand up and take a 10-minute activity break. Walk around, stretch, or do light exercises.',
          sound: true,
        },
        trigger: null,
      });

      Alert.alert(
        '🚶 Time to Stand Up!',
        'You\'ve been sitting for 50 minutes. Time for a 10-minute activity break!\n\n• Walk around the house\n• Do light stretching\n• Move your arms and legs',
        [
          { text: 'Start Activity Break', onPress: () => setIsRunning(true) }
        ]
      );
    } else {
      // Activity break complete, back to sitting
      const newSessions = dailySessions + 1;
      setDailySessions(newSessions);
      saveDailyProgress(newSessions);
      
      setTimerState('sitting');
      setTimeRemaining(50 * 60); // 50 minutes
      setCurrentCycle(currentCycle + 1);
      
      await Notifications.scheduleNotificationAsync({
        content: {
          title: '✅ Great Job!',
          body: 'Activity break complete! You can sit down now. The next reminder will be in 50 minutes.',
          sound: true,
        },
        trigger: null,
      });

      Alert.alert(
        '✅ Well Done!',
        `Great job completing your activity break!\n\nYou can sit down now. Your next movement reminder will be in 50 minutes.\n\nDaily sessions completed: ${newSessions}`,
        [
          { text: 'Continue', onPress: () => setIsRunning(true) }
        ]
      );
    }
  };

  const startTimer = () => {
    setIsRunning(true);
  };

  const pauseTimer = () => {
    setIsRunning(false);
  };

  const resetTimer = () => {
    setIsRunning(false);
    if (timerState === 'sitting') {
      setTimeRemaining(50 * 60);
    } else {
      setTimeRemaining(10 * 60);
    }
  };

  const formatTime = (seconds: number) => {
    const minutes = Math.floor(seconds / 60);
    const remainingSeconds = seconds % 60;
    return `${minutes.toString().padStart(2, '0')}:${remainingSeconds.toString().padStart(2, '0')}`;
  };

  const getTimerTitle = () => {
    if (timerState === 'sitting') {
      return 'Sitting Time';
    } else {
      return 'Activity Break';
    }
  };

  const getActivitySuggestion = () => {
    if (timerState === 'activity') {
      const suggestions = [
        '🚶 Walk around your home',
        '🤸 Do gentle stretches',
        '💪 Move your arms and legs',
        '🌅 Look out the window',
        '🧘 Take deep breaths'
      ];
      return suggestions[Math.floor(Math.random() * suggestions.length)];
    }
    return '';
  };

  return (
    <SafeAreaView style={styles.container}>
      <StatusBar style="light" />
      
      {/* Header */}
      <View style={styles.header}>
        <Text style={styles.headerTitle}>Health Reminder</Text>
        <Text style={styles.headerSubtitle}>Cycle {currentCycle} • Today: {dailySessions} completed</Text>
      </View>

      {/* Main Timer Display */}
      <View style={styles.timerContainer}>
        <Text style={styles.timerLabel}>{getTimerTitle()}</Text>
        <Text style={[
          styles.timerText,
          { color: timerState === 'sitting' ? '#4A90E2' : '#E85D75' }
        ]}>
          {formatTime(timeRemaining)}
        </Text>
        
        {timerState === 'activity' && (
          <Text style={styles.activitySuggestion}>
            {getActivitySuggestion()}
          </Text>
        )}
      </View>

      {/* Control Buttons */}
      <View style={styles.buttonContainer}>
        {!isRunning ? (
          <TouchableOpacity
            style={[styles.button, styles.startButton]}
            onPress={startTimer}
          >
            <Text style={styles.buttonText}>
              {timeRemaining === (timerState === 'sitting' ? 50 * 60 : 10 * 60) ? 'Start' : 'Resume'}
            </Text>
          </TouchableOpacity>
        ) : (
          <TouchableOpacity
            style={[styles.button, styles.pauseButton]}
            onPress={pauseTimer}
          >
            <Text style={styles.buttonText}>Pause</Text>
          </TouchableOpacity>
        )}
        
        <TouchableOpacity
          style={[styles.button, styles.resetButton]}
          onPress={resetTimer}
        >
          <Text style={styles.buttonText}>Reset</Text>
        </TouchableOpacity>
      </View>

      {/* Instructions */}
      <View style={styles.instructionsContainer}>
        <Text style={styles.instructionsTitle}>How it works:</Text>
        <Text style={styles.instructionsText}>
          • Sit for 50 minutes, then get a reminder{'\n'}
          • Take a 10-minute activity break{'\n'}
          • Repeat throughout your day{'\n'}
          • Track your daily progress
        </Text>
      </View>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#1A1A1A',
    padding: 20,
  },
  header: {
    alignItems: 'center',
    marginBottom: 40,
    marginTop: 20,
  },
  headerTitle: {
    fontSize: 32,
    fontWeight: 'bold',
    color: '#FFFFFF',
    marginBottom: 8,
  },
  headerSubtitle: {
    fontSize: 18,
    color: '#B0B0B0',
  },
  timerContainer: {
    alignItems: 'center',
    marginBottom: 60,
    backgroundColor: '#2A2A2A',
    borderRadius: 20,
    padding: 40,
    marginHorizontal: 10,
  },
  timerLabel: {
    fontSize: 24,
    color: '#FFFFFF',
    marginBottom: 10,
    fontWeight: '600',
  },
  timerText: {
    fontSize: 72,
    fontWeight: 'bold',
    fontFamily: Platform.OS === 'ios' ? 'Menlo' : 'monospace',
    marginBottom: 20,
  },
  activitySuggestion: {
    fontSize: 20,
    color: '#FFA500',
    textAlign: 'center',
    fontWeight: '500',
  },
  buttonContainer: {
    flexDirection: 'row',
    justifyContent: 'space-around',
    marginBottom: 40,
    paddingHorizontal: 20,
  },
  button: {
    paddingVertical: 18,
    paddingHorizontal: 30,
    borderRadius: 15,
    minWidth: 120,
    alignItems: 'center',
  },
  startButton: {
    backgroundColor: '#4CAF50',
  },
  pauseButton: {
    backgroundColor: '#FF9800',
  },
  resetButton: {
    backgroundColor: '#607D8B',
  },
  buttonText: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: 'bold',
  },
  instructionsContainer: {
    backgroundColor: '#2A2A2A',
    borderRadius: 15,
    padding: 20,
    marginHorizontal: 10,
  },
  instructionsTitle: {
    fontSize: 22,
    color: '#FFFFFF',
    fontWeight: 'bold',
    marginBottom: 12,
  },
  instructionsText: {
    fontSize: 18,
    color: '#B0B0B0',
    lineHeight: 26,
  },
});