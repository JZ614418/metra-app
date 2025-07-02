import React from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'

interface SchemaDisplayProps {
  schema: any
}

const SchemaDisplay: React.FC<SchemaDisplayProps> = ({ schema }) => {
  // Helper function to display nested object values
  const renderValue = (value: any): React.ReactNode => {
    if (value === null || value === undefined) {
      return <span className="text-gray-400">N/A</span>
    }
    
    if (typeof value === 'object' && !Array.isArray(value)) {
      return (
        <div className="ml-4 mt-1 space-y-1">
          {Object.entries(value).map(([key, val]) => (
            <div key={key} className="flex gap-2">
              <span className="text-gray-600">{key}:</span>
              {renderValue(val)}
            </div>
          ))}
        </div>
      )
    }
    
    if (Array.isArray(value)) {
      return (
        <div className="flex gap-1 flex-wrap">
          {value.map((item, index) => (
            <Badge key={index} variant="outline" className="text-xs">
              {item}
            </Badge>
          ))}
        </div>
      )
    }
    
    return <span className="text-gray-800 font-medium">{String(value)}</span>
  }
  
  // Extract main fields to display
  const mainFields = ['task_name', 'task_type', 'domain', 'language', 'input_type', 'output_type']
  const additionalFields = Object.keys(schema).filter(key => !mainFields.includes(key))
  
  return (
    <div className="space-y-4">
      {/* Main fields */}
      <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
        {mainFields.map(field => {
          if (schema[field] !== undefined) {
            return (
              <div key={field}>
                <p className="text-sm text-gray-500 capitalize">
                  {field.replace(/_/g, ' ')}
                </p>
                <p className="font-medium text-gray-900">
                  {renderValue(schema[field])}
                </p>
              </div>
            )
          }
          return null
        })}
      </div>
      
      {/* Additional fields */}
      {additionalFields.length > 0 && (
        <div className="border-t pt-4 space-y-2">
          {additionalFields.map(field => (
            <div key={field}>
              <p className="text-sm text-gray-500 capitalize">
                {field.replace(/_/g, ' ')}
              </p>
              <div className="mt-1">
                {renderValue(schema[field])}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}

export default SchemaDisplay 