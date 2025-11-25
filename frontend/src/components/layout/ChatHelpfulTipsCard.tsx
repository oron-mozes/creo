import React from 'react'

const tips = [
  'Share your budget range so we can filter the right creators.',
  'Tell us your target audience (age, location, interests) for better matches.',
  'Provide a website or socials to personalize outreach.',
  'Confirm business details once to skip repeated questions.',
]

export function ChatHelpfulTipsCard() {
  return (
    <div className="bg-white p-6 border border-gray-200 rounded-3xl shadow-sm animate-fade-in">
      <h3 className="font-semibold mb-5 flex items-center gap-2 text-lg">
        <svg className="h-5 w-5" style={{ color: 'rgb(0, 160, 235)' }} fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M13 16h-1v-4h-1m1-4h.01M12 18.5A6.5 6.5 0 1 0 12 5.5a6.5 6.5 0 0 0 0 13z" />
        </svg>
        Helpful Tips
      </h3>
      <ul className="space-y-3 text-sm text-gray-700">
        {tips.map((tip, idx) => (
          <li key={idx} className="flex gap-2">
            <span className="text-blue-500">•</span>
            <span>{tip}</span>
          </li>
        ))}
      </ul>
    </div>
  )
}
