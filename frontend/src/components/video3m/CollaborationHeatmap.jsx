import React, { useRef, useEffect, useState, useCallback, useMemo } from 'react';

/**
 * CollaborationHeatmap — renders classroom position density on a canvas.
 * Props:
 *   heatmap: number[][] (2D grid, values 0–1)
 *   clusters: Array<{ x, y, label, density }> (cluster annotations)
 */

// ─── Color scale: white → yellow → orange → red ───────────────────────────
function valueToColor(val) {
  const v = Math.max(0, Math.min(1, val));
  if (v < 0.25) {
    const t = v / 0.25;
    return [255, Math.round(255 - t * 30), Math.round(255 - t * 180)];
  } else if (v < 0.5) {
    const t = (v - 0.25) / 0.25;
    return [255, Math.round(225 - t * 105), Math.round(75 - t * 75)];
  } else if (v < 0.75) {
    const t = (v - 0.5) / 0.25;
    return [255, Math.round(120 - t * 60), 0];
  } else {
    const t = (v - 0.75) / 0.25;
    return [255, Math.round(60 - t * 60), 0];
  }
}

// ─── Derive human-readable stats from heatmap data ────────────────────────
function computeStats(heatmap, clusters, discussionGroupsCount) {
  if (!heatmap.length) return null;
  const rows = heatmap.length;
  const cols = heatmap[0]?.length || 0;
  if (!cols) return null;

  let maxVal = 0, maxR = 0, maxC = 0;
  let totalVal = 0, cellCount = 0;
  let passiveCells = 0;

  for (let r = 0; r < rows; r++) {
    for (let c = 0; c < cols; c++) {
      const v = heatmap[r][c] ?? 0;
      totalVal += v;
      cellCount++;
      if (v > maxVal) { maxVal = v; maxR = r; maxC = c; }
      if (v < 0.2) passiveCells++;
    }
  }

  const avgDensity = cellCount > 0 ? (totalVal / cellCount) * 100 : 0;
  const passivePct = cellCount > 0 ? (passiveCells / cellCount) * 100 : 0;

  // Use discussionGroupsCount from backend if provided, otherwise fall back to clusters.length
  const clusterCount = discussionGroupsCount != null ? discussionGroupsCount : clusters.length;

  return {
    hotspot: { row: maxR + 1, col: maxC + 1, val: Math.round(maxVal * 100) },
    clusterCount,
    avgDensity: Math.round(avgDensity),
    passivePct: Math.round(passivePct),
    rows,
    cols,
    hotRow: maxR,
    hotCol: maxC,
  };
}

// ─── Generate natural-language summary ────────────────────────────────────
function generateSummary(stats, heatmap) {
  if (!stats) return '';
  const { hotRow, hotCol, rows, cols, clusterCount, avgDensity, passivePct } = stats;

  // Determine zone labels
  const rowZone = hotRow < rows / 3 ? 'depan' : hotRow < (rows * 2) / 3 ? 'tengah' : 'belakang';
  const colZone = hotCol < cols / 3 ? 'kiri' : hotCol < (cols * 2) / 3 ? 'tengah' : 'kanan';
  const zoneLabel = rowZone === colZone ? rowZone : `${rowZone}-${colZone}`;

  const parts = [];

  parts.push(
    `Siswa paling aktif berkolaborasi di area ${zoneLabel} kelas.`
  );

  if (clusterCount > 0) {
    parts.push(
      `Terdeteksi ${clusterCount} kelompok diskusi aktif.`
    );
  } else {
    parts.push('Belum terdeteksi kelompok diskusi yang jelas.');
  }

  if (passivePct > 40) {
    // Find which zone is most passive
    const halfR = Math.floor(rows / 2);
    const halfC = Math.floor(cols / 2);
    let quadSums = { 'depan-kiri': 0, 'depan-kanan': 0, 'belakang-kiri': 0, 'belakang-kanan': 0 };
    let quadCounts = { 'depan-kiri': 0, 'depan-kanan': 0, 'belakang-kiri': 0, 'belakang-kanan': 0 };
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const rz = r < halfR ? 'depan' : 'belakang';
        const cz = c < halfC ? 'kiri' : 'kanan';
        const key = `${rz}-${cz}`;
        quadSums[key] += heatmap[r][c] ?? 0;
        quadCounts[key]++;
      }
    }
    let minAvg = Infinity, passiveZone = '';
    for (const [key, sum] of Object.entries(quadSums)) {
      const avg = sum / (quadCounts[key] || 1);
      if (avg < minAvg) { minAvg = avg; passiveZone = key; }
    }
    parts.push(`Area ${passiveZone} kelas cenderung pasif (${passivePct}% area tidak aktif).`);
  } else {
    parts.push(`Distribusi siswa cukup merata dengan rata-rata kepadatan ${avgDensity}%.`);
  }

  return parts.join(' ');
}

