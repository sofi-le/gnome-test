import React, { useState } from 'react';
import {
  View, Text, StyleSheet, ScrollView, TouchableOpacity,
  Image, SafeAreaView, StatusBar, Dimensions,
} from 'react-native';
import { useFonts } from 'expo-font';
import { InriaSerif_400Regular, InriaSerif_700Bold } from '@expo-google-fonts/inria-serif';
import BottomNav, { TabKey } from './BottomNav';
import { useApp } from './lib/AppContext';
import { GeneResult, RiskCondition, CarrierResult, TraitResult } from './lib/types';

const C = {
  bg:           '#F7F6F2',
  surface:      '#FFFFFF',
  primary:      '#1A1B14',
  secondary:    '#686760',
  light:        '#A6A59F',
  green:        '#44A353',
  olive:        '#363E28',
  red:          '#EB412A',
  amber:        '#F5A62B',
  blue:         '#4A90F9',
  purple:       '#9966FE',
  border:       '#E5E2DB',
  lavender:     '#EDE9FF',
  lavenderText: '#6B4ECC',
  blueBg:       '#E5EEFE',
  blueText:     '#3366B2',
  lightGreen:   '#DAE4CF',
};

const { width: SCREEN_W } = Dimensions.get('window');

const TABS = [
  { label: 'Drugs',      accent: C.amber  },
  { label: 'Risk',       accent: C.red    },
  { label: 'Carrier',    accent: C.red    },
  { label: 'Traits',     accent: C.blue   },
  { label: 'AI Summary', accent: C.green  },
];

// ─── Helpers ────────────────────────────────────────────────────────────────

function Badge({ label, bg, color }: { label: string; bg: string; color: string }) {
  return (
    <View style={[bs.wrap, { backgroundColor: bg }]}>
      <Text style={[bs.text, { color }]}>{label}</Text>
    </View>
  );
}
const bs = StyleSheet.create({
  wrap: { borderRadius: 6, paddingHorizontal: 8, paddingVertical: 3, alignSelf: 'flex-start', flexShrink: 1 },
  text: { fontSize: 8, fontWeight: '700', letterSpacing: 0.4 },
});

function MetaRow({ label, value, serif, serifBold }: { label: string; value: string; serif?: string; serifBold?: string }) {
  return (
    <View style={ms.row}>
      <Text style={[ms.label, { fontFamily: serifBold }]}>{label}</Text>
      <Text style={[ms.value, { fontFamily: serif }]}>{value}</Text>
    </View>
  );
}
const ms = StyleSheet.create({
  row:   { flexDirection: 'row', marginBottom: 3 },
  label: { fontSize: 8, color: C.secondary, width: 100 },
  value: { fontSize: 8, color: C.secondary, flex: 1 },
});

function Divider() {
  return <View style={{ height: StyleSheet.hairlineWidth, backgroundColor: C.border, marginVertical: 8 }} />;
}

function PercentileBar({ pct, accent }: { pct: number; accent: string }) {
  const clamped = Math.min(100, Math.max(0, pct));
  return (
    <View style={{ marginTop: 6, marginBottom: 4 }}>
      <View style={pb.track}>
        <View style={[pb.fill, { width: `${clamped}%`, backgroundColor: accent }]} />
        <View style={[pb.dot, { left: `${clamped}%`, marginLeft: -6, backgroundColor: accent }]} />
      </View>
      <View style={pb.labels}>
        <Text style={pb.label}>0</Text>
        <Text style={pb.label}>50</Text>
        <Text style={pb.label}>100</Text>
      </View>
    </View>
  );
}
const pb = StyleSheet.create({
  track:  { height: 7, backgroundColor: C.border, borderRadius: 3, position: 'relative' },
  fill:   { position: 'absolute', top: 0, bottom: 0, left: 0, borderRadius: 3 },
  dot:    { position: 'absolute', top: -2.5, width: 12, height: 12, borderRadius: 6 },
  labels: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 3 },
  label:  { fontSize: 8, color: C.secondary },
});

function SectionCard({ accent, children }: { accent: string; children: React.ReactNode }) {
  return (
    <View style={[sc.wrap, { borderLeftColor: accent }]}>
      {children}
    </View>
  );
}
const sc = StyleSheet.create({
  wrap: {
    backgroundColor: C.surface, borderRadius: 14, borderLeftWidth: 4,
    marginBottom: 12,
    shadowColor: '#000', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.08, shadowRadius: 14, elevation: 3,
    overflow: 'hidden',
  },
});

