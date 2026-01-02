import axios from "axios";
import { debugLog, debugError } from "../utils/debug";

// API configuration from environment variables
const GEOLOCATION_API_PROVIDER =
  import.meta.env.VITE_GEOLOCATION_API_PROVIDER || "ipapi";
const IPAPI_TOKEN = import.meta.env.VITE_IPAPI_TOKEN || "";
const IPINFO_TOKEN = import.meta.env.VITE_IPINFO_TOKEN || "";

/**
 * Location data structure returned by the service
 * @typedef {Object} LocationData
 * @property {string} ip - IP address
 * @property {string} city - City name
 * @property {string} region - Region/State name
 * @property {string} country - Country name
 * @property {string} countryCode - Country code (ISO 3166-1 alpha-2)
 * @property {number} latitude - Latitude coordinate
 * @property {number} longitude - Longitude coordinate
 * @property {string} timezone - Timezone (e.g., "America/New_York")
 * @property {string} isp - Internet Service Provider
 */

/**
 * Cache for location data to avoid redundant API calls
 * Key: IP address, Value: LocationData
 */
const locationCache = new Map();

/**
 * Cache expiration time (5 minutes)
 */
const CACHE_EXPIRY_MS = 5 * 60 * 1000;

/**
 * Check if an IP address is private/local
 * @param {string} ip - IP address to check
 * @returns {boolean} True if IP is private/local
 */
const isPrivateIP = (ip) => {
  if (!ip) return true;

  // Localhost
  if (ip === "127.0.0.1" || ip === "localhost" || ip === "::1") return true;

  // Private IP ranges
  if (ip.startsWith("192.168.")) return true;
  if (ip.startsWith("10.")) return true;
  if (
    ip.startsWith("172.16.") ||
    ip.startsWith("172.17.") ||
    ip.startsWith("172.18.") ||
    ip.startsWith("172.19.") ||
    ip.startsWith("172.20.") ||
    ip.startsWith("172.21.") ||
    ip.startsWith("172.22.") ||
    ip.startsWith("172.23.") ||
    ip.startsWith("172.24.") ||
    ip.startsWith("172.25.") ||
    ip.startsWith("172.26.") ||
    ip.startsWith("172.27.") ||
    ip.startsWith("172.28.") ||
    ip.startsWith("172.29.") ||
    ip.startsWith("172.30.") ||
    ip.startsWith("172.31.")
  )
    return true;

  return false;
};

/**
 * Fetch location from ipapi.co
 * @param {string} ip - IP address
 * @returns {Promise<LocationData|null>} Location data or null on error
 */
const fetchFromIpapi = async (ip) => {
  try {
    const url = IPAPI_TOKEN
      ? `https://ipapi.co/${ip}/json/?key=${IPAPI_TOKEN}`
      : `https://ipapi.co/${ip}/json/`;

    const response = await axios.get(url, { timeout: 5000 });

    if (response.data.error) {
      debugError(`ipapi.co error for IP ${ip}:`, response.data.reason);
      return null;
    }

    return {
      ip: response.data.ip || ip,
      city: response.data.city || "Unknown",
      region: response.data.region || response.data.region_code || "Unknown",
      country: response.data.country_name || "Unknown",
      countryCode: response.data.country_code || "",
      latitude: response.data.latitude || 0,
      longitude: response.data.longitude || 0,
      timezone: response.data.timezone || "Unknown",
      isp: response.data.org || "Unknown",
    };
  } catch (error) {
    debugError(`Error fetching from ipapi.co for IP ${ip}:`, error);
    return null;
  }
};

/**
 * Fetch location from ip-api.com
 * @param {string} ip - IP address
 * @returns {Promise<LocationData|null>} Location data or null on error
 */
const fetchFromIpApi = async (ip) => {
  try {
    const url = `http://ip-api.com/json/${ip}`;
    const response = await axios.get(url, { timeout: 5000 });

    if (response.data.status === "fail") {
      debugError(`ip-api.com error for IP ${ip}:`, response.data.message);
      return null;
    }

    return {
      ip: response.data.query || ip,
      city: response.data.city || "Unknown",
      region: response.data.regionName || response.data.region || "Unknown",
      country: response.data.country || "Unknown",
      countryCode: response.data.countryCode || "",
      latitude: response.data.lat || 0,
      longitude: response.data.lon || 0,
      timezone: response.data.timezone || "Unknown",
      isp: response.data.isp || response.data.org || "Unknown",
    };
  } catch (error) {
    debugError(`Error fetching from ip-api.com for IP ${ip}:`, error);
    return null;
  }
};

/**
 * Fetch location from ipinfo.io
 * @param {string} ip - IP address
 * @returns {Promise<LocationData|null>} Location data or null on error
 */
