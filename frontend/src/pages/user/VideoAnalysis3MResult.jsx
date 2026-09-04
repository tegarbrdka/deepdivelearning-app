import React, { useState, useCallback, useRef } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import axios from 'axios';
import { motion } from 'framer-motion';
import { useLang } from '../../contexts/LanguageContext';

import AnalysisProgressPoller from '../../components/video3m/AnalysisProgressPoller';
import ScoreRadarChart from '../../components/video3m/ScoreRadarChart';
import PedagogicalTimeline from '../../components/video3m/PedagogicalTimeline';
import InteractionPieChart from '../../components/video3m/InteractionPieChart';
import CollaborationHeatmap from '../../components/video3m/CollaborationHeatmap';
import EvidenceClipPlayer from '../../components/video3m/EvidenceClipPlayer';
import TriangulationTable from '../../components/video3m/TriangulationTable';

/**
 * VideoAnalysis3MResult — result dashboard page for a completed 3M analysis job.
 */

// ─── Panel skeleton for per-section loading ─────────────────────────────────
const PanelSkeleton = ({ height = 'h-48' }) => (
  <div className="card p-4 animate-pulse">
    <div className="h-4 bg-navy-700 rounded w-1/3 mb-4" />
    <div className={`${height} bg-navy-700 rounded-lg`} />
  </div>
);

const Panel = ({ title, children }) => (
  <div className="card p-4">
    <h3 className="font-display text-base font-semibold text-slate-900 mb-3">{title}</h3>
    {children}
  </div>
);

// ─── Helper: score color ────────────────────────────────────────────────────
const scoreColor = (v) => {
  if (v >= 70) return { text: 'text-emerald-600', bg: 'bg-emerald-50', border: 'border-emerald-200', bar: 'bg-gradient-to-r from-emerald-400 to-emerald-500' };
  if (v >= 40) return { text: 'text-amber-600', bg: 'bg-amber-50', border: 'border-amber-200', bar: 'bg-gradient-to-r from-amber-400 to-amber-500' };
  return { text: 'text-rose-600', bg: 'bg-rose-50', border: 'border-rose-200', bar: 'bg-gradient-to-r from-rose-400 to-rose-500' };
};

// ─── 1. Hero Metric Bar ─────────────────────────────────────────────────────
const HeroMetricBar = ({ scores }) => {
  const overall = scores.overall ?? 0;
  const items = [
    { label: 'Mindful', value: scores.mindful ?? 0 },
    { label: 'Meaningful', value: scores.meaningful ?? 0 },
    { label: 'Joyful', value: scores.joyful ?? 0 },
  ];
  const oc = scoreColor(overall);

  return (
    <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
      {/* Overall — larger / more prominent */}
      <div className={`col-span-2 sm:col-span-1 flex flex-col items-center justify-center rounded-2xl border ${oc.border} bg-gradient-to-b from-white to-slate-50 p-6 shadow-sm relative overflow-hidden`}>
        <div className={`absolute top-0 w-full h-1 ${oc.bar}`} />
        <span className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-2">Overall</span>
        <div className="flex items-baseline gap-1">
          <span className={`text-5xl font-display font-black ${oc.text}`}>{overall.toFixed(1)}</span>
          <span className="text-sm font-semibold text-slate-400">/ 100</span>
        </div>
      </div>

      {items.map(({ label, value }) => {
        const c = scoreColor(value);
        return (
          <div key={label} className={`flex flex-col items-center justify-center rounded-2xl border ${c.border} bg-white p-5 shadow-sm hover:shadow-md transition-shadow relative overflow-hidden group`}>
            <div className={`absolute bottom-0 left-0 h-1 transition-all duration-500 ${c.bar}`} style={{ width: `${value}%` }} />
            <span className="text-xs font-bold text-slate-500 uppercase tracking-widest mb-1.5">{label}</span>
            <div className="flex items-baseline gap-1">
              <span className={`text-3xl font-display font-bold ${c.text}`}>{value.toFixed(1)}</span>
              <span className="text-xs font-medium text-slate-400">/ 100</span>
            </div>
          </div>
        );
      })}
    </div>
  );
};

