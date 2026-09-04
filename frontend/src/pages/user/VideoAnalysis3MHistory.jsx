import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useLang } from '../../contexts/LanguageContext';

/**
 * VideoAnalysis3MHistory — paginated history of 3M analysis jobs for the current user.
 */

const STATUS_STYLES = {
  complete: 'bg-green-100 text-green-700',
  processing: 'bg-blue-100 text-blue-700',
  queued: 'bg-gray-100 text-gray-600',
  failed: 'bg-red-100 text-red-700',
};

const ScoreBadge = ({ value }) => {
  if (value == null) return <span className="text-gray-300">–</span>;
  const color =
    value >= 70 ? 'text-green-600' : value >= 40 ? 'text-yellow-600' : 'text-red-600';
  return <span className={`font-semibold ${color}`}>{value.toFixed(1)}</span>;
};

const VideoAnalysis3MHistory = () => {
  const navigate = useNavigate();
  const { t } = useLang();
  const token = localStorage.getItem('token');

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(15);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const params = { page, limit };
      if (statusFilter) params.status = statusFilter;
      const res = await axios.get('/api/video-analysis/history', {
        headers: { Authorization: `Bearer ${token}` },
        params,
      });
      setItems(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      setError(err.response?.data?.detail || 'Gagal memuat riwayat.');
    } finally {
      setLoading(false);
    }
  }, [page, limit, statusFilter, token]);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  const totalPages = Math.ceil(total / limit);

  const handleExportCSV = async (jobId) => {
    try {
      const response = await axios.get(
        `/api/video-analysis/export/${jobId}/csv`,
        {
          headers: { Authorization: `Bearer ${token}` },
          responseType: 'blob',
        }
      );
      const url = URL.createObjectURL(new Blob([response.data], { type: 'text/csv' }));
      const a = document.createElement('a');
      a.href = url;
      a.download = `analisis_3m_${jobId.slice(0, 8)}.csv`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    } catch (err) {
      console.error("Export error:", err);
      alert("Gagal mengunduh file CSV.");
    }
  };

  return (
    <div className="max-w-5xl mx-auto p-4 sm:p-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3 mb-5">
        <h1 className="text-xl font-bold text-gray-800">{t('video3m.historyTitle')}</h1>
        <button
          onClick={() => navigate('/user/video-analysis-3m')}
          className="px-4 py-2 bg-indigo-600 text-white text-sm rounded-lg hover:bg-indigo-700"
        >
          {t('video3m.historyNewBtn')}
        </button>
      </div>

      {/* Filters */}
      <div className="flex gap-3 mb-4 flex-wrap">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
          className="border border-gray-300 rounded-lg px-3 py-1.5 text-sm text-gray-700"
        >
          <option value="">{t('history.filterAll') || 'Semua Status'}</option>
          <option value="complete">Selesai</option>
          <option value="processing">Diproses</option>
          <option value="queued">Antrian</option>
          <option value="failed">Gagal</option>
        </select>
      </div>

      {error && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {error}
        </div>
      )}

      {loading ? (
        <div className="text-center py-12 text-gray-400">{t('common.loading') || 'Memuat...'}</div>
      ) : (
        <>
          <div className="overflow-x-auto rounded-xl border border-gray-200 shadow-sm">
            <table className="w-full text-sm">
              <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
                <tr>
                  <th className="px-3 py-2 text-left">{t('video3m.historyColVideo')}</th>
                  <th className="px-3 py-2 text-center">{t('video3m.historyColStatus')}</th>
                  <th className="px-3 py-2 text-center">{t('video3m.historyColMindful')}</th>
                  <th className="px-3 py-2 text-center">{t('video3m.historyColMeaningful')}</th>
                  <th className="px-3 py-2 text-center">{t('video3m.historyColJoyful')}</th>
                  <th className="px-3 py-2 text-center">{t('video3m.historyColOverall')}</th>
                  <th className="px-3 py-2 text-center">{t('video3m.historyColDate')}</th>
                  <th className="px-3 py-2 text-center">{t('video3m.historyColAction')}</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-100">
                {items.length === 0 && (
                  <tr>
                    <td colSpan={8} className="text-center py-8 text-gray-400">
                      {t('video3m.historyEmpty')}
                    </td>
                  </tr>
                )}
                {items.map((item) => (
                  <tr key={item.job_id} className="hover:bg-gray-50">
                    <td className="px-3 py-2 font-medium text-gray-800 max-w-xs truncate">
                      {item.video_name || item.job_id.slice(0, 8)}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${STATUS_STYLES[item.status] || 'bg-gray-100 text-gray-600'}`}>
                        {item.status}
                      </span>
                    </td>
                    <td className="px-3 py-2 text-center"><ScoreBadge value={item.mindful_score} /></td>
                    <td className="px-3 py-2 text-center"><ScoreBadge value={item.meaningful_score} /></td>
                    <td className="px-3 py-2 text-center"><ScoreBadge value={item.joyful_score} /></td>
                    <td className="px-3 py-2 text-center"><ScoreBadge value={item.overall_3m_score} /></td>
                    <td className="px-3 py-2 text-center text-gray-500 text-xs">
                      {item.created_at ? new Date(item.created_at).toLocaleDateString('id-ID') : '–'}
                    </td>
                    <td className="px-3 py-2 text-center">
                      <div className="flex gap-1 justify-center">
                        {item.status === 'complete' && (
                          <>
                            <button
                              onClick={() => navigate(`/user/video-analysis-3m/result/${item.job_id}`)}
                              className="px-2 py-1 text-xs bg-indigo-50 text-indigo-700 rounded hover:bg-indigo-100"
                            >
                              {t('video3m.historyView')}
                            </button>
                            <button
                              onClick={() => handleExportCSV(item.job_id)}
                              className="px-2 py-1 text-xs bg-gray-50 text-gray-600 rounded hover:bg-gray-100"
                            >
                              CSV
                            </button>
                          </>
                        )}
                        {(item.status === 'processing' || item.status === 'queued') && (
                          <button
                            onClick={() => navigate(`/user/video-analysis-3m/result/${item.job_id}`)}
                            className="px-2 py-1 text-xs bg-blue-50 text-blue-700 rounded hover:bg-blue-100"
                          >
                            {t('video3m.historyMonitor')}
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* Pagination */}
          {totalPages > 1 && (
            <div className="flex items-center justify-between mt-4">
              <p className="text-sm text-gray-500">
                {total} hasil · Halaman {page} dari {totalPages}
              </p>
              <div className="flex gap-2">
                <button
                  onClick={() => setPage((p) => Math.max(1, p - 1))}
                  disabled={page === 1}
                  className="px-3 py-1 text-sm border rounded disabled:opacity-40 hover:bg-gray-50"
                >
                  ← Sebelumnya
                </button>
                <button
                  onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                  disabled={page === totalPages}
                  className="px-3 py-1 text-sm border rounded disabled:opacity-40 hover:bg-gray-50"
                >
                  Berikutnya →
                </button>
              </div>
            </div>
          )}
        </>
      )}
    </div>
  );
};

export default VideoAnalysis3MHistory;
