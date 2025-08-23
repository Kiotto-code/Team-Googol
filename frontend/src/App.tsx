import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { useState } from 'react';
import type { User } from './types';
import Navbar from './components/Navbar';
import HomePage from './pages/HomePage';
import ResumeBuilder from './pages/ResumeBuilder';
import JobMatcher from './pages/JobMatcher';
import MockInterview from './pages/MockInterview';
import SalaryInsights from './pages/SalaryInsights';
import Roadmap from './pages/Roadmap';
import EmailAutomation from './pages/EmailAutomation';
import './App.css';

function App() {
  const [user, setUser] = useState<User | null>(null);

  return (
    <Router>
      <div className="min-h-screen bg-gray-50">
        <Navbar user={user} setUser={setUser} />
        <main>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/resume" element={<ResumeBuilder />} />
            <Route path="/jobs" element={<JobMatcher />} />
            <Route path="/interview" element={<MockInterview />} />
            <Route path="/salary" element={<SalaryInsights />} />
            <Route path="/roadmap" element={<Roadmap />} />
            <Route path="/email" element={<EmailAutomation />} />
          </Routes>
        </main>
      </div>
    </Router>
  );
}

export default App;
