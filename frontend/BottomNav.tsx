import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity } from 'react-native';
import { useFonts } from 'expo-font';
import { InriaSerif_400Regular, InriaSerif_700Bold } from '@expo-google-fonts/inria-serif';

const C = {
  surface:   '#FFFFFF',
  green:     '#44A353',
  secondary: '#686760',
  border:    '#E5E2DB',
  light:     '#A6A59F',
};

export type TabKey = 'home' | 'tree' | 'reports' | 'scan' | 'profile';

const TABS: { key: TabKey; label: string; shape: 'house' | 'tree' | 'doc' | 'scan' | 'person' }[] = [
  { key: 'home',    label: 'Home',    shape: 'house'  },
  { key: 'tree',    label: 'Tree',    shape: 'tree'   },
  { key: 'reports', label: 'Reports', shape: 'doc'    },
  { key: 'scan',    label: 'Scan',    shape: 'scan'   },
  { key: 'profile', label: 'Profile', shape: 'person' },
];

// Simple icon shapes built from Views — no external icon library needed
function NavIcon({ shape, active }: { shape: string; active: boolean }) {
  const col = active ? C.green : C.light;
  switch (shape) {
    case 'house':
      return (
        <View style={{ alignItems: 'center', width: 20, height: 18 }}>
          {/* roof */}
          <View style={{ width: 0, height: 0, borderLeftWidth: 10, borderRightWidth: 10,
            borderBottomWidth: 8, borderLeftColor: 'transparent',
            borderRightColor: 'transparent', borderBottomColor: col }} />
          {/* walls */}
          <View style={{ width: 14, height: 9, backgroundColor: col, borderRadius: 1 }} />
        </View>
      );
    case 'tree':
      return (
        <View style={{ alignItems: 'center', width: 20, height: 18 }}>
          <View style={{ width: 14, height: 11, borderRadius: 7, backgroundColor: col }} />
          <View style={{ width: 3, height: 7, backgroundColor: col, marginTop: 0, borderRadius: 1 }} />
        </View>
      );
    case 'doc':
      return (
        <View style={{ width: 14, height: 18, backgroundColor: col, borderRadius: 3,
          justifyContent: 'center', alignItems: 'center' }}>
          {[0, 1, 2].map(i => (
            <View key={i} style={{ width: 8, height: 1.5, backgroundColor: '#fff',
              borderRadius: 1, marginBottom: i < 2 ? 2 : 0 }} />
          ))}
        </View>
      );
    case 'scan':
      return (
        <View style={{ width: 18, height: 18, borderWidth: 2, borderColor: col,
          borderRadius: 4, justifyContent: 'center', alignItems: 'center' }}>
          <View style={{ width: 10, height: 1.5, backgroundColor: col, borderRadius: 1 }} />
        </View>
      );
    case 'person':
      return (
        <View style={{ alignItems: 'center', width: 20, height: 18 }}>
          <View style={{ width: 10, height: 10, borderRadius: 5, backgroundColor: col }} />
          <View style={{ width: 16, height: 7, borderTopLeftRadius: 8, borderTopRightRadius: 8,
            backgroundColor: col, marginTop: 1 }} />
        </View>
      );
    default:
      return <View style={{ width: 16, height: 16, borderRadius: 4, backgroundColor: col }} />;
  }
}

interface Props {
  activeTab: TabKey;
  onTabPress: (tab: TabKey) => void;
}

export default function BottomNav({ activeTab, onTabPress }: Props) {
  const [fontsLoaded] = useFonts({ InriaSerif_400Regular, InriaSerif_700Bold });
  const serif     = fontsLoaded ? 'InriaSerif_400Regular' : undefined;
  const serifBold = fontsLoaded ? 'InriaSerif_700Bold'    : undefined;

  return (
    <View style={styles.bar}>
      {TABS.map(t => {
        const active = t.key === activeTab;
        return (
          <TouchableOpacity
            key={t.key}
            style={styles.tab}
            onPress={() => onTabPress(t.key)}
            activeOpacity={0.7}
          >
            <NavIcon shape={t.shape} active={active} />
            <Text style={[styles.label, {
              fontFamily: active ? serifBold : serif,
              color: active ? C.green : C.secondary,
            }]}>
              {t.label}
            </Text>
          </TouchableOpacity>
        );
      })}
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    backgroundColor: C.surface,
    borderTopWidth: StyleSheet.hairlineWidth,
    borderTopColor: C.border,
    paddingBottom: 8,
    paddingTop: 10,
  },
  tab: {
    flex: 1,
    alignItems: 'center',
    gap: 4,
  },
  label: {
    fontSize: 8,
  },
});
