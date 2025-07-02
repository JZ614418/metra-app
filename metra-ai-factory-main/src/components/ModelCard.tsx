import React from 'react'
import { Card, CardContent, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Download, Heart, User, ArrowRight } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useModelStore, ModelRecommendation } from '@/stores/modelStore'

interface ModelCardProps {
  model: ModelRecommendation
}

export const ModelCard: React.FC<ModelCardProps> = ({ model }) => {
  const navigate = useNavigate()
  const { setSelectedModel } = useModelStore()
  
  const handleSelectModel = () => {
    setSelectedModel(model)
    navigate('/data-builder')
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
    <Card className="hover:shadow-lg transition-shadow duration-200">
      <CardHeader>
        <CardTitle className="text-lg font-semibold flex items-center justify-between">
          <span className="truncate">{model.model_name}</span>
          {model.author && (
            <div className="flex items-center gap-1 text-sm text-gray-500">
              <User className="h-3 w-3" />
              <span>{model.author}</span>
            </div>
          )}
        </CardTitle>
      </CardHeader>
      
      <CardContent className="space-y-4">
        <p className="text-sm text-gray-600">
          {model.description || 'No description available'}
        </p>
        
        <div className="flex flex-wrap gap-2">
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
        
        <div className="flex items-center gap-4 text-sm text-gray-500">
          <div className="flex items-center gap-1">
            <Download className="h-4 w-4" />
            <span>{formatNumber(model.downloads)} downloads</span>
          </div>
          <div className="flex items-center gap-1">
            <Heart className="h-4 w-4" />
            <span>{formatNumber(model.likes)} likes</span>
          </div>
        </div>
      </CardContent>
      
      <CardFooter>
        <Button 
          onClick={handleSelectModel} 
          className="w-full bg-gray-900 hover:bg-gray-800"
        >
          Select & Continue
          <ArrowRight className="ml-2 h-4 w-4" />
        </Button>
      </CardFooter>
    </Card>
  )
} 