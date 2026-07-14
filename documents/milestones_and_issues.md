# Milestones & GitHub Issues: Monolith to React + DRF Migration

This document outlines the milestones and specific GitHub issues required to execute the refactoring of **PlasticKothay** into a decoupled Django REST Framework and React application.

---

## 1. Project Milestones

```text
+---------------------------------------------------------------------------------+
| Milestone 1: Core API Setup & CORS Integration (Target: Week 1)                 |
| - Django REST Framework installed and configured                                |
| - CORS configuration active for localhost frontend development                  |
+---------------------------------------------------------------------------------+
                                      |
                                      v
+---------------------------------------------------------------------------------+
| Milestone 2: Serializers & Authentication APIs (Target: Week 2)                 |
| - MongoEngine DRF Serializers established for User, OTP, and Posts              |
| - JWT Auth / Verification endpoints active and tested                           |
+---------------------------------------------------------------------------------+
                                      |
                                      v
+---------------------------------------------------------------------------------+
| Milestone 3: Report and Admin Feature APIs (Target: Week 3)                     |
| - Posts submission and filtering APIs fully developed                           |
| - Google Drive Upload and Admin Accept/Reject flow migrated to API endpoints    |
+---------------------------------------------------------------------------------+
                                      |
                                      v
+---------------------------------------------------------------------------------+
| Milestone 4: Frontend App Bootstrap & Auth Integration (Target: Week 4)        |
| - React, Vite, TypeScript initialized and Axios instance configured             |
| - Frontend routing and AuthContext integration complete                         |
+---------------------------------------------------------------------------------+
                                      |
                                      v
+---------------------------------------------------------------------------------+
| Milestone 5: Map Integration & Post Creation Flow (Target: Week 5)              |
| - Leaflet Map showing current reports deployed in React                         |
| - Report submission (with base64 camera photo) active from React client         |
+---------------------------------------------------------------------------------+
                                      |
                                      v
+---------------------------------------------------------------------------------+
| Milestone 6: Admin Dashboard & End-to-End Release (Target: Week 6)              |
| - React Superadmin Dashboard, metrics charts, and approval panels completed     |
| - Final verification, cross-browser check, and launch production build         |
+---------------------------------------------------------------------------------+
```

---

## 2. GitHub Issue Templates & Work Items

Below are the industry-standard GitHub Issues categorized by Milestone. You can copy-paste these markdown templates directly into GitHub Issues.

### Milestone 1: Core API Setup & CORS Integration

