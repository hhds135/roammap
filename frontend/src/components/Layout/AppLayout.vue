<template>
  <div class="app-layout">
    <main class="main-content">
      <router-view />
    </main>
    <TabBar />
  </div>
</template>

<script setup>
import TabBar from './TabBar.vue';
</script>

<style scoped>
.app-layout {
  display: flex;
  flex-direction: column;
  height: 100vh;
  overflow: hidden;
}

.main-content {
  flex: 1;
  overflow: hidden;
  position: relative;
}
</style>