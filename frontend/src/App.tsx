import {
  BrowserRouter,
  Navigate,
  Route,
  Routes,
  useParams,
} from "react-router-dom";

import { AuthProvider } from "./context/AuthContext";
import { AppLayout } from "./layouts/AppLayout";

import AuthPage from "./pages/AuthPage";
import Dashboard from "./pages/Dashboard";
import Code from "./pages/Code";
import CodeProblem from "./pages/CodeProblem";
import Practice from "./pages/Practice";
import Progress from "./pages/Progress";
import Documents from "./pages/Documents";
import DocumentChat from "./pages/DocumentChat";
import Tutor from "./pages/Tutor";
import Settings from "./pages/Settings";

import { ComingSoon } from "./components/ComingSoon";

function PracticeDetail() {
  const { id } = useParams();

  return (
    <ComingSoon
      title={`Problem #${id}`}
      phase="Phase 8"
      note="Problem statement, editor, hints and AI feedback."
    />
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Authentication */}
          <Route
            path="/auth"
            element={<AuthPage mode="login" />}
          />

          <Route
            path="/auth/login"
            element={<AuthPage mode="login" />}
          />

          <Route
            path="/auth/register"
            element={<AuthPage mode="register" />}
          />

          {/* Application */}
          <Route element={<AppLayout />}>
            <Route
              path="/"
              element={<Navigate to="/dashboard" replace />}
            />

            <Route
              path="/dashboard"
              element={<Dashboard />}
            />

            {/* Coding */}
            <Route
              path="/code"
              element={<Code />}
            />

            <Route
              path="/code/:id"
              element={<CodeProblem />}
            />

            {/* Practice */}
            <Route
              path="/practice"
              element={<Practice />}
            />

            <Route
              path="/practice/:id"
              element={<PracticeDetail />}
            />

            {/* Progress */}
            <Route
              path="/progress"
              element={<Progress />}
            />

            {/* Documents */}
            <Route
              path="/documents"
              element={<Documents />}
            />

            <Route
              path="/documents/:id"
              element={<DocumentChat />}
            />

            {/* Tutor */}
            <Route
              path="/tutor"
              element={<Tutor />}
            />

            {/* Settings */}
            <Route
              path="/settings"
              element={<Settings />}
            />

            {/* Unknown application route */}
            <Route
              path="*"
              element={<Navigate to="/dashboard" replace />}
            />
          </Route>

          {/* Unknown public route */}
          <Route
            path="*"
            element={<Navigate to="/dashboard" replace />}
          />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}