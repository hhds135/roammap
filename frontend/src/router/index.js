import { createRouter, createWebHistory } from 'vue-router';
import { useAuth } from '../composables/useAuth';

const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('../views/Login.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('../views/Register.vue'),
    meta: { requiresGuest: true }
  },
  {
    path: '/',
    component: () => import('../components/Layout/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      {
        path: '',
        redirect: '/feed'
      },
      {
        path: 'feed',
        name: 'Feed',
        component: () => import('../views/FeedView.vue')
      },
      {
        path: 'interests',
        name: 'Interests',
        component: () => import('../views/InterestsView.vue')
      },
      {
        path: 'favorites',
        name: 'Favorites',
        component: () => import('../views/FavoritesView.vue')
      },
      {
        path: 'search-users',
        name: 'SearchUsers',
        component: () => import('../views/SearchUsersView.vue')
      },
      {
        path: 'notifications',
        name: 'Notifications',
        component: () => import('../views/NotificationsView.vue')
      },
      {
        path: 'edit-profile',
        name: 'EditProfile',
        component: () => import('../views/EditProfileView.vue')
      },
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('../views/UserProfileView.vue')
      },
      {
        path: 'profile/:userId',
        name: 'UserProfile',
        component: () => import('../views/UserProfileView.vue')
      },
      {
        path: 'map',
        name: 'Map',
        component: () => import('../views/MapView.vue')
      },
      {
        path: 'create',
        name: 'CreatePost',
        component: () => import('../views/CreatePostView.vue')
      },
      {
        path: 'create-corner',
        name: 'CreateCorner',
        component: () => import('../views/CreateCornerView.vue')
      },
      {
        path: 'edit-corner/:cornerId',
        name: 'EditCorner',
        component: () => import('../views/EditCornerView.vue')
      },
      {
        path: 'post/:postId',
        name: 'PostDetail',
        component: () => import('../views/PostDetailView.vue')
      }
    ]
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

router.beforeEach((to, from, next) => {
  const { loadUser, isAuthenticated } = useAuth();
  loadUser();

  const requiresAuth = to.matched.some(record => record.meta.requiresAuth);
  const requiresGuest = to.matched.some(record => record.meta.requiresGuest);

  if (requiresAuth && !isAuthenticated.value) {
    next('/login');
  } else if (requiresGuest && isAuthenticated.value) {
    next('/feed');
  } else {
    next();
  }
});

export default router;