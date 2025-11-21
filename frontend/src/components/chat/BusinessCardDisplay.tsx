// BusinessCardDisplay component for showing creator business card
import React from 'react'
import { Card, CardHeader, CardTitle, CardContent } from '../ui'
import type { BusinessCard } from '../../types'

interface BusinessCardDisplayProps {
  businessCard: BusinessCard
  className?: string
}

export function BusinessCardDisplay({ businessCard, className = '' }: BusinessCardDisplayProps) {
  return (
    <Card className={`border-2 border-primary ${className}`}>
      <CardHeader>
        <CardTitle>Creator Found!</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {businessCard.name && (
            <div>
              <span className="font-semibold text-gray-700">Name:</span>
              <span className="ml-2 text-gray-900">{businessCard.name}</span>
            </div>
          )}

          {businessCard.email && (
            <div>
              <span className="font-semibold text-gray-700">Email:</span>
              <a
                href={`mailto:${businessCard.email}`}
                className="ml-2 text-primary hover:underline"
              >
                {businessCard.email}
              </a>
            </div>
          )}

          {businessCard.phone && (
            <div>
              <span className="font-semibold text-gray-700">Phone:</span>
              <a
                href={`tel:${businessCard.phone}`}
                className="ml-2 text-primary hover:underline"
              >
                {businessCard.phone}
              </a>
            </div>
          )}

          {businessCard.website && (
            <div>
              <span className="font-semibold text-gray-700">Website:</span>
              <a
                href={businessCard.website}
                target="_blank"
                rel="noopener noreferrer"
                className="ml-2 text-primary hover:underline"
              >
                {businessCard.website}
              </a>
            </div>
          )}

          {businessCard.social_links && businessCard.social_links.length > 0 && (
            <div>
              <span className="font-semibold text-gray-700">Social:</span>
              <div className="flex flex-wrap gap-2 mt-2">
                {businessCard.social_links.map((link, index) => (
                  <a
                    key={index}
                    href={link}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="px-3 py-1 bg-gray-100 text-primary rounded-full text-sm hover:bg-gray-200"
                  >
                    {new URL(link).hostname}
                  </a>
                ))}
              </div>
            </div>
          )}

          {businessCard.description && (
            <div className="pt-3 border-t border-gray-200">
              <p className="text-gray-700">{businessCard.description}</p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  )
}
