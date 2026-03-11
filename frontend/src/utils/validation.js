export const validators = {
  username(username) {
    if (!username || username.trim().length < 3) {
      return { valid: false, message: 'Username must be at least 3 characters' };
    }
    return { valid: true };
  },

  password(password) {
    if (!password || password.length < 6) {
      return { valid: false, message: 'Password must be at least 6 characters' };
    }
    return { valid: true };
  }
};