import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Image, SafeAreaView, StatusBar, Dimensions,
} from 'react-native';
import { useFonts } from 'expo-font';
import { InriaSerif_400Regular, InriaSerif_700Bold } from '@expo-google-fonts/inria-serif';
import BottomNav, { TabKey } from './BottomNav';
import { useApp } from './lib/AppContext';
import { RiskCondition } from './lib/types';

const C = {
  bg:            '#F7F6F2',
  surface:       '#FFFFFF',
  textPrimary:   '#1A1B14',
  textSecondary: '#686760',
  textLight:     '#A6A59F',
  green:         '#44A353',
  olive:         '#363E28',
  red:           '#EB412A',
  amber:         '#F5A62B',
  border:        '#E5E2DB',
  lightGreen:    '#EEF2E9',
};

const { width: SCREEN_W } = Dimensions.get('window');

// Badge color from risk tier
function riskAccent(tier?: string): string {
  switch (tier) {
    case 'high':     return C.red;
    case 'moderate': return C.amber;
    case 'low':      return '#4A90F9';
    default:         return C.green;
  }
}

function riskBadgeLabel(tier?: string, label?: string): string {
  if (label) return label.toUpperCase();
  switch (tier) {
    case 'high':     return 'HIGH RISK';
    case 'moderate': return 'ELEVATED';
    case 'average':  return 'AVERAGE';
    case 'low':      return 'LOW';
    default:         return 'UNKNOWN';
  }
}

const REPORT_TABS: { key: number; accent: string }[] = [
  { key: 0, accent: C.amber  },
  { key: 1, accent: C.red    },
  { key: 2, accent: C.red    },
  { key: 3, accent: '#4A90F9'},
  { key: 4, accent: C.green  },
];

interface Props {
  onOpenReport?: (tab: number) => void;
  onTabPress?: (tab: TabKey) => void;
}

