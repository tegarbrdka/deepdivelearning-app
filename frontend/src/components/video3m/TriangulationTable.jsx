import React from 'react';

/**
 * TriangulationTable — comparison table of planned vs detected activities.
 * Props:
 *   triangulation: { alignment_score: number, items: Array<{ activity, planned, detected, status, evidence, recommendation }> }
 */

const STATUS_STYLES = {
  success: 'bg-green-100 text-green-700 border-green-300',
  misalignment: 'bg-red-100 text-red-700 border-red-300',
  not_detected: 'bg-gray-100 text-gray-500 border-gray-300',
};

const STATUS_LABELS = {
  success: 'Sesuai',
  misalignment: 'Tidak Sesuai',
  not_detected: 'Tidak Terdeteksi',
};

const TriangulationTable = ({ triangulation = {} }) => {
  const { alignment_score = 0, items = [] } = triangulation;

  if (!items.length) {
    return (
      <p className="text-sm text-gray-400 text-center py-6">
        Tidak ada data triangulasi RPP.
      </p>
    );
  }

  const scoreColor =
    alignment_score >= 70
      ? 'text-green-600'
      : alignment_score >= 40
      ? 'text-yellow-600'
      : 'text-red-600';

  return (
    <div>
      <div className="flex items-center gap-2 mb-3">
        <span className="text-sm text-gray-600 font-medium">Skor Keselarasan RPP:</span>
        <span className={`text-xl font-bold ${scoreColor}`}>
          {alignment_score.toFixed(1)}%
        </span>
      </div>

      <div className="overflow-x-auto rounded-lg border border-gray-200">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 text-gray-600 text-xs uppercase">
            <tr>
              <th className="px-3 py-2 text-left">Aktivitas Direncanakan</th>
              <th className="px-3 py-2 text-center">Terdeteksi</th>
              <th className="px-3 py-2 text-center">Status</th>
              <th className="px-3 py-2 text-left">Bukti / Rekomendasi</th>
            </tr>
          </thead>
          <tbody className="divide-y divide-gray-100">
            {items.map((item, idx) => (
              <tr key={idx} className="hover:bg-gray-50">
                <td className="px-3 py-2 font-medium text-gray-800">{item.activity}</td>
                <td className="px-3 py-2 text-center">
                  {item.detected ? (
                    <span className="text-green-500 text-base">✓</span>
                  ) : (
                    <span className="text-gray-300 text-base">–</span>
                  )}
                </td>
                <td className="px-3 py-2 text-center">
                  <span
                    className={`inline-block px-2 py-0.5 rounded-full text-xs font-semibold border ${
                      STATUS_STYLES[item.status] || STATUS_STYLES.not_detected
                    }`}
                  >
                    {STATUS_LABELS[item.status] || item.status}
                  </span>
                </td>
                <td className="px-3 py-2 text-gray-600 text-xs">
                  {item.status === 'misalignment' && item.recommendation ? (
                    <span className="text-red-600">{item.recommendation}</span>
                  ) : (
                    item.evidence || '–'
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default TriangulationTable;
