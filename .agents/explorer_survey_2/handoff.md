# Frontend & UI Architecture Survey Report ('Pace' Project)

## 1. Observation

Direct examination of the workspace revealed two frontend-related directories at the root level (`d:\IIT-Bhuv`):
1. `d:\IIT-Bhuv\frontend\index.html`: A legacy/standalone single-file prototype.
2. `d:\IIT-Bhuv\mobile\`: The active React + Vite + TypeScript + Capacitor mobile SPA application.

### 1.1 Frontend Framework, Build System & Dependencies
Inspecting `d:\IIT-Bhuv\mobile\package.json` (lines 1-33):
```json
{
  "name": "mobile",
  "private": true,
  "version": "0.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc -b && vite build",
    "lint": "oxlint",
    "preview": "vite preview"
  },
  "dependencies": {
    "@capacitor/android": "^8.5.2",
    "@capacitor/core": "^8.5.2",
    "@capacitor/geolocation": "^8.2.2",
    "@capacitor/ios": "^8.5.2",
    "lucide-react": "^1.45.0",
    "react": "^19.2.8",
    "react-dom": "^19.2.8",
    "react-router-dom": "^7.18.3"
  },
  "devDependencies": {
    "@capacitor/cli": "^8.5.2",
    "@types/node": "^24.13.3",
    "@types/react": "^19.2.18",
    "@types/react-dom": "^19.2.7",
    "@vitejs/plugin-react": "^6.1.1",
    "oxlint": "^1.81.0",
    "typescript": "~6.0.2",
    "vite": "^8.3.0"
  }
}
```
Key observations:
- **Framework**: React 19.2.8 with React DOM 19.2.8.
- **Build System**: Vite 8.3.0 with `@vitejs/plugin-react` 6.1.1.
- **TypeScript**: TypeScript ~6.0.2 configured with composite project references (`tsconfig.json` referencing `tsconfig.app.json` and `tsconfig.node.json`).
  - `tsconfig.app.json` specifies `"target": "es2023"`, `"moduleResolution": "bundler"`, `"verbatimModuleSyntax": true`, `"jsx": "react-jsx"`, `"allowImportingTsExtensions": true`.
- **Routing**: `react-router-dom` 7.18.3.
- **Icons**: `lucide-react` 1.45.0.
- **Mobile Container**: Capacitor 8.5.2 (`@capacitor/core`, `@capacitor/cli`, `@capacitor/android`, `@capacitor/ios`, `@capacitor/geolocation`).
  - `capacitor.config.ts`: `appId: 'com.pace.app'`, `appName: 'Pace'`, `webDir: 'dist'`.
- **Missing Dependencies**:
  - `@capawesome-team/capacitor-health` (referenced in R4 and `plan.md` section 1, but not yet present in `package.json` or `node_modules`).
  - No chart library installed (`chart.js` or `recharts`). In `frontend/index.html`, Chart.js was loaded via CDN script tag.

### 1.2 Existing UI Components, Pages, Navigation & Styling
- **Entry Point**: `mobile/src/main.tsx` (lines 6-10):
  ```tsx
  createRoot(document.getElementById('root')!).render(
    <StrictMode>
      <App />
    </StrictMode>,
  )
  ```
- **Routing Structure**: `mobile/src/App.tsx` (lines 11-23):
  ```tsx
  <Router>
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<Navigate to="/dashboard" replace />} />
        <Route path="dashboard" element={<Dashboard />} />
        <Route path="planner" element={<Planner />} />
        <Route path="chat" element={<Chat />} />
        <Route path="calendar" element={<Calendar />} />
        <Route path="settings" element={<Settings />} />
      </Route>
    </Routes>
  </Router>
  ```
- **Layout Shell**: `mobile/src/components/Layout.tsx` (lines 7-14):
  - Renders `<Header />`, `<main style={{ flex: 1, overflowY: 'auto', padding: '1rem', paddingBottom: '2rem' }}><Outlet /></main>`, and `<Footer />`.
- **Persistent Header**: `mobile/src/components/Header.tsx` (lines 5-21):
  - Brand name "Pace" (bold italic, color: `var(--primary)`).
  - Subtitle "Good Morning Champ!!".
  - Streak counter: Hardcoded `<span>12</span>` and `<Flame size={20} color="#ff7675" fill="#ff7675" />` (lines 17-19).
- **Bottom Navigation**: `mobile/src/components/Footer.tsx` (lines 5-31):
  - 5 routes: `/dashboard` (`LayoutDashboard`), `/planner` (`ListTodo`), `/chat` (`Bot`), `/calendar` (`CalendarDays`), `/settings` (`User`).
  - Rendered using `<NavLink className={({isActive}) => `neu-btn ${isActive ? 'active' : ''}`} style={{ padding: '0.8rem', borderRadius: '50%' }}>{item.icon}</NavLink>`.
  - Missing text labels below icons; lacks Strava-style active branding and center action emphasis.
- **Pages**:
  - `mobile/src/pages/Dashboard.tsx`
  - `mobile/src/pages/Planner.tsx`
  - `mobile/src/pages/Chat.tsx`
  - `mobile/src/pages/Calendar.tsx`
  - `mobile/src/pages/Settings.tsx`
  - All 5 page files are currently one-line skeleton stubs: `<div className="neu-box"><h2>{Tab} Tab</h2><p>This view will be built out next!</p></div>`.
- **Styling Framework**:
  - **No Tailwind CSS**: No `tailwind.config.js` or `postcss.config.js`.
  - **Custom Neumorphism CSS** in `mobile/src/index.css`:
    - Variables: `--bg: #e0e5ec`, `--text: #4a4a4a`, `--primary: #0984e3`, `--danger: #ff7675`.
    - Drop shadows: `--neu-shadow: 9px 9px 16px rgb(163,177,198,0.6), -9px -9px 16px rgba(255,255,255, 0.5)`
    - Inset shadows: `--neu-shadow-inset: inset 5px 5px 10px rgb(163,177,198,0.6), inset -5px -5px 10px rgba(255,255,255, 0.5)`
    - CSS utility classes: `.neu-box`, `.neu-btn`, `.neu-btn.active`.
  - `mobile/src/App.css` contains default Vite boilerplate styles which are currently unused.

