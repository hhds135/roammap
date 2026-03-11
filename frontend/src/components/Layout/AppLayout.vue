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
  min-height: 100vh;
  padding-bottom: 70px;
}

.main-content {
  min-height: 100vh;
}
</style>