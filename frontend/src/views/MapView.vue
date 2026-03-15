<template>
  <div class="map-view">
    <!-- Search Bar -->
    <div class="search-bar">
      <div class="search-input">
        <span class="search-icon">🔍</span>
        <input
          v-model="searchQuery"
          type="text"
          placeholder="Search places..."
          @keyup.enter="handleSearch"
        />
        <button v-if="searchQuery" @click="clearSearch" class="clear-button">×</button>
      </div>
      <button @click="handleSearch" class="search-button">Search</button>
      <button @click="resetMap" class="reset-button">Reset</button>
    </div>

    <!-- Create Corner Button -->
    <button @click="goToCreateCorner" class="create-corner-button">
      <span class="button-icon">➕</span>
      <span class="button-label">Add Corner</span>
    </button>

    <!-- Map Container -->
    <div ref="mapContainer" class="map-container"></div>

    <!-- Side Panel (Corner Details) -->
    <div :class="['side-panel', { open: selectedCorner }]">
      <div class="panel-header">
        <h2>{{ selectedCorner?.name || '' }}</h2>
        <button @click="closePanel" class="close-button">×</button>
      </div>

      <div class="panel-content">
        <div v-if="selectedCorner" class="corner-info">
          <!-- Images -->
          <div v-if="selectedCorner.images && selectedCorner.images.length > 0" class="corner-images">
            <div class="images-grid">
              <img
                v-for="(imageId, idx) in selectedCorner.images.slice(0, 4)"
                :key="idx"
                :src="getMediaUrl(imageId)"
                :alt="`${selectedCorner.name} image ${idx + 1}`"
                @click="openImageViewer(idx)"
              />
            </div>
            <div v-if="selectedCorner.images.length > 4" class="more-images">
              +{{ selectedCorner.images.length - 4 }} more
            </div>
          </div>

          <p v-if="selectedCorner.description" class="description">
            {{ selectedCorner.description }}
          </p>

          <div class="stats">
            <div class="stat-item">
              <span class="stat-number">{{ cornerPosts.length }}</span>
              <span class="stat-label">Posts</span>
            </div>
            <div v-if="selectedCorner.distance" class="stat-item">
              <span class="stat-number">{{ formatDistance(selectedCorner.distance) }}</span>
              <span class="stat-label">Away</span>
            </div>
          </div>

          <div class="posts-section">
            <h3>Posts at this location</h3>
            <div v-if="loadingPosts" class="loading">
              <div class="spinner"></div>
            </div>
            <div v-else-if="cornerPosts.length === 0" class="empty-state">
              <p>No posts yet</p>
            </div>
            <div v-else class="corner-posts">
              <PostCard
                v-for="post in cornerPosts"
                :key="post._id"
                :post="post"
                compact
              />
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Route Display (if any route is selected) -->
    <div v-if="displayedRoute" class="route-info">
      <div class="route-header">
        <span class="route-icon">🛤️</span>
        <span class="route-name">{{ displayedRoute.route_name }}</span>
        <button @click="clearRoute" class="clear-route">×</button>
      </div>
      <div class="route-stops">
        <div
          v-for="(stop, idx) in displayedRoute.corners"
          :key="stop._id"
          class="route-stop"
        >
          <span class="stop-number">{{ idx + 1 }}</span>
          <span class="stop-name">{{ stop.name }}</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted, watch, markRaw } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import polyline from '@mapbox/polyline';
import { cornersApi } from '../api/corners';
import { postsApi } from '../api/posts';
import { mediaApi } from '../api/media';
import PostCard from '../components/Feed/PostCard.vue';