### 1.3 Backend Communication & Dev Server
- **Backend API**:
  - Backend runs FastAPI at `http://localhost:8000` with open CORS (`allow_origins=["*"]` in `backend/main.py:11-17`).
  - Existing endpoints in `backend/main.py`:
    - `GET /`
    - `GET /api/data/acwr_history` (returns array of `{ date, acwr, workload }`)
    - `POST /api/onboard/chat` (accepts `{ history: [{role, content}] }`)
    - `POST /api/plan/generate` (query params `athlete_id`, `target_date`, `current_fatigue`, `current_sleep`)
    - `POST /api/logs/submit` (body `DailyLog`)
    - `POST /api/events/add` (body `Event`)
- **Frontend API Client**:
  - Currently, `mobile/src/` has NO API client, services directory, or base URL configuration.
- **Vite Configuration**:
  - `mobile/vite.config.ts`:
    ```ts
    import react from '@vitejs/plugin-react'
    import { defineConfig } from 'vite'

    export default defineConfig({
      plugins: [react()],
    })
    ```
    No proxy is configured yet for `/api` requests.
- **Vite Dev Server**:
  - Command: `npm run dev` in `mobile/` runs `vite` on port 5173.

---

## 2. Logic Chain

1. **Active Frontend Identification**:
   - `frontend/index.html` is an unbundled, legacy vanilla HTML/JS prototype referencing external CDN scripts.
   - `mobile/` has full Vite, React 19, TypeScript, Capacitor configs, and a 5-tab router shell matching the R3 specifications.
   - Therefore, all R3/R4 implementation work must target `d:\IIT-Bhuv\mobile`.

