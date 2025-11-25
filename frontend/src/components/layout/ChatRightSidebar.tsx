import React from 'react'
import { ChatPastChatsCard } from './ChatPastChatsCard'
import { ChatHelpfulTipsCard } from './ChatHelpfulTipsCard'

type Props = {
  onSelectSession: (sessionId: string) => void
}

export function ChatRightSidebar({ onSelectSession }: Props) {
  return (
    <div className="lg:sticky lg:top-24 space-y-6 h-fit">
      <ChatPastChatsCard onSelectSession={onSelectSession} />
      <ChatHelpfulTipsCard />
    </div>
  )
}