export default function DashboardScreen({ onOpenReport, onTabPress }: Props) {
  const [fontsLoaded] = useFonts({ InriaSerif_400Regular, InriaSerif_700Bold });
  const [healthScoreExpanded, setHealthScoreExpanded] = useState(false);
  const { report, parseResult, healthScore, dominantAncestry } = useApp();

  const serif     = fontsLoaded ? 'InriaSerif_400Regular' : undefined;
  const serifBold = fontsLoaded ? 'InriaSerif_700Bold'    : undefined;

  // — Derived data —
  const conditions = report?.disease_risk.conditions ?? [];
  const computedConditions = conditions.filter(c => c.status === 'computed' && c.percentile != null);

  // Top priority = highest percentile (most at risk)
  const topPriority: RiskCondition | null =
    computedConditions.length > 0
      ? [...computedConditions].sort((a, b) => (b.percentile ?? 0) - (a.percentile ?? 0))[0]
      : null;

  const topPercentile = topPriority?.percentile ?? 72;

  const pgx    = report?.pharmacogenomics;
  const carrier = report?.carrier_status;
  const traits  = report?.nutrition_traits;

  const reportRows = [
    { label: 'Drugs',    subtitle: pgx    ? `${pgx.summary.genes_tested} genes tested`          : '—', accent: C.amber,   tab: 0 },
    { label: 'Risk',     subtitle: pgx    ? `${computedConditions.length} conditions assessed`   : '—', accent: C.red,     tab: 1 },
    { label: 'Carrier',  subtitle: carrier ? `${carrier.conditions_tested} conditions screened`  : '—', accent: '#9966FE', tab: 2 },
    { label: 'Traits',   subtitle: traits  ? `${traits.total_tested} traits analyzed`            : '—', accent: '#4A90F9', tab: 3 },
    { label: 'Ancestry', subtitle: dominantAncestry !== 'Unknown' ? dominantAncestry            : '—', accent: C.green,   tab: 4 },
  ];

  const source = parseResult?.source ?? 'DNA file';
  const snpCount = parseResult?.snp_count;

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={C.bg} />

      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent} showsVerticalScrollIndicator={false}>

        {/* ── Header ──────────────────────────────────────────────────── */}
        <View style={styles.header}>
          <View>
            <Text style={[styles.greeting, { fontFamily: serifBold }]}>Good morning, Alex</Text>
            {snpCount && (
              <Text style={[styles.subGreeting, { fontFamily: serif }]}>
                {snpCount.toLocaleString()} SNPs · {source}
              </Text>
            )}
          </View>
          <Image source={require('./assets/images/small gene tree.png')} style={styles.leafDecor} resizeMode="contain" />
        </View>

        {/* ── Health Score card ───────────────────────────────────────── */}
        <View style={styles.card}>
          <View style={styles.scoreHeader}>
            <Text style={[styles.sectionLabel, { fontFamily: serif }]}>Your Health Score</Text>
            <TouchableOpacity onPress={() => setHealthScoreExpanded(!healthScoreExpanded)}>
              <Text style={[styles.infoIcon, { fontFamily: serif }]}>ⓘ</Text>
            </TouchableOpacity>
          </View>
          <View style={styles.scoreRow}>
            <Text style={[styles.scoreNum, { fontFamily: serifBold }]}>{healthScore}</Text>
            <Text style={[styles.scoreOf,  { fontFamily: serif }]}> /100</Text>
          </View>
          <Text style={[styles.percentile, { fontFamily: serif }]}>
            {topPercentile.toFixed(0)}th percentile
            {dominantAncestry !== 'Unknown' ? ` · ${dominantAncestry} ancestry` : ''}
          </Text>
          <View style={styles.barTrack}>
            <View style={[styles.barFill, { width: `${healthScore}%` }]} />
            <View style={[styles.barDot,  { left: `${healthScore}%`, marginLeft: -5.5 }]} />
          </View>
          {healthScoreExpanded && (
            <View style={styles.infoSection}>
              <Text style={[styles.infoTitle, { fontFamily: serifBold }]}>How is this calculated?</Text>
              <Text style={[styles.infoText, { fontFamily: serif }]}>
                Your health score is derived from weighted risk assessments across:
              </Text>
              <Text style={[styles.infoBullet, { fontFamily: serif }]}>
                • Pharmacogenomics (drug metabolism compatibility)
              </Text>
              <Text style={[styles.infoBullet, { fontFamily: serif }]}>
                • Disease risk profiles (genetic predispositions)
              </Text>
              <Text style={[styles.infoBullet, { fontFamily: serif }]}>
                • Carrier status (recessive condition screening)
              </Text>
              <Text style={[styles.infoBullet, { fontFamily: serif }]}>
                • Nutrition & lifestyle traits (personalized insights)
              </Text>
              <Text style={[styles.infoText, { fontFamily: serif, marginTop: 8 }]}>
                Higher scores indicate better genetic compatibility and lower overall risk. Your ancestry is factored into risk benchmarking for accuracy.
              </Text>
            </View>
          )}
        </View>

        {/* ── Top Priority ────────────────────────────────────────────── */}
        <Text style={[styles.sectionHeader, { fontFamily: serifBold }]}>Top Priority</Text>

        {topPriority ? (
          <TouchableOpacity style={styles.priorityCard} onPress={() => onOpenReport?.(1)} activeOpacity={0.8}>
            <View style={[styles.accentBar, { backgroundColor: riskAccent(topPriority.risk_tier) }]} />
            <View style={styles.priorityContent}>
              <View style={styles.priorityTopRow}>
                <Text style={[styles.geneName, { fontFamily: serifBold }]}>
                  {topPriority.label ?? topPriority.condition}
                </Text>
                <View style={[styles.riskBadge, { backgroundColor: riskAccent(topPriority.risk_tier) }]}>
                  <Text style={[styles.riskBadgeText, { fontFamily: serifBold }]}>
                    {riskBadgeLabel(topPriority.risk_tier, topPriority.risk_label)}
                  </Text>
                </View>
              </View>
              {topPriority.description ? (
                <Text style={[styles.priorityDesc, { fontFamily: serif }]}>{topPriority.description}</Text>
              ) : null}
              <Text style={[styles.priorityRisk, { fontFamily: serifBold }]}>
                {topPriority.percentile?.toFixed(0)}th percentile risk
              </Text>
              {topPriority.ancestry_adjustment?.note ? (
                <Text style={[styles.priorityNote, { fontFamily: serif }]}>
                  {topPriority.ancestry_adjustment.note}
                </Text>
              ) : null}
              <Text style={[styles.priorityLink, { fontFamily: serif }]}>See full report →</Text>
            </View>
          </TouchableOpacity>
        ) : (
          <View style={styles.priorityCard}>
            <View style={[styles.accentBar, { backgroundColor: C.green }]} />
            <View style={styles.priorityContent}>
              <Text style={[styles.geneName, { fontFamily: serifBold }]}>No high-risk findings</Text>
              <Text style={[styles.priorityDesc, { fontFamily: serif }]}>
                Your risk scores are within normal range. Keep up healthy habits.
              </Text>
            </View>
          </View>
        )}

        {/* ── Explore Reports ─────────────────────────────────────────── */}
        <Text style={[styles.sectionHeader, { fontFamily: serifBold }]}>Explore Your Reports</Text>

        <View style={styles.reportsCard}>
          {reportRows.map((item, i) => (
            <TouchableOpacity
              key={item.label}
              style={[styles.reportRow, i < reportRows.length - 1 && styles.reportRowBorder]}
              activeOpacity={0.7}
              onPress={() => onOpenReport?.(item.tab)}
            >
              <View style={[styles.reportAccent, { backgroundColor: item.accent }]} />
              <View style={[styles.reportIcon, { backgroundColor: item.accent }]} />
              <View style={styles.reportLabels}>
                <Text style={[styles.reportTitle, { fontFamily: serifBold }]}>{item.label}</Text>
                <Text style={[styles.reportSubtitle, { fontFamily: serif }]}>{item.subtitle}</Text>
              </View>
              <Text style={[styles.chevron, { fontFamily: serif }]}>›</Text>
            </TouchableOpacity>
          ))}
        </View>

        <View style={{ height: 20 }} />
      </ScrollView>

      <BottomNav activeTab="home" onTabPress={onTabPress ?? (() => {})} />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },
  scroll: { flex: 1 },
  scrollContent: { paddingHorizontal: 18, paddingTop: 16, paddingBottom: 16 },

  header: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 14 },
  greeting: { fontSize: 23, color: C.textPrimary },
  subGreeting: { fontSize: 10, color: C.textSecondary, marginTop: 2 },
  leafDecor: { width: 48, height: 48, opacity: 0.85 },

  card: {
    backgroundColor: C.surface, borderRadius: 13, padding: 14, marginBottom: 14,
    shadowColor: '#000', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.07, shadowRadius: 14, elevation: 3,
  },
  sectionLabel: { fontSize: 10, color: C.textSecondary, marginBottom: 4 },
  scoreRow: { flexDirection: 'row', alignItems: 'flex-end', marginBottom: 2 },
  scoreNum: { fontSize: 38, color: C.textPrimary, lineHeight: 44 },
  scoreOf:  { fontSize: 15, color: C.textSecondary, marginBottom: 6 },
  percentile: { fontSize: 10, color: C.textSecondary, marginBottom: 10 },
  barTrack: { height: 6, backgroundColor: C.border, borderRadius: 3, position: 'relative' },
  barFill:  { position: 'absolute', top: 0, bottom: 0, left: 0, backgroundColor: C.green, borderRadius: 3 },
  barDot:   { position: 'absolute', top: -3, width: 11, height: 11, borderRadius: 6, backgroundColor: C.green },

  sectionHeader: { fontSize: 10, color: C.textSecondary, marginBottom: 8, letterSpacing: 0.2 },

  priorityCard: {
    backgroundColor: C.surface, borderRadius: 11, flexDirection: 'row',
    marginBottom: 14, overflow: 'hidden',
    shadowColor: '#000', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.07, shadowRadius: 11, elevation: 3,
  },
  accentBar: { width: 4 },
  priorityContent: { flex: 1, paddingHorizontal: 12, paddingVertical: 10 },
  priorityTopRow: { flexDirection: 'row', alignItems: 'flex-start', justifyContent: 'space-between', marginBottom: 5, gap: 8 },
  geneName: { fontSize: 13, color: C.textPrimary, flex: 1, flexWrap: 'wrap' },
  riskBadge: { borderRadius: 5, paddingHorizontal: 7, paddingVertical: 3, flexShrink: 0 },
  riskBadgeText: { color: '#fff', fontSize: 8, letterSpacing: 0.3 },
  priorityDesc: { fontSize: 10, color: C.textSecondary, marginBottom: 3 },
  priorityRisk: { fontSize: 10, color: C.red, marginBottom: 2 },
  priorityNote: { fontSize: 9, color: C.textSecondary, marginBottom: 3, fontStyle: 'italic' },
  priorityLink: { fontSize: 10, color: C.green },

  reportsCard: {
    backgroundColor: C.surface, borderRadius: 11, overflow: 'hidden',
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.05, shadowRadius: 8, elevation: 2,
  },
  reportRow: { flexDirection: 'row', alignItems: 'center', height: 52, paddingRight: 16, gap: 12 },
  reportRowBorder: { borderBottomWidth: StyleSheet.hairlineWidth, borderBottomColor: C.border },
  reportAccent: { width: 4, alignSelf: 'stretch' },
  reportIcon:   { width: 22, height: 22, borderRadius: 6 },
  reportLabels: { flex: 1 },
  reportTitle:    { fontSize: 12, color: C.textPrimary, marginBottom: 2 },
  reportSubtitle: { fontSize: 9,  color: C.textSecondary },
  chevron: { fontSize: 18, color: C.textLight, marginTop: -2 },

  scoreHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8 },
  infoIcon: { fontSize: 16, color: C.textLight, fontWeight: '600' },
  infoSection: { marginTop: 12, paddingTop: 12, borderTopWidth: StyleSheet.hairlineWidth, borderTopColor: C.border },
  infoTitle: { fontSize: 11, color: C.textPrimary, marginBottom: 6 },
  infoText: { fontSize: 10, color: C.textSecondary, lineHeight: 15, marginBottom: 6 },
  infoBullet: { fontSize: 10, color: C.textSecondary, lineHeight: 15, marginLeft: 4 },
});