function EmptyState({ text }: { text: string }) {
  return (
    <View style={styles.emptyBox}>
      <View style={[styles.emptyIcon, { backgroundColor: '#99CC80' }]} />
      <Text style={styles.emptyText}>{text}</Text>
    </View>
  );
}

// ─── Severity helpers ────────────────────────────────────────────────────────

function drugSeverityColor(s: string): string {
  if (s === 'HIGH')     return C.red;
  if (s === 'MODERATE') return C.amber;
  return C.green;
}

function riskAccent(tier?: string): string {
  if (tier === 'high')     return C.red;
  if (tier === 'moderate') return C.amber;
  if (tier === 'low')      return C.blue;
  return C.green;
}

function riskBadgeLabel(tier?: string, label?: string): string {
  if (label) return label.toUpperCase();
  if (tier === 'high')     return 'HIGH RISK';
  if (tier === 'moderate') return 'ELEVATED';
  if (tier === 'average')  return 'AVERAGE';
  if (tier === 'low')      return 'LOW';
  return 'UNKNOWN';
}

function carrierAccent(status: string): string {
  if (status === 'carrier')  return C.amber;
  if (status === 'affected') return C.red;
  return C.green;
}

function carrierDot(status: string): string {
  return carrierAccent(status);
}

// ─── TAB CONTENT ────────────────────────────────────────────────────────────

function DrugsTab({ serif, serifBold }: { serif?: string; serifBold?: string }) {
  const { report } = useApp();
  const allGenes: GeneResult[] = report?.pharmacogenomics.genes ?? [];
  const genes = allGenes.filter(g => g.status !== 'not_callable');
  const notCallable = allGenes.filter(g => g.status === 'not_callable');
  const summary = report?.pharmacogenomics.summary;

  return (
    <ScrollView contentContainerStyle={styles.tabContent} showsVerticalScrollIndicator={false}>
      <Text style={[styles.pageTitle, { fontFamily: serifBold }]}>Drugs</Text>
      {summary && (
        <View style={styles.summaryChips}>
          <View style={[styles.chip, { backgroundColor: '#FEF1F1' }]}>
            <Text style={[styles.chipNum, { fontFamily: serifBold, color: C.red }]}>{summary.high_risk_drugs}</Text>
            <Text style={[styles.chipLabel, { fontFamily: serif }]}>High risk</Text>
          </View>
          <View style={[styles.chip, { backgroundColor: '#FFF7E2' }]}>
            <Text style={[styles.chipNum, { fontFamily: serifBold, color: C.amber }]}>{summary.moderate_risk_drugs}</Text>
            <Text style={[styles.chipLabel, { fontFamily: serif }]}>Moderate</Text>
          </View>
          <View style={[styles.chip, { backgroundColor: C.lightGreen }]}>
            <Text style={[styles.chipNum, { fontFamily: serifBold, color: C.green }]}>{summary.genes_tested}</Text>
            <Text style={[styles.chipLabel, { fontFamily: serif }]}>Genes tested</Text>
          </View>
        </View>
      )}

      {genes.length === 0 && notCallable.length === 0 && <EmptyState text="No pharmacogenomics data available." />}

      {genes.map(gene => (
        <SectionCard key={gene.gene} accent={C.amber}>
          <View style={styles.cardInner}>
            <View style={styles.cardTopRow}>
              <View>
                <Text style={[styles.geneName, { fontFamily: serifBold }]}>{gene.gene}</Text>
                <Text style={[styles.geneAllele, { fontFamily: serifBold }]}>{gene.metabolizer_status}</Text>
              </View>
              <Badge
                label={(gene.status_label ?? '').toUpperCase()}
                bg="#FFF7E2"
                color="#B26E00"
              />
            </View>
            <MetaRow label="Phenotype" value={gene.status_label ?? ''} serif={serif} serifBold={serifBold} />

            {(gene.drug_flags?.length ?? 0) > 0 && (
              <>
                <Divider />
                <Text style={[styles.subheading, { fontFamily: serifBold }]}>Affected Drugs</Text>
                {gene.drug_flags.map((flag, i) => (
                  <View key={i} style={[styles.drugItem, { borderLeftColor: drugSeverityColor(flag.severity) }]}>
                    <View style={styles.drugHeader}>
                      <Text style={[styles.drugName, { fontFamily: serifBold }]}>{flag.drug}</Text>
                      <Badge label={flag.severity} bg={drugSeverityColor(flag.severity)} color="#fff" />
                    </View>
                    <MetaRow label="Action"  value={flag.action} serif={serif} serifBold={serifBold} />
                    <MetaRow label="Reason"  value={flag.reason} serif={serif} serifBold={serifBold} />
                  </View>
                ))}
              </>
            )}

            {(gene.drug_flags?.length ?? 0) === 0 && (
              <Text style={[styles.noFlags, { fontFamily: serif }]}>No drug interactions flagged for this gene.</Text>
            )}
          </View>
        </SectionCard>
      ))}

      {notCallable.map(gene => (
        <View key={gene.gene} style={[styles.infoBox, { backgroundColor: C.blueBg, borderLeftColor: C.blue }]}>
          <Text style={[styles.infoBoxTitle, { fontFamily: serifBold, color: C.blueText }]}>{gene.gene} — Not Callable</Text>
          <Text style={[styles.infoBoxBody, { fontFamily: serif, color: C.blueText, marginBottom: 6 }]}>{gene.disclaimer}</Text>
          {(gene.affected_drugs ?? []).map((drug, i) => (
            <Text key={i} style={[styles.infoBoxBody, { fontFamily: serif, color: C.blueText }]}>· {drug}</Text>
          ))}
        </View>
      ))}
    </ScrollView>
  );
}

