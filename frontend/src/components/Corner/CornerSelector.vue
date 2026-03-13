<template>
  <div class="corner-selector">
    <label>Corners</label>
    
    <!-- Selected Corners List -->
    <div class="corner-list">
      <div
        v-for="corner in selectedCorners"
        :key="corner._id"
        class="corner-item"
      >
        <span class="corner-name">📍 {{ corner.name }}</span>
        <button type="button" @click="removeCorner(corner)" class="remove">×</button>
      </div>
      
      <button
        type="button"
        @click="openCornerSelector"
        class="add-corner-btn"
      >
        <span class="add-icon">➕</span>
        <span class="add-text">Add Corner</span>
      </button>
    </div>
    
    <p class="hint">Add corners to tag your post location(s)</p>

    <!-- Corner Selector Modal -->
    <div v-if="showSelector" class="corner-selector-modal" @click.self="closeSelector">
      <div class="modal-content">
        <div class="modal-header">
          <h2>Select Corner</h2>
          <button @click="closeSelector" class="close-btn">×</button>
        </div>

        <!-- Search -->
        <div class="search-section">
          <div class="search-input-wrapper">
            <span class="search-icon">🔍</span>
            <input
              v-model="searchQuery"
              type="text"
              placeholder="Search corners..."
              @keyup.enter="handleSearch"
            />
            <button v-if="searchQuery" @click="clearSearch" class="clear-search">×</button>
          </div>
          <button @click="handleSearch" class="search-btn">Search</button>
        </div>

        <!-- Tabs -->
        <div class="tabs">
          <button
            :class="['tab-btn', { active: activeTab === 'nearby' }]"
            @click="switchTab('nearby')"
          >
            Nearby (10km)
          </button>
          <button
            :class="['tab-btn', { active: activeTab === 'search' }]"
            @click="switchTab('search')"
          >
            Search Results
          </button>
        </div>

        <!-- Loading -->
        <div v-if="loading" class="loading">
          <div class="spinner"></div>
          <p>Loading...</p>
        </div>

        <!-- Corner List -->
        <div v-else-if="filteredCorners.length > 0" class="corners-scroll">
          <div
            v-for="corner in filteredCorners"
            :key="corner._id"
            :class="['corner-result-item', { selected: isCornerSelected(corner) }]"
            @click="toggleCorner(corner)"
          >
            <div class="corner-info">
              <span class="corner-name">{{ corner.name }}</span>
              <span v-if="corner.distance" class="corner-distance">
                {{ formatDistance(corner.distance) }} away
              </span>
              <span v-if="corner.description" class="corner-description">
                {{ corner.description }}
              </span>
            </div>
            <div class="corner-check">
              <span v-if="isCornerSelected(corner)" class="check-icon">✓</span>
            </div>
          </div>
        </div>

        <!-- Empty State -->
        <div v-else class="empty-state">
          <p v-if="activeTab === 'nearby'">No nearby corners found</p>
          <p v-else>No search results found</p>
        </div>

        <!-- Action Buttons -->
        <div class="modal-actions">
          <button @click="closeSelector" class="btn-cancel">Cancel</button>
          <button @click="confirmSelection" class="btn-confirm" :disabled="newSelection.length === 0">
            Confirm ({{ newSelection.length }})
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { cornersApi } from '../../api/corners';

const router = useRouter();

const props = defineProps({
  modelValue: {
    type: Array,
    default: () => []
  }
});

const emit = defineEmits(['update:modelValue']);

const showSelector = ref(false);
const searchQuery = ref('');
const activeTab = ref('nearby');
const nearbyCorners = ref([]);
const searchResults = ref([]);
const loading = ref(false);
const newSelection = ref([]);
const userLocation = ref({ lat: 31.2304, lng: 121.4737 }); // Default: Shanghai

const selectedCorners = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

const filteredCorners = computed(() => {
  return activeTab.value === 'nearby' ? nearbyCorners.value : searchResults.value;
});

