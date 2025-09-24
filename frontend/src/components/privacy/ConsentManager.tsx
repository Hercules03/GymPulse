import React, { useState, useEffect } from 'react';
import { MapPin, Eye, BarChart3, Settings, Check, X } from 'lucide-react';

interface ConsentPreferences {
  location: boolean;
  analytics: boolean;
  notifications: boolean;
  ageVerified: boolean;
}

interface ConsentManagerProps {
  onConsentUpdate: (preferences: ConsentPreferences) => void;
  initialPreferences?: ConsentPreferences;
  showAgeVerification?: boolean;
}

const defaultPreferences: ConsentPreferences = {
  location: false,
  analytics: false,
  notifications: false,
  ageVerified: false
};

export default function ConsentManager({ 
  onConsentUpdate, 
  initialPreferences = defaultPreferences,
  showAgeVerification = true
}: ConsentManagerProps) {
  const [preferences, setPreferences] = useState<ConsentPreferences>(initialPreferences);
  const [hasChanges, setHasChanges] = useState(false);
  const [ageInput, setAgeInput] = useState('');
  const [ageVerificationError, setAgeVerificationError] = useState('');

  useEffect(() => {
    // Load saved preferences from localStorage
    const savedPreferences = localStorage.getItem('gym-pulse-consent');
    if (savedPreferences) {
      try {
        const parsed = JSON.parse(savedPreferences);
        setPreferences({ ...defaultPreferences, ...parsed });
      } catch (e) {
        console.warn('Failed to parse saved consent preferences');
      }
    }
  }, []);

  const updatePreference = (key: keyof ConsentPreferences, value: boolean) => {
    const newPreferences = { ...preferences, [key]: value };
    setPreferences(newPreferences);
    setHasChanges(true);
  };

  const handleAgeVerification = () => {
    const age = parseInt(ageInput);
    
    if (isNaN(age)) {
      setAgeVerificationError('Please enter a valid age');
      return;
    }
    
    if (age < 13) {
      setAgeVerificationError('This service is not available for users under 13');
      return;
    }
    
    if (age < 18) {
      // For users under 18, disable certain features
      setPreferences(prev => ({
        ...prev,
        ageVerified: true,
        analytics: false,  // Disable analytics for minors
        notifications: false  // Disable notifications for minors
      }));
      setAgeVerificationError('');
      setHasChanges(true);
    } else {
      setPreferences(prev => ({ ...prev, ageVerified: true }));
      setAgeVerificationError('');
      setHasChanges(true);
    }
  };

  const savePreferences = () => {
    // Save to localStorage
    localStorage.setItem('gym-pulse-consent', JSON.stringify(preferences));
    
    // Log consent for audit trail (in production, send to backend)
    const consentLog = {
      timestamp: new Date().toISOString(),
      preferences: preferences,
      userAgent: navigator.userAgent,
      ip: 'logged_separately', // In production, log IP separately
      sessionId: Date.now().toString() // Simple session ID for demo
    };
    
    console.log('Consent logged:', consentLog);
    
    // Update parent component
    onConsentUpdate(preferences);
    setHasChanges(false);
  };

  const withdrawAllConsent = () => {
    const withdrawnPreferences = {
      location: false,
      analytics: false,
      notifications: false,
      ageVerified: preferences.ageVerified // Keep age verification
    };
    
    setPreferences(withdrawnPreferences);
    setHasChanges(true);
    
    // Log consent withdrawal
    console.log('All consent withdrawn at:', new Date().toISOString());
  };

  const ConsentToggle = ({
    id: _,
    label,
    description,
    icon: Icon,
    enabled,
    onChange,
    disabled = false 
  }: {
    id: string;
    label: string;
    description: string;
    icon: React.ElementType;
    enabled: boolean;
    onChange: (enabled: boolean) => void;
    disabled?: boolean;
  }) => (
    <div className="flex items-start gap-4 p-4 border border-gray-200 rounded-lg">
      <Icon className="w-5 h-5 text-blue-600 mt-1" />
      <div className="flex-1">
        <div className="flex items-center justify-between">
          <h4 className="font-medium text-gray-900">{label}</h4>
          <label className="relative inline-flex items-center cursor-pointer">
            <input
              type="checkbox"
              checked={enabled}
              onChange={(e) => onChange(e.target.checked)}
              disabled={disabled}
              className="sr-only"
            />
            <div className={`w-11 h-6 rounded-full transition-colors ${
              enabled ? 'bg-blue-600' : 'bg-gray-300'
            } ${disabled ? 'opacity-50 cursor-not-allowed' : ''}`}>
              <div className={`w-4 h-4 rounded-full bg-white transition-transform transform ${
                enabled ? 'translate-x-6' : 'translate-x-1'
              } mt-1`} />
            </div>
          </label>
        </div>
        <p className="text-sm text-gray-600 mt-1">{description}</p>
        {disabled && (
          <p className="text-xs text-amber-600 mt-1">
            Disabled for users under 18 for privacy protection
          </p>
        )}
      </div>
    </div>
  );

  const isMinor = preferences.ageVerified && parseInt(ageInput) < 18;

  return (
    <div className="max-w-2xl mx-auto p-6 bg-white rounded-lg shadow-lg">
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-2">
          <Settings className="w-6 h-6 text-blue-600" />
          <h2 className="text-xl font-semibold text-gray-900">Privacy Preferences</h2>
        </div>
        <p className="text-gray-600">
          Manage your data and privacy preferences. You can change these settings at any time.
        </p>
      </div>

      {/* Age Verification */}
      {showAgeVerification && !preferences.ageVerified && (
        <div className="mb-6 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
          <h3 className="font-semibold text-yellow-800 mb-2">Age Verification Required</h3>
          <p className="text-sm text-yellow-700 mb-3">
            Please verify your age to customize your privacy preferences according to Hong Kong privacy laws.
          </p>
          <div className="flex gap-2">
            <input
              type="number"
              placeholder="Enter your age"
              value={ageInput}
              onChange={(e) => setAgeInput(e.target.value)}
              className="flex-1 px-3 py-2 border border-yellow-300 rounded-lg focus:ring-2 focus:ring-yellow-500 focus:border-transparent"
              min="1"
              max="120"
            />
            <button
              onClick={handleAgeVerification}
              className="px-4 py-2 bg-yellow-600 text-white rounded-lg hover:bg-yellow-700 transition-colors"
            >
              Verify
            </button>
          </div>
          {ageVerificationError && (
            <p className="text-sm text-red-600 mt-2">{ageVerificationError}</p>
          )}
        </div>
      )}

      {preferences.ageVerified && (
        <div className="space-y-4 mb-6">
          <ConsentToggle
            id="location"
            label="Location Services"
            description="Allow access to your location to calculate travel times to gyms. Location data is used only for your current session and is not stored."
            icon={MapPin}
            enabled={preferences.location}
            onChange={(enabled) => updatePreference('location', enabled)}
          />

          <ConsentToggle
            id="analytics"
            label="Anonymous Analytics"
            description="Help improve the service by sharing anonymous usage patterns. No personal data is collected."
            icon={BarChart3}
            enabled={preferences.analytics}
            onChange={(enabled) => updatePreference('analytics', enabled)}
            disabled={isMinor}
          />

          <ConsentToggle
            id="notifications"
            label="Machine Availability Alerts"
            description="Receive notifications when your preferred machines become available."
            icon={Eye}
            enabled={preferences.notifications}
            onChange={(enabled) => updatePreference('notifications', enabled)}
            disabled={isMinor}
          />
        </div>
      )}

      {/* Summary */}
      {preferences.ageVerified && (
        <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h3 className="font-semibold text-blue-800 mb-2">Current Settings Summary</h3>
          <div className="space-y-1 text-sm">
            <div className="flex items-center gap-2">
              {preferences.location ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <X className="w-4 h-4 text-red-600" />
              )}
              <span className="text-blue-700">
                Location sharing: {preferences.location ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {preferences.analytics ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <X className="w-4 h-4 text-red-600" />
              )}
              <span className="text-blue-700">
                Anonymous analytics: {preferences.analytics ? 'Enabled' : 'Disabled'}
              </span>
            </div>
            <div className="flex items-center gap-2">
              {preferences.notifications ? (
                <Check className="w-4 h-4 text-green-600" />
              ) : (
                <X className="w-4 h-4 text-red-600" />
              )}
              <span className="text-blue-700">
                Notifications: {preferences.notifications ? 'Enabled' : 'Disabled'}
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Action Buttons */}
      {preferences.ageVerified && (
        <div className="flex flex-col sm:flex-row gap-3">
          <button
            onClick={savePreferences}
            disabled={!hasChanges}
            className={`flex-1 px-6 py-3 rounded-lg font-medium transition-colors ${
              hasChanges 
                ? 'bg-blue-600 text-white hover:bg-blue-700' 
                : 'bg-gray-300 text-gray-500 cursor-not-allowed'
            }`}
          >
            Save Preferences
          </button>
          
          <button
            onClick={withdrawAllConsent}
            className="flex-1 px-6 py-3 bg-red-600 text-white rounded-lg hover:bg-red-700 transition-colors font-medium"
          >
            Withdraw All Consent
          </button>
        </div>
      )}

      <div className="mt-4 text-xs text-gray-500">
        <p>
          Your privacy preferences are stored locally on your device. 
          Consent decisions are logged for legal compliance as required by Hong Kong PDPO.
        </p>
        <p className="mt-1">
          Last updated: {new Date().toLocaleDateString('en-HK')} | 
          Changes take effect immediately
        </p>
      </div>
    </div>
  );
}