function RiskTab({ serif, serifBold }: { serif?: string; serifBold?: string }) {
  const { report } = useApp();
  const conditions: RiskCondition[] = report?.disease_risk.conditions ?? [];
  const equityNote = report?.disease_risk.equity_note;
  const computed = conditions.filter(c => c.status === 'computed');

  return (
    <ScrollView contentContainerStyle={styles.tabContent} showsVerticalScrollIndicator={false}>
      <Text style={[styles.pageTitle, { fontFamily: serifBold }]}>Risk</Text>

      {computed.length === 0 && <EmptyState text="Risk scores not yet available." />}

      {computed.map((c, i) => (
        <SectionCard key={i} accent={riskAccent(c.risk_tier)}>
          <View style={styles.cardInner}>
            <View style={styles.cardTopRow}>
              <View style={{ flex: 1 }}>
                <Text style={[styles.geneName, { fontFamily: serifBold }]}>
                  {c.label ?? c.condition}
                </Text>
                {c.description && (
                  <Text style={[styles.subtitle, { fontFamily: serif }]}>{c.description}</Text>
                )}
              </View>
              <Badge
                label={riskBadgeLabel(c.risk_tier, c.risk_label)}
                bg={riskAccent(c.risk_tier)}
                color="#fff"
              />
            </View>

            {c.percentile != null && (
              <>
                <Text style={[styles.percentileNum, { fontFamily: serifBold }]}>
                  {c.percentile.toFixed(0)}th percentile
                </Text>
                <PercentileBar pct={c.percentile} accent={riskAccent(c.risk_tier)} />
              </>
            )}

            {(c.raw_score != null || c.snps_matched != null) && (
              <View style={styles.statsRow}>
                {c.raw_score != null && (
                  <MetaRow label="Raw score"    value={c.raw_score.toFixed(3)} serif={serif} serifBold={serifBold} />
                )}
                {c.snps_matched != null && (
                  <MetaRow label="SNPs matched" value={`${c.snps_matched}`}   serif={serif} serifBold={serifBold} />
                )}
              </View>
            )}

            {c.ancestry_adjustment?.note && (
              <Text style={[styles.ancestryNote, { fontFamily: serif }]}>
                Ancestry note  ·  {c.ancestry_adjustment.note}
              </Text>
            )}
          </View>
        </SectionCard>
      ))}

      {equityNote && (
        <View style={[styles.infoBox, { backgroundColor: C.blueBg, borderLeftColor: C.blue }]}>
          <Text style={[styles.infoBoxTitle, { fontFamily: serifBold, color: C.blueText }]}>Equity Note</Text>
          <Text style={[styles.infoBoxBody,  { fontFamily: serif,     color: C.blueText }]}>{equityNote}</Text>
        </View>
      )}
    </ScrollView>
  );
}