// Get user location
const getUserLocation = () => {
  if ('geolocation' in navigator) {
    navigator.geolocation.getCurrentPosition(
      (position) => {
        userLocation.value = {
          lat: position.coords.latitude,
          lng: position.coords.longitude
        };
      },
      () => {
        console.log('Could not get user location, using default');
      }
    );
  }
};

// Load nearby corners
const loadNearbyCorners = async () => {
  loading.value = true;
  try {
    const response = await cornersApi.getNearby({
      lat: userLocation.value.lat,
      lng: userLocation.value.lng,
      radius: 10000, // 10km
      limit: 20
    });

    if (response.success && response.data?.corners) {
      nearbyCorners.value = response.data.corners;
    }
  } catch (err) {
    console.error('Failed to load nearby corners:', err);
  } finally {
    loading.value = false;
  }
};

// Search corners
const handleSearch = async () => {
  if (!searchQuery.value.trim()) return;

  loading.value = true;
  activeTab.value = 'search';

  try {
    const response = await cornersApi.search(searchQuery.value.trim(), { limit: 20 });
    if (response.success && response.data?.corners) {
      searchResults.value = response.data.corners;
    }
  } catch (err) {
    console.error('Failed to search corners:', err);
  } finally {
    loading.value = false;
  }
};

const clearSearch = () => {
  searchQuery.value = '';
  searchResults.value = [];
  activeTab.value = 'nearby';
};

const switchTab = (tab) => {
  activeTab.value = tab;
};

const openCornerSelector = () => {
  showSelector.value = true;
  newSelection.value = [...selectedCorners.value];
  
  if (activeTab.value === 'nearby' && nearbyCorners.value.length === 0) {
    loadNearbyCorners();
  }
};

const closeSelector = () => {
  showSelector.value = false;
  searchQuery.value = '';
  searchResults.value = [];
  activeTab.value = 'nearby';
};

const isCornerSelected = (corner) => {
  return newSelection.value.some(c => c._id === corner._id);
};

const toggleCorner = (corner) => {
  if (isCornerSelected(corner)) {
    newSelection.value = newSelection.value.filter(c => c._id !== corner._id);
  } else {
    newSelection.value.push(corner);
  }
};

const confirmSelection = () => {
  selectedCorners.value = [...newSelection.value];
  closeSelector();
};

const removeCorner = (corner) => {
  selectedCorners.value = selectedCorners.value.filter(c => c._id !== corner._id);
};

const goToMap = () => {
  // Store current post data in sessionStorage
  sessionStorage.setItem('pending_post_data', JSON.stringify({
    corners: selectedCorners.value
  }));
  
  // Navigate to create corner with redirect back to post
  router.push({
    path: '/create-corner',
    query: { redirect_to_post: 'true' }
  });
};

const formatDistance = (meters) => {
  if (meters < 1000) {
    return `${Math.round(meters)}m`;
  }
  return `${(meters / 1000).toFixed(1)}km`;
};

// Check if we're returning from creating a corner
onMounted(() => {
  getUserLocation();

  const pendingData = sessionStorage.getItem('pending_post_data');
  if (pendingData) {
    try {
      const data = JSON.parse(pendingData);
      if (data.corners) {
        selectedCorners.value = data.corners;
      }
      sessionStorage.removeItem('pending_post_data');
    } catch (e) {
      console.error('Failed to parse pending data:', e);
    }
  }
});
</script>

<style scoped>
.corner-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.corner-selector label {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.corner-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.corner-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 10px 14px;
  background: #f5f5f5;
  border-radius: 8px;
  transition: all 0.3s;
}

.corner-item:hover {
  background: #e8e8e8;
}

.corner-name {
  flex: 1;
  font-size: 14px;
  color: #333;
}

.remove {
  background: none;
  border: none;
  color: #999;
  font-size: 20px;
  cursor: pointer;
  padding: 0;
  width: 24px;
  height: 24px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s;
}

.remove:hover {
  background: #ff6b6b;
  color: white;
}

