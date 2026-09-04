import React from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  ReferenceArea,
  BarChart,
  Bar,
} from 'recharts';

/**
 * PedagogicalTimeline — per-fragment 3M score line chart, event timeline strip,
 * and per-fragment talk-time stacked bar chart.
 *
 * Props:
 *   fragments: Array<{ index, start_sec, end_sec, label, mindful, meaningful, joyful,
 *                       teacher_talk_pct, student_talk_pct }>
 *   onFragmentClick: (fragment) => void
 *   activeFragmentIndex: number | null
 *   ahaMoments: number[]          — timestamps in seconds
 *   laughterEvents: number[]      — timestamps in seconds
 *   applauseEvents: number[]      — timestamps in seconds
 *   seatingTransitions: Array<{ timestamp_sec, formation }>
 */

// ─── Line chart helpers ──────────────────────────────────────────────────────

const ActiveDot = ({ cx, cy, payload, activeFragmentIndex, baseColor }) => {
  const isActive = payload?.index === activeFragmentIndex;
  if (isActive) {
    return (
      <g>
        <circle cx={cx} cy={cy} r={9} fill={baseColor} opacity={0.25} />
        <circle cx={cx} cy={cy} r={6} fill={baseColor} stroke="#fff" strokeWidth={2} />
      </g>
    );
  }
  return <circle cx={cx} cy={cy} r={4} fill={baseColor} stroke="#fff" strokeWidth={1.5} />;
};

const CustomTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-4 py-3 text-xs min-w-[220px]">
      <p className="font-bold text-slate-800 mb-2 border-b pb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.color }} className="font-semibold flex justify-between mb-1">
          <span>{p.name}:</span>
          <span>{p.value?.toFixed(1)} / 100</span>
        </p>
      ))}
      <div className="mt-2 pt-2 border-t border-slate-100 text-slate-500 text-[10px] leading-relaxed">
        <p>💡 <b className="text-emerald-600">Skor &gt; 70:</b> Praktik Terbaik</p>
        <p>⚠️ <b className="text-rose-600">Skor &lt; 40:</b> Perlu Perbaikan</p>
        <p className="mt-1 italic text-indigo-400">Klik titik grafik untuk lihat bukti video</p>
      </div>
    </div>
  );
};

// ─── Event Timeline Strip ────────────────────────────────────────────────────

const EVENT_TYPES = [
  { key: 'aha',       icon: '💡', color: '#eab308', label: 'Momen Aha' },
  { key: 'laughter',  icon: '😄', color: '#f97316', label: 'Tawa' },
  { key: 'applause',  icon: '👏', color: '#22c55e', label: 'Tepuk Tangan' },
  { key: 'seating',   icon: '🪑', color: '#3b82f6', label: 'Transisi Formasi' },
];

const EventMarker = ({ icon, color, tooltip, pct }) => (
  <div
    className="absolute -translate-x-1/2 -translate-y-1/2 top-1/2 cursor-default select-none"
    style={{ left: `${pct}%` }}
    title={tooltip}
  >
    <span
      className="text-base leading-none drop-shadow-sm"
      style={{ filter: `drop-shadow(0 0 2px ${color})` }}
    >
      {icon}
    </span>
  </div>
);

