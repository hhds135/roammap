<template>
  <div class="route-selector">
    <label>Route (Optional)</label>
    <div class="route-section">
      <div v-if="route && route.cornerIds.length >= 2" class="route-preview">
        <div class="route-header">
          <span class="route-icon">🛤️</span>
          <input 
            type="text" 
            v-model="route.routeName" 
            placeholder="Route name (e.g., Weekend Coffee Tour)" 
            class="route-name-input"
          />
          <button type="button" @click="clearRoute" class="clear-route-btn">×</button>
        </div>
        <div class="route-stops">
          <div 
            v-for="(corner, idx) in getOrderedCorners()" 
            :key="corner._id"
            class="route-stop"
          >
            <span class="stop-number">{{ idx + 1 }}</span>
            <span class="stop-name">{{ corner.name }}</span>
            <button 
              type="button" 
              @click="removeStop(idx)" 
              class="remove-stop"
            >×</button>
          </div>
        </div>
      </div>
      <div v-else class="route-placeholder">
        <p>Add at least 2 corners to create a route</p>
      </div>
    </div>
    <p class="hint">Create a route by adding corners in sequence</p>
  </div>
</template>

<script setup>
import { computed, watch } from 'vue';

const props = defineProps({
  corners: {
    type: Array,
    default: () => []
  },
  modelValue: {
    type: Object,
    default: null
  }
});

const emit = defineEmits(['update:modelValue']);

const route = computed({
  get: () => props.modelValue,
  set: (value) => emit('update:modelValue', value)
});

// Get corners in route order
const getOrderedCorners = () => {
  if (!route.value || !route.value.cornerIds) return [];
  
  return route.value.cornerIds
    .map(id => props.corners.find(c => c._id === id))
    .filter(Boolean);
};

const removeStop = (index) => {
  if (!route.value) return;
  
  const newCornerIds = [...route.value.cornerIds];
  newCornerIds.splice(index, 1);
  
  if (newCornerIds.length < 2) {
    route.value = null;
  } else {
    route.value = {
      ...route.value,
      cornerIds: newCornerIds
    };
  }
};

const clearRoute = () => {
  route.value = null;
};

// Auto-create route when 2+ corners are added
watch(() => props.corners.length, (newLength, oldLength) => {
  if (newLength >= 2 && (!route.value || route.value.cornerIds.length < 2)) {
    // Auto-create route with all corners in order
    route.value = {
      routeName: '',
      cornerIds: props.corners.map(c => c._id)
    };
  }
});
</script>

<style scoped>
.route-selector {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.route-selector label {
  font-weight: 600;
  color: #333;
  font-size: 14px;
}

.route-section {
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 16px;
  background: white;
}

.route-preview {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.route-header {
  display: flex;
  align-items: center;
  gap: 12px;
}

.route-icon {
  font-size: 24px;
}

.route-name-input {
  flex: 1;
  padding: 8px 12px;
  border: 1px solid #ddd;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
}

.route-name-input:focus {
  outline: none;
  border-color: #409eff;
}

.clear-route-btn {
  background: none;
  border: none;
  color: #999;
  font-size: 24px;
  cursor: pointer;
  padding: 0;
  width: 28px;
  height: 28px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  transition: all 0.3s;
}

.clear-route-btn:hover {
  background: #ff6b6b;
  color: white;
}

.route-stops {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.route-stop {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 14px;
  background: #f5f5f5;
  border-radius: 8px;
  transition: all 0.3s;
}

.route-stop:hover {
  background: #e8e8e8;
}

.stop-number {
  width: 28px;
  height: 28px;
  background: linear-gradient(135deg, #ff6b6b 0%, #ff8787 100%);
  color: white;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 14px;
  font-weight: 600;
  flex-shrink: 0;
}

.stop-name {
  flex: 1;
  font-size: 14px;
  color: #333;
  font-weight: 500;
}

.remove-stop {
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

.remove-stop:hover {
  background: #ff6b6b;
  color: white;
}

.route-placeholder {
  padding: 20px;
  text-align: center;
  color: #999;
  font-size: 14px;
}

.hint {
  margin: 4px 0 0 0;
  font-size: 12px;
  color: #999;
  font-style: italic;
}
</style>