// Handle route changes - reset map state when navigating away from map with query params
const handleRouteChange = (newRoute) => {
  // Only reset if we're leaving /map with query params (corner_id, show_route, etc.)
  if (newRoute.path === '/map' && Object.keys(newRoute.query).length > 0) {
    return; // Don't reset, we're navigating to map with params
  }
  
  // Reset state when navigating away from /map
  if (newRoute.path !== '/map') {
    // Clear all state
    searchQuery.value = '';
    selectedCorner.value = null;
    cornerPosts.value = [];
    displayedRoute.value = null;
    currentRouteCorners.value = null;
    routeMode.value = 'driving';
    
    if (routeLayer && map.value) {
      map.value.removeLayer(routeLayer);
      routeLayer = null;
    }
    
    routeMarkers.forEach(marker => {
      try {
        if (map.value) map.value.removeLayer(marker);
      } catch (e) {}
    });
    routeMarkers = [];
    
    if (tempLocationMarker && map.value) {
      map.value.removeLayer(tempLocationMarker);
      tempLocationMarker = null;
    }
    selectedMapLocation.value = null;
  }
};

const router = useRouter();
const route = useRoute();

// Fix for Leaflet default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const mapContainer = ref(null);
const map = ref(null);
const userLocation = ref({ lat: 31.2304, lng: 121.4737 }); // Default: Shanghai
const selectedMapLocation = ref(null); // Store user-selected location on map
const nearbyCorners = ref([]);
const selectedCorner = ref(null);
const cornerPosts = ref([]);
const loadingPosts = ref(false);
const searchQuery = ref('');
const displayedRoute = ref(null);
const currentRouteCorners = ref(null); // Store corners for route display

let markers = []; // Corner markers (clickable to view posts)
let routeMarkers = []; // Route stop markers (numbered 1, 2, 3...)
let routeLayer = null;
let userMarker = null;
let tempLocationMarker = null;

// OSRM routing service
const OSRM_BASE_URL = 'https://router.project-osrm.org/route/v1';

// Fetch real route from OSRM API
const fetchRouteFromOSRM = async (coordinates, profile = 'driving') => {
  // coordinates: array of [lng, lat]
  if (coordinates.length < 2) return null;

  // Format coordinates for OSRM: lng,lat;lng,lat;...
  const coordsStr = coordinates.map(c => `${c[0]},${c[1]}`).join(';');
  const url = `${OSRM_BASE_URL}/${profile}/${coordsStr}?overview=full&geometries=polyline`;

  try {
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`OSRM API error: ${response.status}`);
    }
    const data = await response.json();
    
    if (data.code === 'Ok' && data.routes && data.routes.length > 0) {
      const route = data.routes[0];
      // Decode polyline to get coordinates
      // polyline.decode returns [[lat, lng], ...], need to swap to [lng, lat]
      const decodedCoords = polyline.decode(route.geometry, 5);
      const latLngs = decodedCoords.map(c => [c[0], c[1]]); // [lat, lng]
      
      return {
        coordinates: latLngs,
        distance: route.distance, // in meters
        duration: route.duration, // in seconds
      };
    }
    return null;
  } catch (err) {
    console.error('Failed to fetch route from OSRM:', err);
    return null;
  }
};

// Initialize map
const initMap = () => {
  // Use markRaw to prevent Vue from proxying the map object
  const leafletMap = L.map(mapContainer.value).setView([userLocation.value.lat, userLocation.value.lng], 14);
  map.value = markRaw(leafletMap);

  // Add OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map.value);

  // Add user location marker
  updateUserMarker();

  // Add map click handler for selecting location
  map.value.on('click', handleMapClick);

  // Add moveend event to reload corners when map is moved/zoomed
  map.value.on('moveend', handleMapMoveEnd);

  // Load nearby corners
  loadNearbyCorners();
};

// Handle map move/zoom end - reload corners based on current viewport
const handleMapMoveEnd = () => {
  // Don't reload if a route is being displayed
  if (displayedRoute.value) return;
  
  // Get current map center
  const center = map.value.getCenter();
  loadCornersAtLocation(center.lat, center.lng);
};

// Load corners at a specific location
const loadCornersAtLocation = async (lat, lng) => {
  try {
    const response = await cornersApi.getNearby({
      lat: lat,
      lng: lng,
      radius: 10000, // 10km
      limit: 50
    });

    if (response.success && response.data?.corners) {
      nearbyCorners.value = response.data.corners;
      displayCorners(response.data.corners);
    }
  } catch (err) {
    console.error('Failed to load corners:', err);
  }
};

