import React from 'react';
import { Box } from '@mui/material';

/**
 * Sparkline component for rendering mini time series charts
 * @param {Array} data - Array of numeric values for the sparkline
 * @param {string} color - Color for the line (default: 'green' or 'red' based on trend)
 * @param {number} width - Width of the sparkline (default: 100)
 * @param {number} height - Height of the sparkline (default: 30)
 */
const Sparkline = ({ data = [], color = 'green', width = 100, height = 30 }) => {
  if (!data || data.length === 0) {
    return (
      <Box
        sx={{
          width,
          height,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: 'text.secondary',
          fontSize: '10px',
        }}
      >
        --
      </Box>
    );
  }

  // Normalize data to fit within the SVG viewBox
  const min = Math.min(...data);
  const max = Math.max(...data);
  const range = max - min || 1; // Avoid division by zero
  const padding = 2;

  // Map data points to SVG coordinates
  const points = data.map((value, index) => {
    const x = ((index / (data.length - 1)) * (width - padding * 2)) + padding;
    const y = height - padding - ((value - min) / range) * (height - padding * 2);
    return `${x},${y}`;
  }).join(' ');

  // Determine line color
  const lineColor = color === 'red' ? '#ef5350' : color === 'green' ? '#4caf50' : '#1976d2';

  return (
    <Box
      sx={{
        width,
        height,
        display: 'flex',
        alignItems: 'center',
      }}
    >
      <svg
        width={width}
        height={height}
        viewBox={`0 0 ${width} ${height}`}
        style={{ display: 'block' }}
      >
        <polyline
          points={points}
          fill="none"
          stroke={lineColor}
          strokeWidth="1.5"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
      </svg>
    </Box>
  );
};

export default Sparkline;