const EventTimelineStrip = ({ ahaMoments, laughterEvents, applauseEvents, seatingTransitions, videoDuration }) => {
  if (videoDuration <= 0) return null;

  const hasAny =
    ahaMoments.length > 0 ||
    laughterEvents.length > 0 ||
    applauseEvents.length > 0 ||
    seatingTransitions.length > 0;

  if (!hasAny) return null;

  const toPct = (sec) => Math.min(100, Math.max(0, (sec / videoDuration) * 100));

  return (
    <div className="mt-4">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
        Garis Waktu Kejadian
      </p>

      {/* Strip */}
      <div className="relative h-8 bg-gray-100 rounded-full overflow-visible border border-gray-200">
        {/* Base line */}
        <div className="absolute top-1/2 left-0 right-0 h-0.5 bg-gray-300 -translate-y-1/2" />

        {ahaMoments.map((ts, i) => (
          <EventMarker
            key={`aha-${i}`}
            icon="💡"
            color="#eab308"
            tooltip={`Momen Aha — ${formatSec(ts)}`}
            pct={toPct(ts)}
          />
        ))}
        {laughterEvents.map((ts, i) => (
          <EventMarker
            key={`laugh-${i}`}
            icon="😄"
            color="#f97316"
            tooltip={`Tawa — ${formatSec(ts)}`}
            pct={toPct(ts)}
          />
        ))}
        {applauseEvents.map((ts, i) => (
          <EventMarker
            key={`applause-${i}`}
            icon="👏"
            color="#22c55e"
            tooltip={`Tepuk Tangan — ${formatSec(ts)}`}
            pct={toPct(ts)}
          />
        ))}
        {seatingTransitions.map((ev, i) => (
          <EventMarker
            key={`seat-${i}`}
            icon="🪑"
            color="#3b82f6"
            tooltip={`Transisi Formasi: ${ev.formation || '?'} — ${formatSec(ev.timestamp_sec)}`}
            pct={toPct(ev.timestamp_sec)}
          />
        ))}
      </div>

      {/* Time labels */}
      <div className="flex justify-between text-xs text-gray-400 mt-1 px-1">
        <span>0:00</span>
        <span>{formatSec(videoDuration)}</span>
      </div>

      {/* Legend */}
      <div className="flex flex-wrap gap-3 mt-2">
        {EVENT_TYPES.map(({ key, icon, label, color }) => {
          const hasData =
            (key === 'aha' && ahaMoments.length > 0) ||
            (key === 'laughter' && laughterEvents.length > 0) ||
            (key === 'applause' && applauseEvents.length > 0) ||
            (key === 'seating' && seatingTransitions.length > 0);
          if (!hasData) return null;
          return (
            <span key={key} className="flex items-center gap-1 text-xs text-gray-600">
              <span>{icon}</span>
              <span style={{ color }}>{label}</span>
            </span>
          );
        })}
      </div>
    </div>
  );
};

// ─── Per-Fragment Talk-Time Bar Chart ────────────────────────────────────────

const TalkTimeTooltip = ({ active, payload, label }) => {
  if (!active || !payload?.length) return null;
  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-lg px-4 py-3 text-xs min-w-[200px]">
      <p className="font-bold text-slate-800 mb-2 border-b pb-1">{label}</p>
      {payload.map((p) => (
        <p key={p.dataKey} style={{ color: p.fill }} className="font-semibold flex justify-between mb-1">
          <span>{p.name}:</span>
          <span>{p.value != null ? `${p.value.toFixed(1)}%` : '—'}</span>
        </p>
      ))}
      <div className="mt-2 pt-2 border-t border-slate-100 text-slate-500 text-[10px] leading-relaxed">
        <p>Porsi ideal untuk aktivitas Guru adalah <b className="text-indigo-600">30% - 40%</b>.</p>
        <p>Sisa waktu sangat baik jika diisi oleh respons/diskusi Siswa.</p>
      </div>
    </div>
  );
};