2. **R3 Requirements Analysis**:
   - **Persistent Header with Dynamic Streak Counter**:
     - Observation: `Header.tsx:17` hardcodes `<span>12</span>`.
     - In `ORIGINAL_REQUEST.md` (R1 & R3), streaks are driven by completing daily tasks in `training_plans`.
     - Logic: `Header.tsx` must consume streak state dynamically. We should introduce an `AthleteContext` or `StreakContext` that fetches the streak from the backend and updates immediately when quests are marked complete on the Dashboard or Planner tabs.
     - Dynamic greeting logic: Calculate greeting based on local time (Morning/Afternoon/Evening) and user name.
   - **Strava-Style Bottom Navigation Bar**:
     - Observation: `Footer.tsx` renders 5 icon-only circular buttons using neumorphic active inset shadows.
     - Strava design language requires:
       1. Clear labels under icons ("Home", "Planner", "Pace AI", "Calendar", "Profile").
       2. Strava accent color (`#FC5200` or energetic Pace orange/blue highlight) for the active tab.
       3. Elevated / prominent center action tab (Pace AI Chat).
       4. Safe area inset padding for mobile viewports (`paddingBottom: calc(0.5rem + env(safe-area-inset-bottom, 0px))`).
   - **5-Tab Mobile Pages**:
     - All 5 pages are currently empty stubs.
     - `Dashboard.tsx`: Needs Health Stats Grid (Steps, Active Calories, Distance, Sleep, Resting HR) using Health Provider with Web Mock fallback (R4), ACWR line chart, Today's Quests list with completion toggles, and Upcoming Trials.
     - `Planner.tsx`: Needs 1-day rolling Quests generator display (R1), task status toggles, and plan generation trigger (`/api/plan/generate`).
     - `Chat.tsx`: Needs Pace AI intent router conversation view (R2) with message history, quick prompts, and action execution status.
     - `Calendar.tsx`: Needs upcoming match/trial calendar list and quick-add event modal.
     - `Settings.tsx`: Needs athlete profile metrics, mock health mode status toggle, and streak reset/test controls.

3. **Backend Communication & Proxy**:
   - In dev mode, browser calls to `http://localhost:8000` directly can encounter CORS or cross-origin quirks if ports change.
   - Adding a Vite proxy in `mobile/vite.config.ts` mapping `/api` to `http://localhost:8000` allows clean relative fetch calls (`/api/...`) in web mode.
   - For Capacitor on Android/iOS, a service helper `getApiBaseUrl()` should return `http://10.0.2.2:8000` (Android emulator) or the configured IP/env var when running on native devices.

4. **Health Provider & Mock Architecture (R4 Integration)**:
   - R4 requires `@capawesome-team/capacitor-health` with browser fallback to mock data.
   - Logic: Create `src/services/healthService.ts` and `src/context/HealthContext.tsx`. Detect platform via `Capacitor.getPlatform()`. If `'web'` or if native call fails, serve realistic athlete mock data (e.g. 8,450 steps, 540 kcal, 6.2 km, 58 bpm resting HR, 7.5 hrs sleep) so local web development and acceptance testing work seamlessly without device deployment.

---

## 3. Caveats

1. **Tool Execution Permission**: Interactive shell commands (`npm run build` / `npm run dev`) through `run_command` require user confirmation prompts. Exploration was conducted via static file inspection, code analysis, and dependency verification.
2. **Capacitor Health Package**: `@capawesome-team/capacitor-health` is not yet installed in `package.json`. If installing native packages in React 19 / Vite 8 environments causes peer dependency warnings, the web mock provider layer is designed to handle this gracefully even before native plugins are added.
3. **Chart Library**: `chart.js` is not installed in `mobile/node_modules`. An SVG-based responsive ACWR chart component or adding `chart.js` / lightweight canvas chart will be needed for `Dashboard.tsx`.
4. **Backend Route Evolution**: Backend routes may be expanded by Explorer 1 (R1 Quests table) and Explorer 3 (R2 Chat Intent Router). Frontend API services should use flexible interfaces matching the R1-R4 acceptance criteria.

---

## 4. Conclusion

The frontend foundation for the 'Pace' mobile application is located in `d:\IIT-Bhuv\mobile`. It has a working React 19 + TypeScript + Vite + Capacitor setup with a basic 5-tab router shell, but all 5 tab pages are placeholder stubs, the streak counter is hardcoded, the bottom navigation lacks Strava styling/labels, and no API service or health provider exists.

