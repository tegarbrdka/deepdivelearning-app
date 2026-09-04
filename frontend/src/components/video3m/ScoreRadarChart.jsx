import React from 'react';
import {
  RadarChart,
  Radar,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  ResponsiveContainer,
  Tooltip,
} from 'recharts';

/**
 * ScoreRadarChart — renders a three-axis radar chart for 3M scores.
 * Props:
 *   scores: { mindful: number, meaningful: number, joyful: number }
 */
const ScoreRadarChart = ({ scores = {} }) => {
  const { mindful = 0, meaningful = 0, joyful = 0 } = scores;

  const data = [
    { aspect: 'Mindful', score: mindful },
    { aspect: 'Meaningful', score: meaningful },
    { aspect: 'Joyful', score: joyful },
  ];

  const getColor = (value) => {
    if (value >= 70) return '#22c55e';   // green
    if (value >= 40) return '#eab308';   // yellow
    return '#ef4444';                     // red
  };

  const overall = Math.round((mindful + meaningful + joyful) / 3);
  const overallColor = getColor(overall);

  return (
    <div className="flex flex-col items-center gap-2">
      <ResponsiveContainer width="100%" height={260}>
        <RadarChart data={data} margin={{ top: 10, right: 30, bottom: 10, left: 30 }}>
          <PolarGrid />
          <PolarAngleAxis
            dataKey="aspect"
            tick={{ fontSize: 13, fontWeight: 600 }}
          />
          <PolarRadiusAxis
            angle={90}
            domain={[0, 100]}
            tick={{ fontSize: 10 }}
            tickCount={6}
          />
          <Radar
            name="Skor 3M"
            dataKey="score"
            stroke="#6366f1"
            fill="#6366f1"
            fillOpacity={0.35}
          />
          <Tooltip
            formatter={(value) => [`${value}/100`, 'Skor']}
          />
        </RadarChart>
      </ResponsiveContainer>

      {/* Score badges */}
      <div className="flex gap-4 flex-wrap justify-center">
        {data.map(({ aspect, score }) => (
          <div
            key={aspect}
            className="flex flex-col items-center px-3 py-1 rounded-lg border"
            style={{ borderColor: getColor(score) }}
          >
            <span className="text-xs text-gray-500">{aspect}</span>
            <span
              className="text-lg font-bold"
              style={{ color: getColor(score) }}
            >
              {score.toFixed(1)}
            </span>
          </div>
        ))}
        <div
          className="flex flex-col items-center px-3 py-1 rounded-lg border-2"
          style={{ borderColor: overallColor }}
        >
          <span className="text-xs text-gray-500">Overall</span>
          <span className="text-lg font-bold" style={{ color: overallColor }}>
            {overall}
          </span>
        </div>
      </div>
    </div>
  );
};

export default ScoreRadarChart;
