import React, { useState } from 'react';
import { View, StyleSheet, StatusBar, Platform, Alert } from 'react-native';
import { AppProvider, useApp } from './lib/AppContext';
import UploadScreen from './UploadScreen';
import ProcessingScreen from './ProcessingScreen';
import DashboardScreen from './DashboardScreen';
import ReportsScreen from './ReportsScreen';
import TreeScreen from './TreeScreen';
import ScanScreen from './ScanScreen';
import ProfileScreen from './ProfileScreen';
import { TabKey } from './BottomNav';

type AppScreen = 'upload' | 'processing' | 'main';

function AppInner() {
  const { error, reset } = useApp();
  const [appScreen, setAppScreen] = useState<AppScreen>('upload');
  const [activeTab,  setActiveTab]  = useState<TabKey>('home');
  const [reportTab,  setReportTab]  = useState(0);

  // Show error alert if report generation failed but still navigate to dashboard
  React.useEffect(() => {
    if (error && appScreen === 'main') {
      Alert.alert(
        'Report issue',
        'Some results may be incomplete: ' + error,
        [{ text: 'OK' }],
      );
    }
  }, [error, appScreen]);

  const handleTabPress = (tab: TabKey) => setActiveTab(tab);

  const handleOpenReport = (tab: number) => {
    setReportTab(tab);
    setActiveTab('reports');
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="dark-content" backgroundColor="#F7F6F2" />

      {appScreen === 'upload' && (
        <UploadScreen
          onFileSelected={() => setTimeout(() => setAppScreen('processing'), 400)}
        />
      )}

      {appScreen === 'processing' && (
        <ProcessingScreen onDone={() => setAppScreen('main')} />
      )}

      {appScreen === 'main' && (
        <>
          {activeTab === 'home' && (
            <DashboardScreen onOpenReport={handleOpenReport} onTabPress={handleTabPress} />
          )}
          {activeTab === 'tree' && (
            <TreeScreen onTabPress={handleTabPress} />
          )}
          {activeTab === 'reports' && (
            <ReportsScreen initialTab={reportTab} onTabPress={handleTabPress} />
          )}
          {activeTab === 'scan' && (
            <ScanScreen onTabPress={handleTabPress} />
          )}
          {activeTab === 'profile' && (
            <ProfileScreen onTabPress={handleTabPress} />
          )}
        </>
      )}
    </View>
  );
}

export default function App() {
  return (
    <AppProvider>
      <AppInner />
    </AppProvider>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#F7F6F2',
    paddingTop: Platform.OS === 'android' ? StatusBar.currentHeight : 0,
  },
});
