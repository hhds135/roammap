<template>
  <div class="register-page">
    <div class="register-container">
      <div class="brand">
        <h1>🗺️ RoamMap</h1>
        <p>Discover hidden corners, share your stories</p>
      </div>
      <RegisterForm />
    </div>
  </div>
</template>

<script setup>
import RegisterForm from '../components/Auth/RegisterForm.vue';
</script>

<style scoped>
.register-page {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  display: flex;
  align-items: center;
  justify-content: center;
}

.register-container {
  width: 100%;
  max-width: 500px;
  padding: 20px;
}

.brand {
  text-align: center;
  margin-bottom: 30px;
  color: white;
}

.brand h1 {
  font-size: 32px;
  margin-bottom: 10px;
}

.brand p {
  font-size: 16px;
  opacity: 0.9;
}
</style>
