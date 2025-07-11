import React from 'react'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Download, Heart, User, ChevronRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useModelStore } from '@/stores/modelStore'

export interface ModelRecommendation {
  model_id: string
  model_name: string
  description?: string
  tags: string[]
  downloads: number
  likes: number
  author?: string
}

interface ModelCardProps {
  model: ModelRecommendation
}

export const ModelCard: React.FC<ModelCardProps> = ({ model }) => {
  const navigate = useNavigate()
  const { setSelectedModel } = useModelStore()
  
  const handleSelectModel = () => {
    setSelectedModel(model)
    navigate('/dashboard')
  }
  
  const formatNumber = (num: number): string => {
    if (num >= 1000000) {
      return `${(num / 1000000).toFixed(1)}M`
    } else if (num >= 1000) {
      return `${(num / 1000).toFixed(1)}K`
    }
    return num.toString()
  }
  
  return (
    <Card className="hover:shadow-lg transition-shadow duration-200 border-gray-200">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <CardTitle className="text-lg font-semibold">{model.model_name}</CardTitle>
            {model.author && (
              <div className="flex items-center gap-1 text-sm text-gray-500 mt-1">
                <User className="h-3 w-3" />
                <span>{model.author}</span>
              </div>
            )}
          </div>
        </div>
      </CardHeader>
      
      <CardContent className="space-y-3">
        {model.description && (
          <CardDescription className="text-sm text-gray-600">
            {model.description}
          </CardDescription>
        )}
        
        <div className="flex flex-wrap gap-1">
          {model.tags.slice(0, 5).map((tag, index) => (
            <Badge key={index} variant="secondary" className="text-xs">
              {tag}
            </Badge>
          ))}
          {model.tags.length > 5 && (
            <Badge variant="outline" className="text-xs">
              +{model.tags.length - 5} more
            </Badge>
          )}
        </div>
        
        <div className="flex items-center gap-4 text-sm text-gray-600">
          <div className="flex items-center gap-1">
            <Download className="h-4 w-4" />
            <span>{formatNumber(model.downloads)}</span>
          </div>
          <div className="flex items-center gap-1">
            <Heart className="h-4 w-4" />
            <span>{formatNumber(model.likes)}</span>
          </div>
        </div>
      </CardContent>
      
      <CardFooter>
        <Button 
          onClick={handleSelectModel} 
          className="w-full bg-gray-900 hover:bg-gray-800"
        >
          Select & Continue
          <ChevronRight className="h-4 w-4 ml-2" />
        </Button>
      </CardFooter>
    </Card>
  )
} 