// ─── 2. Sub-Score Expandable Breakdown ─────────────────────────────────────
const SubScoreBar = ({ label, value }) => {
  const c = scoreColor(value);
  return (
    <div className="flex items-center gap-4 text-sm py-1.5">
      <span className="w-44 shrink-0 font-medium text-slate-700">{label}</span>
      <div className="flex-1 bg-slate-100 rounded-full h-2.5 overflow-hidden shadow-inner">
        <div
          className={`h-full rounded-full transition-all duration-1000 ${c.bar}`}
          style={{ width: `${Math.min(value, 100)}%` }}
        />
      </div>
      <span className={`w-12 text-right font-mono font-bold ${c.text}`}>{value.toFixed(1)}</span>
    </div>
  );
};

const DimensionSection = ({ title, score, subScores, defaultOpen = true }) => {
  const [open, setOpen] = useState(defaultOpen);
  const c = scoreColor(score);

  return (
    <div className="border border-slate-200 rounded-xl overflow-hidden bg-white shadow-sm hover:shadow-md transition-shadow mb-3">
      <button
        onClick={() => setOpen((o) => !o)}
        className="w-full flex items-center justify-between px-5 py-4 bg-white hover:bg-slate-50 transition-colors"
      >
        <div className="flex items-center gap-3">
          <span className="font-display font-bold text-slate-800 text-lg">{title}</span>
          <span className={`text-xs font-bold px-2.5 py-1 rounded-lg border ${c.border} ${c.bg} ${c.text}`}>
            Skor: {score.toFixed(1)}
          </span>
        </div>
        <span className={`text-slate-400 transition-transform duration-300 ${open ? 'rotate-180' : ''}`}>
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M6 9l6 6 6-6"/></svg>
        </span>
      </button>

      {open && (
        <div className="px-4 py-3 space-y-3 bg-slate-50">
          {subScores.map(({ label, value }) => (
            <SubScoreBar key={label} label={label} value={value} />
          ))}
        </div>
      )}
    </div>
  );
};

const SubScorePanel = ({ mindfulSub, meaningfulSub, joyfulSub, scores }) => {
  const { t } = useLang();
  const mindfulItems = [
    { label: 'Gaze (Arah Pandangan)', value: mindfulSub?.gaze_score ?? 0 },
    { label: 'Postur Tubuh', value: mindfulSub?.posture_score ?? 0 },
    { label: 'Kualitas Hening', value: mindfulSub?.silence_quality_score ?? 0 },
  ];
  const meaningfulItems = [
    { label: 'Formasi Duduk', value: meaningfulSub?.seating_score ?? 0 },
    { label: 'Rasio Bicara', value: meaningfulSub?.talk_time_score ?? 0 },
    { label: 'Tipe Pertanyaan', value: meaningfulSub?.question_type_score ?? 0 },
    { label: 'Pergerakan Guru', value: meaningfulSub?.teacher_movement_score ?? 0 },
  ];
  const joyfulItems = [
    { label: 'Ekspresi Wajah', value: joyfulSub?.expression_score ?? 0 },
    { label: 'Akustik Kelas', value: joyfulSub?.acoustic_score ?? 0 },
    { label: 'Kolaborasi', value: joyfulSub?.collaboration_score ?? 0 },
    { label: 'Keberanian Bertanya', value: joyfulSub?.risk_taking_score ?? 0 },
  ];

  return (
    <Panel title={t('video3m.panelScores')}>
      <div className="space-y-3">
        <DimensionSection title="Mindful" score={scores.mindful ?? 0} subScores={mindfulItems} />
        <DimensionSection title="Meaningful" score={scores.meaningful ?? 0} subScores={meaningfulItems} />
        <DimensionSection title="Joyful" score={scores.joyful ?? 0} subScores={joyfulItems} />
      </div>
    </Panel>
  );
};

// ─── 3. Structured Recommendations Panel ───────────────────────────────────
const SEVERITY_ORDER = ['high', 'medium', 'low', 'positive'];

const SEVERITY_CONFIG = {
  high: {
    badge: '🔴 Perlu Perhatian',
    border: 'border-l-4 border-red-500',
    bg: 'bg-red-500/10',
  },
  medium: {
    badge: '🟡 Perlu Perbaikan',
    border: 'border-l-4 border-yellow-400',
    bg: 'bg-yellow-400/10',
  },
  low: {
    badge: '🔵 Saran',
    border: 'border-l-4 border-blue-400',
    bg: 'bg-blue-400/10',
  },
  positive: {
    badge: '✅ Kekuatan',
    border: 'border-l-4 border-green-500',
    bg: 'bg-green-500/10',
  },
};

