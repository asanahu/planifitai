# PlanifitAI Web

MVP frontend built with React, TypeScript, Vite and Tailwind CSS.

## Development

```bash
npm install
npm run dev
```

Create a `.env` file based on `.env.example` with the API URL.

## Build

```bash
npm run build
```

## Onboarding flow & flags

After login, if your profile is incomplete or you have no active routine you will be redirected to an onboarding wizard.
The wizard first asks for basic profile data and then creates an initial plan. When `VITE_FEATURE_AI=1` the plan is generated
using the AI endpoints; otherwise a template defined by `VITE_FALLBACK_TEMPLATE_ID` is cloned. You can bypass the flow by
visiting any page with `?skip=1` in the URL.
