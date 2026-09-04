import React, { useState, useEffect, useRef } from 'react';

/**
 * EvidenceClipPlayer — thumbnail grid + modal video player for evidence clips.
 * Props:
 *   clips: Array<{ id, clip_name, clip_url, start_sec, end_sec, clip_type, aspect, description, score }>
 *   highlightFragment: { index, start_sec, end_sec } | null
 *     When set, clips overlapping that time range are highlighted and scrolled into view.
 *   onClearHighlight: () => void  — called when user clicks "Tampilkan semua"
 */

const ASPECT_COLORS = {
  mindful: 'bg-blue-50 border border-blue-200 text-blue-700',
  meaningful: 'bg-emerald-50 border border-emerald-200 text-emerald-700',
  joyful: 'bg-orange-50 border border-orange-200 text-orange-700',
};

const TYPE_COLORS = {
  best_practice: 'bg-teal-50 border border-teal-200 text-teal-700',
  improvement: 'bg-rose-50 border border-rose-200 text-rose-700',
};

const TYPE_LABELS = {
  best_practice: 'Praktik Terbaik',
  improvement: 'Perlu Perbaikan',
};

const formatTime = (sec) => {
  const m = Math.floor(sec / 60);
  const s = Math.floor(sec % 60);
  return `${m}:${s.toString().padStart(2, '0')}`;
};