// Update user marker
const updateUserMarker = () => {
  if (userMarker) {
    map.value.removeLayer(userMarker);
  }

  const userIcon = L.divIcon({
    className: 'user-marker',
    html: '<div class="user-marker-inner"></div>',
    iconSize: [24, 24],
    iconAnchor: [12, 12],
    popupAnchor: [0, -12]
  });

  // Use markRaw to prevent Vue from proxying the marker
  userMarker = markRaw(L.marker([userLocation.value.lat, userLocation.value.lng], {
    icon: userIcon,
    zIndex: 1000
  }).addTo(map.value));
};

// Get user location
const getUserLocation = () => {
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        userLocation.value = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        map.value.setView([userLocation.value.lat, userLocation.value.lng], 14);
        updateUserMarker();
        loadNearbyCorners();
      },
      () => {
        console.log('Could not get user location, using default');
      }
    );
  }
};

// Map click handler for selecting location
const handleMapClick = (e) => {
  const { lat, lng } = e.latlng;
  
  // Remove existing temp marker
  if (tempLocationMarker) {
    map.value.removeLayer(tempLocationMarker);
  }
  
  // Add temp marker to show selected location
  const tempIcon = L.divIcon({
    className: 'temp-location-marker',
    html: '<div class="temp-marker-inner"></div>',
    iconSize: [30, 30],
    iconAnchor: [15, 30],
    popupAnchor: [0, -30]
  });
  
  // Use markRaw to prevent Vue from proxying the marker
  tempLocationMarker = markRaw(L.marker([lat, lng], {
    icon: tempIcon,
    zIndex: 999
  }).addTo(map.value));
  
  tempLocationMarker.bindPopup('<div style="text-align:center;"><strong>Selected Location</strong><br>Click "Add Corner" to create a corner here</div>');
  tempLocationMarker.openPopup();
  
  // Store selected location for create corner
  selectedMapLocation.value = { lat, lng };
};

// Load nearby corners based on user location
const loadNearbyCorners = async () => {
  await loadCornersAtLocation(userLocation.value.lat, userLocation.value.lng);
};

// Display corners on map
const displayCorners = (corners) => {
  // Clear existing markers
  markers.forEach(marker => map.value.removeLayer(marker));
  markers = [];

  corners.forEach(corner => {
    const [lng, lat] = corner.location.coordinates;
    // Use markRaw to prevent Vue from proxying the marker
    const marker = markRaw(L.marker([lat, lng]).addTo(map.value));

    marker.on('click', () => selectCorner(corner));
    markers.push(marker);
  });
};

// Search corners
const handleSearch = async () => {
  if (!searchQuery.value.trim()) {
    loadNearbyCorners();
    return;
  }

  try {
    const response = await cornersApi.search(searchQuery.value, { limit: 20 });

    if (response.success && response.data?.corners) {
      nearbyCorners.value = response.data.corners;
      displayCorners(response.data.corners);

      // Fit map to show all results
      if (response.data.corners.length > 0) {
        const bounds = L.latLngBounds(
          response.data.corners.map(c => {
            const [lng, lat] = c.location.coordinates;
            return [lat, lng];
          })
        );
        map.value.fitBounds(bounds, { padding: [50, 50] });
      }
    }
  } catch (err) {
    console.error('Search failed:', err);
  }
};

// Clear search
const clearSearch = () => {
  searchQuery.value = '';
  loadNearbyCorners();
};

