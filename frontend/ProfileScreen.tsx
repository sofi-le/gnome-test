import React from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  SafeAreaView, StatusBar, Dimensions,
} from 'react-native';
import { useFonts } from 'expo-font';
import { InriaSerif_400Regular, InriaSerif_700Bold } from '@expo-google-fonts/inria-serif';
import BottomNav, { TabKey } from './BottomNav';

const C = {
  bg:        '#F7F6F2',
  surface:   '#FFFFFF',
  primary:   '#1A1B14',
  secondary: '#686760',
  light:     '#A6A59F',
  green:     '#44A353',
  olive:     '#363E28',
  lightGreen:'#EEF2E9',
  lightOlive:'#DAE4CF',
  border:    '#E5E2DB',
  red:       '#EB412A',
};

const { width: W } = Dimensions.get('window');

const SETTINGS = [
  { section: 'Account',  items: ['Edit Profile', 'Change Email', 'Privacy Settings'] },
  { section: 'Data',     items: ['Download My Data', 'Delete My Data', 'Re-upload DNA File'] },
  { section: 'App',      items: ['Notifications', 'Appearance', 'About G-Nome'] },
];

interface Props {
  onTabPress: (tab: TabKey) => void;
}

export default function ProfileScreen({ onTabPress }: Props) {
  const [fontsLoaded] = useFonts({ InriaSerif_400Regular, InriaSerif_700Bold });
  const serif     = fontsLoaded ? 'InriaSerif_400Regular' : undefined;
  const serifBold = fontsLoaded ? 'InriaSerif_700Bold'    : undefined;

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={C.bg} />

      <ScrollView showsVerticalScrollIndicator={false} contentContainerStyle={styles.content}>

        {/* ── Header ─────────────────────────────────────────────────── */}
        <View style={styles.header}>
          <Text style={[styles.pageTitle, { fontFamily: serifBold }]}>Profile</Text>
        </View>

        {/* ── Avatar + name card ──────────────────────────────────────── */}
        <View style={styles.profileCard}>
          <View style={styles.avatar}>
            <Text style={[styles.avatarInitial, { fontFamily: serifBold }]}>A</Text>
          </View>
          <View style={{ flex: 1 }}>
            <Text style={[styles.name, { fontFamily: serifBold }]}>Alex Johnson</Text>
            <Text style={[styles.email, { fontFamily: serif }]}>alex@example.com</Text>
          </View>
          <TouchableOpacity style={styles.editBtn} activeOpacity={0.7}>
            <Text style={[styles.editBtnText, { fontFamily: serifBold }]}>Edit</Text>
          </TouchableOpacity>
        </View>

        {/* ── Health score summary ────────────────────────────────────── */}
        <View style={styles.statsRow}>
          {[
            { val: '72',   label: 'Health Score',  color: C.green },
            { val: '4M+',  label: 'SNPs Analyzed', color: C.olive },
            { val: '3',    label: 'Reports Ready',  color: '#4A90F9' },
          ].map(s => (
            <View key={s.label} style={styles.statBox}>
              <Text style={[styles.statVal, { fontFamily: serifBold, color: s.color }]}>{s.val}</Text>
              <Text style={[styles.statLabel, { fontFamily: serif }]}>{s.label}</Text>
            </View>
          ))}
        </View>

        {/* ── DNA file info ───────────────────────────────────────────── */}
        <View style={styles.dnaCard}>
          <View style={[styles.dnaAccent, { backgroundColor: C.green }]} />
          <View style={styles.dnaContent}>
            <Text style={[styles.dnaTitle, { fontFamily: serifBold }]}>DNA File</Text>
            <Text style={[styles.dnaSource, { fontFamily: serif }]}>Source: 23andMe</Text>
            <Text style={[styles.dnaDate, { fontFamily: serif }]}>Uploaded: May 28, 2026</Text>
          </View>
          <View style={styles.dnaBadge}>
            <Text style={[styles.dnaBadgeText, { fontFamily: serifBold }]}>ACTIVE</Text>
          </View>
        </View>

        {/* ── Settings sections ───────────────────────────────────────── */}
        {SETTINGS.map(section => (
          <View key={section.section} style={styles.settingsSection}>
            <Text style={[styles.sectionLabel, { fontFamily: serifBold }]}>{section.section}</Text>
            <View style={styles.settingsCard}>
              {section.items.map((item, i) => (
                <TouchableOpacity
                  key={item}
                  style={[
                    styles.settingsRow,
                    i < section.items.length - 1 && styles.settingsRowBorder,
                  ]}
                  activeOpacity={0.6}
                >
                  <Text style={[styles.settingsItem, { fontFamily: serif }]}>{item}</Text>
                  <Text style={[styles.chevron, { fontFamily: serif }]}>›</Text>
                </TouchableOpacity>
              ))}
            </View>
          </View>
        ))}

        {/* ── Sign out ────────────────────────────────────────────────── */}
        <TouchableOpacity style={styles.signOutBtn} activeOpacity={0.7}>
          <Text style={[styles.signOutText, { fontFamily: serifBold }]}>Sign Out</Text>
        </TouchableOpacity>

        <View style={{ height: 16 }} />
      </ScrollView>

      <BottomNav activeTab="profile" onTabPress={onTabPress} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root:    { flex: 1, backgroundColor: C.bg },
  content: { paddingHorizontal: 18, paddingBottom: 16 },

  header:    { paddingTop: 16, paddingBottom: 12 },
  pageTitle: { fontSize: 21, color: C.primary },

  // Profile card
  profileCard: {
    backgroundColor: C.surface,
    borderRadius: 14,
    padding: 16,
    flexDirection: 'row',
    alignItems: 'center',
    gap: 14,
    marginBottom: 12,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.07,
    shadowRadius: 12,
    elevation: 3,
  },
  avatar: {
    width: 52,
    height: 52,
    borderRadius: 26,
    backgroundColor: C.lightOlive,
    alignItems: 'center',
    justifyContent: 'center',
  },
  avatarInitial: { fontSize: 22, color: C.olive },
  name:  { fontSize: 16, color: C.primary, marginBottom: 2 },
  email: { fontSize: 11, color: C.secondary },
  editBtn: {
    backgroundColor: C.lightGreen,
    borderRadius: 8,
    paddingHorizontal: 12,
    paddingVertical: 6,
  },
  editBtnText: { fontSize: 11, color: C.green },

  // Stats
  statsRow: { flexDirection: 'row', gap: 10, marginBottom: 12 },
  statBox: {
    flex: 1,
    backgroundColor: C.surface,
    borderRadius: 12,
    paddingVertical: 14,
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  statVal:   { fontSize: 20 },
  statLabel: { fontSize: 8, color: C.secondary, marginTop: 3, textAlign: 'center' },

  // DNA card
  dnaCard: {
    backgroundColor: C.surface,
    borderRadius: 12,
    flexDirection: 'row',
    overflow: 'hidden',
    marginBottom: 18,
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.06,
    shadowRadius: 10,
    elevation: 2,
  },
  dnaAccent:  { width: 4 },
  dnaContent: { flex: 1, padding: 12 },
  dnaTitle:   { fontSize: 13, color: C.primary, marginBottom: 2 },
  dnaSource:  { fontSize: 10, color: C.secondary },
  dnaDate:    { fontSize: 10, color: C.secondary },
  dnaBadge: {
    backgroundColor: C.lightGreen,
    margin: 12,
    borderRadius: 6,
    paddingHorizontal: 8,
    paddingVertical: 4,
    alignSelf: 'center',
  },
  dnaBadgeText: { fontSize: 8, color: C.green },

  // Settings
  settingsSection: { marginBottom: 14 },
  sectionLabel: {
    fontSize: 10,
    color: C.secondary,
    marginBottom: 6,
    letterSpacing: 0.3,
  },
  settingsCard: {
    backgroundColor: C.surface,
    borderRadius: 12,
    overflow: 'hidden',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.05,
    shadowRadius: 8,
    elevation: 2,
  },
  settingsRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 14,
    paddingVertical: 13,
  },
  settingsRowBorder: {
    borderBottomWidth: StyleSheet.hairlineWidth,
    borderBottomColor: C.border,
  },
  settingsItem: { fontSize: 13, color: C.primary },
  chevron:      { fontSize: 18, color: C.light },

  // Sign out
  signOutBtn: {
    height: 46,
    borderRadius: 12,
    borderWidth: 1.5,
    borderColor: C.red,
    alignItems: 'center',
    justifyContent: 'center',
    marginTop: 4,
    marginBottom: 8,
  },
  signOutText: { fontSize: 14, color: C.red },
});
