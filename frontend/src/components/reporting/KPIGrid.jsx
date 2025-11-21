import { Grid, Typography } from '@mui/material'
import KPICard from './KPICard'

export default function KPIGrid({ displayedKPIs, formatValue, getSourceColor, getSourceLabel, theme }) {
  if (!displayedKPIs || displayedKPIs.length === 0) {
    return null
  }

  return (
    <>
      <Typography 
        variant="h5" 
        fontWeight={700} 
        sx={{ 
          mt: 5, 
          mb: 3,
          fontSize: '1.5rem',
          letterSpacing: '-0.02em',
          color: 'text.primary'
        }}
      >
        All Performance Metrics
      </Typography>
      
      <Grid container spacing={2} sx={{ mb: 4 }}>
        {displayedKPIs.map(([key, kpi], index) => (
          <KPICard
            key={key}
            kpi={kpi}
            kpiKey={key}
            index={index}
            theme={theme}
          />
        ))}
      </Grid>
    </>
  )
}
