'use client'

interface SystemStatusData {
  agent_ready: boolean
  running_programs: Array<{
    name: string
    title: string
    id: string
  }>
  memory_stats: Record<string, any>
  performance_stats: Record<string, any>
}

interface SystemStatusProps {
  status: SystemStatusData | null
}

export default function SystemStatus({ status }: SystemStatusProps) {
  if (!status) {
    return (
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">System Status</h2>
        <div className="animate-pulse space-y-3">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-3/4"></div>
          <div className="h-4 bg-gray-200 rounded w-1/2"></div>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      {/* Agent Status */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Agent Status</h2>
        <div className="flex items-center space-x-3">
          <div className={`w-3 h-3 rounded-full ${status.agent_ready ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span className="text-sm font-medium">
            {status.agent_ready ? 'Agent Ready' : 'Agent Not Ready'}
          </span>
        </div>
      </div>

      {/* Memory Stats */}
      {status.memory_stats && Object.keys(status.memory_stats).length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Memory Statistics</h2>
          <div className="space-y-2">
            {Object.entries(status.memory_stats).map(([key, value]) => (
              <div key={key} className="flex justify-between text-sm">
                <span className="text-gray-600 capitalize">{key.replace('_', ' ')}:</span>
                <span className="font-medium">{value}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Performance Stats */}
      {status.performance_stats && Object.keys(status.performance_stats).length > 0 && (
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Performance</h2>
          <div className="space-y-3">
            {Object.entries(status.performance_stats).map(([category, stats]: [string, any]) => (
              <div key={category} className="border-l-4 border-blue-500 pl-3">
                <h3 className="text-sm font-medium text-gray-900 capitalize">
                  {category.replace('_', ' ')}
                </h3>
                {typeof stats === 'object' && stats !== null ? (
                  <div className="mt-1 space-y-1">
                    {Object.entries(stats).map(([key, value]: [string, any]) => (
                      <div key={key} className="flex justify-between text-xs text-gray-600">
                        <span className="capitalize">{key.replace('_', ' ')}:</span>
                        <span>{value}</span>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-xs text-gray-600 mt-1">{stats}</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Running Programs Summary */}
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-4">Running Programs</h2>
        <div className="flex items-center justify-between">
          <span className="text-sm text-gray-600">
            {status.running_programs.length} programs detected
          </span>
          <div className="text-2xl">🖥️</div>
        </div>
        {status.running_programs.length > 0 && (
          <div className="mt-3 text-xs text-gray-500">
            <div className="truncate">
              {status.running_programs.slice(0, 3).map(prog => prog.name).join(', ')}
              {status.running_programs.length > 3 && ` +${status.running_programs.length - 3} more`}
            </div>
          </div>
        )}
      </div>
    </div>
  )
}