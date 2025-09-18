import React, { useState, useEffect } from 'react';

interface TestResult {
  success: boolean;
  data?: any;
  error?: string;
  indicators?: {
    forecast?: boolean;
    insights?: boolean;
    anomalies?: boolean;
  };
  hasInsights?: boolean;
  firstCall?: number;
  secondCall?: number;
  improvement?: string;
}

interface TestResults {
  apiConnection: TestResult | null;
  mlData: TestResult | null;
  geminiInsights: TestResult | null;
  caching: TestResult | null;
}

const MLValidationPage: React.FC = () => {
  const [testResults, setTestResults] = useState<TestResults>({
    apiConnection: null,
    mlData: null,
    geminiInsights: null,
    caching: null
  });

  const [isRunning, setIsRunning] = useState(false);

  const API_BASE = 'https://cp58oqed6g.execute-api.ap-east-1.amazonaws.com/prod';

  const runTests = async () => {
    console.log('🧪 Starting ML Integration Tests...');
    setIsRunning(true);

    // Reset results
    setTestResults({
      apiConnection: null,
      mlData: null,
      geminiInsights: null,
      caching: null
    });

    // Test 1: API Connection
    try {
      const response = await fetch(`${API_BASE}/branches`);
      const data = await response.json();
      setTestResults(prev => ({
        ...prev,
        apiConnection: { success: true, data: data }
      }));
      console.log('✅ API Connection: SUCCESS');
    } catch (error: any) {
      setTestResults(prev => ({
        ...prev,
        apiConnection: { success: false, error: error.message }
      }));
      console.log('❌ API Connection: FAILED', error);
    }

    // Test 2: ML Data (Machine History)
    try {
      const response = await fetch(`${API_BASE}/machines/leg-press-01/history`);
      const data = await response.json();

      // Check for ML indicators
      const hasMLData = data.forecast || data.ml_insights || data.anomalies;

      setTestResults(prev => ({
        ...prev,
        mlData: {
          success: hasMLData,
          data: data,
          indicators: {
            forecast: !!data.forecast,
            insights: !!data.ml_insights,
            anomalies: !!data.anomalies
          }
        }
      }));
      console.log('✅ ML Data Test:', hasMLData ? 'SUCCESS' : 'NO ML DATA');
    } catch (error: any) {
      setTestResults(prev => ({
        ...prev,
        mlData: { success: false, error: error.message }
      }));
      console.log('❌ ML Data: FAILED', error);
    }

    // Test 3: Gemini AI Integration
    try {
      const response = await fetch(`${API_BASE}/chat`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: 'Analyze usage patterns for gym equipment',
          location: { lat: 22.2819, lon: 114.1577 }
        })
      });
      const data = await response.json();

      setTestResults(prev => ({
        ...prev,
        geminiInsights: {
          success: true,
          data: data,
          hasInsights: data.insights || data.response
        }
      }));
      console.log('✅ Gemini AI: SUCCESS');
    } catch (error: any) {
      setTestResults(prev => ({
        ...prev,
        geminiInsights: { success: false, error: error.message }
      }));
      console.log('❌ Gemini AI: FAILED', error);
    }

    // Test 4: Caching Test (lightweight endpoint for better cache detection)
    try {
      console.log('🔄 Testing caching system...');
      const start1 = Date.now();
      await fetch(`${API_BASE}/branches`);
      const time1 = Date.now() - start1;

      // Small delay to ensure different timestamp
      await new Promise(resolve => setTimeout(resolve, 100));

      const start2 = Date.now();
      await fetch(`${API_BASE}/branches`);
      const time2 = Date.now() - start2;

      const cachingWorking = time2 < time1 * 0.5; // Second call should be much faster

      setTestResults(prev => ({
        ...prev,
        caching: {
          success: cachingWorking,
          firstCall: time1,
          secondCall: time2,
          improvement: `${((time1 - time2) / time1 * 100).toFixed(1)}%`
        }
      }));
      console.log('✅ Caching Test:', cachingWorking ? 'WORKING' : 'NOT DETECTED');
    } catch (error: any) {
      console.log('⚠️ Caching test inconclusive');
      setTestResults(prev => ({
        ...prev,
        caching: { success: false, error: 'Test inconclusive' }
      }));
    }

    setIsRunning(false);
  };

  return (
    <div className="p-6 max-w-4xl mx-auto">
      <h1 className="text-2xl font-bold mb-6">🧪 ML Integration Validation</h1>

      <button
        onClick={runTests}
        disabled={isRunning}
        className={`px-4 py-2 rounded mb-6 hover:opacity-80 transition-opacity ${
          isRunning
            ? 'bg-gray-400 text-gray-700 cursor-not-allowed'
            : 'bg-blue-500 text-white hover:bg-blue-600'
        }`}
      >
        {isRunning ? '🔄 Running Tests...' : 'Run All Tests'}
      </button>

      <div className="space-y-4">
        {/* API Connection Test */}
        <div className="border p-4 rounded bg-white shadow-sm">
          <h3 className="font-semibold text-lg mb-2">1. API Connection</h3>
          {testResults.apiConnection ? (
            <div className={testResults.apiConnection.success ? 'text-green-600' : 'text-red-600'}>
              <div className="flex items-center gap-2 mb-2">
                {testResults.apiConnection.success ? '✅' : '❌'}
                <span className="font-medium">
                  {testResults.apiConnection.success ? 'Connected' : 'Failed'}
                </span>
              </div>
              {testResults.apiConnection.error && (
                <p className="text-sm bg-red-50 p-2 rounded border">
                  Error: {testResults.apiConnection.error}
                </p>
              )}
              {testResults.apiConnection.success && testResults.apiConnection.data && (
                <p className="text-sm text-gray-600">
                  Found {testResults.apiConnection.data.branches?.length || 0} branches
                </p>
              )}
            </div>
          ) : (
            <div className="text-gray-500">⏳ Waiting for test to run...</div>
          )}
        </div>

        {/* ML Data Test */}
        <div className="border p-4 rounded bg-white shadow-sm">
          <h3 className="font-semibold text-lg mb-2">2. ML Data Integration</h3>
          {testResults.mlData ? (
            <div className={testResults.mlData.success ? 'text-green-600' : 'text-red-600'}>
              <div className="flex items-center gap-2 mb-2">
                {testResults.mlData.success ? '✅' : '❌'}
                <span className="font-medium">
                  {testResults.mlData.success ? 'ML Data Found' : 'No ML Data'}
                </span>
              </div>
              {testResults.mlData.indicators && (
                <div className="text-sm mt-2 space-y-1">
                  <p>Forecast: {testResults.mlData.indicators.forecast ? '✅' : '❌'}</p>
                  <p>AI Insights: {testResults.mlData.indicators.insights ? '✅' : '❌'}</p>
                  <p>Anomalies: {testResults.mlData.indicators.anomalies ? '✅' : '❌'}</p>
                </div>
              )}
              {testResults.mlData.error && (
                <p className="text-sm bg-red-50 p-2 rounded border mt-2">
                  Error: {testResults.mlData.error}
                </p>
              )}
            </div>
          ) : (
            <div className="text-gray-500">⏳ Waiting for test to run...</div>
          )}
        </div>

        {/* Gemini AI Test */}
        <div className="border p-4 rounded bg-white shadow-sm">
          <h3 className="font-semibold text-lg mb-2">3. Gemini AI Integration</h3>
          {testResults.geminiInsights ? (
            <div className={testResults.geminiInsights.success ? 'text-green-600' : 'text-red-600'}>
              <div className="flex items-center gap-2 mb-2">
                {testResults.geminiInsights.success ? '✅' : '❌'}
                <span className="font-medium">
                  {testResults.geminiInsights.success ? 'AI Working' : 'AI Failed'}
                </span>
              </div>
              {testResults.geminiInsights.data && testResults.geminiInsights.success && (
                <div className="text-sm mt-2 bg-gray-100 p-3 rounded border max-h-64 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-xs">
                    {JSON.stringify(testResults.geminiInsights.data, null, 2)}
                  </pre>
                </div>
              )}
              {testResults.geminiInsights.error && (
                <p className="text-sm bg-red-50 p-2 rounded border mt-2">
                  Error: {testResults.geminiInsights.error}
                </p>
              )}
            </div>
          ) : (
            <div className="text-gray-500">⏳ Waiting for test to run...</div>
          )}
        </div>

        {/* Caching Test */}
        <div className="border p-4 rounded bg-white shadow-sm">
          <h3 className="font-semibold text-lg mb-2">4. Caching System</h3>
          {testResults.caching ? (
            <div className={testResults.caching.success ? 'text-green-600' : 'text-yellow-600'}>
              <div className="flex items-center gap-2 mb-2">
                {testResults.caching.success ? '✅' : '⚠️'}
                <span className="font-medium">
                  {testResults.caching.success ? 'Caching Working' : 'Caching Unclear'}
                </span>
              </div>
              {testResults.caching.firstCall !== undefined && (
                <div className="text-sm mt-2 space-y-1">
                  <p>First call: {testResults.caching.firstCall}ms</p>
                  <p>Second call: {testResults.caching.secondCall}ms</p>
                  <p>Improvement: {testResults.caching.improvement}</p>
                </div>
              )}
              {testResults.caching.error && (
                <p className="text-sm bg-yellow-50 p-2 rounded border mt-2">
                  Note: {testResults.caching.error}
                </p>
              )}
            </div>
          ) : (
            <div className="text-gray-500">⏳ Waiting for test to run...</div>
          )}
        </div>
      </div>

      {/* Overall Status */}
      <div className="mt-8 p-4 border rounded bg-blue-50">
        <h3 className="font-semibold text-lg mb-2">🎯 Overall Status</h3>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
          <div className="text-center">
            <div className="text-2xl mb-1">
              {testResults.apiConnection?.success ? '✅' : testResults.apiConnection === null ? '⏳' : '❌'}
            </div>
            <div>API</div>
          </div>
          <div className="text-center">
            <div className="text-2xl mb-1">
              {testResults.mlData?.success ? '✅' : testResults.mlData === null ? '⏳' : '❌'}
            </div>
            <div>ML Data</div>
          </div>
          <div className="text-center">
            <div className="text-2xl mb-1">
              {testResults.geminiInsights?.success ? '✅' : testResults.geminiInsights === null ? '⏳' : '❌'}
            </div>
            <div>Gemini AI</div>
          </div>
          <div className="text-center">
            <div className="text-2xl mb-1">
              {testResults.caching?.success ? '✅' : testResults.caching === null ? '⏳' : '⚠️'}
            </div>
            <div>Caching</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default MLValidationPage;