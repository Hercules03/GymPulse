import React from 'react';
import { Shield, MapPin, Clock, Database, AlertCircle } from 'lucide-react';

interface PrivacyNoticeProps {
  onAccept: () => void;
  onDecline: () => void;
  showLocationConsent?: boolean;
}

export default function PrivacyNotice({ onAccept, onDecline, showLocationConsent = true }: PrivacyNoticeProps) {
  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl max-h-[90vh] overflow-y-auto m-4">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center gap-3 mb-4">
            <Shield className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-semibold text-gray-900">Privacy Notice</h2>
          </div>
          
          {/* Purpose */}
          <div className="mb-6">
            <p className="text-gray-700 mb-4">
              GymPulse helps you find available gym equipment in real-time. We are committed to protecting 
              your privacy and following Hong Kong's Personal Data (Privacy) Ordinance (PDPO).
            </p>
          </div>
          
          {/* Data Collection */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Database className="w-5 h-5 text-blue-600" />
              What Data We Collect
            </h3>
            
            <div className="space-y-3 ml-7">
              <div className="flex items-start gap-2">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-800">Machine Occupancy Data</p>
                  <p className="text-sm text-gray-600">
                    We collect anonymous equipment availability status (occupied/free) to show real-time availability. 
                    No personal information is collected from gym equipment.
                  </p>
                </div>
              </div>
              
              {showLocationConsent && (
                <div className="flex items-start gap-2">
                  <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                  <div>
                    <p className="font-medium text-gray-800">Location Data (Optional)</p>
                    <p className="text-sm text-gray-600">
                      With your consent, we use your location to calculate travel times to nearby gyms. 
                      Location data is used only for your current session and is not stored permanently.
                    </p>
                  </div>
                </div>
              )}
              
              <div className="flex items-start gap-2">
                <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
                <div>
                  <p className="font-medium text-gray-800">Usage Analytics</p>
                  <p className="text-sm text-gray-600">
                    We collect anonymous usage patterns to improve availability predictions. 
                    No individual user behavior is tracked.
                  </p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Location Privacy */}
          {showLocationConsent && (
            <div className="mb-6 p-4 bg-amber-50 border border-amber-200 rounded-lg">
              <div className="flex items-start gap-3">
                <MapPin className="w-5 h-5 text-amber-600 mt-0.5" />
                <div>
                  <h4 className="font-semibold text-amber-800">Location Privacy</h4>
                  <ul className="text-sm text-amber-700 mt-1 space-y-1">
                    <li>• Location is only used to calculate travel times</li>
                    <li>• Your precise location is rounded to protect privacy</li>
                    <li>• Location data is deleted when you close the app</li>
                    <li>• You can use the app without sharing your location</li>
                  </ul>
                </div>
              </div>
            </div>
          )}
          
          {/* Data Retention */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3 flex items-center gap-2">
              <Clock className="w-5 h-5 text-blue-600" />
              How Long We Keep Data
            </h3>
            
            <div className="ml-7 space-y-2">
              <p className="text-sm text-gray-600">• Machine availability: Real-time only</p>
              <p className="text-sm text-gray-600">• Historical patterns: 30 days for forecasting</p>
              <p className="text-sm text-gray-600">• Your location: Current session only</p>
              <p className="text-sm text-gray-600">• Aggregated statistics: 90 days for service improvement</p>
            </div>
          </div>
          
          {/* Your Rights */}
          <div className="mb-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-3">Your Rights Under PDPO</h3>
            
            <div className="ml-0 space-y-2">
              <p className="text-sm text-gray-600">
                • <strong>Access:</strong> Request information about data we process
              </p>
              <p className="text-sm text-gray-600">
                • <strong>Correction:</strong> Request correction of inaccurate data
              </p>
              <p className="text-sm text-gray-600">
                • <strong>Erasure:</strong> Request deletion of your data
              </p>
              <p className="text-sm text-gray-600">
                • <strong>Withdraw Consent:</strong> Stop location sharing at any time
              </p>
            </div>
          </div>
          
          {/* Legal Basis */}
          <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
            <h4 className="font-semibold text-blue-800 mb-2">Legal Basis for Processing</h4>
            <p className="text-sm text-blue-700">
              We process equipment availability data based on legitimate interest to provide 
              the gym availability service. Location data is processed only with your explicit consent.
            </p>
          </div>
          
          {/* Important Notice */}
          <div className="mb-6 p-4 bg-gray-50 border border-gray-200 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-gray-600 mt-0.5" />
              <div>
                <h4 className="font-semibold text-gray-800">Important</h4>
                <p className="text-sm text-gray-600 mt-1">
                  This service is designed with privacy-by-design principles. We collect only 
                  the minimum data necessary to provide gym availability information and use 
                  automated data deletion to protect your privacy.
                </p>
              </div>
            </div>
          </div>
          
          {/* Contact */}
          <div className="mb-6">
            <h4 className="font-medium text-gray-800 mb-2">Questions or Concerns?</h4>
            <p className="text-sm text-gray-600">
              If you have questions about this privacy notice or want to exercise your rights, 
              please contact us through the app's support section.
            </p>
          </div>
          
          {/* Action Buttons */}
          <div className="flex flex-col sm:flex-row gap-3 pt-4 border-t border-gray-200">
            <button
              onClick={onAccept}
              className="flex-1 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors font-medium"
            >
              Accept and Continue
            </button>
            <button
              onClick={onDecline}
              className="flex-1 bg-gray-200 text-gray-800 px-6 py-3 rounded-lg hover:bg-gray-300 transition-colors font-medium"
            >
              Decline
            </button>
          </div>
          
          <p className="text-xs text-gray-500 mt-3 text-center">
            Last updated: {new Date().toLocaleDateString('en-HK')} | 
            Compliant with Hong Kong PDPO
          </p>
        </div>
      </div>
    </div>
  );
}