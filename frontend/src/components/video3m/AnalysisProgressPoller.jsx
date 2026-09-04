import React, { useEffect, useRef, useState } from 'react';
import axios from 'axios';

/**
 * AnalysisProgressPoller — polls job status and shows a progress bar.
 * Props:
 *   jobId: string
 *   onComplete: (jobId: string) => void
 */

const STAGE_LABELS = {
  fragmenting: 'Memotong video...',
  audio_processing: 'Menganalisis audio...',
  aggregating: 'Menghitung skor 3M...',
  extracting_evidence: 'Mengekstrak klip bukti...',
  triangulating: 'Membandingkan dengan RPP...',
  complete: 'Analisis selesai!',
  failed: 'Analisis gagal.',
  queued: 'Menunggu giliran...',
};

const getStageLabelDynamic = (stage) => {
  if (!stage) return 'Memproses...';
  // Handle "cv_processing (n/total)" pattern
  if (stage.startsWith('cv_processing')) {
    const match = stage.match(/\((\d+)\/(\d+)\)/);
    if (match) return `Memproses fragmen ${match[1]}/${match[2]}...`;
    return 'Memproses fragmen video...';
  }
  return STAGE_LABELS[stage] || stage;
};

const AnalysisProgressPoller = ({ jobId, onComplete }) => {
  const [status, setStatus] = useState('queued');
  const [stage, setStage] = useState('queued');
  const [progress, setProgress] = useState(0);
  const [errorMsg, setErrorMsg] = useState(null);
  const intervalRef = useRef(null);

  useEffect(() => {
    if (!jobId) return;

    const poll = async () => {
      try {
        const token = localStorage.getItem('token');
        const res = await axios.get(`/api/video-analysis/jobs/${jobId}`, {
          headers: { Authorization: `Bearer ${token}` },
        });
        const data = res.data;
        setStatus(data.status);
        setStage(data.stage || data.status);
        setProgress(data.progress || 0);

        if (data.status === 'complete') {
          clearInterval(intervalRef.current);
          if (onComplete) onComplete(jobId);
        } else if (data.status === 'failed') {
          clearInterval(intervalRef.current);
          setErrorMsg(data.error_msg || 'Terjadi kesalahan saat analisis.');
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    };

    poll(); // immediate first call
    intervalRef.current = setInterval(poll, 5000);

    return () => clearInterval(intervalRef.current);
  }, [jobId, onComplete]);

  const stageLabel = getStageLabelDynamic(stage);
  const isComplete = status === 'complete';
  const isFailed = status === 'failed';

  return (
    <div className="w-full max-w-lg mx-auto p-4">
      <div className="flex items-center justify-between mb-2">
        <span className={`text-sm font-medium ${isFailed ? 'text-red-600' : isComplete ? 'text-green-600' : 'text-gray-700'}`}>
          {stageLabel}
        </span>
        <span className="text-sm text-gray-500">{Math.round(progress)}%</span>
      </div>

      {/* Progress bar */}
      <div className="w-full bg-gray-200 rounded-full h-3 overflow-hidden">
        <div
          className={`h-3 rounded-full transition-all duration-500 ${
            isFailed ? 'bg-red-500' : isComplete ? 'bg-green-500' : 'bg-indigo-500'
          }`}
          style={{ width: `${progress}%` }}
        />
      </div>

      {isFailed && errorMsg && (
        <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          <strong>Error:</strong> {errorMsg}
        </div>
      )}

      {!isComplete && !isFailed && (
        <p className="text-xs text-gray-400 mt-2 text-center">
          Halaman ini akan diperbarui otomatis setiap 5 detik.
        </p>
      )}
    </div>
  );
};

export default AnalysisProgressPoller;