### Proposed Component Hierarchy & Directory Architecture:
```
mobile/src/
├── components/
│   ├── Layout.tsx             # Persistent shell (Header + scrollable content + Footer)
│   ├── Header.tsx             # Dynamic greeting & live streak counter with flame
│   ├── Footer.tsx             # Strava-style bottom navigation (icons + labels + elevated center tab)
│   ├── QuestsList.tsx         # Today's quests with completion checkmarks
│   ├── AcwrChart.tsx          # Workload graph rendering ACWR & 1.5 danger line
│   ├── HealthStatsGrid.tsx    # 5-metric grid (Steps, Calories, Distance, Sleep, HR)
│   └── EventCard.tsx          # Event list item with badges (Match, Trial)
├── context/
│   ├── AthleteContext.tsx     # Holds streak, profile, and daily quests state
│   └── HealthContext.tsx      # R4 Health provider with seamless web mock fallback
├── services/
│   ├── api.ts                 # Typed fetch client connecting to FastAPI backend
│   └── healthService.ts       # Capacitor Health / Mock fallback data provider
├── pages/
│   ├── Dashboard.tsx          # Health stats, ACWR chart, today's quests preview
│   ├── Planner.tsx            # 1-day rolling Quests, task editor, plan generation
│   ├── Chat.tsx               # Pace AI conversational intent router UI
│   ├── Calendar.tsx           # Match/trial schedule and event addition
│   └── Settings.tsx           # Athlete metrics, mock health toggle, streak tester
├── types/
│   └── index.ts               # TypeScript data models (Quest, Event, Athlete, HealthData, Chat)
├── App.tsx                    # Routes + Provider wrapping
├── main.tsx                   # React root entry
└── index.css                  # Neumorphic styling system with mobile safe-area utilities
```

### Actionable Delta for R3 Implementation:
1. **Configure Vite Proxy**: Add `server.proxy` for `/api` -> `http://localhost:8000` in `mobile/vite.config.ts`.
2. **Build API Service & Types**: Create `mobile/src/services/api.ts` and `mobile/src/types/index.ts`.
3. **Implement Health Provider (R4)**: Create `mobile/src/services/healthService.ts` and `mobile/src/context/HealthContext.tsx` with browser mock data fallback.
4. **Implement Athlete / Streak State**: Create `mobile/src/context/AthleteContext.tsx` syncing streak count with completed quests.
5. **Update Header (`Header.tsx`)**: Connect dynamic streak counter and time-of-day greeting.
6. **Rebuild Bottom Nav (`Footer.tsx`)**: Implement Strava-style layout with labels, active accent colors, and prominent center Pace AI tab.
7. **Populate 5 Tab Pages**:
   - `Dashboard.tsx`: Health metrics grid, ACWR chart, Today's Quests, upcoming event preview.
   - `Planner.tsx`: Quests list, task complete/edit actions, regenerate plan button.
   - `Chat.tsx`: Intent router chat interface with quick action suggestions.
   - `Calendar.tsx`: Event list and event addition modal.
   - `Settings.tsx`: Athlete profile metrics and health mock toggle.

---

## 5. Verification Method

To independently verify the frontend architecture, implementation, and acceptance criteria:

1. **Static Typecheck & Build**:
   ```bash
   cd d:\IIT-Bhuv\mobile
   npm run build
   ```
   *Expected result*: TypeScript compiles with zero errors and Vite outputs the production bundle to `mobile/dist/`.

2. **Linting Check**:
   ```bash
   cd d:\IIT-Bhuv\mobile
   npm run lint
   ```
   *Expected result*: `oxlint` completes with 0 errors.

3. **Dev Server & Route Verification (R3 & R4 Acceptance Criteria)**:
   ```bash
   cd d:\IIT-Bhuv\mobile
   npm run dev
   ```
   - Open `http://localhost:5173` in a web browser.
   - Check navigation to all 5 tabs:
     - `/dashboard`: Verify Health mock grid renders (steps, calories, HR, sleep) without native plugin crash, and ACWR chart renders.
     - `/planner`: Verify Quests list renders and completed tasks trigger streak updates.
     - `/chat`: Verify chat interface renders with Pace persona.
     - `/calendar`: Verify event calendar and add-event controls render.
     - `/settings`: Verify profile settings and mock status indicator render.
   - Check Persistent Header: Verify "Pace" logo, dynamic greeting, and flame streak badge are visible and persistent across all routes.
   - Check Strava-Style Footer: Verify 5 labeled tabs, elevated center action button, and active tab highlighting.

4. **Invalidation Conditions**:
   - Build fails due to missing packages or TypeScript errors.
   - Browser crashes on `dashboard` tab due to unhandled Capacitor native health plugin calls.
   - Streak counter remains hardcoded at 12 instead of responding to completed tasks.
   - Footer tabs omit text labels or lack Strava-style visual hierarchy.