function CarrierTab({ serif, serifBold }: { serif?: string; serifBold?: string }) {
  const { report } = useApp();
  const results: CarrierResult[] = report?.carrier_status.results ?? [];
  const summary = report?.carrier_status;

  return (
    <ScrollView contentContainerStyle={styles.tabContent} showsVerticalScrollIndicator={false}>
      <Text style={[styles.pageTitle, { fontFamily: serifBold }]}>Carrier</Text>
      {summary && (
        <View style={styles.summaryChips}>
          <View style={[styles.chip, { backgroundColor: '#FFF7E2' }]}>
            <Text style={[styles.chipNum, { fontFamily: serifBold, color: C.amber }]}>{summary.carriers_found}</Text>
            <Text style={[styles.chipLabel, { fontFamily: serif }]}>Carriers found</Text>
          </View>
          <View style={[styles.chip, { backgroundColor: C.lightGreen }]}>
            <Text style={[styles.chipNum, { fontFamily: serifBold, color: C.green }]}>{summary.conditions_tested}</Text>
            <Text style={[styles.chipLabel, { fontFamily: serif }]}>Tested</Text>
          </View>
        </View>
      )}

      {results.length === 0 && <EmptyState text="No carrier data available." />}

      {results.map((r, i) => (
        <SectionCard key={i} accent={carrierAccent(r.status)}>
          <View style={styles.cardInner}>
            <View style={styles.cardTopRow}>
              <Text style={[styles.geneName, { fontFamily: serifBold }]}>{r.gene}</Text>
              <View style={[{ width: 14, height: 14, borderRadius: 7, marginTop: 2 }, { backgroundColor: carrierDot(r.status) }]} />
            </View>
            <Text style={[styles.subtitle, { fontFamily: serif }]}>{r.status_label}</Text>

            {r.rsid && r.rsid !== 'N/A' && (
              <>
                <Divider />
                <Text style={[styles.subheading, { fontFamily: serifBold }]}>Variant found</Text>
                <View style={styles.variantBox}>
                  <Text style={[styles.rsid, { fontFamily: serifBold }]}>{r.rsid}</Text>
                  <Text style={[styles.variantMeta, { fontFamily: serif }]}>{r.condition}</Text>
                  {r.genotype && (
                    <Text style={[styles.variantMeta, { fontFamily: serif }]}>Genotype: {r.genotype}</Text>
                  )}
                </View>
              </>
            )}

            {r.detail && (
              <Text style={[styles.carrierNote, { fontFamily: serif }]}>{r.detail}</Text>
            )}
            {r.notes && (
              <Text style={[styles.carrierNote, { fontFamily: serif, marginTop: 4 }]}>{r.notes}</Text>
            )}
          </View>
        </SectionCard>
      ))}

      {summary?.disclaimer && (
        <View style={[styles.infoBox, { backgroundColor: C.blueBg, borderLeftColor: C.blue }]}>
          <Text style={[styles.infoBoxBody, { fontFamily: serif, color: C.blueText }]}>{summary.disclaimer}</Text>
        </View>
      )}
    </ScrollView>
  );
}

function TraitsTab({ serif, serifBold }: { serif?: string; serifBold?: string }) {
  const { report } = useApp();
  const traits: TraitResult[] = (report?.nutrition_traits.traits ?? []).filter(t => t.status !== 'not_tested');

  // Group by category
  const grouped: Record<string, TraitResult[]> = {};
  traits.forEach(t => {
    const cat = t.category || 'Other';
    if (!grouped[cat]) grouped[cat] = [];
    grouped[cat].push(t);
  });

  return (
    <ScrollView contentContainerStyle={styles.tabContent} showsVerticalScrollIndicator={false}>
      {Object.keys(grouped).length === 0 && <EmptyState text="No trait data available." />}

      {Object.entries(grouped).map(([category, items]) => (
        <View key={category}>
          <Text style={[styles.sectionGroupLabel, { fontFamily: serifBold }]}>{category}</Text>
          {items.map((t, i) => (
            <View key={i} style={[styles.traitCard, { marginBottom: 10 }]}>
              <View style={styles.traitCardInner}>
                <View style={styles.traitTopRow}>
                  <Text style={[styles.traitName, { fontFamily: serifBold }]}>{t.name}</Text>
                  {t.label && (
                    <Badge label={t.label.toUpperCase()} bg={C.lavender} color={C.lavenderText} />
                  )}
                </View>
                <MetaRow label="Gene"   value={t.gene}   serif={serif} serifBold={serifBold} />
                {t.rsid && <MetaRow label="rsID"   value={t.rsid}   serif={serif} serifBold={serifBold} />}
                {t.detail && (
                  <>
                    <Divider />
                    <Text style={[styles.traitBody, { fontFamily: serif }]}>{t.detail}</Text>
                  </>
                )}
              </View>
            </View>
          ))}
        </View>
      ))}
    </ScrollView>
  );
}

