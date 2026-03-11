export const storage = {
  setToken(token) {
    localStorage.setItem('auth_token', token);
  },

  getToken() {
    return localStorage.getItem('auth_token');
  },

  clearToken() {
    localStorage.removeItem('auth_token');
  },

  setUser(user) {
    localStorage.setItem('current_user', JSON.stringify(user));
  },

  getUser() {
    const userStr = localStorage.getItem('current_user');
    return userStr ? JSON.parse(userStr) : null;
  },

  clearUser() {
    localStorage.removeItem('current_user');
  },

  clearAuth() {
    this.clearToken();
    this.clearUser();
  }
};