// Reset map to initial state
const resetMap = () => {
  // Clear URL query parameters
  router.replace({ path: '/map' });

  // Clear search query
  searchQuery.value = '';

  // Clear route display
  if (routeLayer) {
    map.value.removeLayer(routeLayer);
    routeLayer = null;
  }
  displayedRoute.value = null;
  currentRouteCorners.value = null;

  // Remove route stop markers
  routeMarkers.forEach(marker => {
    try {
      map.value.removeLayer(marker);
    } catch (e) {}
  });
  routeMarkers = [];

  // Clear selected corner and close panel
  selectedCorner.value = null;
  cornerPosts.value = [];

  // Remove temp location marker
  if (tempLocationMarker) {
    map.value.removeLayer(tempLocationMarker);
    tempLocationMarker = null;
  }
  selectedMapLocation.value = null;

  // Move map to current user location and reload nearby corners
  map.value.setView([userLocation.value.lat, userLocation.value.lng], 14);
  updateUserMarker();
  loadNearbyCorners();

  // Try to re-acquire user location in background (will update if successful)
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        userLocation.value = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
        map.value.setView([userLocation.value.lat, userLocation.value.lng], 14);
        updateUserMarker();
        loadNearbyCorners();
      },
      () => {
        // Location failed, keep using current stored location
      }
    );
  }
};

// Select corner
const selectCorner = async (corner) => {
  selectedCorner.value = corner;
  loadingPosts.value = true;

  try {
    const response = await cornersApi.getPosts(corner._id, { limit: 20 });

    if (response.success && response.data?.posts) {
      cornerPosts.value = response.data.posts;
    }
  } catch (err) {
    console.error('Failed to load corner posts:', err);
  } finally {
    loadingPosts.value = false;
  }
};

// Close panel
const closePanel = () => {
  selectedCorner.value = null;
  cornerPosts.value = [];
};

