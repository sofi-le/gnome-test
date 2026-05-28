import React, { createContext, useContext, useState, ReactNode } from 'react';
import { ParseResult, ReportResult } from './types';

interface AppState {
  sessionId: string | null;
  parseResult: ParseResult | null;
  report: ReportResult | null;
  error: string | null;
}

interface AppContextValue extends AppState {
  setParseResult: (r: ParseResult) => void;
  setReport: (r: ReportResult) => void;
  setError: (e: string | null) => void;
  reset: () => void;
  // Derived helpers
  healthScore: number;
  dominantAncestry: string;
}

const defaultState: AppState = {
  sessionId: null,
  parseResult: null,
  report: null,
  error: null,
};

const AppContext = createContext<AppContextValue>({
  ...defaultState,
  setParseResult: () => {},
  setReport: () => {},
  setError: () => {},
  reset: () => {},
  healthScore: 72,
  dominantAncestry: 'Unknown',
});

export function AppProvider({ children }: { children: ReactNode }) {
  const [state, setState] = useState<AppState>(defaultState);

  const setParseResult = (r: ParseResult) =>
    setState(s => ({ ...s, sessionId: r.session_id, parseResult: r, error: null }));

  const setReport = (r: ReportResult) =>
    setState(s => ({ ...s, report: r, error: null }));

  const setError = (e: string | null) =>
    setState(s => ({ ...s, error: e }));

  const reset = () => setState(defaultState);

  // Compute health score from disease risk percentiles
  // avg 50th percentile → score 72, higher risk → lower score
  const computedConditions = state.report?.disease_risk.conditions.filter(
    c => c.status === 'computed' && c.percentile != null,
  ) ?? [];

  const avgPct =
    computedConditions.length > 0
      ? computedConditions.reduce((s, c) => s + (c.percentile ?? 50), 0) /
        computedConditions.length
      : 50;

  const healthScore = Math.max(20, Math.min(99, Math.round(100 - avgPct * 0.56)));

  // Dominant ancestry from parse result
  const ancestry = state.parseResult?.ancestry ?? {};
  const dominantAncestry =
    Object.keys(ancestry).length > 0
      ? Object.entries(ancestry).sort((a, b) => b[1] - a[1])[0][0]
      : 'Unknown';

  return (
    <AppContext.Provider
      value={{
        ...state,
        setParseResult,
        setReport,
        setError,
        reset,
        healthScore,
        dominantAncestry,
      }}
    >
      {children}
    </AppContext.Provider>
  );
}

export function useApp() {
  return useContext(AppContext);
}