function AISummaryTab({ serif, serifBold }: { serif?: string; serifBold?: string }) {
  const { report } = useApp();
  const reportText = report?.report_text;
  const equityNote = report?.disease_risk.equity_note;

  return (
    <ScrollView contentContainerStyle={styles.tabContent} showsVerticalScrollIndicator={false}>
      <View style={styles.summaryCard}>
        <Text style={[styles.summaryTitle, { fontFamily: serifBold }]}>Your Genomic Summary</Text>
        {reportText?.llm_generated === false && (
          <View style={[styles.chip, { backgroundColor: '#FFF7E2', alignSelf: 'flex-start', marginBottom: 8 }]}>
            <Text style={[styles.chipLabel, { fontFamily: serif, color: C.amber }]}>AI summary unavailable — showing structured report</Text>
          </View>
        )}
        <Text style={[styles.summaryBody, { fontFamily: serif }]}>
          {reportText?.full_text ?? 'Generating your personalised report…'}
        </Text>
        <Image
          source={require('./assets/images/small gene tree.png')}
          style={styles.summaryDecor}
          resizeMode="contain"
        />
      </View>

      {equityNote && (
        <View style={[styles.infoBox, { backgroundColor: C.blueBg, borderLeftColor: C.blue }]}>
          <View style={styles.infoBoxHeader}>
            <View style={styles.infoIcon} />
            <Text style={[styles.infoBoxTitle, { fontFamily: serifBold, color: C.blueText }]}>
              Equity & Accuracy Note
            </Text>
          </View>
          <Text style={[styles.infoBoxBody, { fontFamily: serif, color: C.blueText }]}>{equityNote}</Text>
        </View>
      )}
    </ScrollView>
  );
}

// ─── Main Screen ─────────────────────────────────────────────────────────────

interface Props {
  initialTab?: number;
  onBack?: () => void;
  onTabPress?: (tab: TabKey) => void;
}

export default function ReportsScreen({ initialTab = 0, onBack, onTabPress }: Props) {
  const [fontsLoaded] = useFonts({ InriaSerif_400Regular, InriaSerif_700Bold });
  const [activeTab, setActiveTab] = useState(initialTab);

  const serif     = fontsLoaded ? 'InriaSerif_400Regular' : undefined;
  const serifBold = fontsLoaded ? 'InriaSerif_700Bold'    : undefined;
  const tabProps  = { serif, serifBold };

  return (
    <SafeAreaView style={styles.root}>
      <StatusBar barStyle="dark-content" backgroundColor={C.bg} />

      {/* ── Top tab strip ───────────────────────────────────────────── */}
      <View style={styles.tabStrip}>
        <View style={styles.tabStripDivider} />
        {TABS.map((t, i) => {
          const active = i === activeTab;
          return (
            <TouchableOpacity key={t.label} style={styles.tabBtn} onPress={() => setActiveTab(i)}>
              <Text style={[styles.tabLabel, {
                fontFamily: active ? serifBold : serif,
                color: active ? t.accent : C.light,
              }]} numberOfLines={1}>
                {t.label}
              </Text>
              {active && <View style={[styles.tabUnderline, { backgroundColor: t.accent }]} />}
            </TouchableOpacity>
          );
        })}
      </View>

      {activeTab === 0 && <DrugsTab     {...tabProps} />}
      {activeTab === 1 && <RiskTab      {...tabProps} />}
      {activeTab === 2 && <CarrierTab   {...tabProps} />}
      {activeTab === 3 && <TraitsTab    {...tabProps} />}
      {activeTab === 4 && <AISummaryTab {...tabProps} />}

      <BottomNav activeTab="reports" onTabPress={onTabPress ?? (() => {})} />
    </SafeAreaView>
  );
}

