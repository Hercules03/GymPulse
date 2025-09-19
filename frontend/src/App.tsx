import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './Layout';
import Dashboard from './pages/Dashbord';
import Branches from './pages/Branches';
import Machines from './pages/Machines';
import MachineDetail from './pages/MachineDetail';
import './globals.css';

function App() {
  return (
    <Router>
      <Routes>
        <Route path="/" element={<Navigate to="/branches" replace />} />
        <Route path="/*" element={
          <Layout>
            <Routes>
              <Route path="/branches" element={<Branches />} />
              <Route path="/dashboard/:branchId" element={<Dashboard />} />
              <Route path="/machines" element={<Machines />} />
              <Route path="/machine-detail" element={<MachineDetail />} />
            </Routes>
          </Layout>
        } />
      </Routes>
    </Router>
  );
}

export default App;
