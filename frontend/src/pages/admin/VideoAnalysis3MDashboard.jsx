import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  LineChart,
  Line,
} from 'recharts';

/**
 * VideoAnalysis3MDashboard — admin/principal aggregate view of all 3M analyses.
 * Guarded: only admin or principal roles can access.
 */

const ScoreBadge = ({ value }) => {
  if (value == null) return <span className="text-gray-300">–</span>;
  const color =
    value >= 70 ? 'text-green-600' : value >= 40 ? 'text-yellow-600' : 'text-red-600';
  return <span className={`font-semibold ${color}`}>{value.toFixed(1)}</span>;
};

const VideoAnalysis3MDashboard = () => {
  const navigate = useNavigate();
  const token = localStorage.getItem('token');
  const role = localStorage.getItem('role');

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Guard: redirect non-admin/non-principal
  useEffect(() => {
    if (role !== 'admin' && role !== 'principal') {
      navigate('/user/dashboard');
    }
  }, [role, navigate]);

  const fetchData = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const res = await axios.get('/api/video-analysis/history', {
        headers: { Authorization: `Bearer ${token}` },
        params: { page, limit, status: 'complete' },
      });
      setItems(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Gagal memuat data.');
    } finally {
      setLoading(false);
    }
  }, [page, limit, token]);

  useEffect(() => {
    fetchData();
  }, [fetchData]);

  // Aggregate stats
  const completed = items.filter((i) => i.overall_3m_score != null);
  const avgMindful = completed.length
    ? completed.reduce((s, i) => s + (i.mindful_score || 0), 0) / completed.length
    : 0;
  const avgMeaningful = completed.length
    ? completed.reduce((s, i) => s + (i.meaningful_score || 0), 0) / completed.length
    : 0;
  const avgJoyful = completed.length
    ? completed.reduce((s, i) => s + (i.joyful_score || 0), 0) / completed.length
    : 0;
  const avgOverall = completed.length
    ? completed.reduce((s, i) => s + (i.overall_3m_score || 0), 0) / completed.length
    : 0;

  // Trend data (last 10 completed, ordered by date)
  const trendData = [...completed]
    .sort((a, b) => new Date(a.created_at) - new Date(b.created_at))
    .slice(-10)
    .map((item, idx) => ({
      label: `#${idx + 1}`,
      mindful: item.mindful_score || 0,
      meaningful: item.meaningful_score || 0,
      joyful: item.joyful_score || 0,
    }));

  // Anonymized teacher comparison
  const teacherMap = {};
  completed.forEach((item) => {
    const key = item.job_id.slice(0, 8); // anonymized
    if (!teacherMap[key]) teacherMap[key] = { count: 0, mindful: 0, meaningful: 0, joyful: 0, overall: 0 };
    teacherMap[key].count++;
    teacherMap[key].mindful += item.mindful_score || 0;
    teacherMap[key].meaningful += item.meaningful_score || 0;
    teacherMap[key].joyful += item.joyful_score || 0;
    teacherMap[key].overall += item.overall_3m_score || 0;
  });
  const teacherRows = Object.entries(teacherMap).map(([key, v], idx) => ({
    label: `Guru ${String.fromCharCode(65 + idx)}`,
    count: v.count,
    mindful: v.mindful / v.count,
    meaningful: v.meaningful / v.count,
    joyful: v.joyful / v.count,
    overall: v.overall / v.count,
  }));

  const totalPages = Math.ceil(total / limit);

  return (
    <div className="max-w-6xl mx-auto p-4 sm:p-6">
      <h1 className="text-2xl font-bold text-gray-800 mb-1">Dashboard 3M — Sekolah</h1>
      <p className="text-gray-500 text-sm mb-6">Ringkasan analisis video pembelajaran seluruh guru.</p>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">{error}</div>
      )}

      {/* Stat cards */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
        {[
          { label: 'Total Analisis', value: total, unit: '' },
          { label: 'Rata-rata Mindful', value: avgMindful.toFixed(1), unit: '/100' },
          { label: 'Rata-rata Meaningful', value: avgMeaningful.toFixed(1), unit: '/100' },
          { label: 'Rata-rata Joyful', value: avgJoyful.toFixed(1), unit: '/100' },
        ].map(({ label, value, unit }) => (
          <div key={label} className="bg-white rounded-xl border border-gray-200 p-4 text-center shadow-sm">
            <p className="text-xs text-gray-500 mb-1">{label}</p>
            <p className="text-2xl font-bold text-indigo-600">{value}<span className="text-sm text-gray-400">{unit}</span></p>
          </div>
        ))}
      </div>

      {/* Trend chart */}
      {trendData.length > 1 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Tren Skor 3M (10 Analisis Terakhir)</h3>
          <ResponsiveContainer width="100%" height={220}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="mindful" name="Mindful" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="meaningful" name="Meaningful" stroke="#22c55e" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="joyful" name="Joyful" stroke="#f97316" strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Teacher comparison */}
      {teacherRows.length > 0 && (
        <div className="bg-white rounded-xl border border-gray-200 p-4 mb-6 shadow-sm">
          <h3 className="text-sm font-semibold text-gray-700 mb-3">Perbandingan Rata-rata per Guru (Anonim)</h3>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={teacherRows}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="label" tick={{ fontSize: 11 }} />
              <YAxis domain={[0, 100]} tick={{ fontSize: 11 }} />
              <Tooltip />
              <Legend />
              <Bar dataKey="mindful" name="Mindful" fill="#3b82f6" />
              <Bar dataKey="meaningful" name="Meaningful" fill="#22c55e" />
              <Bar dataKey="joyful" name="Joyful" fill="#f97316" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* History table */}
      <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
        <div className="px-4 py-3 border-b flex items-center justify-between">
          <h3 className="text-sm font-semibold text-gray-700">Semua Analisis</h3>
          <span className="text-xs text-gray-400">{total} total</span>
        </div>
        {loading ? (
          <div className="text-center py-10 text-gray-400">Memuat...</div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
                <tr>
                  <th className="px-3 py-2 text-left">Video</th>
                  <th className="px-3 py-2 text-center">Mindful</th>
                  <th className="px-3 py-2 text-center">Meaningful</th>
                  <th className="px-3 py-2 text-center">Joyful</th>
                  <th className="px-3 py-2 text-center">Overall</th>
                  <th className="px-3 py-2 text-center">Tanggal</th>
                  <th className="px-3 py-2 text-center">Aksi</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.map((item) => (
                  <tr key={item.job_id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 text-gray-800 max-w-xs truncate">{item.video_name || item.job_id.slice(0, 8)}</td>
                    <td className="px-3 py-2 text-center"><ScoreBadge value={item.mindful_score} /></td>
                    <td className="px-3 py-2 text-center"><ScoreBadge value={item.meaningful_score} /></td>
                    <td className="px-3 py-2 text-center"><ScoreBadge value={item.joyful_score} /></td>
                    <td className="px-3 py-2 text-center"><ScoreBadge value={item.overall_3m_score} /></td>
                    <td className="px-3 py-2 text-center text-gray-500 text-xs">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString('id-ID') : '–'}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <button
                        onClick={() => navigate(`/user/video-analysis-3m/result/${item.job_id}`)}
                        className="px-2 py-1 text-xs bg-indigo-50 text-indigo-700 rounded hover:bg-indigo-100"
                      >
                        Lihat
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}

        {totalPages > 1 && (
          <div className="flex items-center justify-between px-4 py-3 border-t">
            <p className="text-xs text-gray-500">Halaman {page} dari {totalPages}</p>
            <div className="flex gap-2">
              <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page === 1} className="px-3 py-1 text-xs border rounded disabled:opacity-40">←</button>
              <button onClick={() => setPage((p) => Math.min(totalPages, p + 1))} disabled={page === totalPages} className="px-3 py-1 text-xs border rounded disabled:opacity-40">→</button>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default VideoAnalysis3MDashboard;