const EvidenceClipPlayer = ({ clips = [], highlightFragment = null, onClearHighlight }) => {
  const [selected, setSelected] = useState(null);
  const highlightedRef = useRef(null);

  // Determine which clips overlap the highlighted fragment time range
  const highlightedClipIds = React.useMemo(() => {
    if (!highlightFragment) return new Set();
    const { start_sec, end_sec } = highlightFragment;
    return new Set(
      clips
        .filter((c) => c.end_sec > start_sec && c.start_sec < end_sec)
        .map((c) => c.id)
    );
  }, [highlightFragment, clips]);

  // Auto-scroll to first highlighted clip when fragment changes
  useEffect(() => {
    if (highlightFragment && highlightedRef.current) {
      highlightedRef.current.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }
  }, [highlightFragment]);

  const bestPractice = clips.filter((c) => c.clip_type === 'best_practice');
  const improvement = clips.filter((c) => c.clip_type === 'improvement');

  const renderClipCard = (clip, isFirstHighlighted) => {
    const isHighlighted = highlightedClipIds.has(clip.id);
    return (
      <button
        key={clip.id}
        ref={isFirstHighlighted ? highlightedRef : null}
        onClick={() => setSelected(clip)}
        className={`text-left rounded-xl border overflow-hidden hover:shadow-lg transition-all duration-300 bg-white group flex flex-col h-full
          ${isHighlighted
            ? 'border-violet-300 ring-4 ring-violet-50 shadow-md scale-[1.02]'
            : 'border-slate-200 hover:-translate-y-1'
          }`}
      >
        {/* Thumbnail placeholder */}
        <div className={`h-28 w-full flex items-center justify-center relative bg-gradient-to-br transition-all duration-300
          ${isHighlighted ? 'from-violet-100 to-teal-50' : 'from-slate-100 to-slate-50 border-b border-slate-100'}`}
        >
          <div className={`w-12 h-12 rounded-full flex items-center justify-center shadow-sm transition-all duration-300 group-hover:scale-110 ${isHighlighted ? 'bg-violet-500 shadow-violet-500/30' : 'bg-white shadow-slate-200/50'}`}>
            <svg className={`w-5 h-5 ml-1 ${isHighlighted ? 'text-white' : 'text-slate-400 group-hover:text-violet-500'}`} fill="currentColor" viewBox="0 0 24 24">
              <path d="M8 5v14l11-7z" />
            </svg>
          </div>
          {isHighlighted && (
            <span className="absolute top-2 right-2 bg-gradient-to-r from-violet-500 to-teal-400 text-white shadow-md text-[10px] uppercase tracking-wider px-2 py-0.5 rounded-full font-bold">
              ✦ Fragmen ini
            </span>
          )}
        </div>
        <div className="p-3 flex-1 flex flex-col">
          <div className="flex gap-1 flex-wrap mb-1">
            <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${ASPECT_COLORS[clip.aspect] || 'bg-gray-100 text-gray-600'}`}>
              {clip.aspect}
            </span>
            <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${TYPE_COLORS[clip.clip_type] || 'bg-gray-100 text-gray-600'}`}>
              {TYPE_LABELS[clip.clip_type] || clip.clip_type}
            </span>
          </div>
          <p className="text-xs font-semibold text-slate-700 line-clamp-2 mt-2 flex-1 leading-relaxed">{clip.description || clip.clip_name}</p>
          <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-100">
            <span className="text-xs font-mono font-medium text-slate-500 bg-slate-50 px-2 py-1 rounded">
              {formatTime(clip.start_sec)} – {formatTime(clip.end_sec)}
            </span>
            <span className="text-xs font-bold text-slate-400">
              Skor: {clip.score?.toFixed(0)}
            </span>
          </div>
        </div>
      </button>
    );
  };

  const renderGroup = (group, title) => {
    if (!group.length) return null;
    let firstHighlightedSeen = false;
    return (
      <div className="mb-4">
        <h4 className="text-sm font-semibold text-gray-600 mb-2">{title}</h4>
        <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
          {group.map((clip) => {
            const isFirst = !firstHighlightedSeen && highlightedClipIds.has(clip.id);
            if (isFirst) firstHighlightedSeen = true;
            return renderClipCard(clip, isFirst);
          })}
        </div>
      </div>
    );
  };

  return (
    <div>
      {highlightFragment && (
        <div className="flex items-center justify-between bg-violet-50 border border-violet-200 rounded-xl px-4 py-3 mb-4 shadow-sm">
          <div className="flex items-center gap-3 text-sm text-violet-800">
            <span className="text-lg">🎯</span>
            <span>
              Menampilkan klip untuk{' '}
              <strong className="font-bold">Fragmen {highlightFragment.index + 1}</strong>
              {' '}<span className="text-violet-600/80">({formatTime(highlightFragment.start_sec)} – {formatTime(highlightFragment.end_sec)})</span>
              {highlightedClipIds.size === 0 && (
                <span className="text-violet-400 font-medium ml-2">— tidak ada klip di rentang ini</span>
              )}
            </span>
          </div>
          <button
            onClick={onClearHighlight}
            className="text-xs font-semibold text-violet-600 hover:text-violet-800 bg-white hover:bg-violet-100 px-3 py-1.5 rounded-lg border border-violet-200 transition-colors whitespace-nowrap shadow-sm"
          >
            Tampilkan semua
          </button>
        </div>
      )}

      {!clips.length && (
        <p className="text-sm text-gray-400 text-center py-6">Tidak ada klip bukti tersedia.</p>
      )}
      {renderGroup(bestPractice, 'Praktik Terbaik')}
      {renderGroup(improvement, 'Peluang Perbaikan')}

      {/* Modal */}
      {selected && (
        <div
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/70"
          onClick={() => setSelected(null)}
        >
          <div
            className="bg-white rounded-xl shadow-2xl max-w-2xl w-full mx-4 overflow-hidden"
            onClick={(e) => e.stopPropagation()}
          >
            <div className="flex items-center justify-between px-4 py-3 border-b">
              <div className="flex gap-2">
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${ASPECT_COLORS[selected.aspect] || 'bg-gray-100 text-gray-600'}`}>
                  {selected.aspect}
                </span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${TYPE_COLORS[selected.clip_type] || 'bg-gray-100 text-gray-600'}`}>
                  {TYPE_LABELS[selected.clip_type] || selected.clip_type}
                </span>
              </div>
              <button
                onClick={() => setSelected(null)}
                className="text-gray-400 hover:text-gray-600 text-xl leading-none"
              >
                ×
              </button>
            </div>
            <video
              src={selected.clip_url}
              controls
              autoPlay
              className="w-full max-h-80 bg-black"
            />
            <div className="px-4 py-3">
              <p className="text-sm text-gray-700">{selected.description}</p>
              <p className="text-xs text-gray-400 mt-1">
                {formatTime(selected.start_sec)} – {formatTime(selected.end_sec)} &nbsp;|&nbsp; Skor: {selected.score?.toFixed(0)}/100
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default EvidenceClipPlayer;
