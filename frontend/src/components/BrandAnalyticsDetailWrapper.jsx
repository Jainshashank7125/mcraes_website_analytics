import { useParams, useNavigate } from 'react-router-dom'
import { useEffect, useState } from 'react'
import { CircularProgress, Box } from '@mui/material'
import BrandAnalyticsDetail from './BrandAnalyticsDetail'
import { syncAPI } from '../services/api'
import { useToast } from '../contexts/ToastContext'
import { getErrorMessage } from '../utils/errorHandler'

function BrandAnalyticsDetailWrapper() {
  const { id } = useParams()
  const navigate = useNavigate()
  const [brand, setBrand] = useState(null)
  const [loading, setLoading] = useState(true)
  const { showError } = useToast()

  useEffect(() => {
    const loadBrand = async () => {
      try {
        setLoading(true)
        
        const brandId = parseInt(id)
        if (isNaN(brandId)) {
          showError('Invalid brand ID')
          setLoading(false)
          return
        }
        
        // Get brand details
        const brandsResponse = await syncAPI.getBrands()
        const brands = brandsResponse.items || brandsResponse || []
        const foundBrand = brands.find(b => b.id === brandId)
        
        if (!foundBrand) {
          showError(`Brand with ID ${brandId} not found`)
        } else {
          setBrand(foundBrand)
        }
      } catch (err) {
        showError(getErrorMessage(err))
      } finally {
        setLoading(false)
      }
    }
    
    loadBrand()
  }, [id, showError])

  const handleBack = () => {
    navigate('/brands')
  }

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="50vh">
        <CircularProgress size={40} thickness={4} />
      </Box>
    )
  }

  if (!brand) {
    return null
  }

  return (
    <BrandAnalyticsDetail
      brandId={parseInt(id)}
      brand={brand}
      onBack={handleBack}
    />
  )
}

export default BrandAnalyticsDetailWrapper

