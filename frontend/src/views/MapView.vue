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
    </div>

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
import { ref, onMounted, onUnmounted } from 'vue';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { cornersApi } from '../api/corners';
import { postsApi } from '../api/posts';
import PostCard from '../components/Feed/PostCard.vue';

// Fix for Leaflet default marker icons
delete L.Icon.Default.prototype._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/images/marker-shadow.png',
});

const mapContainer = ref(null);
const map = ref(null);
const userLocation = ref({ lat: 52.4862, lng: -1.8904 }); // Default: Birmingham
const nearbyCorners = ref([]);
const selectedCorner = ref(null);
const cornerPosts = ref([]);
const loadingPosts = ref(false);
const searchQuery = ref('');
const displayedRoute = ref(null);

let markers = [];
let routeLayer = null;
let userMarker = null;

// Initialize map
const initMap = () => {
  map.value = L.map(mapContainer.value).setView([userLocation.value.lat, userLocation.value.lng], 14);

  // Add OpenStreetMap tiles
  L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
    attribution: '© OpenStreetMap contributors',
    maxZoom: 19
  }).addTo(map.value);

  // Add user location marker
  updateUserMarker();

  // Load nearby corners
  loadNearbyCorners();
};

// Update user marker
const updateUserMarker = () => {
  if (userMarker) {
    map.value.removeLayer(userMarker);
  }

  const userIcon = L.divIcon({
    className: 'user-marker',
    html: '<div class="user-marker-inner"></div>',
    iconSize: [20, 20],
    iconAnchor: [10, 10]
  });

  userMarker = L.marker([userLocation.value.lat, userLocation.value.lng], {
    icon: userIcon
  }).addTo(map.value);
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

// Load nearby corners
const loadNearbyCorners = async () => {
  try {
    const response = await cornersApi.getNearby({
      lat: userLocation.value.lat,
      lng: userLocation.value.lng,
      radius: 10000, // 10km
      limit: 50
    });

    if (response.success && response.data?.corners) {
      nearbyCorners.value = response.data.corners;
      displayCorners(response.data.corners);
    }
  } catch (err) {
    console.error('Failed to load nearby corners:', err);
  }
};

// Display corners on map
const displayCorners = (corners) => {
  // Clear existing markers
  markers.forEach(marker => map.value.removeLayer(marker));
  markers = [];

  corners.forEach(corner => {
    const [lng, lat] = corner.location.coordinates;
    const marker = L.marker([lat, lng]).addTo(map.value);

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

// Display route on map
const displayRoute = (route) => {
  if (routeLayer) {
    map.value.removeLayer(routeLayer);
  }

  if (!route.corners || route.corners.length < 2) return;

  const latLngs = route.corners.map(corner => {
    const [lng, lat] = corner.location.coordinates;
    return [lat, lng];
  });

  // Create a styled polyline for the route
  // Note: For real navigation routes, you would need to integrate a routing service like OSRM
  // This is a simplified visualization connecting the corners directly
  routeLayer = L.polyline(latLngs, {
    color: '#409eff',
    weight: 5,
    opacity: 0.8,
    dashArray: '10, 10'
  }).addTo(map.value);

  // Add markers for each stop
  route.corners.forEach((corner, idx) => {
    const [lng, lat] = corner.location.coordinates;
    const stopIcon = L.divIcon({
      className: 'route-stop-marker',
      html: `<div class="stop-number">${idx + 1}</div>`,
      iconSize: [30, 30],
      iconAnchor: [15, 15]
    });

    const marker = L.marker([lat, lng], { icon: stopIcon }).addTo(map.value);
    marker.bindPopup(`<strong>${corner.name}</strong>`);
    markers.push(marker);
  });

  // Fit map to show the entire route
  map.value.fitBounds(routeLayer.getBounds(), { padding: [50, 50] });

  displayedRoute.value = route;
};

// Clear route display
const clearRoute = () => {
  if (routeLayer) {
    map.value.removeLayer(routeLayer);
    routeLayer = null;
  }
  displayedRoute.value = null;

  // Remove route stop markers
  markers.forEach(marker => map.value.removeLayer(marker));
  markers = [];

  // Reload nearby corners
  loadNearbyCorners();
};

// Format distance
const formatDistance = (meters) => {
  if (meters < 1000) {
    return `${Math.round(meters)}m`;
  }
  return `${(meters / 1000).toFixed(1)}km`;
};

// Expose displayRoute for external use
defineExpose({
  displayRoute
});

onMounted(() => {
  initMap();
  getUserLocation();
});

onUnmounted(() => {
  if (map.value) {
    map.value.remove();
  }
});
</script>

<style scoped>
.map-view {
  height: 100vh;
  width: 100%;
  position: relative;
}

/* Search Bar */
.search-bar {
  position: absolute;
  top: 20px;
  left: 20px;
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
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
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
  width: 20px;
  height: 20px;
  background: #409eff;
  border: 3px solid white;
  border-radius: 50%;
  box-shadow: 0 2px 8px rgba(64, 158, 255, 0.5);
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
</style>