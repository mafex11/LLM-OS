'use client'

import { useState } from 'react'

interface Program {
  name: string
  title: string
  id: string
}

interface RunningProgramsProps {
  programs: Program[]
}

export default function RunningPrograms({ programs }: RunningProgramsProps) {
  const [refreshedPrograms, setRefreshedPrograms] = useState<Program[]>(programs)
  const [isRefreshing, setIsRefreshing] = useState(false)

  const refreshPrograms = async () => {
    setIsRefreshing(true)
    try {
      const response = await fetch('http://localhost:8000/api/programs')
      if (response.ok) {
        const data = await response.json()
        setRefreshedPrograms(data)
      }
    } catch (error) {
      console.error('Failed to refresh programs:', error)
    } finally {
      setIsRefreshing(false)
    }
  }

  // Group programs by name
  const groupedPrograms = refreshedPrograms.reduce((acc, program) => {
    if (!acc[program.name]) {
      acc[program.name] = []
    }
    acc[program.name].push(program)
    return acc
  }, {} as Record<string, Program[]>)

  return (
    <div className="bg-white rounded-lg shadow-sm border">
      <div className="flex justify-between items-center p-6 border-b">
        <h2 className="text-lg font-semibold text-gray-900">Running Programs</h2>
        <button
          onClick={refreshPrograms}
          disabled={isRefreshing}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          {isRefreshing ? (
            <>
              <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></span>
              Refreshing...
            </>
          ) : (
            'Refresh'
          )}
        </button>
      </div>

      <div className="p-6">
        {Object.keys(groupedPrograms).length === 0 ? (
          <div className="text-center text-gray-500 py-8">
            <div className="text-4xl mb-2">🖥️</div>
            <p>No programs with visible windows detected</p>
            <p className="text-sm mt-1">Click refresh to scan for running applications</p>
          </div>
        ) : (
          <div className="space-y-4">
            {Object.entries(groupedPrograms).map(([name, instances]) => (
              <div key={name} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-3">
                  <h3 className="font-medium text-gray-900 capitalize">
                    {name.replace('.exe', '')}
                  </h3>
                  <span className="text-sm text-gray-500">
                    {instances.length} instance{instances.length > 1 ? 's' : ''}
                  </span>
                </div>
                
                <div className="space-y-2">
                  {instances.map((instance, index) => (
                    <div key={`${instance.id}-${index}`} className="flex items-center justify-between bg-gray-50 rounded p-2">
                      <div className="flex-1 min-w-0">
                        <div className="text-sm text-gray-900 truncate">
                          {instance.title || instance.name}
                        </div>
                        <div className="text-xs text-gray-500">
                          Process ID: {instance.id}
                        </div>
                      </div>
                      <div className="flex items-center space-x-2 ml-3">
                        <div className="w-2 h-2 bg-green-500 rounded-full" title="Running"></div>
                        <button
                          onClick={() => {
                            // This would trigger a command to focus/switch to this program
                            console.log('Switch to:', instance.name)
                          }}
                          className="text-xs px-2 py-1 bg-blue-100 text-blue-700 rounded hover:bg-blue-200 transition-colors"
                        >
                          Focus
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Quick Actions */}
        <div className="mt-6 pt-6 border-t">
          <h3 className="text-sm font-medium text-gray-700 mb-3">Quick Actions</h3>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            {[
              { label: 'Open Notepad', command: 'open notepad' },
              { label: 'Open Calculator', command: 'open calculator' },
              { label: 'Open Browser', command: 'open chrome' },
              { label: 'Show Desktop', command: 'show desktop' }
            ].map((action) => (
              <button
                key={action.label}
                onClick={() => {
                  // This would send the command to the agent
                  console.log('Execute command:', action.command)
                }}
                className="px-3 py-2 text-xs bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
              >
                {action.label}
              </button>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}