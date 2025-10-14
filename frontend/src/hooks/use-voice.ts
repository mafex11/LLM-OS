"use client"

import { useState, useRef, useCallback } from 'react'
import { useToast } from '@/hooks/use-toast'

interface VoiceRecorderOptions {
  onTranscript?: (transcript: string) => void
  onError?: (error: string) => void
  onStart?: () => void
  onStop?: () => void
}

export function useVoice(options: VoiceRecorderOptions = {}) {
  const [isRecording, setIsRecording] = useState(false)
  const [isSupported, setIsSupported] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const mediaRecorderRef = useRef<MediaRecorder | null>(null)
  const audioChunksRef = useRef<Blob[]>([])
  const streamRef = useRef<MediaStream | null>(null)
  const { toast } = useToast()

  // Check if browser supports required APIs
  const checkSupport = useCallback(() => {
    const supported = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia && window.MediaRecorder)
    setIsSupported(supported)
    return supported
  }, [])

  const startRecording = useCallback(async () => {
    try {
      setError(null)
      
      if (!checkSupport()) {
        throw new Error('Your browser does not support voice recording')
      }

      // Request microphone permission
      const stream = await navigator.mediaDevices.getUserMedia({ 
        audio: {
          echoCancellation: true,
          noiseSuppression: true,
          sampleRate: 16000
        } 
      })
      
      streamRef.current = stream
      audioChunksRef.current = []

      // Create MediaRecorder
      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: 'audio/webm;codecs=opus'
      })
      
      mediaRecorderRef.current = mediaRecorder

      // Handle data available
      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data)
        }
      }

      // Handle recording stop
      mediaRecorder.onstop = async () => {
        try {
          const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' })
          await processAudio(audioBlob)
        } catch (err) {
          console.error('Error processing audio:', err)
          options.onError?.(err instanceof Error ? err.message : 'Failed to process audio')
        }
      }

      // Start recording
      mediaRecorder.start(1000) // Collect data every second
      setIsRecording(true)
      options.onStart?.()

      toast({
        title: "Voice Recording Started",
        description: "Listening for your voice...",
      })

    } catch (err) {
      console.error('Error starting recording:', err)
      let errorMessage = 'Failed to start voice recording'
      
      if (err instanceof Error) {
        if (err.name === 'NotAllowedError') {
          errorMessage = 'Microphone access denied. Please allow microphone access and try again.'
        } else if (err.name === 'NotFoundError') {
          errorMessage = 'No microphone found. Please connect a microphone and try again.'
        } else if (err.name === 'NotSupportedError') {
          errorMessage = 'Voice recording is not supported in this browser.'
        } else {
          errorMessage = err.message
        }
      }
      
      setError(errorMessage)
      options.onError?.(errorMessage)
      
      toast({
        title: "Voice Recording Failed",
        description: errorMessage,
        variant: "destructive"
      })
    }
  }, [checkSupport, options, toast])

  const stopRecording = useCallback(() => {
    try {
      if (mediaRecorderRef.current && isRecording) {
        mediaRecorderRef.current.stop()
      }
      
      if (streamRef.current) {
        streamRef.current.getTracks().forEach(track => track.stop())
        streamRef.current = null
      }
      
      setIsRecording(false)
      options.onStop?.()

      toast({
        title: "Voice Recording Stopped",
        description: "Processing your audio...",
      })

    } catch (err) {
      console.error('Error stopping recording:', err)
      setError('Failed to stop recording')
    }
  }, [isRecording, options, toast])

  const processAudio = async (audioBlob: Blob) => {
    try {
      // Convert blob to base64
      const arrayBuffer = await audioBlob.arrayBuffer()
      const base64Audio = btoa(String.fromCharCode(...new Uint8Array(arrayBuffer)))
      
      // Send to backend for transcription
      const response = await fetch('http://localhost:8000/api/voice/transcribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          audio_data: base64Audio,
          mime_type: 'audio/webm'
        })
      })

      if (!response.ok) {
        throw new Error(`Transcription failed: ${response.statusText}`)
      }

      const result = await response.json()
      
      if (result.transcript) {
        options.onTranscript?.(result.transcript)
        toast({
          title: "Voice Command Received",
          description: `"${result.transcript}"`,
        })
      } else {
        throw new Error('No transcript received')
      }

    } catch (err) {
      console.error('Error processing audio:', err)
      const errorMsg = err instanceof Error ? err.message : 'Failed to process audio'
      options.onError?.(errorMsg)
      
      toast({
        title: "Transcription Failed",
        description: errorMsg,
        variant: "destructive"
      })
    }
  }

  const toggleRecording = useCallback(() => {
    if (isRecording) {
      stopRecording()
    } else {
      startRecording()
    }
  }, [isRecording, startRecording, stopRecording])

  return {
    isRecording,
    isSupported,
    error,
    startRecording,
    stopRecording,
    toggleRecording,
    checkSupport
  }
}
