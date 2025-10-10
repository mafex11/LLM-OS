"use client"

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'

interface ApiKeys {
  google_api_key: string
  elevenlabs_api_key: string
  deepgram_api_key: string
}

interface ApiKeyContextType {
  apiKeys: ApiKeys
  setApiKeys: (keys: ApiKeys) => void
  updateApiKey: (keyName: keyof ApiKeys, value: string) => void
  getApiKey: (keyName: keyof ApiKeys) => string
  hasApiKey: (keyName: keyof ApiKeys) => boolean
}

const ApiKeyContext = createContext<ApiKeyContextType | undefined>(undefined)

export function ApiKeyProvider({ children }: { children: ReactNode }) {
  const [apiKeys, setApiKeysState] = useState<ApiKeys>({
    google_api_key: "",
    elevenlabs_api_key: "",
    deepgram_api_key: ""
  })

  // Load API keys from localStorage on mount
  useEffect(() => {
    const loadApiKeys = () => {
      try {
        const saved = localStorage.getItem('apiKeys')
        if (saved) {
          const parsed = JSON.parse(saved)
          setApiKeysState(parsed)
        }
      } catch (error) {
        console.error('Failed to load API keys from localStorage:', error)
      }
    }

    loadApiKeys()
  }, [])

  // Save API keys to localStorage whenever they change
  useEffect(() => {
    try {
      localStorage.setItem('apiKeys', JSON.stringify(apiKeys))
    } catch (error) {
      console.error('Failed to save API keys to localStorage:', error)
    }
  }, [apiKeys])

  const setApiKeys = (keys: ApiKeys) => {
    setApiKeysState(keys)
  }

  const updateApiKey = (keyName: keyof ApiKeys, value: string) => {
    setApiKeysState(prev => ({
      ...prev,
      [keyName]: value
    }))
  }

  const getApiKey = (keyName: keyof ApiKeys): string => {
    return apiKeys[keyName] || ""
  }

  const hasApiKey = (keyName: keyof ApiKeys): boolean => {
    return !!(apiKeys[keyName] && apiKeys[keyName].trim() !== "")
  }

  return (
    <ApiKeyContext.Provider value={{
      apiKeys,
      setApiKeys,
      updateApiKey,
      getApiKey,
      hasApiKey
    }}>
      {children}
    </ApiKeyContext.Provider>
  )
}

export function useApiKeys() {
  const context = useContext(ApiKeyContext)
  if (context === undefined) {
    throw new Error('useApiKeys must be used within an ApiKeyProvider')
  }
  return context
}