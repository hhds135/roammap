# Urban Canvas

Urban Canvas is an app that allows its users to post and create locations (also called "corners") on a map based on geographic coordinates using FLask API. It combines aspects of social networking with user-generated content, allowing a user to share their created corner with the community and discover new places through their friends, family, or other sources.

The Urban Canvas application consists of a Flask API backend (to provide user authentication, management, and location data) and a Vue 3 front end with an interactive mapping interface using Leaflet. The capability to register an account, send and receive friend requests, and create corners will be part of this app. Users also have an option of setting the visibility of their created corners (e.g. public, private, or friends only). Corners can contain media (in the form of images, videos, etc.) so users will be able to like, comment, save, or share their content to others.

To create a lightweight solution without having users deploy their own database, the Urban Canvas platform utilizes json files for user data storage. The backend of the application supports the use of JWT (JSON Web Token) for authentication and has a full set of HTTP RESTful API endpoints available for each of the following functions: user management (e.g. creating, updating, deleting, retrieving user information), managing user created corners, managing user authored posts, managing user created comments, managing user likes, managing user favorites, and managing user friend relationships. In addition, the application contains a means of backing up the user data and corner data by generating a timestamp and saving user/corner data to a backup.

The Vue 3 front end is supported by the Vue Router for site navigation, Element Plus for UI components, and Leaflet for interactive map displays. This allows the user to interact with various features as they check out the map, manage social contacts, and find new ways to engage with content. The Application is installed using Vite, which allows rapid development and optimized build output for production.

Prerequisites and Setup:

- Backend Requirements: Python 3.12+ is required for the backend
- Frontend Requirements: Node.js is required for the frontend

Backend Setup:

- Navigate to the backend directory in a terminal
- Run python app.py to start the Flask server
- The backend API will be available at http://localhost:5200

Frontend Setup:

✦  - Navigate to the frontend directory in a separate terminal
- Install dependencies with npm install
- Run npm run dev to start the development server
- The frontend development server typically runs at http://localhost:5173