import React, { useEffect, useRef, useState } from 'react';
import {
  View, Text, StyleSheet, Image, SafeAreaView,
  StatusBar, Animated, Dimensions,
} from 'react-native';
import { useFonts, PlayfairDisplay_700Bold } from '@expo-google-fonts/playfair-display';
import { getReport } from './lib/api';
import { useApp } from './lib/AppContext';

const C = {
  bg:        '#F7F6F2',
  textSecondary: '#686760',
  green:     '#44A353',
  olive:     '#363E28',
  border:    '#E5E2DB',
};

const { width: SCREEN_W } = Dimensions.get('window');
const BAR_W = SCREEN_W - 54 - 48;

const STEPS = [
  'Parsing your SNPs…',
  'Running pharmacogenomics…',
  'Computing disease risk scores…',
  'Generating your health passport…',
];
// Each step activates when progress reaches these fractions
const STEP_THRESHOLDS = [0.18, 0.42, 0.68, 1.0];

interface Props {
  onDone?: () => void;
}

export default function ProcessingScreen({ onDone }: Props) {
  const { sessionId, setReport, setError } = useApp();
  const [fontsLoaded]   = useFonts({ PlayfairDisplay_700Bold });
  const [completedSteps, setCompletedSteps] = useState(0);
  const [progressPct, setProgressPct]       = useState(0);
  const [statusMsg, setStatusMsg]           = useState('');

  const progress    = useRef(new Animated.Value(0)).current;
  const apiDone     = useRef(false);
  const reportError = useRef<string | null>(null);

  useEffect(() => {
    // — Kick off API call in background —
    if (sessionId) {
      console.log('[Processing] starting getReport for session:', sessionId);
      getReport(sessionId)
        .then(report => {
          console.log('[Processing] report received:', {
            genes: report.pharmacogenomics?.genes?.length,
            conditions: report.disease_risk?.conditions?.length,
            carriers: report.carrier_status?.results?.length,
            traits: report.nutrition_traits?.traits?.length,
            llm: report.report_text?.llm_generated,
          });
          setReport(report);
          apiDone.current = true;
        })
        .catch(err => {
          console.error('[Processing] getReport error:', err);
          reportError.current = err?.message ?? 'Report generation failed';
          apiDone.current = true;
        });
    } else {
      console.warn('[Processing] no sessionId — skipping report fetch');
      apiDone.current = true;
    }

    // — Animate to 92% over 9s —
    Animated.timing(progress, {
      toValue: 0.92,
      duration: 9000,
      useNativeDriver: false,
    }).start(() => {
      // Hold at 92% and poll until API finishes
      const poll = setInterval(() => {
        if (!apiDone.current) return;
        clearInterval(poll);
        // Quickly fill to 100%
        Animated.timing(progress, {
          toValue: 1,
          duration: 600,
          useNativeDriver: false,
        }).start(() => {
          if (reportError.current) {
            setError(reportError.current);
          }
          setTimeout(() => onDone?.(), 200);
        });
      }, 150);
    });

    // Track percentage + completed steps
    const listenerId = progress.addListener(({ value }) => {
      const pct = Math.round(value * 100);
      setProgressPct(pct);
      const done = STEP_THRESHOLDS.filter(t => value >= t).length;
      setCompletedSteps(done);
    });

    return () => progress.removeListener(listenerId);
  }, []);

  const fillWidth = progress.interpolate({ inputRange: [0, 1], outputRange: [0, BAR_W] });
  const dotLeft   = progress.interpolate({ inputRange: [0, 1], outputRange: [0, BAR_W - 6] });

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={C.bg} />

      <Text style={[styles.title, fontsLoaded && styles.titleFont]}>
        Building Your{'\n'}Genomic Passport
      </Text>

      <Image
        source={require('./assets/images/gnome and tree.png')}
        style={styles.illustration}
        resizeMode="contain"
      />

      <View style={styles.stepsArea}>
        {STEPS.map((label, i) => {
          const done    = i < completedSteps;
          const pending = i >= completedSteps;
          return (
            <View key={i}>
              <View style={styles.stepRow}>
                <View style={[styles.circle, done ? styles.circleGreen : styles.circlePending]}>
                  {done
                    ? <Text style={styles.checkMark}>✓</Text>
                    : <View style={styles.innerDot} />}
                </View>
                <Text style={[styles.stepText, pending && styles.stepTextPending]}>{label}</Text>
              </View>
              {i < STEPS.length - 1 && <View style={styles.connector} />}
            </View>
          );
        })}
      </View>

      <View style={styles.progressRow}>
        <View style={styles.barContainer}>
          <View style={styles.barTrack} />
          <Animated.View style={[styles.barFill, { width: fillWidth }]} />
          <Animated.View style={[styles.barDot,  { left: dotLeft   }]} />
        </View>
        <Text style={styles.pctText}>{progressPct}%</Text>
      </View>

      <Text style={styles.hint}>
        {progressPct >= 92 && !apiDone.current
          ? 'Waiting for AI report…'
          : 'This may take a few minutes'}
      </Text>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg, alignItems: 'center' },

  title: { fontSize: 19, fontWeight: '700', color: C.olive, textAlign: 'center', marginTop: 24, lineHeight: 27 },
  titleFont: { fontFamily: 'PlayfairDisplay_700Bold' },

  illustration: { width: SCREEN_W - 60, height: 250, marginTop: 8 },

  stepsArea: { alignSelf: 'stretch', marginHorizontal: 27, marginTop: 10 },
  stepRow: { flexDirection: 'row', alignItems: 'center', gap: 14 },
  circle: { width: 20, height: 20, borderRadius: 10, alignItems: 'center', justifyContent: 'center' },
  circleGreen:   { backgroundColor: C.green },
  circlePending: { borderWidth: 2, borderColor: '#C8C5BE', backgroundColor: 'transparent' },
  checkMark: { color: '#fff', fontSize: 10, fontWeight: '700', lineHeight: 12 },
  innerDot:  { width: 6, height: 6, borderRadius: 3, backgroundColor: '#C8C5BE' },
  stepText:  { fontSize: 11, color: '#1A1B14', flex: 1 },
  stepTextPending: { color: C.textSecondary },
  connector: { width: 2, height: 10, backgroundColor: C.border, marginLeft: 9, marginVertical: 1 },

  progressRow: {
    flexDirection: 'row', alignItems: 'center',
    marginHorizontal: 27, marginTop: 22, alignSelf: 'stretch',
  },
  barContainer: { flex: 1, height: 6, position: 'relative' },
  barTrack: { position: 'absolute', top: 0, left: 0, right: 0, bottom: 0, backgroundColor: C.border, borderRadius: 3 },
  barFill:  { position: 'absolute', top: 0, left: 0, bottom: 0, backgroundColor: C.green, borderRadius: 3 },
  barDot:   { position: 'absolute', top: -3, width: 12, height: 12, borderRadius: 6, backgroundColor: C.green },
  pctText:  { marginLeft: 8, width: 40, fontSize: 11, fontWeight: '600', color: C.green },

  hint: { fontSize: 10, color: C.textSecondary, marginTop: 8, textAlign: 'center' },
});