const fetchFromIpinfo = async (ip) => {
  try {
    const url = IPINFO_TOKEN
      ? `https://ipinfo.io/${ip}?token=${IPINFO_TOKEN}`
      : `https://ipinfo.io/${ip}/json`;

    const response = await axios.get(url, { timeout: 5000 });

    if (response.data.error) {
      debugError(`ipinfo.io error for IP ${ip}:`, response.data.error);
      return null;
    }

    // Parse location coordinates (format: "lat,lng")
    let latitude = 0;
    let longitude = 0;
    if (response.data.loc) {
      const [lat, lng] = response.data.loc.split(",");
      latitude = parseFloat(lat) || 0;
      longitude = parseFloat(lng) || 0;
    }

    return {
      ip: response.data.ip || ip,
      city: response.data.city || "Unknown",
      region: response.data.region || "Unknown",
      country: response.data.country || "Unknown",
      countryCode: response.data.country || "",
      latitude,
      longitude,
      timezone: response.data.timezone || "Unknown",
      isp: response.data.org || "Unknown",
    };
  } catch (error) {
    debugError(`Error fetching from ipinfo.io for IP ${ip}:`, error);
    return null;
  }
};

/**
 * Get location data for an IP address
 * Uses caching to avoid redundant API calls
 *
 * @param {string} ip - IP address to geolocate
 * @returns {Promise<LocationData|null>} Location data or null if unavailable
 */
export const getLocationByIP = async (ip) => {
  // Validate IP
  if (!ip || typeof ip !== "string") {
    debugError("Invalid IP address provided:", ip);
    return null;
  }

  // Check cache first
  const cached = locationCache.get(ip);
  if (cached) {
    const now = Date.now();
    if (now - cached.timestamp < CACHE_EXPIRY_MS) {
      debugLog(`Using cached location for IP: ${ip}`);
      return cached.data;
    } else {
      // Cache expired, remove it
      locationCache.delete(ip);
    }
  }

  // Skip private IPs (they can't be geolocated)
  if (isPrivateIP(ip)) {
    debugLog(`Skipping geolocation for private IP: ${ip}`);
    return {
      ip,
      city: "Private Network",
      region: "Local",
      country: "Local",
      countryCode: "",
      latitude: 0,
      longitude: 0,
      timezone: "Unknown",
      isp: "Local Network",
    };
  }

  // Fetch location based on configured provider
  let locationData = null;

  try {
    switch (GEOLOCATION_API_PROVIDER.toLowerCase()) {
      case "ipapi":
        locationData = await fetchFromIpapi(ip);
        // Fallback to ip-api.com if ipapi.co fails
        if (!locationData) {
          debugLog(`Falling back to ip-api.com for IP: ${ip}`);
          locationData = await fetchFromIpApi(ip);
        }
        break;

      case "ip-api":
        locationData = await fetchFromIpApi(ip);
        // Fallback to ipapi.co if ip-api.com fails
        if (!locationData) {
          debugLog(`Falling back to ipapi.co for IP: ${ip}`);
          locationData = await fetchFromIpapi(ip);
        }
        break;

      case "ipinfo":
        locationData = await fetchFromIpinfo(ip);
        // Fallback to ip-api.com if ipinfo.io fails
        if (!locationData) {
          debugLog(`Falling back to ip-api.com for IP: ${ip}`);
          locationData = await fetchFromIpApi(ip);
        }
        break;

      default:
        debugError(`Unknown geolocation provider: ${GEOLOCATION_API_PROVIDER}`);
        locationData = await fetchFromIpApi(ip);
    }

    // Cache the result if successful
    if (locationData) {
      locationCache.set(ip, {
        data: locationData,
        timestamp: Date.now(),
      });
    }

    return locationData;
  } catch (error) {
    debugError(`Error fetching location for IP ${ip}:`, error);
    return null;
  }
};

/**
 * Get location data for multiple IP addresses
 * Fetches locations in parallel with rate limiting consideration
 *
 * @param {string[]} ips - Array of IP addresses
 * @returns {Promise<Map<string, LocationData|null>>} Map of IP to location data
 */
export const getLocationsByIPs = async (ips) => {
  if (!Array.isArray(ips) || ips.length === 0) {
    return new Map();
  }

  // Remove duplicates and filter invalid IPs
  const uniqueIPs = [
    ...new Set(ips.filter((ip) => ip && typeof ip === "string")),
  ];

  if (uniqueIPs.length === 0) {
    return new Map();
  }

  // Fetch all locations in parallel (with a small delay to respect rate limits)
  const locationMap = new Map();
  const fetchPromises = uniqueIPs.map(async (ip, index) => {
    // Add small delay to avoid hitting rate limits (50ms between requests)
    if (index > 0) {
      await new Promise((resolve) => setTimeout(resolve, 50 * index));
    }

    const location = await getLocationByIP(ip);
    locationMap.set(ip, location);
  });

  await Promise.all(fetchPromises);

  return locationMap;
};

/**
 * Clear the location cache
 * Useful for testing or when you want to force fresh data
 */
export const clearLocationCache = () => {
  locationCache.clear();
  debugLog("Location cache cleared");
};

/**
 * Get cache statistics
 * @returns {Object} Cache statistics
 */
export const getCacheStats = () => {
  return {
    size: locationCache.size,
    entries: Array.from(locationCache.keys()),
  };
};
