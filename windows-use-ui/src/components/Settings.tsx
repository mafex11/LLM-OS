'use client'

import { useState } from 'react'

interface SettingsData {
  enable_tts: boolean
  tts_voice_id: string
  cache_timeout: number
  max_steps: number
}

export default function Settings() {
  const [settings, setSettings] = useState<SettingsData>({
    enable_tts: true,
    tts_voice_id: '21m00Tcm4TlvDq8ikWAM',
    cache_timeout: 2.0,
    max_steps: 30
  })
  const [isLoading, setIsLoading] = useState(false)
  const [message, setMessage] = useState<{ type: 'success' | 'error', text: string } | null>(null)

  const handleSave = async () => {
    setIsLoading(true)
    setMessage(null)
    
    try {
      const response = await fetch('http://localhost:8000/api/settings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(settings),
      })

      if (!response.ok) {
        throw new Error('Failed to update settings')
      }

      setMessage({ type: 'success', text: 'Settings updated successfully!' })
    } catch (error) {
      setMessage({ 
        type: 'error', 
        text: error instanceof Error ? error.message : 'Unknown error' 
      })
    } finally {
      setIsLoading(false)
    }
  }

  const handleReset = () => {
    setSettings({
      enable_tts: true,
      tts_voice_id: '21m00Tcm4TlvDq8ikWAM',
      cache_timeout: 2.0,
      max_steps: 30
    })
  }

  return (
    <div className="max-w-2xl">
      <div className="bg-white rounded-lg shadow-sm border p-6">
        <h2 className="text-lg font-semibold text-gray-900 mb-6">Settings</h2>

        {/* Message Display */}
        {message && (
          <div className={`mb-4 p-3 rounded ${
            message.type === 'success' 
              ? 'bg-green-100 text-green-700 border border-green-200' 
              : 'bg-red-100 text-red-700 border border-red-200'
          }`}>
            {message.text}
          </div>
        )}

        <div className="space-y-6">
          {/* Text-to-Speech Settings */}
          <div className="border-b pb-6">
            <h3 className="text-md font-medium text-gray-900 mb-4">Text-to-Speech</h3>
            
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <label className="text-sm font-medium text-gray-700">
                    Enable TTS
                  </label>
                  <p className="text-xs text-gray-500">
                    Allow the agent to speak responses
                  </p>
                </div>
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={settings.enable_tts}
                    onChange={(e) => setSettings(prev => ({ ...prev, enable_tts: e.target.checked }))}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-blue-600"></div>
                </label>
              </div>

              {settings.enable_tts && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Voice ID
                  </label>
                  <input
                    type="text"
                    value={settings.tts_voice_id}
                    onChange={(e) => setSettings(prev => ({ ...prev, tts_voice_id: e.target.value }))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    placeholder="Enter ElevenLabs voice ID"
                  />
                  <p className="text-xs text-gray-500 mt-1">
                    Default: 21m00Tcm4TlvDq8ikWAM (Rachel)
                  </p>
                </div>
              )}
            </div>
          </div>

          {/* Performance Settings */}
          <div className="border-b pb-6">
            <h3 className="text-md font-medium text-gray-900 mb-4">Performance</h3>
            
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Cache Timeout (seconds)
                </label>
                <input
                  type="number"
                  min="0.1"
                  max="10"
                  step="0.1"
                  value={settings.cache_timeout}
                  onChange={(e) => setSettings(prev => ({ ...prev, cache_timeout: parseFloat(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  How long to cache screenshots and app data (lower = more responsive, higher = faster)
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Max Steps
                </label>
                <input
                  type="number"
                  min="5"
                  max="100"
                  value={settings.max_steps}
                  onChange={(e) => setSettings(prev => ({ ...prev, max_steps: parseInt(e.target.value) }))}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">
                  Maximum number of steps the agent can take per query
                </p>
              </div>
            </div>
          </div>

          {/* Advanced Actions */}
          <div>
            <h3 className="text-md font-medium text-gray-900 mb-4">Advanced</h3>
            
            <div className="grid grid-cols-2 gap-4">
              <button
                onClick={() => {
                  // Clear conversation
                  fetch('http://localhost:8000/api/conversation/clear', { method: 'POST' })
                    .then(() => setMessage({ type: 'success', text: 'Conversation cleared' }))
                    .catch(() => setMessage({ type: 'error', text: 'Failed to clear conversation' }))
                }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
              >
                Clear Conversation
              </button>
              
              <button
                onClick={() => {
                  // Clear memories
                  fetch('http://localhost:8000/api/memories/clear', { method: 'POST' })
                    .then(() => setMessage({ type: 'success', text: 'Memories cleared' }))
                    .catch(() => setMessage({ type: 'error', text: 'Failed to clear memories' }))
                }}
                className="px-4 py-2 bg-gray-100 text-gray-700 rounded hover:bg-gray-200 transition-colors"
              >
                Clear Memories
              </button>
            </div>
          </div>
        </div>

        {/* Action Buttons */}
        <div className="flex justify-between items-center pt-6 border-t">
          <button
            onClick={handleReset}
            className="px-4 py-2 text-gray-700 bg-gray-100 rounded hover:bg-gray-200 transition-colors"
          >
            Reset to Defaults
          </button>
          
          <button
            onClick={handleSave}
            disabled={isLoading}
            className="px-6 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isLoading ? 'Saving...' : 'Save Settings'}
          </button>
        </div>
      </div>
    </div>
  )
}