.add-corner-btn {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.add-corner-btn:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(102, 126, 234, 0.4);
}

.add-icon {
  font-size: 18px;
}

.add-text {
  font-size: 14px;
}

.hint {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #999;
  font-style: italic;
}

/* Modal Styles */
.corner-selector-modal {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 2000;
  padding: 20px;
}

.modal-content {
  background: white;
  border-radius: 12px;
  width: 100%;
  max-width: 500px;
  max-height: 80vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 20px;
  border-bottom: 1px solid #f0f0f0;
}

.modal-header h2 {
  margin: 0;
  font-size: 20px;
  color: #333;
}

.close-btn {
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
}

.close-btn:hover {
  color: #333;
}

.search-section {
  display: flex;
  gap: 10px;
  padding: 16px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.search-input-wrapper {
  flex: 1;
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  background: #f5f5f5;
  border-radius: 8px;
  border: 1px solid #e0e0e0;
}

.search-input-wrapper:focus-within {
  border-color: #409eff;
  background: white;
}

.search-icon {
  font-size: 18px;
}

.search-input-wrapper input {
  flex: 1;
  border: none;
  outline: none;
  font-size: 14px;
  background: transparent;
}

.clear-search {
  background: none;
  border: none;
  color: #999;
  font-size: 18px;
  cursor: pointer;
  padding: 0;
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.clear-search:hover {
  color: #333;
}

.search-btn {
  padding: 10px 20px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
}

.tabs {
  display: flex;
  gap: 2px;
  padding: 12px 20px;
  border-bottom: 1px solid #f0f0f0;
}

.tab-btn {
  flex: 1;
  padding: 8px 16px;
  background: transparent;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 14px;
  color: #666;
  transition: all 0.3s;
}

.tab-btn:hover {
  background: #f5f5f5;
}

.tab-btn.active {
  background: #e3f2fd;
  color: #409eff;
  font-weight: 500;
}

.corners-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 12px 20px;
}

.corner-result-item {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px;
  background: #f8f9fa;
  border-radius: 10px;
  margin-bottom: 10px;
  cursor: pointer;
  transition: all 0.3s;
  border: 2px solid transparent;
}

.corner-result-item:hover {
  background: #e9ecef;
  transform: translateX(4px);
}

.corner-result-item.selected {
  border-color: #409eff;
  background: #e3f2fd;
}

.corner-info {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.corner-result-item .corner-name {
  font-weight: 600;
  color: #333;
  font-size: 15px;
}

.corner-distance {
  font-size: 13px;
  color: #667eea;
}

.corner-description {
  font-size: 13px;
  color: #666;
  font-style: italic;
}

.corner-check {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  border: 2px solid #e0e0e0;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
}

.corner-result-item.selected .corner-check {
  background: #409eff;
  border-color: #409eff;
}

.check-icon {
  color: white;
  font-size: 16px;
  font-weight: bold;
}

.loading {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #999;
}

.spinner {
  width: 40px;
  height: 40px;
  border: 3px solid #f3f3f3;
  border-top: 3px solid #409eff;
  border-radius: 50%;
  animation: spin 1s linear infinite;
  margin-bottom: 12px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.empty-state {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
  color: #999;
}

.modal-actions {
  display: flex;
  gap: 12px;
  padding: 16px 20px;
  border-top: 1px solid #f0f0f0;
}

.btn-cancel {
  flex: 1;
  padding: 12px;
  background: white;
  color: #666;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  transition: all 0.3s;
}

.btn-cancel:hover {
  border-color: #409eff;
  color: #409eff;
}

.btn-confirm {
  flex: 1;
  padding: 12px;
  background: linear-gradient(135deg, #409eff 0%, #66b1ff 100%);
  color: white;
  border: none;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  font-weight: 600;
  transition: all 0.3s;
}

.btn-confirm:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(64, 158, 255, 0.3);
}

.btn-confirm:disabled {
  background: #ccc;
  cursor: not-allowed;
  transform: none;
  box-shadow: none;
}
</style>