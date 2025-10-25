"use client"

import { useState, useEffect, useCallback } from "react"

export interface AudioDevice {
  deviceId: string
  label: string
  kind: MediaDeviceKind
}

export interface AudioDeviceState {
  inputDevices: AudioDevice[]
  outputDevices: AudioDevice[]
  selectedInputDevice: string | null
  selectedOutputDevice: string | null
  hasPermission: boolean
  isLoading: boolean
  error: string | null
}

export const useAudioDevices = () => {
  const [state, setState] = useState<AudioDeviceState>({
    inputDevices: [],
    outputDevices: [],
    selectedInputDevice: null,
    selectedOutputDevice: null,
    hasPermission: false,
    isLoading: false,
    error: null
  })

  const checkPermission = useCallback(async () => {
    try {
      const result = await navigator.permissions.query({ name: 'microphone' as PermissionName })
      return result.state === 'granted'
    } catch (error) {
      // Fallback for browsers that don't support permissions API
      return false
    }
  }, [])

  const requestPermission = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    
    try {
      // Check if we're in Electron app
      const isElectron = typeof window !== 'undefined' && window.electronAPI
      
      if (isElectron) {
        // Use Electron API for microphone permission
        const granted = await window.electronAPI.requestMicrophonePermission()
        setState(prev => ({ 
          ...prev, 
          hasPermission: granted,
          isLoading: false 
        }))
        
        if (granted) {
          await enumerateDevices()
        }
        
        return granted
      } else {
        // Use browser API for microphone permission
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true })
        // Stop the stream immediately as we only needed it for permission
        stream.getTracks().forEach(track => track.stop())
        
        const hasPermission = await checkPermission()
        setState(prev => ({ 
          ...prev, 
          hasPermission,
          isLoading: false 
        }))
        
        if (hasPermission) {
          await enumerateDevices()
        }
        
        return hasPermission
      }
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to request microphone permission'
      setState(prev => ({ 
        ...prev, 
        error: errorMessage,
        isLoading: false 
      }))
      return false
    }
  }, [checkPermission])

  const enumerateDevices = useCallback(async () => {
    setState(prev => ({ ...prev, isLoading: true, error: null }))
    
    try {
      // Check if we're in Electron app
      const isElectron = typeof window !== 'undefined' && window.electronAPI
      
      let devices
      if (isElectron) {
        // Use Electron API for device enumeration
        devices = await window.electronAPI.getAudioDevices()
      } else {
        // Use browser API for device enumeration
        devices = await navigator.mediaDevices.enumerateDevices()
      }
      
      const inputDevices = devices
        .filter(device => device.kind === 'audioinput')
        .map(device => ({
          deviceId: device.deviceId,
          label: device.label || `Microphone ${device.deviceId.slice(0, 8)}`,
          kind: device.kind
        }))
      
      const outputDevices = devices
        .filter(device => device.kind === 'audiooutput')
        .map(device => ({
          deviceId: device.deviceId,
          label: device.label || `Speaker ${device.deviceId.slice(0, 8)}`,
          kind: device.kind
        }))
      
      setState(prev => ({
        ...prev,
        inputDevices,
        outputDevices,
        selectedInputDevice: inputDevices[0]?.deviceId || null,
        selectedOutputDevice: outputDevices[0]?.deviceId || null,
        isLoading: false
      }))
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'Failed to enumerate audio devices'
      setState(prev => ({ 
        ...prev, 
        error: errorMessage,
        isLoading: false 
      }))
    }
  }, [])

  const setSelectedInputDevice = useCallback((deviceId: string) => {
    setState(prev => ({ ...prev, selectedInputDevice: deviceId }))
  }, [])

  const setSelectedOutputDevice = useCallback((deviceId: string) => {
    setState(prev => ({ ...prev, selectedOutputDevice: deviceId }))
  }, [])

  const refreshDevices = useCallback(async () => {
    const hasPermission = await checkPermission()
    if (hasPermission) {
      await enumerateDevices()
    }
  }, [checkPermission, enumerateDevices])

  useEffect(() => {
    const initializeDevices = async () => {
      const hasPermission = await checkPermission()
      setState(prev => ({ ...prev, hasPermission }))
      
      if (hasPermission) {
        await enumerateDevices()
      }
    }

    initializeDevices()

    // Listen for device changes
    const handleDeviceChange = () => {
      if (state.hasPermission) {
        enumerateDevices()
      }
    }

    navigator.mediaDevices.addEventListener('devicechange', handleDeviceChange)
    
    return () => {
      navigator.mediaDevices.removeEventListener('devicechange', handleDeviceChange)
    }
  }, [checkPermission, enumerateDevices, state.hasPermission])

  return {
    ...state,
    requestPermission,
    setSelectedInputDevice,
    setSelectedOutputDevice,
    refreshDevices
  }
}
