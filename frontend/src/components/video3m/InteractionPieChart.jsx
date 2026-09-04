import React from 'react';
import {
  PieChart,
  Pie,
  Cell,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';

/**
 * InteractionPieChart — donut chart for talk-time distribution.
 * Props:
 *   talkTime:  { teacher_pct, student_pct, silence_pct, meets_dl_standard }
 *   deviation: number | undefined  — deviation from DL standard (from talkTime.deviation)
 */
const COLORS = {
  teacher: '#ef4444',
  student: '#22c55e',
  silence: '#9ca3af',
};

const RADIAN = Math.PI / 180;

const renderCustomLabel = ({ cx, cy, midAngle, innerRadius, outerRadius, percent }) => {
  if (percent < 0.04) return null;
  const radius = innerRadius + (outerRadius - innerRadius) * 0.55;
  const x = cx + radius * Math.cos(-midAngle * RADIAN);
  const y = cy + radius * Math.sin(-midAngle * RADIAN);
  return (
    <text x={x} y={y} fill="white" textAnchor="middle" dominantBaseline="central" fontSize={12} fontWeight={600}>
      {`${(percent * 100).toFixed(1)}%`}
    </text>
  );
};

const InteractionPieChart = ({ talkTime = {}, deviation }) => {
  const {
    teacher_pct = 0,
    student_pct = 0,
    silence_pct = 0,
    meets_dl_standard = false,
  } = talkTime;

  // Allow deviation to come from the prop directly or from talkTime.deviation
  const deviationValue = deviation ?? talkTime.deviation;

  const data = [
    { name: 'Guru', value: teacher_pct, color: COLORS.teacher },
    { name: 'Siswa', value: student_pct, color: COLORS.student },
    { name: 'Hening', value: silence_pct, color: COLORS.silence },
  ].filter((d) => d.value > 0);

  return (
    <div className="flex flex-col items-center gap-2">
      {meets_dl_standard && (
        <div className="px-3 py-1 rounded-full bg-green-100 text-green-700 text-xs font-semibold border border-green-300">
          ✓ Memenuhi Standar Deep Learning
        </div>
      )}

      <ResponsiveContainer width="100%" height={220}>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={55}
            outerRadius={90}
            dataKey="value"
            labelLine={false}
            label={renderCustomLabel}
          >
            {data.map((entry, index) => (
              <Cell key={index} fill={entry.color} />
            ))}
          </Pie>
          <Tooltip formatter={(value) => [`${value.toFixed(1)}%`]} />
          <Legend />
        </PieChart>
      </ResponsiveContainer>

      {/* DL Standard annotation */}
      <div className="text-xs text-gray-500 text-center border rounded p-2 bg-gray-50 w-full">
        <span className="font-semibold">Standar Deep Learning:</span>{' '}
        Guru 30–40% &nbsp;|&nbsp; Siswa 60–70% &nbsp;|&nbsp; Hening ~10%
      </div>

      {/* Deviation info */}
      {deviationValue != null && deviationValue > 0 && (
        <div className="text-xs text-center text-orange-600 font-semibold mt-1">
          ⚠ Deviasi dari standar: {Number(deviationValue).toFixed(1)}%
        </div>
      )}
    </div>
  );
};

export default InteractionPieChart;