// ─── Generate teacher recommendations ─────────────────────────────────────
function generateRecommendations(stats, heatmap) {
  if (!stats) return [];
  const { passivePct, avgDensity, clusterCount, hotRow, hotCol, rows, cols } = stats;
  const recs = [];

  // Passive area recommendation
  if (passivePct > 35) {
    const halfR = Math.floor(rows / 2);
    const halfC = Math.floor(cols / 2);
    let quadSums = { 'depan-kiri': 0, 'depan-kanan': 0, 'belakang-kiri': 0, 'belakang-kanan': 0 };
    let quadCounts = { 'depan-kiri': 0, 'depan-kanan': 0, 'belakang-kiri': 0, 'belakang-kanan': 0 };
    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const rz = r < halfR ? 'depan' : 'belakang';
        const cz = c < halfC ? 'kiri' : 'kanan';
        const key = `${rz}-${cz}`;
        quadSums[key] += heatmap[r][c] ?? 0;
        quadCounts[key]++;
      }
    }
    let minAvg = Infinity, passiveZone = '';
    for (const [key, sum] of Object.entries(quadSums)) {
      const avg = sum / (quadCounts[key] || 1);
      if (avg < minAvg) { minAvg = avg; passiveZone = key; }
    }
    recs.push({
      icon: '🔄',
      text: `Pertimbangkan memindahkan kegiatan kelompok ke area ${passiveZone} yang kurang aktif agar distribusi lebih merata.`,
    });
  }

  // Clustering recommendation
  if (clusterCount === 0) {
    recs.push({
      icon: '👥',
      text: 'Tidak terdeteksi kelompok diskusi yang jelas. Coba terapkan aktivitas kolaboratif terstruktur seperti diskusi kelompok kecil.',
    });
  } else if (clusterCount >= 4) {
    recs.push({
      icon: '✅',
      text: `Terdeteksi ${clusterCount} kelompok diskusi aktif — kolaborasi kelas berjalan baik. Pertahankan pola ini.`,
    });
  }

  // Low average density
  if (avgDensity < 30) {
    recs.push({
      icon: '⚠️',
      text: 'Rata-rata kepadatan siswa rendah. Pastikan semua siswa terlibat aktif, bukan hanya kelompok tertentu.',
    });
  }

  // Hotspot too concentrated
  const hotRowZone = hotRow < rows / 3 ? 'depan' : hotRow < (rows * 2) / 3 ? 'tengah' : 'belakang';
  if (hotRowZone === 'depan' && passivePct > 30) {
    recs.push({
      icon: '📍',
      text: 'Aktivitas terpusat di bagian depan kelas. Dorong siswa di bagian belakang untuk lebih aktif berpartisipasi.',
    });
  }

  if (recs.length === 0) {
    recs.push({
      icon: '✅',
      text: 'Pola kolaborasi kelas terlihat baik dan merata. Tidak ada rekomendasi khusus saat ini.',
    });
  }

  return recs;
}

