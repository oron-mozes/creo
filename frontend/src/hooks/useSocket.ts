// useSocket hook for Socket.IO connection management
import { useEffect, useState, useCallback } from 'react'
import { Socket } from 'socket.io-client'
import { socketService } from '../services/socketService'
import type { SocketEvents } from '../types'

export function useSocket() {
  const [socket, setSocket] = useState<Socket | null>(null)
  const [isConnected, setIsConnected] = useState(false)

  useEffect(() => {
    const newSocket = socketService.connect()
    setSocket(newSocket)

    const handleConnect = () => setIsConnected(true)
    const handleDisconnect = () => setIsConnected(false)

    newSocket.on('connect', handleConnect)
    newSocket.on('disconnect', handleDisconnect)

    // Set initial connection state
    setIsConnected(newSocket.connected)

    return () => {
      newSocket.off('connect', handleConnect)
      newSocket.off('disconnect', handleDisconnect)
      socketService.disconnect()
    }
  }, [])

  const emit = useCallback(<K extends keyof SocketEvents>(
    event: K,
    data: SocketEvents[K]
  ) => {
    socketService.emit(event, data)
  }, [])

  const on = useCallback(<K extends keyof SocketEvents>(
    event: K,
    callback: (data: SocketEvents[K]) => void
  ) => {
    socketService.on(event, callback)
  }, [])

  const off = useCallback(<K extends keyof SocketEvents>(
    event: K,
    callback?: (data: SocketEvents[K]) => void
  ) => {
    socketService.off(event, callback)
  }, [])

  return {
    socket,
    isConnected,
    emit,
    on,
    off,
  }
}
