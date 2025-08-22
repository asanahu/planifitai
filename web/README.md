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

## Deploy

To deploy the web app (e.g. on Vercel or Netlify):

1. Configure environment variables:
   - `VITE_API_BASE_URL` (required)
   - `VITE_FEATURE_AI` (optional)
   - `VITE_FALLBACK_TEMPLATE_ID` (optional)
   - `VITE_DEMO` (optional, set to `1` to enable offline demo with mocked API)
   - `VITE_PWA` (optional, set to `1` to enable PWA features)
2. Build the project:

```bash
npm run build
```

The static output will be generated in the `dist/` folder. Ensure your hosting provider
is configured for single-page applications so that unknown routes fall back to `index.html`.

## Onboarding flow & flags

After login, if your profile is incomplete or you have no active routine you will be redirected to an onboarding wizard.
The wizard first asks for basic profile data and then creates an initial plan. When `VITE_FEATURE_AI=1` the plan is generated
using the AI endpoints; otherwise a template defined by `VITE_FALLBACK_TEMPLATE_ID` is cloned. You can bypass the flow by
visiting any page with `?skip=1` in the URL.

## Cómo probar, e2e y desplegar

### Local demo

```bash
cp .env.example .env
npm i
npm run dev  # en otra terminal: npm run e2e:dev
```

### CI / pre-release

```bash
npm run check
npm run e2e:ci
```

### Despliegue Vercel/Netlify

Define las variables de entorno indicadas y utiliza tu proveedor para construir y servir la carpeta `dist/`.