const PerFragmentTalkTimeChart = ({ fragments }) => {
  const hasData = fragments.some((f) => f.teacher_talk_pct != null);
  if (!hasData) return null;

  const data = fragments.map((f) => ({
    label: f.label,
    'Guru': f.teacher_talk_pct != null ? parseFloat(f.teacher_talk_pct.toFixed(1)) : null,
    'Siswa': f.student_talk_pct != null ? parseFloat(f.student_talk_pct.toFixed(1)) : null,
  }));

  return (
    <div className="mt-5">
      <p className="text-xs font-semibold text-gray-500 uppercase tracking-wide mb-2">
        Distribusi Bicara per Fragmen
      </p>
      <ResponsiveContainer width="100%" height={180}>
        <BarChart data={data} margin={{ top: 4, right: 20, left: 0, bottom: 40 }}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10 }}
            angle={-35}
            textAnchor="end"
            interval={0}
          />
          <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} unit="%" />
          <Tooltip content={<TalkTimeTooltip />} />
          <Legend verticalAlign="top" />
          {/* Reference Areas indicating the ideal pedagogical zone */}
          <ReferenceArea y1={30} y2={40} fill="#e0e7ff" fillOpacity={0.6} />
          
          {/* Max teacher standard */}
          <ReferenceLine
            y={40}
            stroke="#6366f1"
            strokeDasharray="4 4"
            label={{ value: 'Target Maks Guru (40%)', fontSize: 10, fill: '#4f46e5', position: 'insideTopLeft' }}
          />
          {/* Min teacher standard */}
          <ReferenceLine
            y={30}
            stroke="#6366f1"
            strokeDasharray="4 4"
            label={{ value: 'Target Min Guru (30%)', fontSize: 10, fill: '#4f46e5', position: 'insideBottomLeft' }}
          />
          
          {/* Better colors for bars */}
          <Bar dataKey="Guru" stackId="talk" fill="#fb7185" name="Porsi Bicara Guru" />
          <Bar dataKey="Siswa" stackId="talk" fill="#34d399" name="Porsi Bicara Siswa" radius={[3, 3, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
};

// ─── Utility ─────────────────────────────────────────────────────────────────

function formatSec(sec) {
  if (sec == null || isNaN(sec)) return '?';
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
}

// ─── Main Component ───────────────────────────────────────────────────────────

const PedagogicalTimeline = ({
  fragments = [],
  onFragmentClick,
  activeFragmentIndex = null,
  ahaMoments = [],
  laughterEvents = [],
  applauseEvents = [],
  seatingTransitions = [],
}) => {
  if (!fragments.length) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        Tidak ada data timeline.
      </div>
    );
  }

  const handleClick = (data) => {
    if (data && data.activePayload && onFragmentClick) {
      const frag = data.activePayload[0]?.payload;
      if (frag?.index !== undefined) {
        onFragmentClick({ index: frag.index, start_sec: frag.start_sec, end_sec: frag.end_sec, label: frag.label });
      }
    }
  };

  // Compute video duration from fragments
  const videoDuration = fragments.reduce((max, f) => Math.max(max, f.end_sec || 0), 0);

  return (
    <div>
      {activeFragmentIndex !== null && (
        <div className="flex items-center gap-2 text-xs text-indigo-600 bg-indigo-50 border border-indigo-100 rounded px-3 py-1.5 mb-2">
          <span>🎯</span>
          <span>
            Fragmen <strong>{activeFragmentIndex + 1}</strong> dipilih — klip bukti di bawah disorot.
          </span>
        </div>
      )}

      {/* ── Existing Line Chart (unchanged) ── */}
      <ResponsiveContainer width="100%" height={280}>
        <LineChart
          data={fragments}
          margin={{ top: 10, right: 20, left: 0, bottom: 40 }}
          onClick={handleClick}
          style={{ cursor: 'pointer' }}
        >
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis
            dataKey="label"
            tick={{ fontSize: 10 }}
            angle={-35}
            textAnchor="end"
            interval={0}
          />
          <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
          <Tooltip content={<CustomTooltip />} />
          <Legend verticalAlign="top" />
          
          {/* Shaded Areas for Good/Bad performance */}
          <ReferenceArea y1={70} y2={100} fill="#dcfce7" fillOpacity={0.5} />
          <ReferenceArea y1={0} y2={40} fill="#fee2e2" fillOpacity={0.5} />
          
          <ReferenceLine y={70} stroke="#22c55e" strokeDasharray="4 4" label={{ value: 'Target Ideal (>70)', fontSize: 10, fill: '#16a34a', position: 'insideTopLeft' }} />
          <ReferenceLine y={40} stroke="#ef4444" strokeDasharray="4 4" label={{ value: 'Batas Peringatan (<40)', fontSize: 10, fill: '#dc2626', position: 'insideBottomLeft' }} />
          <Line
            type="monotone"
            dataKey="mindful"
            name="Mindful"
            stroke="#3b82f6"
            strokeWidth={2}
            dot={(props) => <ActiveDot key={props.key || `dot-mindful-${props.index}`} {...props} activeFragmentIndex={activeFragmentIndex} baseColor="#3b82f6" />}
            activeDot={{ r: 7, fill: '#3b82f6' }}
          />
          <Line
            type="monotone"
            dataKey="meaningful"
            name="Meaningful"
            stroke="#22c55e"
            strokeWidth={2}
            dot={(props) => <ActiveDot key={props.key || `dot-meaningful-${props.index}`} {...props} activeFragmentIndex={activeFragmentIndex} baseColor="#22c55e" />}
            activeDot={{ r: 7, fill: '#22c55e' }}
          />
          <Line
            type="monotone"
            dataKey="joyful"
            name="Joyful"
            stroke="#f97316"
            strokeWidth={2}
            dot={(props) => <ActiveDot key={props.key || `dot-joyful-${props.index}`} {...props} activeFragmentIndex={activeFragmentIndex} baseColor="#f97316" />}
            activeDot={{ r: 7, fill: '#f97316' }}
          />
        </LineChart>
      </ResponsiveContainer>

      {/* ── Event Timeline Strip ── */}
      <EventTimelineStrip
        ahaMoments={ahaMoments}
        laughterEvents={laughterEvents}
        applauseEvents={applauseEvents}
        seatingTransitions={seatingTransitions}
        videoDuration={videoDuration}
      />

      {/* ── Per-Fragment Talk-Time Bar Chart ── */}
      <PerFragmentTalkTimeChart fragments={fragments} />
    </div>
  );
};

export default PedagogicalTimeline;