// ─── Main Component ────────────────────────────────────────────────────────
const CollaborationHeatmap = ({ heatmap = [], clusters = [], discussionGroupsCount = null }) => {
  const canvasRef = useRef(null);
  const legendRef = useRef(null);
  const cellDims = useRef({ cellW: 1, cellH: 1, rows: 0, cols: 0 });
  const [tooltip, setTooltip] = useState(null);

  // Compute derived data once
  const stats = useMemo(() => computeStats(heatmap, clusters, discussionGroupsCount), [heatmap, clusters, discussionGroupsCount]);
  const summary = useMemo(() => generateSummary(stats, heatmap), [stats, heatmap]);
  const recommendations = useMemo(() => generateRecommendations(stats, heatmap), [stats, heatmap]);

  const draw = useCallback(() => {
    const canvas = canvasRef.current;
    if (!canvas || !heatmap.length) return;

    const rows = heatmap.length;
    const cols = heatmap[0]?.length || 0;
    if (!cols) return;

    const containerWidth = canvas.parentElement?.clientWidth || 600;
    const cellW = Math.max(4, Math.floor(containerWidth / cols));
    const cellH = Math.max(4, Math.floor((containerWidth * 0.55) / rows));

    canvas.width = cellW * cols;
    canvas.height = cellH * rows;
    cellDims.current = { cellW, cellH, rows, cols };

    const ctx = canvas.getContext('2d');

    // Background
    ctx.fillStyle = '#f8fafc';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // ── Overlay: classroom outline ──────────────────────────────────
    // Blackboard at top (10% height)
    const bbH = Math.max(18, Math.round(canvas.height * 0.10));
    ctx.fillStyle = '#1e3a5f';
    ctx.fillRect(Math.round(canvas.width * 0.1), 4, Math.round(canvas.width * 0.8), bbH - 8);
    ctx.fillStyle = '#ffffff';
    ctx.font = `bold ${Math.max(10, bbH - 10)}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText('📋 Papan Tulis', canvas.width / 2, bbH - 4);

    // Teacher desk (bottom-center, 8% height)
    const deskW = Math.round(canvas.width * 0.18);
    const deskH = Math.max(14, Math.round(canvas.height * 0.07));
    const deskX = Math.round((canvas.width - deskW) / 2);
    const deskY = canvas.height - deskH - 4;
    ctx.fillStyle = '#d97706';
    ctx.fillRect(deskX, deskY, deskW, deskH);
    ctx.fillStyle = '#ffffff';
    ctx.font = `bold ${Math.max(9, deskH - 6)}px sans-serif`;
    ctx.textAlign = 'center';
    ctx.fillText('🧑‍🏫 Guru', canvas.width / 2, deskY + deskH - 4);

    // Classroom border
    ctx.strokeStyle = '#94a3b8';
    ctx.lineWidth = 2;
    ctx.strokeRect(1, 1, canvas.width - 2, canvas.height - 2);

    // ── Heatmap cells ───────────────────────────────────────────────
    // Offset cells to leave room for blackboard overlay
    const topOffset = bbH + 2;
    const bottomOffset = deskH + 8;
    const usableH = canvas.height - topOffset - bottomOffset;
    const actualCellH = Math.max(2, Math.floor(usableH / rows));

    // Recalculate for hit-testing with offset
    cellDims.current = { cellW, cellH: actualCellH, rows, cols, topOffset };

    for (let r = 0; r < rows; r++) {
      for (let c = 0; c < cols; c++) {
        const val = heatmap[r][c] ?? 0;
        const [red, green, blue] = valueToColor(val);
        ctx.fillStyle = `rgba(${red},${green},${blue},0.82)`;
        ctx.fillRect(c * cellW, topOffset + r * actualCellH, cellW, actualCellH);
      }
    }

    // Grid lines
    ctx.strokeStyle = 'rgba(0,0,0,0.05)';
    ctx.lineWidth = 0.5;
    for (let c = 0; c <= cols; c++) {
      ctx.beginPath();
      ctx.moveTo(c * cellW, topOffset);
      ctx.lineTo(c * cellW, topOffset + rows * actualCellH);
      ctx.stroke();
    }
    for (let r = 0; r <= rows; r++) {
      ctx.beginPath();
      ctx.moveTo(0, topOffset + r * actualCellH);
      ctx.lineTo(canvas.width, topOffset + r * actualCellH);
      ctx.stroke();
    }

    // ── Cluster annotations ─────────────────────────────────────────
    ctx.font = 'bold 10px sans-serif';
    ctx.textAlign = 'center';
    clusters.forEach((cluster) => {
      const px = (cluster.x / cols) * canvas.width + cellW / 2;
      const py = topOffset + (cluster.y / rows) * (rows * actualCellH) + actualCellH / 2;

      ctx.shadowColor = 'rgba(0,0,0,0.25)';
      ctx.shadowBlur = 4;
      ctx.beginPath();
      ctx.arc(px, py, 14, 0, 2 * Math.PI);
      ctx.fillStyle = 'rgba(255,255,255,0.88)';
      ctx.fill();
      ctx.strokeStyle = '#f97316';
      ctx.lineWidth = 2;
      ctx.stroke();
      ctx.shadowBlur = 0;

      ctx.fillStyle = '#1e293b';
      ctx.fillText(cluster.label?.slice(0, 2) || '👥', px, py + 4);
    });

    // ── Legend bar ──────────────────────────────────────────────────
    const legend = legendRef.current;
    if (legend) {
      const lCtx = legend.getContext('2d');
      const lw = legend.width;
      const lh = legend.height;
      const grad = lCtx.createLinearGradient(0, 0, lw, 0);
      for (let i = 0; i <= 10; i++) {
        const t = i / 10;
        const [r, g, b] = valueToColor(t);
        grad.addColorStop(t, `rgb(${r},${g},${b})`);
      }
      lCtx.clearRect(0, 0, lw, lh);
      lCtx.fillStyle = grad;
      lCtx.fillRect(0, 0, lw, lh);
      lCtx.strokeStyle = 'rgba(0,0,0,0.12)';
      lCtx.lineWidth = 1;
      lCtx.strokeRect(0, 0, lw, lh);
    }
  }, [heatmap, clusters]);

  useEffect(() => { draw(); }, [draw]);

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ro = new ResizeObserver(() => draw());
    ro.observe(canvas.parentElement);
    return () => ro.disconnect();
  }, [draw]);

  const handleMouseMove = useCallback((e) => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const rect = canvas.getBoundingClientRect();
    const scaleX = canvas.width / rect.width;
    const scaleY = canvas.height / rect.height;
    const mx = (e.clientX - rect.left) * scaleX;
    const my = (e.clientY - rect.top) * scaleY;
    const { cellW, cellH, rows, cols, topOffset = 0 } = cellDims.current;
    const adjustedY = my - topOffset;
    const c = Math.floor(mx / cellW);
    const r = Math.floor(adjustedY / cellH);
    if (r >= 0 && r < rows && c >= 0 && c < cols) {
      const val = heatmap[r]?.[c] ?? 0;
      setTooltip({ x: e.clientX - rect.left, y: e.clientY - rect.top, value: val, row: r, col: c });
    } else {
      setTooltip(null);
    }
  }, [heatmap]);

  const handleMouseLeave = useCallback(() => setTooltip(null), []);

  if (!heatmap.length) {
    return (
      <div className="flex items-center justify-center h-40 text-gray-400 text-sm">
        Tidak ada data heatmap.
      </div>
    );
  }

  return (
    <div className="w-full space-y-4">

      {/* ── 2. Stat cards ─────────────────────────────────────────── */}
      {stats && (
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <div className="flex items-center gap-2 bg-red-50 border border-red-100 rounded-lg px-3 py-2">
            <span className="text-lg">🔴</span>
            <div>
              <p className="text-xs text-gray-500 leading-tight">Titik terpanas</p>
              <p className="text-sm font-semibold text-gray-800">
                Baris {stats.hotspot.row}, Kol {stats.hotspot.col}
              </p>
              <p className="text-xs text-red-500 font-mono">{stats.hotspot.val}%</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-blue-50 border border-blue-100 rounded-lg px-3 py-2">
            <span className="text-lg">👥</span>
            <div>
              <p className="text-xs text-gray-500 leading-tight">Kelompok diskusi</p>
              <p className="text-sm font-semibold text-gray-800">{stats.clusterCount} terdeteksi</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-amber-50 border border-amber-100 rounded-lg px-3 py-2">
            <span className="text-lg">📊</span>
            <div>
              <p className="text-xs text-gray-500 leading-tight">Rata-rata kepadatan</p>
              <p className="text-sm font-semibold text-gray-800">{stats.avgDensity}%</p>
            </div>
          </div>
          <div className="flex items-center gap-2 bg-gray-50 border border-gray-200 rounded-lg px-3 py-2">
            <span className="text-lg">⚠️</span>
            <div>
              <p className="text-xs text-gray-500 leading-tight">Area pasif</p>
              <p className="text-sm font-semibold text-gray-800">{stats.passivePct}% ruang</p>
            </div>
          </div>
        </div>
      )}

      {/* ── 3. Heatmap canvas with classroom overlay ──────────────── */}
      <div className="w-full overflow-hidden rounded-lg border border-gray-200 bg-slate-50 relative">
        <canvas
          ref={canvasRef}
          className="w-full"
          style={{ display: 'block', cursor: 'crosshair' }}
          onMouseMove={handleMouseMove}
          onMouseLeave={handleMouseLeave}
        />
        {/* Tooltip */}
        {tooltip && (
          <div
            className="absolute z-50 pointer-events-none bg-gray-900 text-white text-xs rounded px-2 py-1 shadow-lg whitespace-nowrap"
            style={{ left: tooltip.x + 12, top: tooltip.y - 28 }}
          >
            Baris {tooltip.row + 1}, Kolom {tooltip.col + 1}:{' '}
            <span className="font-bold">{(tooltip.value * 100).toFixed(1)}%</span>
          </div>
        )}
      </div>

      {/* Axis labels */}
      <div className="flex justify-between text-xs text-gray-500 px-1 -mt-2">
        <span>← Kiri Kelas</span>
        <span className="font-medium text-gray-600">Posisi Horizontal Siswa</span>
        <span>Kanan Kelas →</span>
      </div>

      {/* Color legend */}
      <div className="flex items-center gap-3 px-1">
        <span className="text-xs text-gray-500 whitespace-nowrap">Kepadatan:</span>
        <div className="flex-1 flex flex-col gap-0.5">
          <canvas ref={legendRef} width={300} height={14} className="w-full rounded" style={{ display: 'block' }} />
          <div className="flex justify-between text-xs text-gray-400">
            <span>Rendah (0%)</span>
            <span>Sedang (50%)</span>
            <span>Tinggi (100%)</span>
          </div>
        </div>
      </div>

      {/* ── 1. Auto summary text ──────────────────────────────────── */}
      {summary && (
        <div className="flex gap-3 bg-blue-50 border border-blue-100 rounded-lg px-4 py-3">
          <span className="text-xl flex-shrink-0">🗺️</span>
          <p className="text-sm text-blue-800 leading-relaxed">{summary}</p>
        </div>
      )}

      {/* ── 4. Teacher recommendations ───────────────────────────── */}
      {recommendations.length > 0 && (
        <div className="border border-indigo-100 rounded-lg overflow-hidden">
          <div className="bg-indigo-50 px-4 py-2 flex items-center gap-2">
            <span className="text-base">💡</span>
            <h4 className="text-sm font-semibold text-indigo-800">Rekomendasi untuk Guru</h4>
          </div>
          <ul className="divide-y divide-gray-100">
            {recommendations.map((rec, i) => (
              <li key={i} className="flex gap-3 px-4 py-3 bg-white">
                <span className="text-base flex-shrink-0">{rec.icon}</span>
                <p className="text-sm text-gray-700 leading-relaxed">{rec.text}</p>
              </li>
            ))}
          </ul>
        </div>
      )}

    </div>
  );
};

export default CollaborationHeatmap;
