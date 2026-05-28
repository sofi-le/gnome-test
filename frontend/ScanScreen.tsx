import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, SafeAreaView, StatusBar, Dimensions } from 'react-native';
import { useFonts } from 'expo-font';
import { InriaSerif_400Regular, InriaSerif_700Bold } from '@expo-google-fonts/inria-serif';
import BottomNav, { TabKey } from './BottomNav';

const C = {
  bg:        '#F7F6F2',
  surface:   '#FFFFFF',
  primary:   '#1A1B14',
  secondary: '#686760',
  green:     '#44A353',
  olive:     '#363E28',
  lightGreen:'#EEF2E9',
  border:    '#E5E2DB',
  lightOlive:'#DAE4CF',
};

const { width: W } = Dimensions.get('window');

interface Props {
  onTabPress: (tab: TabKey) => void;
}

export default function ScanScreen({ onTabPress }: Props) {
  const [fontsLoaded] = useFonts({ InriaSerif_400Regular, InriaSerif_700Bold });
  const serif     = fontsLoaded ? 'InriaSerif_400Regular' : undefined;
  const serifBold = fontsLoaded ? 'InriaSerif_700Bold'    : undefined;

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={C.bg} />

      <View style={styles.header}>
        <Text style={[styles.title, { fontFamily: serifBold }]}>Scan</Text>
      </View>

      <View style={styles.body}>
        {/* Scan frame */}
        <View style={styles.scanFrame}>
          <View style={[styles.corner, styles.tl]} />
          <View style={[styles.corner, styles.tr]} />
          <View style={[styles.corner, styles.bl]} />
          <View style={[styles.corner, styles.br]} />
          {/* Scan line placeholder */}
          <View style={styles.scanLine} />
          <Text style={[styles.scanHint, { fontFamily: serif }]}>
            Point camera at{'\n'}your DNA report QR code
          </Text>
        </View>

        <Text style={[styles.heading, { fontFamily: serifBold }]}>Scan a Report QR Code</Text>
        <Text style={[styles.sub, { fontFamily: serif }]}>
          Quickly load results shared by your healthcare provider or from another device.
        </Text>

        <View style={styles.dividerRow}>
          <View style={styles.dividerLine} />
          <Text style={[styles.dividerText, { fontFamily: serif }]}>or</Text>
          <View style={styles.dividerLine} />
        </View>

        <TouchableOpacity style={styles.uploadBtn} activeOpacity={0.8}>
          <Text style={[styles.uploadBtnText, { fontFamily: serifBold }]}>Enter Code Manually</Text>
        </TouchableOpacity>
      </View>

      <BottomNav activeTab="scan" onTabPress={onTabPress} />
    </SafeAreaView>
  );
}

const FRAME = W - 100;

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  header: { paddingHorizontal: 18, paddingTop: 16, paddingBottom: 8 },
  title:  { fontSize: 21, color: '#1A1B14' },
  body: {
    flex: 1,
    alignItems: 'center',
    paddingHorizontal: 24,
    paddingTop: 20,
  },
  scanFrame: {
    width: FRAME,
    height: FRAME,
    borderRadius: 16,
    backgroundColor: C.lightOlive,
    marginBottom: 28,
    alignItems: 'center',
    justifyContent: 'center',
    position: 'relative',
  },
  corner: {
    position: 'absolute',
    width: 24,
    height: 24,
    borderColor: C.olive,
    borderWidth: 3,
  },
  tl: { top: 14, left: 14,  borderRightWidth: 0, borderBottomWidth: 0, borderTopLeftRadius: 6  },
  tr: { top: 14, right: 14, borderLeftWidth: 0,  borderBottomWidth: 0, borderTopRightRadius: 6 },
  bl: { bottom: 14, left: 14,  borderRightWidth: 0, borderTopWidth: 0, borderBottomLeftRadius: 6  },
  br: { bottom: 14, right: 14, borderLeftWidth: 0,  borderTopWidth: 0, borderBottomRightRadius: 6 },
  scanLine: {
    width: FRAME - 40,
    height: 2,
    backgroundColor: C.green,
    borderRadius: 1,
    opacity: 0.6,
  },
  scanHint: {
    position: 'absolute',
    bottom: 16,
    fontSize: 10,
    color: C.olive,
    textAlign: 'center',
    opacity: 0.7,
  },
  heading: { fontSize: 17, color: '#1A1B14', marginBottom: 8, textAlign: 'center' },
  sub: { fontSize: 12, color: '#686760', textAlign: 'center', lineHeight: 18, marginBottom: 20 },
  dividerRow: { flexDirection: 'row', alignItems: 'center', gap: 10, marginBottom: 20, width: '100%' },
  dividerLine: { flex: 1, height: StyleSheet.hairlineWidth, backgroundColor: C.border },
  dividerText: { fontSize: 11, color: '#A6A59F' },
  uploadBtn: {
    width: '100%',
    height: 48,
    backgroundColor: C.olive,
    borderRadius: 12,
    alignItems: 'center',
    justifyContent: 'center',
  },
  uploadBtnText: { fontSize: 14, color: '#fff' },
});
