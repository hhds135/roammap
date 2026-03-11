<template>
  <div class="interests-view">
    <div class="interests-container">
      <InterestTagManager />
    </div>
  </div>
</template>

<script setup>
import InterestTagManager from '../components/Interests/InterestTagManager.vue';
</script>

<style scoped>
.interests-view {
  min-height: 100vh;
  background: #f5f7fa;
  padding: 20px;
}

.interests-container {
  max-width: 600px;
  margin: 0 auto;
  background: white;
  border-radius: 12px;
  padding: 30px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}
</style>