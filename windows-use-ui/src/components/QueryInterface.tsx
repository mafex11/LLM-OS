'use client'

import { useState } from 'react'

interface QueryInterfaceProps {
  onSubmit: (query: string) => void
  disabled?: boolean
}

export default function QueryInterface({ onSubmit, disabled = false }: QueryInterfaceProps) {
  const [query, setQuery] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!query.trim() || disabled || isSubmitting) return

    setIsSubmitting(true)
    try {
      await onSubmit(query.trim())
      setQuery('')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSubmit(e)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-sm border p-6">
      <h2 className="text-lg font-semibold text-gray-900 mb-4">Send Query</h2>
      
      <form onSubmit={handleSubmit} className="space-y-4">
        <div>
          <textarea
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Enter your command or question for the Windows-Use agent..."
            className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 resize-none"
            rows={3}
            disabled={disabled || isSubmitting}
          />
          <p className="mt-1 text-sm text-gray-500">
            Press Enter to send, Shift+Enter for new line
          </p>
        </div>
        
        <div className="flex justify-between items-center">
          <div className="text-sm text-gray-500">
            {disabled ? 'Agent not ready' : 'Ready to process commands'}
          </div>
          
          <button
            type="submit"
            disabled={!query.trim() || disabled || isSubmitting}
            className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            {isSubmitting ? (
              <>
                <span className="animate-spin inline-block w-4 h-4 border-2 border-white border-t-transparent rounded-full mr-2"></span>
                Processing...
              </>
            ) : (
              'Send Query'
            )}
          </button>
        </div>
      </form>

      {/* Quick Commands */}
      <div className="mt-6 pt-4 border-t">
        <h3 className="text-sm font-medium text-gray-700 mb-2">Quick Commands</h3>
        <div className="flex flex-wrap gap-2">
          {[
            'Open notepad',
            'Take a screenshot',
            'Show running programs',
            'Clear conversation',
            'Get system info'
          ].map((cmd) => (
            <button
              key={cmd}
              onClick={() => setQuery(cmd)}
              className="px-3 py-1 text-xs bg-gray-100 text-gray-700 rounded-full hover:bg-gray-200 transition-colors"
              disabled={disabled || isSubmitting}
            >
              {cmd}
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}