#### Issue 1.1: Install and configure Django REST Framework & CORS
- **Title:** `chore: Install and configure Django REST Framework & CORS headers`
- **Labels:** `chore`, `backend`
- **Milestone:** `Milestone 1: Core API Setup`
- **Description:**
  ```markdown
  ### Description
  Set up the baseline dependencies required to expose the backend as a RESTful JSON API and authorize requests from the React development server.

  ### Tasks
  - [ ] Add `djangorestframework`, `django-cors-headers`, and `pyjwt` to `backend/requirements.txt`.
  - [ ] Install dependencies inside the Python environment.
  - [ ] Add `rest_framework` and `corsheaders` to `INSTALLED_APPS` in `settings.py`.
  - [ ] Add `corsheaders.middleware.CorsMiddleware` to settings `MIDDLEWARE`.
  - [ ] Configure `CORS_ALLOWED_ORIGINS` to include `http://localhost:5173`.
  - [ ] Add baseline `REST_FRAMEWORK` configuration settings.

  ### Acceptance Criteria
  - [ ] Command `pip install -r backend/requirements.txt` runs successfully.
  - [ ] Running the server (`python backend/manage.py runserver`) executes without error.
  - [ ] Outbound responses include standard CORS headers when queried from `http://localhost:5173`.
  ```

---

### Milestone 2: Serializers & Authentication APIs

#### Issue 2.1: Implement MongoEngine custom DRF Serializers
- **Title:** `feat: Create MongoEngine serializers for User, OTP, and Post documents`
- **Labels:** `feat`, `backend`, `database`
- **Milestone:** `Milestone 2: Serializers & Auth`
- **Description:**
  ```markdown
  ### Description
  Since the database is MongoDB via `mongoengine`, custom Serializers must be written manually to translate documents to JSON and vice-versa, specifically handling `ObjectId` and `DateTimeField` serialization.

  ### Tasks
  - [ ] Create `backend/superadmin/serializers.py` and implement `UserSerializer` and `OTPSerializer`.
  - [ ] Create `backend/plastickothay/serializers.py` and implement `PostSerializer` and `RateSerializer`.
  - [ ] Implement a custom `ObjectIdField` to handle MongoDB `ObjectId` field mappings to string representation.
  - [ ] Add field validations for password security and format constraints matching MongoDB schema fields.

  ### Acceptance Criteria
  - [ ] User and Post serializer tests run and successfully serialize/deserialize mock documents.
  - [ ] Validation errors are raised properly when invalid properties (e.g. invalid email) are passed to the serializers.
  ```

#### Issue 2.2: Build authentication and verification API views
- **Title:** `feat: Develop token-based authentication and verification API endpoints`
- **Labels:** `feat`, `backend`, `auth`
- **Milestone:** `Milestone 2: Serializers & Auth`
- **Description:**
  ```markdown
  ### Description
  Convert the traditional session-based signup, login, OTP verification, and password reset template views into JSON-returning DRF API views.

  ### Tasks
  - [ ] Implement `MongoJWTAuthentication` class to validate JWT tokens from authorization header.
  - [ ] Create API endpoint `/api/auth/register/` (signup logic generating registration OTP).
  - [ ] Create API endpoint `/api/auth/verify/` (verifies OTP code and marks user verified).
  - [ ] Create API endpoint `/api/auth/login/` (validates password and issues JWT token).
  - [ ] Create API endpoints `/api/auth/forget-password/` and `/api/auth/reset-password/`.

  ### Acceptance Criteria
  - [ ] Authentication endpoints return proper JSON responses with JWT token upon success, and standard error JSON on failure.
  - [ ] Unauthenticated API endpoints fail with `401 Unauthorized` when requested without a token.
  - [ ] JWT tokens properly parse and authenticate MongoDB custom User models.
  ```

---

### Milestone 3: Report and Admin Feature APIs

#### Issue 3.1: Build post submission and filter endpoints
- **Title:** `feat: Migrate Post reports submission and list filters to DRF views`
- **Labels:** `feat`, `backend`
- **Milestone:** `Milestone 3: Post & Admin APIs`
- **Description:**
  ```markdown
  ### Description
  Re-implement the main reports feed and post detail page views as DRF endpoints. Adapt the filtering features (today, last week, severity level, status) to read from query params.

  ### Tasks
  - [ ] Create `/api/posts/` GET API endpoint supporting filters (`filter=today`, `filter=severity_3`, etc.).
  - [ ] Create `/api/posts/` POST API endpoint to submit a report (accepts base64 image data and calls Google Drive helper).
  - [ ] Create `/api/posts/<id>/` GET/PUT API endpoint to view or update a post description.
  - [ ] Migrate `contribution` dashboard data query calculations to `/api/users/contribution/` view.

  ### Acceptance Criteria
  - [ ] Accessing `/api/posts/?filter=accepted` returns only posts with `status = 1`.
  - [ ] Submitting a JSON payload with a base64 photo creates a new Mongo document and uploads the file to Google Drive.
  ```

#### Issue 3.2: Build admin review and deletion APIs
- **Title:** `feat: Expose admin approval APIs and integrate Google Drive deletion`
- **Labels:** `feat`, `backend`, `admin`
- **Milestone:** `Milestone 3: Post & Admin APIs`
- **Description:**
  ```markdown
  ### Description
  Migrate the admin control actions (accept/reject) to protected DRF API routes, restricted only to administrators (user_type 1 or 2).

  ### Tasks
  - [ ] Create API view `/api/admin/posts/<id>/accept/` (sets status to 1 and emails user via Mailjet).
  - [ ] Create API view `/api/admin/posts/<id>/reject/` (deletes image from Google Drive and removes document).
  - [ ] Secure endpoints with DRF custom permission classes checking user type constraints.

  ### Acceptance Criteria
  - [ ] Requests to admin routes from a non-admin user yield `403 Forbidden`.
  - [ ] Rejecting a post deletes the file on Google Drive and responds with `200 OK` / message metadata.
  ```

---

### Milestone 4: Frontend App Bootstrap & Auth Integration

#### Issue 4.1: Scaffold React + Vite + TypeScript Application
- **Title:** `chore: Scaffold frontend app and configure Axios instance`
- **Labels:** `chore`, `frontend`
- **Milestone:** `Milestone 4: Frontend Core`
- **Description:**
  ```markdown
  ### Description
  Bootstrap the React application inside the empty `/frontend` folder and establish API connectivity defaults.

  ### Tasks
  - [ ] Execute Vite React/TS initialization under `/frontend`.
  - [ ] Install `axios`, `react-router-dom`, and `@types/react-router-dom`.
  - [ ] Configure `vite.config.ts` to proxy `/api` requests to Django backend on port 8000.
  - [ ] Setup Axios instance with interceptors to inject JWT authentication header.

  ### Acceptance Criteria
  - [ ] Frontend workspace compiles cleanly (`npm run build`).
  - [ ] Vite dev server launches without errors.
  - [ ] Axios interceptor correctly retrieves token from local storage and appends it to headers.
  ```

#### Issue 4.2: Build client routes and authentication state context
- **Title:** `feat: Create Auth Context and routing structure`
- **Labels:** `feat`, `frontend`
- **Milestone:** `Milestone 4: Frontend Core`
- **Description:**
  ```markdown
  ### Description
  Build the React Router config and set up authentication state tracking (`AuthContext`) across the frontend client.

  ### Tasks
  - [ ] Design Auth Context (`useAuth` custom hook) to manage authentication states (login, logout, registration, token storage).
  - [ ] Set up client router: Home, Login, Register, Verify, Dashboard, and Contribution pages.
  - [ ] Build a `ProtectedRoute` component to handle path guarding.
  - [ ] Design general navigation layout (Navbar, Footer).

  ### Acceptance Criteria
  - [ ] Accessing `/dashboard` redirects anonymous users to `/login`.
  - [ ] Logging in correctly updates Context user properties and redirects to dashboard.
  ```

---

### Milestone 5: Map Integration & Post Creation Flow

#### Issue 5.1: Integrate Map and posts rendering
- **Title:** `feat: Display reported issues on interactive React map`
- **Labels:** `feat`, `frontend`
- **Milestone:** `Milestone 5: Maps & Reports`
- **Description:**
  ```markdown
  ### Description
  Integrate Leaflet Maps (using `react-leaflet`) on the landing page to visual-map reports of plastic issues, using custom markers reflecting severity color-coding.

  ### Tasks
  - [ ] Install `leaflet` and `react-leaflet`.
  - [ ] Add Leaflet map widget onto landing page component.
  - [ ] Query `/api/posts/` and plot markers at coordinates (`lat` / `lon`).
  - [ ] Display details popup on click (Title, severity, description, photo preview).

  ### Acceptance Criteria
  - [ ] Landing page shows a map containing markers for all active posts.
  - [ ] Clicking a marker displays a descriptive popup with correct image and details.
  ```

#### Issue 5.2: Develop webcam capturing and report posting form
- **Title:** `feat: Build report submission flow with camera integration`
- **Labels:** `feat`, `frontend`
- **Milestone:** `Milestone 5: Maps & Reports`
- **Description:**
  ```markdown
  ### Description
  Implement the report creation flow where users can input information, take a photo using their device's webcam/camera, and submit it.

  ### Tasks
  - [ ] Install `react-webcam` (or code standard HTML5 stream capture).
  - [ ] Build Report Form modal component capturing severity, phone, email, description, and photo.
  - [ ] Capture user's geolocation using the HTML5 Geolocation API.
  - [ ] Encode captured photo as base64 and dispatch payload to `/api/posts/` backend endpoint.

  ### Acceptance Criteria
  - [ ] User can snap a photo directly using their device camera or webcam.
  - [ ] Form submission captures accurate lat/lon coordinates from browser geolocation API.
  - [ ] Submitting the form sends API request and shows a success alert.
  ```

---

### Milestone 6: Admin Dashboard & End-to-End Release

#### Issue 6.1: Build admin dashboard metrics and control panel
- **Title:** `feat: Build React Admin Dashboard console`
- **Labels:** `feat`, `frontend`, `admin`
- **Milestone:** `Milestone 6: Admin & Release`
- **Description:**
  ```markdown
  ### Description
  Construct the administrative control dashboard for supervisors to review submissions, inspect analytics, and accept or reject report requests.

  ### Tasks
  - [ ] Implement Admin Dashboard page (protected for admin users only).
  - [ ] Draw metrics charts (Accepts vs Rejects counts) using `recharts`.
  - [ ] Render pending reports list with accept (Approve) and reject (Delete) CTA buttons.
  - [ ] Hook control buttons to `/api/admin/posts/<id>/accept/` and `/api/admin/posts/<id>/reject/`.

  ### Acceptance Criteria
  - [ ] Admin panel fetches dashboard stats and visualizes weekly trends correctly.
  - [ ] Clicking "Approve" removes the report from the pending queue on screen and updates status dynamically.
  ```

#### Issue 6.2: End-to-End QA and build optimization
- **Title:** `chore: End-to-end integration QA & production building`
- **Labels:** `chore`, `qa`
- **Milestone:** `Milestone 6: Admin & Release`
- **Description:**
  ```markdown
  ### Description
  Execute final validation on integrations: MongoDB transactions, Google Drive uploads, CORS authorizations, and token lifetimes. Build React app production resources.

  ### Tasks
  - [ ] Perform security reviews: check JWT encryption algorithms, verify endpoints block unauthenticated actions.
  - [ ] Compile production distribution (`npm run build`).
  - [ ] Configure backend static routing to host the compiled React app bundle or set up reverse proxy guidelines.

  ### Acceptance Criteria
  - [ ] Frontend builds into static assets in the `/frontend/dist` directory with zero build warnings.
  - [ ] API security verify script tests run successfully.
  ```
