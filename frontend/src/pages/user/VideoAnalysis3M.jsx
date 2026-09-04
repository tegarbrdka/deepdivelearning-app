import React, { useState, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import axios from 'axios';
import { useLang } from '../../contexts/LanguageContext';

/**
 * VideoAnalysis3M — upload page for 3M video analysis.
 * Supports optional RPP document upload for triangulation.
 */

const MAX_VIDEO_SIZE_GB = 2;
const MAX_VIDEO_SIZE_BYTES = MAX_VIDEO_SIZE_GB * 1024 * 1024 * 1024;

const VideoAnalysis3M = () => {
  const navigate = useNavigate();
  const { t } = useLang();
  const videoInputRef = useRef(null);
  const rppInputRef = useRef(null);

  const [videoFile, setVideoFile] = useState(null);
  const [rppFile, setRppFile] = useState(null);
  const [videoError, setVideoError] = useState('');
  const [rppError, setRppError] = useState('');
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [submitError, setSubmitError] = useState('');

  const validateVideo = (file) => {
    if (!file) return '';
    if (!file.name.toLowerCase().endsWith('.mp4')) {
      return t('video3m.validationVideoFormat');
    }
    if (file.size > MAX_VIDEO_SIZE_BYTES) {
      return t('video3m.validationVideoSize');
    }
    return '';
  };

  const validateRpp = (file) => {
    if (!file) return '';
    const ext = file.name.split('.').pop().toLowerCase();
    if (!['pdf', 'docx', 'doc'].includes(ext)) {
      return t('video3m.validationRppFormat');
    }
    return '';
  };

  const handleVideoDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const err = validateVideo(file);
      setVideoError(err);
      if (!err) setVideoFile(file);
    }
  };

  const handleRppDrop = (e) => {
    e.preventDefault();
    const file = e.dataTransfer.files[0];
    if (file) {
      const err = validateRpp(file);
      setRppError(err);
      if (!err) setRppFile(file);
    }
  };

  const handleVideoChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const err = validateVideo(file);
      setVideoError(err);
      if (!err) setVideoFile(file);
    }
  };

  const handleRppChange = (e) => {
    const file = e.target.files[0];
    if (file) {
      const err = validateRpp(file);
      setRppError(err);
      if (!err) setRppFile(file);
    }
  };

  const formatSize = (bytes) => {
    if (bytes >= 1024 * 1024 * 1024) return `${(bytes / (1024 * 1024 * 1024)).toFixed(2)} GB`;
    if (bytes >= 1024 * 1024) return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
    return `${(bytes / 1024).toFixed(0)} KB`;
  };

  const handleSubmit = async () => {
    if (!videoFile) {
      setSubmitError(t('video3m.validationNoVideo'));
      return;
    }
    setSubmitError('');
    setUploading(true);
    setUploadProgress(0);

    try {
      const token = localStorage.getItem('token');
      const formData = new FormData();
      formData.append('video', videoFile);

      let endpoint = '/api/video-analysis/upload';
      if (rppFile) {
        formData.append('rpp', rppFile);
        endpoint = '/api/video-analysis/upload-with-rpp';
      }
      const url = endpoint;

      const res = await axios.post(url, formData, {
        headers: {
          Authorization: `Bearer ${token}`,
        },
        onUploadProgress: (e) => {
          const pct = Math.round((e.loaded / e.total) * 100);
          setUploadProgress(pct);
        },
        timeout: 0,
      });

      const { job_id } = res.data;
      navigate(`/video-analysis-3m/result/${job_id}`);
    } catch (err) {
      const msg = err.response?.data?.detail || t('video3m.uploadError');
      setSubmitError(msg);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="max-w-2xl mx-auto p-6">
      <div className="flex items-center gap-2 mb-1">
        <h1 className="text-2xl font-bold text-gray-800">{t('video3m.uploadTitle')}</h1>
        <div className="group relative flex items-center mt-1">
          <span className="cursor-help text-slate-400 hover:text-indigo-500 transition-colors">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="10"></circle><path d="M9.09 9a3 3 0 0 1 5.83 1c0 2-3 3-3 3"></path><line x1="12" y1="17" x2="12.01" y2="17"></line></svg>
          </span>
          <div className="absolute bottom-full left-1/2 -translate-x-1/2 mb-2 hidden w-64 p-3 bg-gray-900 text-white text-xs rounded-lg shadow-xl group-hover:block z-10 font-normal leading-relaxed">
            <strong className="text-indigo-800 dark:text-indigo-300 block mb-1">3M Framework</strong>
            <ul className="space-y-1">
              <li><b>Mindful:</b> Kehadiran utuh guru & siswa (Fokus, Hening).</li>
              <li><b>Meaningful:</b> Pembelajaran bermakna (Interaksi, Formasi).</li>
              <li><b>Joyful:</b> Suasana menyenangkan (Ekspresi, Kolaborasi).</li>
            </ul>
            <div className="absolute top-full left-1/2 -translate-x-1/2 -mt-1 border-4 border-transparent border-t-gray-900"></div>
          </div>
        </div>
      </div>
      <p className="text-gray-500 text-sm mb-6">
        {t('video3m.uploadSubtitle')}
      </p>

      {/* Video upload zone */}
      <div
        className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors mb-4 ${
          videoFile ? 'border-indigo-400 bg-indigo-50' : 'border-gray-300 hover:border-indigo-400 hover:bg-gray-50'
        }`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleVideoDrop}
        onClick={() => videoInputRef.current?.click()}
      >
        <input
          ref={videoInputRef}
          type="file"
          accept=".mp4,video/mp4"
          className="hidden"
          onChange={handleVideoChange}
        />
        {videoFile ? (
          <div>
            <p className="text-indigo-700 font-semibold">{videoFile.name}</p>
            <p className="text-gray-500 text-sm">{formatSize(videoFile.size)}</p>
          </div>
        ) : (
          <div>
            <svg className="w-10 h-10 text-gray-400 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M15 10l4.553-2.069A1 1 0 0121 8.82v6.36a1 1 0 01-1.447.89L15 14M3 8a2 2 0 012-2h8a2 2 0 012 2v8a2 2 0 01-2 2H5a2 2 0 01-2-2V8z" />
            </svg>
            <p className="text-gray-600 font-medium">{t('video3m.uploadVideoZone')}</p>
            <p className="text-gray-400 text-sm">{t('upload.dragDrop').split('atau')[1] ? 'atau ' + t('upload.dragDrop').split('atau')[1] : 'atau klik untuk memilih file'}</p>
            <p className="text-gray-400 text-xs mt-1">{t('video3m.uploadVideoHint')}</p>
          </div>
        )}
      </div>
      {videoError && <p className="text-red-500 text-sm mb-3">{videoError}</p>}

      {/* RPP upload zone (optional) */}
      <div
        className={`border-2 border-dashed rounded-xl p-4 text-center cursor-pointer transition-colors mb-4 ${
          rppFile ? 'border-green-400 bg-green-50' : 'border-gray-200 hover:border-green-400 hover:bg-gray-50'
        }`}
        onDragOver={(e) => e.preventDefault()}
        onDrop={handleRppDrop}
        onClick={() => rppInputRef.current?.click()}
      >
        <input
          ref={rppInputRef}
          type="file"
          accept=".pdf,.docx,.doc"
          className="hidden"
          onChange={handleRppChange}
        />
        {rppFile ? (
          <div>
            <p className="text-green-700 font-semibold">{rppFile.name}</p>
            <p className="text-gray-500 text-sm">{formatSize(rppFile.size)}</p>
          </div>
        ) : (
          <div>
            <p className="text-gray-500 text-sm font-medium">
              📄 {t('video3m.uploadRppZone')}
            </p>
            <p className="text-gray-400 text-xs">{t('video3m.uploadRppHint')}</p>
          </div>
        )}
      </div>
      {rppError && <p className="text-red-500 text-sm mb-3">{rppError}</p>}

      {/* Upload progress */}
      {uploading && (
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-1">
            <span>{t('video3m.uploading')}</span>
            <span>{uploadProgress}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className="bg-indigo-500 h-2 rounded-full transition-all"
              style={{ width: `${uploadProgress}%` }}
            />
          </div>
        </div>
      )}

      {submitError && (
        <div className="mb-4 p-3 bg-red-50 border border-red-200 rounded text-sm text-red-700">
          {submitError}
        </div>
      )}

      <button
        onClick={handleSubmit}
        disabled={uploading || !videoFile || !!videoError || !!rppError}
        className="w-full py-3 px-6 bg-indigo-600 text-white font-semibold rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
      >
        {uploading ? t('video3m.uploading') : t('video3m.uploadBtn')}
      </button>
      
      {/* Time Expectation Helper */}
      <p className="text-xs text-slate-500 mt-4 text-center flex items-start justify-center gap-1.5 px-4">
        <span className="text-sm leading-none">ℹ️</span>
        <span className="leading-relaxed">
          Proses analisis berbasis Deep Learning dapat memakan waktu <b>5-15 menit</b> tergantung durasi video. Anda dapat meninggalkan halaman ini dan mengecek hasil akhirnya nanti di menu <b>Riwayat</b>.
        </span>
      </p>
    </div>
  );
};

export default VideoAnalysis3M;