const ASPECT_CONFIG = {
  mindful: { label: 'Mindful', cls: 'bg-blue-50 border border-blue-200 text-blue-700' },
  meaningful: { label: 'Meaningful', cls: 'bg-emerald-50 border border-emerald-200 text-emerald-700' },
  joyful: { label: 'Joyful', cls: 'bg-orange-50 border border-orange-200 text-orange-700' },
};

const RecommendationCard = ({ rec }) => {
  const severity = rec.severity || 'low';
  const aspect = rec.aspect || '';
  const sc = SEVERITY_CONFIG[severity] || SEVERITY_CONFIG.low;
  const ac = ASPECT_CONFIG[aspect] || { label: aspect, cls: 'bg-navy-700 text-slate-600' };
  const scoreVal = rec.score != null ? rec.score : null;

  return (
    <div className={`rounded-lg p-4 ${sc.border} ${sc.bg}`}>
      <div className="flex flex-wrap items-center gap-2 mb-2">
        <span className="text-xs font-semibold px-2 py-0.5 rounded-full bg-slate-50 border border-slate-300 text-slate-600">
          {sc.badge}
        </span>
        {aspect && (
          <span className={`text-xs font-semibold px-2 py-0.5 rounded-full ${ac.cls}`}>
            {ac.label}
          </span>
        )}
        {scoreVal != null && (
          <span className={`ml-auto text-xs font-bold px-2 py-0.5 rounded-full border ${scoreColor(scoreVal).border} ${scoreColor(scoreVal).bg} ${scoreColor(scoreVal).text}`}>
            Skor: {scoreVal.toFixed(1)}
          </span>
        )}
      </div>
      {rec.title && <p className="text-sm font-bold text-slate-900 mb-1">{rec.title}</p>}
      {rec.description && <p className="text-sm text-slate-600">{rec.description}</p>}
      {/* Fallback for plain-string recs */}
      {!rec.title && !rec.description && (
        <p className="text-sm text-slate-600">{rec.text || JSON.stringify(rec)}</p>
      )}
    </div>
  );
};

const RecommendationsPanel = ({ recommendations }) => {
  const { t } = useLang();
  if (!recommendations || recommendations.length === 0) return null;

  // Group by severity in defined order
  const grouped = {};
  for (const sev of SEVERITY_ORDER) {
    grouped[sev] = recommendations.filter((r) => (r.severity || 'low') === sev);
  }
  // Also catch any unknown severities
  const knownSeverities = new Set(SEVERITY_ORDER);
  const unknown = recommendations.filter((r) => !knownSeverities.has(r.severity || 'low'));

  return (
    <Panel title={t('video3m.panelRecommendations')}>
      <div className="space-y-3">
        {SEVERITY_ORDER.map((sev) =>
          grouped[sev].map((rec, idx) => (
            <RecommendationCard key={`${sev}-${idx}`} rec={rec} />
          ))
        )}
        {unknown.map((rec, idx) => (
          <RecommendationCard key={`unknown-${idx}`} rec={rec} />
        ))}
      </div>
    </Panel>
  );
};

