'use client'

import { DetectionData } from '@/types/detection'

interface TechnicalDetailsProps {
  detection: DetectionData | null
}

export function TechnicalDetails({ detection }: TechnicalDetailsProps) {
  if (!detection) {
    return null
  }

  return (
    <details className="mt-6 bg-white rounded-lg shadow">
      <summary className="cursor-pointer p-4 text-sm font-medium text-gray-700 hover:text-gray-900 select-none">
        <div className="flex items-center">
          <svg className="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          Show Technical Details
        </div>
      </summary>
      <div className="p-6 pt-0 border-t border-gray-200">
        <h3 className="text-lg font-semibold mb-4 mt-4">Detection Features</h3>
        <div className="space-y-4">
          {/* Timestamp */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Timestamp</h4>
            <p className="text-sm text-gray-900 font-mono">{detection.timestamp}</p>
          </div>

          {/* Scenario */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Scenario</h4>
            <p className="text-sm text-gray-900">{detection.scenario}</p>
          </div>

          {/* Features */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Feature Vector</h4>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-2 text-xs">
              {Object.entries(detection.features).map(([key, value]) => (
                <div key={key} className="flex justify-between bg-white p-2 rounded border border-gray-200">
                  <span className="font-mono text-gray-600">{key}:</span>
                  <span className="font-mono font-medium text-gray-900">{value.toFixed(4)}</span>
                </div>
              ))}
            </div>
          </div>

          {/* Raw JSON */}
          <div className="bg-gray-50 rounded-lg p-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2">Raw Data</h4>
            <pre className="bg-white p-4 rounded overflow-x-auto text-xs border border-gray-200">
              {JSON.stringify(detection, null, 2)}
            </pre>
          </div>
        </div>
      </div>
    </details>
  )
}
