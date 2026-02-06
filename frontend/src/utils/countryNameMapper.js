/**
 * Maps long country names to shorter versions for display in charts
 * This prevents long country names from being cut off or not showing in chart labels
 */
export const countryNameMap = {
  'United States': 'USA',
  'United States of America': 'USA',
  'United Kingdom': 'UK',
  'United Arab Emirates': 'UAE',
  'Russian Federation': 'Russia',
  'South Korea': 'S. Korea',
  'North Korea': 'N. Korea',
  'Saudi Arabia': 'Saudi Arabia',
  'New Zealand': 'New Zealand',
  'South Africa': 'S. Africa',
  'Czech Republic': 'Czech Rep.',
  'Dominican Republic': 'Dominican Rep.',
  'Bosnia and Herzegovina': 'Bosnia',
  'Trinidad and Tobago': 'Trinidad',
  'Antigua and Barbuda': 'Antigua',
  'Saint Vincent and the Grenadines': 'St. Vincent',
  'Papua New Guinea': 'Papua New Guinea',
  'Democratic Republic of the Congo': 'DR Congo',
  'Republic of the Congo': 'Congo',
  'Central African Republic': 'CAR',
  'Solomon Islands': 'Solomon Is.',
  'Marshall Islands': 'Marshall Is.',
  'Federated States of Micronesia': 'Micronesia',
  'Saint Kitts and Nevis': 'St. Kitts',
  'Saint Lucia': 'St. Lucia',
  'Sao Tome and Principe': 'Sao Tome',
  'Equatorial Guinea': 'Eq. Guinea',
  'Burkina Faso': 'Burkina Faso',
  'Cote d\'Ivoire': 'Cote d\'Ivoire',
  'Timor-Leste': 'Timor-Leste',
  'Brunei Darussalam': 'Brunei',
  'Lao People\'s Democratic Republic': 'Laos',
  'Syrian Arab Republic': 'Syria',
  'Libyan Arab Jamahiriya': 'Libya',
  'Islamic Republic of Iran': 'Iran',
  'Republic of Korea': 'S. Korea',
  'Democratic People\'s Republic of Korea': 'N. Korea',
  'Myanmar': 'Myanmar',
  'The Bahamas': 'Bahamas',
  'The Gambia': 'Gambia',
  'The Netherlands': 'Netherlands',
  'The Philippines': 'Philippines',
};

/**
 * Get shortened country name for display
 * @param {string} countryName - Full country name
 * @returns {string} - Shortened name if mapping exists, otherwise original name
 */
export const getShortCountryName = (countryName) => {
  if (!countryName) return countryName;
  
  // Check exact match first
  if (countryNameMap[countryName]) {
    return countryNameMap[countryName];
  }
  
  // Check case-insensitive match
  const lowerName = countryName.toLowerCase();
  for (const [fullName, shortName] of Object.entries(countryNameMap)) {
    if (fullName.toLowerCase() === lowerName) {
      return shortName;
    }
  }
  
  // If name is longer than 15 characters, truncate it
  if (countryName.length > 15) {
    return countryName.substring(0, 12) + '...';
  }
  
  return countryName;
};

/**
 * Apply country name mapping to geographic data array
 * @param {Array} geographicData - Array of objects with country property
 * @returns {Array} - Array with country names mapped to shorter versions
 */
export const mapGeographicData = (geographicData) => {
  if (!geographicData || !Array.isArray(geographicData)) {
    return geographicData;
  }
  
  return geographicData.map(item => ({
    ...item,
    country: getShortCountryName(item.country),
    // Keep original country name for tooltips
    countryFull: item.country
  }));
};
