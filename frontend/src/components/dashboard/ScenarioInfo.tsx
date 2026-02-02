'use client'

import { Info } from 'lucide-react'

interface ScenarioInfoProps {
  scenario: string
}

export function ScenarioInfo({ scenario }: ScenarioInfoProps) {
  const scenarios: Record<string, { description: string; color: string }> = {
    'Empty room': {
      description: 'No people detected in the monitored area',
      color: 'bg-gray-100 text-gray-800'
    },
    'One person moving': {
      description: 'Single person moving in the area',
      color: 'bg-blue-100 text-blue-800'
    },
    'Two people talking': {
      description: 'Two people present, minimal movement',
      color: 'bg-green-100 text-green-800'
    },
    'Three people sitting': {
      description: 'Three people present, stationary',
      color: 'bg-yellow-100 text-yellow-800'
    },
    'Multiple people': {
      description: 'Multiple people detected in the area',
      color: 'bg-red-100 text-red-800'
    }
  }

  const scenarioInfo = scenarios[scenario] || {
    description: 'Simulated scenario for testing',
    color: 'bg-purple-100 text-purple-800'
  }

  return (
    <div className="flex items-center space-x-3">
      <div className={`inline-flex items-center px-4 py-2 rounded-lg ${scenarioInfo.color} transition-all duration-300`}>
        <Info className="w-4 h-4 mr-2" />
        <span className="font-medium text-sm">{scenario}</span>
      </div>
      {scenario !== 'Unknown' && (
        <div className="text-sm text-gray-600 max-w-md">
          <p>{scenarioInfo.description}</p>
        </div>
      )}
    </div>
  )
}