// ─── Styles ──────────────────────────────────────────────────────────────────
const statusDotStyle = (color: string) => ({
  width: 14, height: 14, borderRadius: 7, backgroundColor: color, marginTop: 2,
});

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: C.bg },

  tabStrip: { flexDirection: 'row', position: 'relative' },
  tabStripDivider: {
    position: 'absolute', bottom: 0, left: 0, right: 0,
    height: StyleSheet.hairlineWidth, backgroundColor: C.border,
  },
  tabBtn:       { flex: 1, alignItems: 'center', paddingVertical: 10, position: 'relative' },
  tabLabel:     { fontSize: 9 },
  tabUnderline: { position: 'absolute', bottom: 0, left: 0, right: 0, height: 3, borderRadius: 2 },

  tabContent: { paddingHorizontal: 18, paddingTop: 16, paddingBottom: 20 },
  pageTitle:  { fontSize: 19, color: C.primary, marginBottom: 12 },
  sectionGroupLabel: { fontSize: 12, color: C.primary, marginBottom: 8, marginTop: 4 },

  summaryChips: { flexDirection: 'row', gap: 8, marginBottom: 14 },
  chip: { borderRadius: 10, paddingHorizontal: 12, paddingVertical: 8, alignItems: 'center' },
  chipNum:   { fontSize: 18 },
  chipLabel: { fontSize: 8, color: C.secondary, marginTop: 2 },

  cardInner:  { padding: 14 },
  cardTopRow: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: 6, gap: 8 },
  geneName:   { fontSize: 14, color: C.primary },
  geneAllele: { fontSize: 20, color: C.primary, marginTop: 2 },
  subtitle:   { fontSize: 11, color: C.secondary, marginBottom: 4 },
  percentileNum: { fontSize: 22, color: C.primary, marginTop: 2 },
  statsRow:   { flexDirection: 'row', gap: 16, marginTop: 4 },
  ancestryNote: { fontSize: 8, color: C.secondary, marginTop: 4, fontStyle: 'italic' },
  subheading: { fontSize: 9, color: C.secondary, marginBottom: 6 },
  noFlags:    { fontSize: 10, color: C.secondary, fontStyle: 'italic' },

  drugItem: {
    backgroundColor: '#FEF1F1', borderRadius: 10, padding: 10, marginTop: 6,
    borderLeftWidth: 3,
  },
  drugHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 4, gap: 8 },
  drugName:   { fontSize: 12, color: C.primary },

  variantBox:   { backgroundColor: C.bg, borderRadius: 8, padding: 10, marginBottom: 8 },
  rsid:         { fontSize: 12, color: C.primary, marginBottom: 2 },
  variantMeta:  { fontSize: 11, color: C.secondary },
  carrierNote:  { fontSize: 10, color: C.secondary, lineHeight: 15 },

  traitCard:      { backgroundColor: C.surface, borderRadius: 14, overflow: 'hidden',
    shadowColor: '#000', shadowOffset: { width: 0, height: 2 }, shadowOpacity: 0.06, shadowRadius: 10, elevation: 2 },
  traitCardInner: { padding: 14 },
  traitTopRow:    { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, gap: 8 },
  traitName:      { fontSize: 13, color: C.primary, flex: 1 },
  traitBody:      { fontSize: 11, color: C.secondary, lineHeight: 16 },

  summaryCard: {
    backgroundColor: C.surface, borderRadius: 14, padding: 16, marginBottom: 14,
    shadowColor: '#000', shadowOffset: { width: 0, height: 3 }, shadowOpacity: 0.07, shadowRadius: 14, elevation: 3,
  },
  summaryTitle: { fontSize: 17, color: C.primary, marginBottom: 10 },
  summaryBody:  { fontSize: 12, color: C.secondary, lineHeight: 19, marginBottom: 12 },
  summaryDecor: { width: 80, height: 60, alignSelf: 'center', opacity: 0.75 },

  emptyBox: {
    flexDirection: 'row', alignItems: 'center', backgroundColor: C.lightGreen,
    borderRadius: 12, padding: 14, gap: 12, marginBottom: 12,
  },
  emptyIcon: { width: 26, height: 26, borderRadius: 13 },
  emptyText: { fontSize: 11, color: C.secondary, flex: 1 },

  infoBox:       { borderLeftWidth: 4, borderRadius: 11, padding: 14, marginBottom: 12 },
  infoBoxHeader: { flexDirection: 'row', alignItems: 'center', gap: 6, marginBottom: 6 },
  infoIcon:      { width: 14, height: 14, borderRadius: 7, borderWidth: 1.5, borderColor: C.blueText },
  infoBoxTitle:  { fontSize: 10 },
  infoBoxBody:   { fontSize: 9, lineHeight: 15 },
});
