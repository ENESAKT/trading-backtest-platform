# Sentry Integration Setup

Sentry is used for error tracking and performance monitoring in both the backend and frontend.

## 1. Get the Sentry DSN
1. Log in to your Sentry dashboard.
2. Go to **Settings > Projects**, select your project (or create one).
3. Navigate to **Client Keys (DSN)**.
4. Copy the DSN value.

## 2. Configure Environment Variables
Add the DSN to your `.env` file on the server (and `.env.example`):
```env
SENTRY_DSN=your_sentry_dsn_here
```

## 3. Backend Integration
The backend is configured in `backend/api/main.py`. The Sentry SDK initializes automatically if `SENTRY_DSN` is present in the environment variables.

## 4. Frontend Integration
In `frontend/src/app.ts`, ensure Sentry is initialized:
```typescript
import * as Sentry from "@sentry/browser";

if (import.meta.env.VITE_SENTRY_DSN) {
  Sentry.init({
    dsn: import.meta.env.VITE_SENTRY_DSN,
    integrations: [Sentry.browserTracingIntegration()],
    tracesSampleRate: 0.1,
  });
}
```
*Note: Make sure to prefix the environment variable with `VITE_` in your frontend build environment (e.g., `VITE_SENTRY_DSN=...`) if using Vite.*