// Display route on map using OSRM for real route
const displayRoute = async (route) => {
  if (routeLayer) {
    map.value.removeLayer(routeLayer);
    routeLayer = null;
  }

  // Remove old route stop markers (not corner markers!)
  routeMarkers.forEach(marker => {
    try {
      map.value.removeLayer(marker);
    } catch (e) {}
  });
  routeMarkers = [];

  if (!route.corners || route.corners.length < 2) return;

  // Store corners for route display
  currentRouteCorners.value = route;

  // Extract coordinates from corners
  const coordinates = route.corners.map(corner => corner.location.coordinates);

  // Try to fetch real route from OSRM (use driving mode by default)
  const routeData = await fetchRouteFromOSRM(coordinates, 'driving');

  let routeCoordinates;
  if (routeData && routeData.coordinates) {
    // Use real route coordinates from OSRM
    routeCoordinates = routeData.coordinates;
  } else {
    // Fallback to straight lines if OSRM fails
    routeCoordinates = route.corners.map(corner => {
      const [lng, lat] = corner.location.coordinates;
      return [lat, lng];
    });
  }

  // Create a styled polyline for the route with bright green color
  routeLayer = markRaw(L.polyline(routeCoordinates, {
    color: '#00C853', // Bright green
    weight: 6,
    opacity: 0.9,
    lineCap: 'round',
    lineJoin: 'round'
  }).addTo(map.value));

  // Add markers for each stop
  route.corners.forEach((corner, idx) => {
    const [lng, lat] = corner.location.coordinates;
    const stopIcon = L.divIcon({
      className: 'route-stop-marker',
      html: `<div class="stop-number">${idx + 1}</div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    });

    const marker = markRaw(L.marker([lat, lng], { icon: stopIcon }).addTo(map.value));
    marker.bindPopup(`<strong>${corner.name}</strong>`);
    routeMarkers.push(marker);
  });

  // Fit map to show the entire route
  map.value.fitBounds(routeLayer.getBounds(), { padding: [50, 50] });

  // Set displayed route (without distance/duration info)
  displayedRoute.value = route;
};

// Clear route display
const clearRoute = () => {
  if (routeLayer) {
    map.value.removeLayer(routeLayer);
    routeLayer = null;
  }
  displayedRoute.value = null;
  currentRouteCorners.value = null;

  // Remove route stop markers only
  routeMarkers.forEach(marker => {
    try {
      map.value.removeLayer(marker);
    } catch (e) {}
  });
  routeMarkers = [];

  // Keep corner markers intact so users can still click and view posts
};

// Format distance
const formatDistance = (meters) => {
  if (meters < 1000) {
    return `${Math.round(meters)}m`;
  }
  return `${(meters / 1000).toFixed(1)}km`;
};

// Get media URL
const getMediaUrl = (fileId) => {
  return mediaApi.getUrl(fileId);
};

// Open image viewer (placeholder for now)
const openImageViewer = (index) => {
  // Can be enhanced with a proper image viewer component
  const imageUrl = getMediaUrl(selectedCorner.value.images[index]);
  window.open(imageUrl, '_blank');
};

// Go to create corner page
const goToCreateCorner = () => {
  // Use selected map location if available, otherwise use current user location
  const location = selectedMapLocation.value || userLocation.value;
  
  router.push({
    path: '/create-corner',
    query: {
      lat: location.lat,
      lng: location.lng
    }
  });
};

// Expose displayRoute for external use
defineExpose({
  displayRoute
});

onMounted(async () => {
  initMap();

  // Check if we need to show a route from URL params or session storage
  const showRoute = route.query.show_route;
  const centerLat = route.query.center_lat;
  const centerLng = route.query.center_lng;

  if (showRoute === 'true') {
    // Try to get route data from session storage
    const routeData = sessionStorage.getItem('route_data');
    if (routeData) {
      try {
        const parsedRoute = JSON.parse(routeData);
        displayRoute(parsedRoute);
        sessionStorage.removeItem('route_data'); // Clear after use
      } catch (e) {
        console.error('Failed to parse route data:', e);
      }
    }
  }

  // Check if we need to highlight a specific corner from URL params
  const cornerId = route.query.corner_id;
  const cornerLat = route.query.lat;
  const cornerLng = route.query.lng;

  if (cornerId && cornerLat && cornerLng) {
    // First center the map on the corner location
    map.value.setView([parseFloat(cornerLat), parseFloat(cornerLng)], 16);

    // Load nearby corners around this location
    try {
      const response = await cornersApi.getNearby({
        lat: parseFloat(cornerLat),
        lng: parseFloat(cornerLng),
        radius: 5000, // 5km around the corner
        limit: 50
      });

      if (response.success && response.data?.corners) {
        nearbyCorners.value = response.data.corners;
        displayCorners(response.data.corners);

        // Find and select the specific corner
        const corner = nearbyCorners.value.find(c => c._id === cornerId);
        if (corner) {
          selectCorner(corner);
        }
      }
    } catch (err) {
      console.error('Failed to load corners around target location:', err);
    }
  } else {
    // Normal flow: get user location, then load nearby corners
    getUserLocation();
  }

  // Center map if coordinates provided (for route view)
  if (centerLat && centerLng && !showRoute && !cornerId) {
    map.value.setView([parseFloat(centerLat), parseFloat(centerLng)], 14);
  }
});

// Watch for route query changes to handle corner clicks when already on MapView page
watch(() => route.query, async (newQuery) => {
  // Handle corner click from PostCard
  const cornerId = newQuery.corner_id;
  const cornerLat = newQuery.lat;
  const cornerLng = newQuery.lng;

  if (cornerId && cornerLat && cornerLng) {
    // Clear any existing route display
    if (routeLayer) {
      map.value.removeLayer(routeLayer);
      routeLayer = null;
    }
    displayedRoute.value = null;
    currentRouteCorners.value = null;
    routeMarkers.forEach(marker => {
      try {
        map.value.removeLayer(marker);
      } catch (e) {}
    });
    routeMarkers = [];

    // Clear selected corner
    selectedCorner.value = null;
    cornerPosts.value = [];

    // Center map on the corner location
    map.value.setView([parseFloat(cornerLat), parseFloat(cornerLng)], 16);

    // Load nearby corners around this location
    try {
      const response = await cornersApi.getNearby({
        lat: parseFloat(cornerLat),
        lng: parseFloat(cornerLng),
        radius: 5000,
        limit: 50
      });

      if (response.success && response.data?.corners) {
        nearbyCorners.value = response.data.corners;
        displayCorners(response.data.corners);

        // Find and select the specific corner
        const corner = nearbyCorners.value.find(c => c._id === cornerId);
        if (corner) {
          selectCorner(corner);
        }
      }
    } catch (err) {
      console.error('Failed to load corners around target location:', err);
    }
  }
}, { deep: true });

onUnmounted(() => {
  if (map.value) {
    map.value.remove();
  }
});
</script>

<style scoped>
.map-view {
  height: 100%;
  width: 100%;
  position: relative;
  overflow: hidden;
}

/* Search Bar */
.search-bar {
  position: absolute;
  top: 20px;
  left: 80px;
  right: 20px;
  z-index: 1000;
  display: flex;
  gap: 10px;
  max-width: 600px;
}

.search-input {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  background: white;
  border-radius: 8px;
  padding: 12px 16px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.15);
}

.search-icon {
  font-size: 18px;
}

.search-input input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 15px;
}

.clear-button {
  background: none;
  border: none;
  color: #999;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 20px;
  height: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-button:hover {
  color: #333;
}

.search-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.3);
  transition: all 0.3s;
}

.search-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.4);
}

.reset-button {
  padding: 12px 24px;
  background: linear-gradient(135deg, #6c757d 0%, #8a939b 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(108, 117, 125, 0.3);
  transition: all 0.3s;
}

.reset-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(108, 117, 125, 0.4);
}

/* Create Corner Button */
.create-corner-button {
  position: absolute;
  top: 80px;
  left: 80px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 12px 20px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ff8787 100%);
  color: white;
  border: none;
  border-radius: 25px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 4px 12px rgba(255, 107, 107, 0.4);
  transition: all 0.3s;
  z-index: 1000;
}

.create-corner-button:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 16px rgba(255, 107, 107, 0.5);
}

.button-icon {
  font-size: 18px;
}

.button-label {
  font-size: 14px;
}

/* Map Container */
.map-container {
  height: 100%;
  width: 100%;
}

/* Side Panel */
.side-panel {
  position: absolute;
  top: 0;
  right: -400px;
  width: 380px;
  height: 100%;
  background: white;
  box-shadow: -4px 0 16px rgba(0, 0, 0, 0.15);
  transition: right 0.3s ease-in-out;
  z-index: 1000;
  display: flex;
  flex-direction: column;
}

.side-panel.open {
  right: 0;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.panel-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.close-button {
  background: none;
  border: none;
  font-size: 28px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 32px;
  height: 32px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: color 0.3s;
}

.close-button:hover {
  color: #333;
}

.panel-content {
  flex: 1;
  overflow-y: auto;
  padding: 20px;
}

.corner-info .description {
  color: #666;
  line-height: 1.6;
  margin-bottom: 20px;
}

.corner-images {
  margin-bottom: 20px;
}

.images-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 8px;
  border-radius: 8px;
  overflow: hidden;
}

.images-grid img {
  width: 100%;
  height: 100px;
  object-fit: cover;
  cursor: pointer;
  transition: opacity 0.2s;
}

.images-grid img:hover {
  opacity: 0.9;
}

.more-images {
  position: relative;
  padding: 8px;
  background: rgba(0, 0, 0, 0.5);
  color: white;
  text-align: center;
  font-size: 14px;
  font-weight: 500;
}

.stats {
  display: flex;
  gap: 20px;
  margin-bottom: 24px;
  padding: 16px;
  background: #f8f9fa;
  border-radius: 8px;
}

.stat-item {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.stat-number {
  font-size: 24px;
  font-weight: 600;
  color: #409eff;
}

.stat-label {
  font-size: 12px;
  color: #999;
  margin-top: 4px;
}

.posts-section h3 {
  margin: 0 0 16px 0;
  font-size: 16px;
  color: #333;
}

.loading {
  display: flex;
  justify-content: center;
  padding: 40px;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  padding: 40px 20px;
  text-align: center;
  color: #999;
}

.corner-posts {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

/* Route Info */
.route-info {
  position: absolute;
  bottom: 20px;
  left: 20px;
  right: 20px;
  max-width: 400px;
  background: white;
  border-radius: 12px;
  box-shadow: 0 4px 16px rgba(0, 0, 0, 0.15);
  z-index: 1000;
}

.route-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 16px;
  border-bottom: 1px solid #f0f0f0;
}

.route-icon {
  font-size: 24px;
}

.route-name {
  flex: 1;
  font-weight: 600;
  color: #333;
}

.clear-route {
  background: none;
  border: none;
  font-size: 24px;
  color: #999;
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-route:hover {
  color: #333;
}

.route-stops {
  padding: 12px;
}

.route-stop {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 8px 12px;
}

.stop-number {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #00C853 0%, #69F0AE 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 2px 6px rgba(0, 200, 83, 0.4);
}

.stop-name {
  flex: 1;
  color: #333;
}

/* Custom Leaflet Marker Styles */
:deep(.user-marker) {
  position: relative;
}

:deep(.user-marker-inner) {
  width: 24px;
  height: 24px;
  background: #409eff;
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.5);
}

:deep(.temp-location-marker) {
  position: relative;
}

:deep(.temp-marker-inner) {
  width: 30px;
  height: 30px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ff8787 100%);
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 0 0 6px rgba(255, 107, 107, 0.3);
}

:deep(.route-stop-marker) {
  position: relative;
}

:deep(.route-stop-marker .stop-number) {
  width: 30px;
  height: 30px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ff8787 100%);
  color: white;
  border: 3px solid white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(255, 107, 107, 0.5);
}

/* Mobile Responsive Styles */
@media (max-width: 600px) {
  /* Search Bar - Stack vertically and reduce padding */
  .search-bar {
    left: 10px;
    right: 10px;
    top: 10px;
    flex-direction: column;
    max-width: none;
    gap: 8px;
  }

  .search-input {
    padding: 10px 12px;
  }

  .search-input input {
    font-size: 16px; /* Prevent iOS zoom on focus */
  }

  .search-button,
  .reset-button {
    padding: 10px 16px;
    font-size: 14px;
  }

  /* Create Corner Button - Smaller and positioned better */
  .create-corner-button {
    top: auto;
    bottom: 90px;
    left: 10px;
    padding: 10px 16px;
    border-radius: 20px;
  }

  .button-label {
    display: none; /* Hide text on mobile, show only icon */
  }

  .button-icon {
    font-size: 20px;
  }

  /* Side Panel - Full width on mobile */
  .side-panel {
    width: 100%;
    right: -100%;
  }

  .panel-header {
    padding: 14px 16px;
  }

  .panel-header h2 {
    font-size: 18px;
  }

  .panel-content {
    padding: 14px;
  }

  .images-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .images-grid img {
    height: 80px;
  }

  .stats {
    gap: 16px;
    padding: 12px;
  }

  .stat-number {
    font-size: 20px;
  }

  .posts-section h3 {
    font-size: 15px;
  }

  .corner-posts {
    gap: 10px;
  }

  /* Route Info - Full width and compact */
  .route-info {
    left: 10px;
    right: 10px;
    bottom: 10px;
    max-width: none;
    border-radius: 10px;
  }

  .route-header {
    padding: 12px;
  }

  .route-icon {
    font-size: 20px;
  }

  .route-name {
    font-size: 14px;
  }

  .route-stops {
    padding: 8px;
    max-height: 150px;
    overflow-y: auto;
  }

  .route-stop {
    padding: 6px 10px;
  }

  .stop-number {
    width: 24px;
    height: 24px;
    font-size: 12px;
  }

  .stop-name {
    font-size: 13px;
  }
}

/* Extra small screens */
@media (max-width: 380px) {
  .search-button,
  .reset-button {
    padding: 8px 12px;
    font-size: 13px;
  }

  .tab-btn {
    font-size: 12px;
    padding: 8px 10px;
  }
}
</style>