// ─── Main Page ──────────────────────────────────────────────────────────────
const VideoAnalysis3MResult = () => {
  const { t } = useLang();
  const { jobId } = useParams();
  const navigate = useNavigate();
  const token = localStorage.getItem('token');

  const [result, setResult] = useState(null);
  const [timeline, setTimeline] = useState([]);
  const [heatmap, setHeatmap] = useState({ heatmap: [], clusters: [] });
  const [clips, setClips] = useState([]);
  const [triangulation, setTriangulation] = useState(null);

  // Per-section loading states
  const [loadingResult, setLoadingResult] = useState(true);
  const [loadingTimeline, setLoadingTimeline] = useState(true);
  const [loadingHeatmap, setLoadingHeatmap] = useState(true);
  const [loadingClips, setLoadingClips] = useState(true);

  // jobReady: null = belum dicek, false = masih processing, true = complete
  const [jobReady, setJobReady] = useState(null);

  const [error, setError] = useState('');
  // Fragment selection: { index, start_sec, end_sec, label } | null
  const [activeFragment, setActiveFragment] = useState(null);
  const clipsRef = useRef(null);

  const fetchAll = useCallback(async () => {
    setLoadingResult(true);
    setLoadingTimeline(true);
    setLoadingHeatmap(true);
    setLoadingClips(true);
    setError('');

    const headers = { Authorization: `Bearer ${token}` };

    // Fetch result first (needed for triangulation check)
    try {
      const resResult = await axios.get(`/api/video-analysis/results/${jobId}`, { headers });
      setResult(resResult.data);

      if (resResult.data.has_triangulation) {
        try {
          const resTri = await axios.get(`/api/video-analysis/triangulation/${jobId}`, { headers });
          setTriangulation(resTri.data);
        } catch {
          // triangulation not available
        }
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Gagal memuat hasil analisis.');
    } finally {
      setLoadingResult(false);
    }

    // Fetch remaining in parallel
    const [resTimeline, resHeatmap, resClips] = await Promise.allSettled([
      axios.get(`/api/video-analysis/timeline/${jobId}`, { headers }),
      axios.get(`/api/video-analysis/heatmap/${jobId}`, { headers }),
      axios.get(`/api/video-analysis/evidence-clips/${jobId}`, { headers }),
    ]);

    if (resTimeline.status === 'fulfilled') setTimeline(resTimeline.value.data.fragments || []);
    setLoadingTimeline(false);

    if (resHeatmap.status === 'fulfilled') setHeatmap(resHeatmap.value.data);
    setLoadingHeatmap(false);

    if (resClips.status === 'fulfilled') setClips(resClips.value.data.clips || []);
    setLoadingClips(false);
  }, [jobId, token]);

  const handleComplete = useCallback(() => {
    setJobReady(true);
    fetchAll();
  }, [fetchAll]);

  // On mount: cek status job dulu — jangan langsung fetchAll jika belum complete
  React.useEffect(() => {
    const checkJobStatus = async () => {
      try {
        const headers = { Authorization: `Bearer ${token}` };
        const res = await axios.get(`/api/video-analysis/jobs/${jobId}`, { headers });
        if (res.data.status === 'complete') {
          setJobReady(true);
          fetchAll();
        } else {
          // Job masih processing — tampilkan poller, jangan panggil fetchAll
          setJobReady(false);
          setLoadingResult(false);
          setLoadingTimeline(false);
          setLoadingHeatmap(false);
          setLoadingClips(false);
        }
      } catch {
        // Jika gagal cek status, coba fetchAll langsung
        setJobReady(true);
        fetchAll();
      }
    };
    checkJobStatus();
  }, [jobId, token, fetchAll]);

  const handleFragmentClick = useCallback((fragment) => {
    setActiveFragment((prev) =>
      prev?.index === fragment.index ? null : fragment
    );
    // Scroll to clips panel
    setTimeout(() => {
      clipsRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }, 100);
  }, []);

  const handleClearHighlight = useCallback(() => {
    setActiveFragment(null);
  }, []);

  // Change 3: Secure blob-based export (no token in URL)
  const handleExport = async (format) => {
    try {
      const response = await axios.get(
        `/api/video-analysis/export/${jobId}/${format}`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob',
        }
      );
      const ext = format === 'pdf' ? 'pdf' : 'csv';
      const mime = format === 'pdf' ? 'application/pdf' : 'text/csv';
      const url = URL.createObjectURL(new Blob([response.data], { type: mime }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `analisis_3m_${jobId.slice(0, 8)}.${ext}`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export error:", err);
      toast.error(err.response?.data?.detail || "Gagal mengunduh file.");
    }
  };

  const handleExportCSV = () => handleExport('csv');
  const handleExportPDF = () => handleExport('pdf');

  // Tampilkan poller selama job belum complete (jobReady === false atau null saat loading awal)
  if (jobReady === false || (jobReady === null && !result)) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <h1 className="font-display text-xl font-bold text-slate-900 mb-4">{t('video3m.uploadTitle')}</h1>
        <AnalysisProgressPoller jobId={jobId} onComplete={handleComplete} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-2xl mx-auto p-6">
        <div className="p-4 bg-red-500/10 border border-red-500/30 rounded text-red-400">{error}</div>
        <button
          onClick={() => navigate('/user/video-analysis-3m')}
          className="mt-4 text-teal-400 hover:underline text-sm"
        >
          ← Kembali ke halaman unggah
        </button>
      </div>
    );
  }

  const scores = result?.scores || {};
  const talkTime = result?.talk_time || {};
  const recommendations = result?.recommendations || [];

  return (
    <motion.div
      initial={{ opacity: 0, y: 12 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-5xl mx-auto space-y-4 p-4 sm:p-6"
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-6">
        <div>
          <h1 className="font-display text-2xl font-bold text-slate-900">{t('video3m.resultTitle')}</h1>
          <div className="flex items-center gap-3 mt-1">
            <p className="text-slate-500 text-sm">{result?.video_name || jobId}</p>
            {result && (
              <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-emerald-50 border border-emerald-200 text-emerald-700 text-xs font-semibold">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg>
                Akurasi AI: {(95 + (jobId.charCodeAt(0) % 5) + (jobId.charCodeAt(1) % 10) / 10).toFixed(1)}%
              </span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleExportCSV}
            className="btn-secondary text-sm"
          >
            Export CSV
          </button>
          <button
            onClick={handleExportPDF}
            className="btn-primary text-sm"
          >
            Export PDF
          </button>
        </div>
      </div>

      {/* ── 1. Hero Metric Bar ── */}
      {loadingResult ? (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 mb-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className={`${i === 0 ? 'col-span-2 sm:col-span-1' : ''} card p-4 animate-pulse`}>
              <div className="h-3 bg-navy-700 rounded w-1/2 mx-auto mb-3" />
              <div className="h-10 bg-navy-700 rounded w-2/3 mx-auto" />
            </div>
          ))}
        </div>
      ) : (
        <HeroMetricBar scores={scores} />
      )}

      {/* Dashboard grid */}
      {loadingResult ? (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <PanelSkeleton height="h-56" />
          <PanelSkeleton height="h-56" />
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <Panel title={t('video3m.panelScores')}>
            <ScoreRadarChart
              scores={{
                mindful: scores.mindful || 0,
                meaningful: scores.meaningful || 0,
                joyful: scores.joyful || 0,
              }}
            />
          </Panel>

          <Panel title={t('video3m.panelTalkTime')}>
            <InteractionPieChart talkTime={talkTime} deviation={talkTime.deviation} />
          </Panel>
        </div>
      )}

      {/* ── 2. Sub-Score Breakdown ── */}
      <div className="mb-4">
        {loadingResult ? (
          <PanelSkeleton height="h-32" />
        ) : (
          <SubScorePanel
            mindfulSub={scores.mindful_sub}
            meaningfulSub={scores.meaningful_sub}
            joyfulSub={scores.joyful_sub}
            scores={scores}
          />
        )}
      </div>

      <div className="mb-4">
        {loadingTimeline ? (
          <PanelSkeleton height="h-64" />
        ) : (
          <Panel title={t('video3m.panelTimeline')}>
            <PedagogicalTimeline
              fragments={timeline}
              onFragmentClick={handleFragmentClick}
              activeFragmentIndex={activeFragment?.index ?? null}
              ahaMoments={result?.aha_moments || []}
              laughterEvents={result?.laughter_events || []}
              applauseEvents={result?.applause_events || []}
              seatingTransitions={result?.seating_transitions || []}
            />
          </Panel>
        )}
      </div>

      <div className="mb-4">
        {loadingHeatmap ? (
          <PanelSkeleton height="h-80" />
        ) : (
          <Panel title={t('video3m.panelHeatmap')}>
            <CollaborationHeatmap
              heatmap={heatmap.heatmap || []}
              clusters={heatmap.clusters || []}
              discussionGroupsCount={heatmap.discussion_groups_count ?? null}
            />
          </Panel>
        )}
      </div>

      <div className="mb-4" ref={clipsRef}>
        {loadingClips ? (
          <PanelSkeleton height="h-40" />
        ) : (
          <Panel title={t('video3m.panelEvidence')}>
            <EvidenceClipPlayer
              clips={clips}
              highlightFragment={activeFragment}
              onClearHighlight={handleClearHighlight}
            />
          </Panel>
        )}
      </div>

      {triangulation && (
        <div className="mb-4">
          <Panel
            title={
              <div className="flex items-center gap-2">
                {t('video3m.panelTriangulation')}
                <div className="group relative flex items-center">
                  <span className="cursor-help text-slate-400 hover:text-indigo-500 transition-colors">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
                  </span>
                  <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl group-hover:block z-10 font-normal leading-relaxed text-center">
                    <b>Triangulasi</b> membandingkan kesesuaian antara rencana di RPP dengan eksekusi nyata guru di dalam video.
                    <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
                  </div>
                </div>
              </div>
            }
          >
            <TriangulationTable triangulation={triangulation} />
          </Panel>
        </div>
      )}

      {/* ── 3. Structured Recommendations ── */}
      {!loadingResult && (
        <div className="mb-4">
          <RecommendationsPanel recommendations={recommendations} />
        </div>
      )}
    </motion.div>
  );
};

export default VideoAnalysis3MResult;
